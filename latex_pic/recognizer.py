from __future__ import annotations

import base64
import io
import os

import requests
from PIL import Image


class ApiFormulaRecognizer:
    def recognize(
        self,
        image: Image.Image,
        api_key: str,
        api_base: str,
        model: str,
        wrap_math: bool = False,
    ) -> str:
        key = api_key.strip() or os.environ.get("OPENROUTER_API_KEY", "")
        if not key:
            raise RuntimeError("请先在主窗口填写 OpenRouter API Key")
        buffer = io.BytesIO()
        image.convert("RGB").save(buffer, format="JPEG", quality=92, optimize=True)
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        output_rule = (
            "Wrap the final LaTeX result in exactly one pair of dollar signs: $...$."
            if wrap_math
            else "Do not include any surrounding dollar signs in the output."
        )
        payload = {
            "model": model.strip() or "google/gemini-2.5-flash-lite",
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Transcribe every mathematical formula in this image to LaTeX. Return only LaTeX, without Markdown fences or explanations. {output_rule} Preserve line breaks when needed."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded}"}},
                ],
            }],
            "max_tokens": 1000,
            "temperature": 0,
        }
        response = requests.post(
            api_base.rstrip("/") + "/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/fangzhi-zhong/LatexPic",
                "X-OpenRouter-Title": "LatexPic",
            },
            json=payload,
            timeout=(10, 60),
        )
        if not response.ok:
            try:
                detail = response.json().get("error", {}).get("message", response.text)
            except ValueError:
                detail = response.text
            raise RuntimeError(f"API {response.status_code}: {detail[:300]}")
        body = response.json()
        choices = body.get("choices", [])
        content = choices[0].get("message", {}).get("content", "") if choices else ""
        if isinstance(content, list):
            content = "".join(part.get("text", "") for part in content if isinstance(part, dict))
        latex = str(content).strip().strip("`").strip()
        if not latex:
            raise RuntimeError("API 没有返回 LaTeX 文本")
        return latex
