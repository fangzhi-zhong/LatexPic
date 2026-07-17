from __future__ import annotations

import queue
import sys
import threading
import traceback
import tkinter as tk
from tkinter import messagebox, ttk

import keyboard
import pystray
from PIL import Image, ImageDraw, ImageGrab

from .recognizer import ApiFormulaRecognizer
from .settings import configure_startup, load_api_key, load_settings, save_api_key, save_settings


class LatexPicApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("LatexPic - 截图公式转 LaTeX")
        self.root.geometry("560x440")
        self.root.minsize(520, 410)
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)

        self.settings = load_settings()
        self.api_recognizer = ApiFormulaRecognizer()
        self.hotkey_handle = None
        self.busy = False
        self.result_queue: queue.Queue[tuple[str, str]] = queue.Queue()
        self.tray: pystray.Icon | None = None

        self.hotkey_var = tk.StringVar(value=self.settings.hotkey)
        self.start_on_boot_var = tk.BooleanVar(value=self.settings.start_on_boot)
        self.api_key_var = tk.StringVar(value=load_api_key())
        self.api_base_var = tk.StringVar(value=self.settings.api_base)
        self.api_model_var = tk.StringVar(value=self.settings.api_model)
        self.status_var = tk.StringVar()
        self._build_ui()
        self._start_tray()
        self.apply_settings(show_error=False)
        self.root.after(100, self._poll_results)

    def _build_ui(self) -> None:
        frame = ttk.Frame(self.root, padding=18)
        frame.pack(fill="both", expand=True)
        ttk.Label(
            frame,
            text="截图后按热键，剪贴板中的公式图片会被识别为 LaTeX。",
            wraplength=450,
        ).pack(anchor="w", pady=(0, 16))

        form = ttk.Frame(frame)
        form.pack(fill="x")
        ttk.Label(form, text="识别热键：").pack(side="left")
        ttk.Entry(form, textvariable=self.hotkey_var).pack(side="left", fill="x", expand=True)
        ttk.Label(frame, text="示例：`、f8、ctrl+alt+l", foreground="#666666").pack(
            anchor="w", padx=(76, 0), pady=(4, 8)
        )
        ttk.Checkbutton(frame, text="开机自动启动（启动后隐藏到系统托盘）", variable=self.start_on_boot_var).pack(anchor="w", pady=(5, 0))

        engine_box = ttk.LabelFrame(frame, text="API 设置", padding=10)
        engine_box.pack(fill="x", pady=(12, 0))
        ttk.Label(engine_box, text="OpenRouter Key：").grid(row=0, column=0, sticky="w")
        ttk.Entry(engine_box, textvariable=self.api_key_var, show="*").grid(row=0, column=1, columnspan=3, sticky="ew")
        ttk.Label(engine_box, text="模型：").grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(engine_box, textvariable=self.api_model_var, width=18).grid(row=1, column=1, sticky="ew", pady=(6, 0))
        ttk.Label(engine_box, text="接口地址：").grid(row=2, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(engine_box, textvariable=self.api_base_var).grid(row=2, column=1, columnspan=3, sticky="ew", pady=(6, 0))
        engine_box.columnconfigure(1, weight=1)

        buttons = ttk.Frame(frame)
        buttons.pack(fill="x", pady=16)
        self.toggle_button = ttk.Button(buttons, command=self.toggle_enabled)
        self.toggle_button.pack(side="left")
        ttk.Button(buttons, text="保存设置", command=self.save_from_ui).pack(side="left", padx=8)
        ttk.Button(buttons, text="立即识别剪贴板", command=self.capture_and_recognize).pack(side="left")

        ttk.Label(frame, textvariable=self.status_var, wraplength=450).pack(anchor="w")

    @staticmethod
    def _icon_image() -> Image.Image:
        image = Image.new("RGBA", (64, 64), (20, 65, 135, 255))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((1, 1, 62, 62), radius=12, fill=(20, 65, 135, 255))
        draw.text((20, 13), "S", fill="white", stroke_width=1)
        return image

    def _start_tray(self) -> None:
        menu = pystray.Menu(
            pystray.MenuItem("打开主窗口", lambda: self.root.after(0, self.show_window), default=True),
            pystray.MenuItem("开启/暂停", lambda: self.root.after(0, self.toggle_enabled)),
            pystray.MenuItem("立即识别剪贴板", lambda: self.root.after(0, self.capture_and_recognize)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("彻底退出", lambda: self.root.after(0, self.quit_app)),
        )
        self.tray = pystray.Icon("LatexPic", self._icon_image(), "LatexPic", menu)
        threading.Thread(target=self.tray.run, daemon=True).start()

    def _refresh_status(self, text: str | None = None) -> None:
        state = "运行中" if self.settings.enabled else "已暂停"
        self.toggle_button.configure(text="暂停" if self.settings.enabled else "开启")
        self.status_var.set(text or f"状态：{state}　热键：{self.settings.hotkey_label}")

    def _register_hotkey(self) -> None:
        if self.hotkey_handle is not None:
            keyboard.remove_hotkey(self.hotkey_handle)
            self.hotkey_handle = None
        if self.settings.enabled:
            self.hotkey_handle = keyboard.add_hotkey(
                self.settings.hotkey,
                lambda: self.root.after(0, self.capture_and_recognize),
                suppress=False,
            )

    def apply_settings(self, show_error: bool = True) -> bool:
        try:
            self._register_hotkey()
            save_settings(self.settings)
            self._refresh_status()
            return True
        except Exception as exc:
            self.settings.enabled = False
            self._refresh_status(f"热键注册失败：{exc}")
            if show_error:
                messagebox.showwarning("无法注册热键", str(exc), parent=self.root)
            return False

    def save_from_ui(self) -> None:
        hotkey = self.hotkey_var.get().strip()
        if not hotkey:
            messagebox.showwarning("热键无效", "热键不能为空。", parent=self.root)
            return
        self.settings.hotkey = hotkey
        self.settings.start_on_boot = self.start_on_boot_var.get()
        save_api_key(self.api_key_var.get())
        self.settings.api_base = self.api_base_var.get().strip() or "https://openrouter.ai/api/v1"
        self.settings.api_model = self.api_model_var.get().strip() or "google/gemini-2.5-flash-lite"
        try:
            configure_startup(self.settings.start_on_boot)
        except OSError as exc:
            messagebox.showwarning("开机启动设置失败", str(exc), parent=self.root)
            return
        if self.apply_settings() and self.tray:
            self.tray.notify("设置已保存", "LatexPic")

    def toggle_enabled(self) -> None:
        self.settings.enabled = not self.settings.enabled
        self.apply_settings()

    def capture_and_recognize(self) -> None:
        if not self.settings.enabled or self.busy:
            return
        content = ImageGrab.grabclipboard()
        if not isinstance(content, Image.Image):
            self._notify("剪贴板中没有图片，请先截图。", error=True)
            return
        self.busy = True
        self._refresh_status("正在使用 API 识别公式……")
        if self.tray:
            self.tray.notify("已开始使用 API 识别，请稍候。", "LatexPic")
        threading.Thread(target=self._recognize_worker, args=(content.copy(),), daemon=True).start()

    def _recognize_worker(self, image: Image.Image) -> None:
        try:
            latex = self.api_recognizer.recognize(
                image,
                load_api_key(),
                self.settings.api_base,
                self.settings.api_model,
            )
            self.result_queue.put(("success", latex))
        except Exception as exc:
            traceback.print_exc()
            self.result_queue.put(("failure", str(exc) or exc.__class__.__name__))

    def _poll_results(self) -> None:
        try:
            while True:
                kind, value = self.result_queue.get_nowait()
                self.busy = False
                if kind == "success":
                    self.root.clipboard_clear()
                    self.root.clipboard_append(value)
                    self.root.update_idletasks()
                    self._notify("识别成功，LaTeX 已复制到剪贴板。")
                else:
                    self._notify(f"识别失败：{value}", error=True)
        except queue.Empty:
            pass
        self.root.after(100, self._poll_results)

    def _notify(self, message: str, error: bool = False) -> None:
        self._refresh_status(message)
        if self.tray:
            self.tray.notify(message, "LatexPic" if not error else "LatexPic 错误")

    def show_window(self) -> None:
        self.root.deiconify()
        self.root.state("normal")
        self.root.lift()
        self.root.focus_force()

    def hide_window(self) -> None:
        self.root.withdraw()
        if self.tray:
            self.tray.notify("程序仍在系统托盘运行。", "LatexPic")

    def quit_app(self) -> None:
        if self.hotkey_handle is not None:
            keyboard.remove_hotkey(self.hotkey_handle)
        keyboard.unhook_all()
        if self.tray:
            self.tray.stop()
        self.root.destroy()

    def run(self) -> int:
        if self.settings.start_minimized or "--minimized" in sys.argv:
            self.root.withdraw()
        self.root.mainloop()
        return 0


def run() -> int:
    try:
        return LatexPicApp().run()
    except Exception:
        traceback.print_exc()
        return 1
