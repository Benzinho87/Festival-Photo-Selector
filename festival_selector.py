from __future__ import annotations

import argparse
import csv
import html
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image, ImageOps
from sklearn.cluster import MiniBatchKMeans
from torch.utils.data import DataLoader, Dataset
from torchvision.models import ResNet18_Weights, resnet18
from tqdm import tqdm


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
DEFAULT_COUNT = 80
DEFAULT_BATCH_SIZE = 24
DEFAULT_BLUR_THRESHOLD = 45.0
DEFAULT_MIN_BRIGHTNESS = 18.0
DEFAULT_MAX_BRIGHTNESS = 238.0


@dataclass
class PhotoRecord:
    path: Path
    sharpness: float
    brightness: float
    contrast: float
    technical_score: float
    feature: np.ndarray | None = None
    cluster: int | None = None
    distance_to_center: float | None = None
    selection_score: float | None = None


class FestivalDataset(Dataset):
    def __init__(self, records: list[PhotoRecord], transform) -> None:
        self.records = records
        self.transform = transform

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int):
        record = self.records[index]
        with Image.open(record.path) as image:
            image = ImageOps.exif_transpose(image).convert("RGB")
            tensor = self.transform(image)
        return tensor, index


def find_images(input_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in input_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def analyse_technical_quality(path: Path) -> tuple[float, float, float]:
    with Image.open(path) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        image.thumbnail((1600, 1600))
        rgb = np.asarray(image)

    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    brightness = float(gray.mean())
    contrast = float(gray.std())
    return sharpness, brightness, contrast


def make_technical_score(
    sharpness: float,
    brightness: float,
    contrast: float,
) -> float:
    sharpness_score = np.clip(np.log1p(sharpness) / np.log1p(1500.0), 0.0, 1.0)
    brightness_score = 1.0 - min(abs(brightness - 118.0) / 118.0, 1.0)
    contrast_score = np.clip(contrast / 70.0, 0.0, 1.0)
    return float(
        0.55 * sharpness_score
        + 0.25 * brightness_score
        + 0.20 * contrast_score
    )


def scan_photos(
    image_paths: list[Path],
    blur_threshold: float,
    min_brightness: float,
    max_brightness: float,
) -> tuple[list[PhotoRecord], list[tuple[Path, str]]]:
    accepted: list[PhotoRecord] = []
    rejected: list[tuple[Path, str]] = []

    for path in tqdm(image_paths, desc="Technische Prüfung"):
        try:
            sharpness, brightness, contrast = analyse_technical_quality(path)
        except Exception as exc:
            rejected.append((path, f"Lesefehler: {exc}"))
            continue

        if brightness < min_brightness:
            rejected.append((path, f"zu dunkel ({brightness:.1f})"))
            continue
        if brightness > max_brightness:
            rejected.append((path, f"zu hell ({brightness:.1f})"))
            continue
        if sharpness < blur_threshold:
            rejected.append((path, f"zu unscharf ({sharpness:.1f})"))
            continue

        accepted.append(
            PhotoRecord(
                path=path,
                sharpness=sharpness,
                brightness=brightness,
                contrast=contrast,
                technical_score=make_technical_score(
                    sharpness,
                    brightness,
                    contrast,
                ),
            )
        )

    return accepted, rejected


def choose_device() -> torch.device:
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def extract_features(
    records: list[PhotoRecord],
    batch_size: int,
) -> None:
    weights = ResNet18_Weights.DEFAULT
    model = resnet18(weights=weights)
    model.fc = torch.nn.Identity()

    device = choose_device()
    model = model.to(device).eval()

    dataset = FestivalDataset(records, weights.transforms())
    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=False,
    )

    with torch.inference_mode():
        for images, indices in tqdm(loader, desc=f"Bildinhalte analysieren ({device.type})"):
            images = images.to(device)
            features = model(images)
            features = torch.nn.functional.normalize(features, dim=1)
            features_np = features.cpu().numpy().astype(np.float32)

            for feature, index in zip(features_np, indices.tolist()):
                records[index].feature = feature


