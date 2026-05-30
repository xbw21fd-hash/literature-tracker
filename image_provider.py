"""gpt-image-2 via OpenAI-compatible Responses API（必须流式）+ WebP 压缩。"""
import os, io, json
import requests

def _responses_url(base):
    base = (base or "").rstrip("/")
    if base.endswith("/chat/completions"):
        base = base[: -len("/chat/completions")]
    if not base.endswith("/v1"):
        base = base + "/v1" if "/v1" not in base else base
    return base + "/responses"

def generate_image_b64(prompt, api_key=None, base=None, timeout=180):
    """返回 PNG base64 字符串；失败返回 None。"""
    api_key = api_key or os.environ.get("IMAGE_API_KEY") or os.environ.get("AI_API_KEY")
    base = base or os.environ.get("IMAGE_API_BASE") or os.environ.get("AI_BASE_URL")
    url = _responses_url(base)
    payload = {"model": "gpt-5.5",
               "input": [{"role": "user", "content": prompt}],
               "tools": [{"type": "image_generation"}],
               "stream": True}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        with requests.post(url, headers=headers, json=payload, stream=True, timeout=timeout) as r:
            r.raise_for_status()
            result_b64 = None
            for raw in r.iter_lines(decode_unicode=True):
                if not raw or not raw.startswith("data:"):
                    continue
                data = raw[5:].strip()
                if not data or data == "[DONE]":
                    continue
                try: ev = json.loads(data)
                except Exception: continue
                if ev.get("type") == "response.output_item.done":
                    item = ev.get("item", {})
                    if item.get("type") == "image_generation_call" and item.get("result"):
                        result_b64 = item["result"]
                elif ev.get("type") == "response.image_generation_call.partial_image":
                    if ev.get("partial_image_b64") and not result_b64:
                        result_b64 = ev["partial_image_b64"]
            return result_b64
    except Exception as e:
        print(f"⚠️ image generation failed: {e}")
        return None

def compress_to_webp(png_bytes, out_path, max_edge=768, quality=80):
    from PIL import Image  # lazy import: Pillow only needed at compression time
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    im = Image.open(io.BytesIO(png_bytes)).convert("RGB")
    w, h = im.size
    if max(w, h) > max_edge:
        scale = max_edge / max(w, h)
        im = im.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    im.save(out_path, "WEBP", quality=quality, method=6)
    return out_path

def generate_and_save(prompt, out_path, max_edge=768, quality=80, **kw):
    import base64
    b64 = generate_image_b64(prompt, **kw)
    if not b64:
        return None
    try:
        compress_to_webp(base64.b64decode(b64), out_path, max_edge, quality)
        return out_path
    except Exception as e:
        print(f"⚠️ compress failed: {e}"); return None
