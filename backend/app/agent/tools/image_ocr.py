from io import BytesIO

from PIL import Image, ImageEnhance

from app.core.config import get_settings


class ImageOcrTool:
    allowed_types = {"image/png", "image/jpeg", "image/webp"}

    def validate(self, content: bytes, content_type: str | None) -> None:
        settings = get_settings()
        if content_type not in self.allowed_types:
            raise ValueError("Unsupported image type")
        if len(content) > settings.max_upload_size_mb * 1024 * 1024:
            raise ValueError("Image is too large")

    def extract_text(self, content: bytes, content_type: str | None = "image/png") -> str:
        self.validate(content, content_type)
        try:
            import pytesseract

            image = Image.open(BytesIO(content))
            image = ImageEnhance.Contrast(image.convert("L")).enhance(1.8)
            if min(image.size) < 1000:
                image = image.resize((image.width * 2, image.height * 2))
            text = pytesseract.image_to_string(image, lang=get_settings().ocr_lang)
        except Exception:
            text = ""
        if not text.strip():
            raise ValueError("OCR did not recognize text")
        return text