def select_diverse_photos(
    records: list[PhotoRecord],
    target_count: int,
) -> list[PhotoRecord]:
    if len(records) < target_count:
        raise ValueError(
            f"Nur {len(records)} geeignete Fotos gefunden, benötigt werden {target_count}."
        )

    features = np.stack([record.feature for record in records])
    clusterer = MiniBatchKMeans(
        n_clusters=target_count,
        random_state=42,
        batch_size=min(1024, max(256, len(records))),
        n_init=10,
    )
    labels = clusterer.fit_predict(features)

    selected: list[PhotoRecord] = []

    for cluster_id in range(target_count):
        member_indices = np.flatnonzero(labels == cluster_id)
        if member_indices.size == 0:
            continue

        center = clusterer.cluster_centers_[cluster_id]
        cluster_features = features[member_indices]
        distances = np.linalg.norm(cluster_features - center, axis=1)

        max_distance = max(float(distances.max()), 1e-9)

        candidates: list[PhotoRecord] = []
        for member_index, distance in zip(member_indices, distances):
            record = records[int(member_index)]
            record.cluster = cluster_id
            record.distance_to_center = float(distance)
            representativeness = 1.0 - float(distance) / max_distance
            record.selection_score = (
                0.68 * record.technical_score
                + 0.32 * representativeness
            )
            candidates.append(record)

        selected.append(
            max(
                candidates,
                key=lambda record: (
                    record.selection_score,
                    record.technical_score,
                ),
            )
        )

    selected.sort(
        key=lambda record: (
            record.selection_score or 0.0,
            record.technical_score,
        ),
        reverse=True,
    )
    return selected[:target_count]


def copy_selection(
    selected: list[PhotoRecord],
    output_dir: Path,
) -> list[tuple[PhotoRecord, Path]]:
    selection_dir = output_dir / "auswahl_80"
    selection_dir.mkdir(parents=True, exist_ok=True)

    copied: list[tuple[PhotoRecord, Path]] = []
    for rank, record in enumerate(selected, start=1):
        target_name = (
            f"{rank:03d}"
            f"_score-{record.selection_score:.3f}"
            f"_{record.path.name}"
        )
        target = selection_dir / target_name
        shutil.copy2(record.path, target)
        copied.append((record, target))

    return copied


def create_thumbnails(
    copied: list[tuple[PhotoRecord, Path]],
    output_dir: Path,
) -> list[tuple[PhotoRecord, Path, Path]]:
    thumb_dir = output_dir / "thumbnails"
    thumb_dir.mkdir(parents=True, exist_ok=True)

    result: list[tuple[PhotoRecord, Path, Path]] = []
    for rank, (record, copied_path) in enumerate(copied, start=1):
        thumb_path = thumb_dir / f"{rank:03d}.jpg"
        with Image.open(copied_path) as image:
            image = ImageOps.exif_transpose(image).convert("RGB")
            image.thumbnail((520, 360))
            image.save(thumb_path, "JPEG", quality=85, optimize=True)
        result.append((record, copied_path, thumb_path))

    return result


def write_csv(
    gallery_items: list[tuple[PhotoRecord, Path, Path]],
    output_dir: Path,
) -> None:
    csv_path = output_dir / "auswahl.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow(
            [
                "Rang",
                "Datei",
                "Original",
                "Auswahl-Score",
                "Technik-Score",
                "Schärfe",
                "Helligkeit",
                "Kontrast",
                "Cluster",
            ]
        )
        for rank, (record, copied_path, _) in enumerate(gallery_items, start=1):
            writer.writerow(
                [
                    rank,
                    copied_path.name,
                    str(record.path),
                    f"{record.selection_score:.4f}",
                    f"{record.technical_score:.4f}",
                    f"{record.sharpness:.2f}",
                    f"{record.brightness:.2f}",
                    f"{record.contrast:.2f}",
                    record.cluster,
                ]
            )


def write_rejected(
    rejected: list[tuple[Path, str]],
    output_dir: Path,
) -> None:
    path = output_dir / "aussortiert.csv"
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow(["Datei", "Grund"])
        for image_path, reason in rejected:
            writer.writerow([str(image_path), reason])


