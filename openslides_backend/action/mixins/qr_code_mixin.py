import io
import segno

from ..action import Action

# Converts a URL to an image byte stream
class QRCodeMixin(Action):
    def render_qr_png(self, url: str, imgKind: str, imgScale: int, imgBorder: int) -> bytes:
        buf = io.BytesIO()
        segno.make(url, error="m").save(buf, kind=imgKind, scale=imgScale, border=imgBorder)
        return buf.getvalue()
