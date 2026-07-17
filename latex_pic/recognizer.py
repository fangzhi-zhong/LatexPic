from __future__ import annotations

import base64
import io
import os

import requests
from PIL import Image


class ApiFormulaRecognizer:
    def recognize(self, image: Image.Image, api_key: str, api_base: str, model: str) -> str:
        key = api_key.strip() or os.environ.get("OPENAI_API_KEY", "")
        if not key:
            raise RuntimeError("请先在主窗口填写 API Key")
        buffer = io.BytesIO()
        image.convert("RGB").save(buffer, format="JPEG", quality=92, optimize=True)
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        payload = {
            "model": model.strip() or "gpt-4o-mini",
            "input": [{
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "Transcribe every mathematical formula in this image to LaTeX. Return only raw LaTeX, without Markdown fences, explanations, or surrounding dollar signs. Preserve line breaks when needed."},
                    {"type": "input_image", "image_url": f"data:image/jpeg;base64,{encoded}", "detail": "high"},
                ],
            }],
            "max_output_tokens": 1000,
        }
        response = requests.post(
            api_base.rstrip("/") + "/responses",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
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
        pieces = [
            item.get("text", "")
            for output in body.get("output", [])
            for item in output.get("content", [])
            if item.get("type") == "output_text"
        ]
        latex = "".join(pieces).strip().strip("`").strip()
        if not latex:
            raise RuntimeError("API 没有返回 LaTeX 文本")
        return latex
