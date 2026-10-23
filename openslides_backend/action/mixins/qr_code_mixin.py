import io
#import segno

from ..action import Action

# Converts a URL to an image byte stream
class QRCodeMixin(Action):
    def render_qr_png(url: str, imgKind: str, imgScale: int, imgBorder: int) -> bytes:
        #buf = io.BytesIO()
        #segno.make(url, error="m").save(buf, imgKind, imgScale, imgBorder)
        #return buf.getvalue()
        return io.BytesIO()
