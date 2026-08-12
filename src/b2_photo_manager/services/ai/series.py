from pathlib import Path

from b2_photo_manager.services.ai.analyzer import hamming_distance
from b2_photo_manager.services.ai.models import AnalysisResult, SeriesGroup


def group_similar_series(
    results: list[AnalysisResult],
    distance_threshold: int = 10,
) -> tuple[SeriesGroup, ...]:
    groups: list[list[AnalysisResult]] = []

    for result in results:
        for group in groups:
            if any(
                hamming_distance(result.perceptual_hash, candidate.perceptual_hash)
                <= distance_threshold
                for candidate in group
            ):
                group.append(result)
                break
        else:
            groups.append([result])

    return tuple(
        SeriesGroup(
            id=index,
            photos=tuple(item.path for item in sorted(group, key=lambda item: str(item.path))),
        )
        for index, group in enumerate(groups, start=1)
    )


def series_lookup(groups: tuple[SeriesGroup, ...]) -> dict[Path, int]:
    return {path: group.id for group in groups for path in group.photos}


