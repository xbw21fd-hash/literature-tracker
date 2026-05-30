import base64, json, os, tempfile
from unittest import mock
import image_provider
from image_provider import generate_image_b64, compress_to_webp

try:
    from PIL import Image
    HAS_PIL = True
except Exception:
    HAS_PIL = False

# A small valid PNG (1x1) base64 — enough for stream-parse equality test (no PIL needed).
_PNG_1x1 = ("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
            "+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")

def _make_png_b64(size=(1600, 900)):
    import io
    buf = io.BytesIO(); Image.new("RGB", size, (10, 80, 180)).save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode()

def test_compress_to_webp_shrinks_and_resizes():
    if not HAS_PIL:
        return  # skipped locally; validated in CI
    src = base64.b64decode(_make_png_b64((1600, 900)))
    out = os.path.join(tempfile.mkdtemp(), "p.webp")
    compress_to_webp(src, out, max_edge=768, quality=80)
    assert os.path.exists(out)
    im = Image.open(out)
    assert im.format == "WEBP"
    assert max(im.size) <= 768

def test_generate_image_parses_stream():
    line = 'data: ' + json.dumps({
        "type": "response.output_item.done",
        "item": {"type": "image_generation_call", "result": _PNG_1x1}})
    class FakeStream:
        status_code = 200
        def iter_lines(self, decode_unicode=True): yield line
        def raise_for_status(self): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False
    with mock.patch.object(image_provider.requests, "post", return_value=FakeStream()):
        got = generate_image_b64("draw a crystal", api_key="k", base="http://h/v1")
    assert got == _PNG_1x1

def test_generate_image_returns_none_on_failure():
    def boom(*a, **k): raise Exception("down")
    with mock.patch.object(image_provider.requests, "post", side_effect=boom):
        assert generate_image_b64("x", api_key="k", base="http://h/v1") is None
