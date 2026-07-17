# LatexPic

一个常驻 Windows 系统托盘的截图公式识别工具。使用 Windows 截图后按下全局热键，LatexPic 会读取剪贴板图片，将其中的数学公式转换成 LaTeX，并把结果自动写回剪贴板。

## 功能特性

- 支持 `Win + Shift + S`、Windows 截图工具及其他会把图片写入剪贴板的截图软件
- 默认使用键盘左上角的 `` ` / ~ `` 键触发识别
- 支持自定义全局热键，例如 `F8`、`Ctrl+Alt+L`
- 使用 OpenAI API 快速识别公式
- 自动将识别结果复制到剪贴板
- 可选择为结果添加 `$...$`
- 开始、成功和失败时显示 Windows 右下角通知
- 关闭主窗口后继续在系统托盘运行
- 可在界面中开启或关闭 Windows 开机自启动
- API Key 从项目根目录 `.env` 读取，不会提交到 Git

## 环境要求

- Windows 10 或 Windows 11
- 64 位 Python 3.11 或 3.12
- 使用 API 模式时需要网络和 OpenAI API Key

## 安装

1. 安装 [Python](https://www.python.org/downloads/)，安装时勾选 **Add Python to PATH**。
2. 下载或克隆本项目。
3. 双击 `install.bat`。
4. 等待依赖安装完成。安装日志保存在 `install.log`。
5. 双击 `run.bat` 启动。

也可以在 PowerShell 中手动安装：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

## 快速开始

1. 启动 LatexPic。
2. 填写 API 设置并点击“保存设置”。
3. 按 `Win + Shift + S` 截取一个数学公式。
4. 按下默认热键 `` ` / ~ ``。
5. 等待右下角出现识别成功通知。
6. 在编辑器中按 `Ctrl + V` 粘贴 LaTeX。

建议截图时尽量只保留一个公式，并使用清晰、对比度高的背景。

## API 配置

默认使用：

```text
模型：gpt-4o-mini
接口：https://api.openai.com/v1
```

在 [OpenAI API Keys](https://platform.openai.com/api-keys) 创建密钥，然后任选一种配置方式。

### 在界面中配置

填写 API Key 并点击“保存设置”。程序会自动将密钥写入项目根目录的 `.env`。

### 手动配置

复制 `.env.example` 为 `.env`：

```env
OPENAI_API_KEY=sk-your-key-here
```

程序优先读取 Windows 环境变量 `OPENAI_API_KEY`，其次读取项目根目录 `.env`。

> [!IMPORTANT]
> `.env` 已加入 `.gitignore`。不要把 API Key 写进源码、README、截图或 Git 提交中。API 调用会产生费用，ChatGPT 订阅与 API 账单相互独立。

## 热键设置

默认热键为 `` ` ``，也就是通常与 `~` 共用的键盘左上角按键。设置框也支持 `keyboard` 库可识别的组合，例如：

```text
f8
ctrl+alt+l
ctrl+shift+space
```

如果默认按键影响正常输入，建议改用 `F8` 或组合键。

## 系统托盘

- 点击窗口关闭按钮只会隐藏窗口，程序仍在后台运行。
- 双击系统托盘图标可重新打开窗口。
- 托盘右键菜单可暂停、立即识别或彻底退出。
- 修改代码、`.env` 或依赖后，应先从托盘彻底退出，再重新运行 `run.bat`。

## 开机启动（可选）

在主窗口勾选“开机自动启动（启动后隐藏到系统托盘）”，然后点击“保存设置”。程序会为当前 Windows 用户添加启动项，不需要管理员权限。取消勾选并再次保存即可删除启动项。

## 配置文件

| 文件 | 用途 |
|---|---|
| `.env` | OpenAI API Key，不提交到 Git |
| `%APPDATA%\LatexPic\settings.json` | 热键、引擎、模型、接口地址等界面设置 |
| `install.log` | 依赖安装日志 |
| `startup.log` | 后台启动和运行异常日志 |

## 常见问题

### 双击 `install.bat` 后安装失败

确认 Python 已加入 PATH，并查看项目目录中的 `install.log`。

### 双击 `run.bat` 没有窗口

先检查系统托盘是否已经存在 LatexPic 图标，再查看 `startup.log`。如果程序已经运行，请先从托盘彻底退出。

### 提示剪贴板中没有图片

请先截图，并确保截图软件把图片复制到了剪贴板，而不是只保存为文件。

### API 返回 401

API Key 无效、已撤销或 `.env` 格式错误。确认内容为 `OPENAI_API_KEY=sk-...`，然后重启程序。

### API 返回额度或账单错误

ChatGPT Plus/Pro 不包含 API 额度。请在 OpenAI 开发者平台检查 API Billing 和使用限额。

## 项目结构

```text
latex_pic/
├── latex_pic/
│   ├── app.py          # 窗口、托盘、热键和任务调度
│   ├── recognizer.py   # API 公式识别器
│   └── settings.py     # JSON 设置与 .env 读写
├── .env.example
├── install.bat
├── main.py
├── requirements.txt
└── run.bat
```

## 隐私说明

- API 模式会把当前剪贴板中的截图发送到所配置的 API 地址。
- LatexPic 不会主动上传其他文件，也不会保存截图副本。
- 识别结果会覆盖当前剪贴板内容。

## 许可证

当前项目尚未添加开源许可证。在添加许可证之前，源码默认保留所有权利。如果希望允许他人自由使用、修改和分发，可后续添加 MIT License。
