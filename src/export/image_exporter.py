from io import BytesIO
from pathlib import Path
from PIL import Image, ImageOps
from src.export.presets import ExportPreset

def _resize_image(image: Image.Image, preset: ExportPreset) -> Image.Image:
    if preset.crop and preset.width and preset.height:
        return ImageOps.fit(image, (preset.width, preset.height), method=Image.Resampling.LANCZOS)
    resized = image.copy()
    if preset.max_edge:
        resized.thumbnail((preset.max_edge, preset.max_edge), Image.Resampling.LANCZOS)
    return resized

def _encode_image(image: Image.Image, preset: ExportPreset, quality: int) -> bytes:
    buffer = BytesIO()
    kwargs = {"format": preset.format, "quality": quality, "optimize": True}
    if preset.format == "JPEG":
        kwargs["progressive"] = True
        image = image.convert("RGB")
    image.save(buffer, **kwargs)
    return buffer.getvalue()

def export_image(source: Path, target: Path, preset: ExportPreset) -> tuple[int, int]:
    with Image.open(source) as original:
        image = ImageOps.exif_transpose(original).convert("RGB")
        image = _resize_image(image, preset)
    max_bytes = preset.max_file_size_kb * 1024
    quality = preset.start_quality
    encoded = _encode_image(image, preset, quality)
    while len(encoded) > max_bytes and quality > preset.min_quality:
        quality = max(preset.min_quality, quality - 4)
        encoded = _encode_image(image, preset, quality)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(encoded)
    return len(encoded), quality

def extension_for(preset: ExportPreset) -> str:
    return ".webp" if preset.format == "WEBP" else ".jpg"
