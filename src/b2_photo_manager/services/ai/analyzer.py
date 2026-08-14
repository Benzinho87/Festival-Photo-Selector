from abc import ABC, abstractmethod
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter, ImageOps, ImageStat

from b2_photo_manager.services.ai.models import (
    AestheticScores,
    AnalysisResult,
    PeopleScores,
    TechnicalScores,
)


class PhotoAnalyzer(ABC):
    @abstractmethod
    def analyze(self, path: Path) -> AnalysisResult:
        raise NotImplementedError


class PillowTechnicalAnalyzer(PhotoAnalyzer):
    def analyze(self, path: Path) -> AnalysisResult:
        signature = file_signature(path)
        with Image.open(path) as image:
            image = ImageOps.exif_transpose(image).convert("RGB")
            width, height = image.size
            work = image.copy()
            work.thumbnail((512, 512), Image.Resampling.LANCZOS)
            gray = ImageOps.grayscale(work)

            sharpness = _sharpness_score(gray)
            exposure = _exposure_score(gray)
            clipping = _clipping_score(gray)
            contrast = _contrast_score(gray)
            noise = _noise_score(gray)
            technical = TechnicalScores(
                sharpness=sharpness,
                exposure=exposure,
                clipping=clipping,
                contrast=contrast,
                noise=noise,
            )
            aesthetic = AestheticScores(
                composition=_composition_score(gray),
                subject_clarity=(sharpness * 0.7 + contrast * 0.3),
                visual_quality=(technical.overall * 0.75 + _composition_score(gray) * 0.25),
            )
            people = _people_scores(work, sharpness)
            score = technical.overall * 0.68 + aesthetic.overall * 0.32
            reasons = _reasons(technical, aesthetic)
            return AnalysisResult(
                path=path,
                file_signature=signature,
                width=width,
                height=height,
                technical=technical,
                aesthetic=aesthetic,
                people=people,
                perceptual_hash=average_hash(gray),
                score=score,
                recommendation=_recommendation(score),
                reasons=reasons,
            )


def file_signature(path: Path) -> str:
    stat = path.stat()
    return f"{stat.st_size}:{stat.st_mtime_ns}"


def average_hash(image: Image.Image, hash_size: int = 8) -> str:
    small = image.resize((hash_size, hash_size), Image.Resampling.LANCZOS)
    pixels = list(small.getdata())
    average = sum(pixels) / len(pixels)
    bits = ["1" if pixel >= average else "0" for pixel in pixels]
    return f"{int(''.join(bits), 2):0{hash_size * hash_size // 4}x}"


def hamming_distance(left: str, right: str) -> int:
    return (int(left, 16) ^ int(right, 16)).bit_count()


def _sharpness_score(gray: Image.Image) -> float:
    edges = gray.filter(ImageFilter.FIND_EDGES)
    stat = ImageStat.Stat(edges)
    return _clamp(stat.stddev[0] / 38.0)


def _exposure_score(gray: Image.Image) -> float:
    mean = ImageStat.Stat(gray).mean[0] / 255.0
    return _clamp(1.0 - abs(mean - 0.50) / 0.42)


def _clipping_score(gray: Image.Image) -> float:
    pixels = list(gray.getdata())
    clipped = sum(1 for pixel in pixels if pixel <= 5 or pixel >= 250) / len(pixels)
    return _clamp(1.0 - clipped / 0.18)


def _contrast_score(gray: Image.Image) -> float:
    return _clamp(ImageStat.Stat(gray).stddev[0] / 72.0)


def _noise_score(gray: Image.Image) -> float:
    smooth = gray.filter(ImageFilter.GaussianBlur(radius=1.2))
    detail = ImageStat.Stat(ImageChops.difference(gray, smooth)).stddev[0]
    return _clamp(1.0 - detail / 42.0)


def _composition_score(gray: Image.Image) -> float:
    width, height = gray.size
    thirds_x = (width / 3, width * 2 / 3)
    thirds_y = (height / 3, height * 2 / 3)
    edges = gray.filter(ImageFilter.FIND_EDGES)
    total = 0.0
    weighted = 0.0
    for y in range(0, height, 4):
        for x in range(0, width, 4):
            value = edges.getpixel((x, y)) / 255.0
            total += value
            dist = min(abs(x - thirds_x[0]), abs(x - thirds_x[1])) / max(width, 1)
            dist += min(abs(y - thirds_y[0]), abs(y - thirds_y[1])) / max(height, 1)
            weighted += value * (1.0 - min(dist, 0.55))
    if total <= 0:
        return 0.45
    return _clamp(weighted / total / 0.86)


def _people_scores(image: Image.Image, sharpness: float) -> PeopleScores:
    pixels = list(image.getdata())
    if not pixels:
        return PeopleScores(face_sharpness=0.0)

    skin_like = 0
    warm_subject = 0
    center_weighted = 0.0
    total_weight = 0.0
    width, height = image.size
    for y in range(0, height, 3):
        for x in range(0, width, 3):
            red, green, blue = image.getpixel((x, y))
            brightness = (red + green + blue) / (3 * 255)
            warm = red > 70 and green > 35 and blue > 20 and red > blue * 1.12
            balanced = abs(red - green) > 8 and max(red, green, blue) - min(red, green, blue) > 18
            if warm and balanced:
                skin_like += 1
                center_distance = abs(x - width / 2) / max(width, 1)
                center_distance += abs(y - height / 2) / max(height, 1)
                center_weighted += max(0.0, 1.0 - center_distance) * brightness
            if red > green > blue and brightness > 0.18:
                warm_subject += 1
            total_weight += 1.0

    skin_ratio = skin_like / total_weight
    warm_ratio = warm_subject / total_weight
    center_signal = center_weighted / max(skin_like, 1)
    people_signal = _clamp(skin_ratio * 7.5 + warm_ratio * 1.4 + center_signal * 0.35)
    faces_present = people_signal >= 0.34
    face_count = 1 if faces_present else 0
    face_sharpness = _clamp(sharpness * 0.55 + people_signal * 0.45)
    eyes_open = _clamp(0.45 + sharpness * 0.35) if faces_present else None
    return PeopleScores(
        faces_present=faces_present,
        face_count=face_count,
        eyes_open=eyes_open,
        face_sharpness=face_sharpness,
    )


def _reasons(technical: TechnicalScores, aesthetic: AestheticScores) -> tuple[str, ...]:
    reasons: list[str] = []
    if technical.sharpness >= 0.72:
        reasons.append("sehr gute Schärfe")
    elif technical.sharpness < 0.35:
        reasons.append("möglicherweise unscharf")
    if technical.exposure >= 0.72 and technical.clipping >= 0.72:
        reasons.append("ausgewogene Belichtung")
    elif technical.clipping < 0.45:
        reasons.append("starkes Clipping erkannt")
    if aesthetic.composition >= 0.68:
        reasons.append("starke Komposition")
    return tuple(reasons or ["solide Gesamtbewertung"])


def _recommendation(score: float) -> str:
    if score >= 0.74:
        return "Empfohlen"
    if score >= 0.55:
        return "Prüfen"
    return "Eher aussortieren"


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))