def write_html_gallery(
    gallery_items: list[tuple[PhotoRecord, Path, Path]],
    output_dir: Path,
) -> None:
    cards: list[str] = []

    for rank, (record, copied_path, thumb_path) in enumerate(gallery_items, start=1):
        cards.append(
            f"""
            <article class="card">
                <a href="{html.escape(copied_path.relative_to(output_dir).as_posix())}">
                    <img src="{html.escape(thumb_path.relative_to(output_dir).as_posix())}"
                         alt="{html.escape(copied_path.name)}"
                         loading="lazy">
                </a>
                <div class="meta">
                    <strong>{rank:02d}. {html.escape(record.path.name)}</strong>
                    <span>Score {record.selection_score:.3f}</span>
                </div>
            </article>
            """
        )

    page = f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Festival-Fotoauswahl</title>
<style>
body {{
    margin: 0;
    padding: 24px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: #111;
    color: #f5f5f5;
}}
h1 {{ margin: 0 0 8px; }}
p {{ color: #bbb; margin: 0 0 24px; }}
.grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 16px;
}}
.card {{
    overflow: hidden;
    background: #1d1d1d;
    border-radius: 10px;
}}
.card img {{
    display: block;
    width: 100%;
    height: 200px;
    object-fit: cover;
}}
.meta {{
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 12px;
    font-size: 13px;
}}
.meta span {{ color: #aaa; }}
</style>
</head>
<body>
<h1>Festival-Fotoauswahl</h1>
<p>{len(gallery_items)} automatisch vorsortierte Fotos. Anklicken öffnet die kopierte Originaldatei.</p>
<section class="grid">
{''.join(cards)}
</section>
</body>
</html>
"""
    (output_dir / "galerie.html").write_text(page, encoding="utf-8")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Wählt technisch gute und inhaltlich abwechslungsreiche Festivalfotos aus."
    )
    parser.add_argument("input", type=Path, help="Ordner mit den Originalfotos")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("festival_auswahl"),
        help="Ausgabeordner",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=DEFAULT_COUNT,
        help="Anzahl auszuwählender Fotos",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help="Batchgröße für die KI-Analyse",
    )
    parser.add_argument(
        "--blur-threshold",
        type=float,
        default=DEFAULT_BLUR_THRESHOLD,
        help="Mindestwert für die Schärfe",
    )
    parser.add_argument(
        "--min-brightness",
        type=float,
        default=DEFAULT_MIN_BRIGHTNESS,
    )
    parser.add_argument(
        "--max-brightness",
        type=float,
        default=DEFAULT_MAX_BRIGHTNESS,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()
    input_dir = args.input.expanduser().resolve()
    output_dir = args.output.expanduser().resolve()

    if not input_dir.is_dir():
        print(f"Fehler: Eingabeordner nicht gefunden: {input_dir}", file=sys.stderr)
        return 1
    if args.count < 1:
        print("Fehler: --count muss mindestens 1 sein.", file=sys.stderr)
        return 1

    image_paths = find_images(input_dir)
    if not image_paths:
        print("Fehler: Keine unterstützten Bilddateien gefunden.", file=sys.stderr)
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"{len(image_paths)} Fotos gefunden.")
    records, rejected = scan_photos(
        image_paths,
        blur_threshold=args.blur_threshold,
        min_brightness=args.min_brightness,
        max_brightness=args.max_brightness,
    )

    if len(records) < args.count:
        print(
            f"Nur {len(records)} Fotos bestehen die Filter. "
            "Starte erneut mit einem niedrigeren --blur-threshold "
            "oder weniger strengen Helligkeitswerten.",
            file=sys.stderr,
        )
        write_rejected(rejected, output_dir)
        return 2

    extract_features(records, batch_size=args.batch_size)
    selected = select_diverse_photos(records, target_count=args.count)
    copied = copy_selection(selected, output_dir)
    gallery_items = create_thumbnails(copied, output_dir)

    write_csv(gallery_items, output_dir)
    write_rejected(rejected, output_dir)
    write_html_gallery(gallery_items, output_dir)

    print()
    print(f"Fertig: {len(selected)} Fotos ausgewählt.")
    print(f"Fotos:   {output_dir / 'auswahl_80'}")
    print(f"Galerie: {output_dir / 'galerie.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
