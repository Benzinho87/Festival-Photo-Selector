from collections import defaultdict
from collections.abc import Callable, Iterable
from dataclasses import replace
from pathlib import Path

from b2_photo_manager.models.photo import Photo
from b2_photo_manager.services.ai.analyzer import PhotoAnalyzer, PillowTechnicalAnalyzer
from b2_photo_manager.services.ai.cache import AnalysisCache
from b2_photo_manager.services.ai.models import (
    AnalysisResult,
    ContentFingerprint,
    SelectionProfile,
    SelectionRequest,
    SelectionSummary,
)
from b2_photo_manager.services.ai.scoring import recommendation_for_score, score_result
from b2_photo_manager.services.ai.series import group_similar_series, series_lookup

ProgressCallback = Callable[[int, int, Path], None]
CancelCallback = Callable[[], bool]


class SelectionEngine:
    def __init__(
        self,
        analyzer: PhotoAnalyzer | None = None,
        cache: AnalysisCache | None = None,
    ) -> None:
        self.analyzer = analyzer or PillowTechnicalAnalyzer()
        self.cache = cache

    def analyze(
        self,
        photos: Iterable[Photo],
        progress_callback: ProgressCallback | None = None,
        cancel_callback: CancelCallback | None = None,
    ) -> tuple[list[AnalysisResult], tuple[tuple[Path, str], ...]]:
        photo_list = list(photos)
        results: list[AnalysisResult] = []
        errors: list[tuple[Path, str]] = []

        for index, photo in enumerate(photo_list, start=1):
            if cancel_callback is not None and cancel_callback():
                break
            if progress_callback is not None:
                progress_callback(index - 1, len(photo_list), photo.path)
            try:
                result = self.cache.get(photo.path) if self.cache is not None else None
                if result is None:
                    result = self.analyzer.analyze(photo.path)
                    if self.cache is not None:
                        self.cache.set(result)
                photo.ai_analysis = result
                photo.ai_score = result.score
                photo.ai_recommendation = result.recommendation
                results.append(result)
            except Exception as exc:
                errors.append((photo.path, str(exc)))

        if self.cache is not None:
            self.cache.save()
        if progress_callback is not None:
            progress_callback(len(results), len(photo_list), Path())
        return results, tuple(errors)

    def select(
        self,
        photos: Iterable[Photo],
        request: SelectionRequest,
    ) -> SelectionSummary:
        photo_list = list(photos)
        analyzed = [photo for photo in photo_list if photo.ai_analysis is not None]
        scored_results: dict[Path, AnalysisResult] = {}
        for photo in analyzed:
            assert photo.ai_analysis is not None
            score = score_result(photo.ai_analysis, request.profile, request.custom_weights)
            updated = replace(
                photo.ai_analysis,
                score=score,
                recommendation=recommendation_for_score(score),
            )
            photo.ai_analysis = updated
            photo.ai_score = score
            photo.ai_recommendation = updated.recommendation
            scored_results[photo.path] = updated

        groups = group_similar_series(list(scored_results.values()))
        lookup = series_lookup(groups)
        ranks = _series_ranks(analyzed, lookup)
        target = request.target.resolve(len(photo_list))
        selected_paths = self._diverse_selection(analyzed, lookup, target, request.profile)
        algorithm_selected_set = set(selected_paths)

        if request.preserve_favorites:
            favorite_paths = [photo.path for photo in photo_list if photo.favorite]
            selected_paths = _merge_keep_order(selected_paths, favorite_paths)

        selected_set = set(selected_paths)
        for photo in photo_list:
            photo.ai_selected = photo.path in selected_set
            photo.selected = photo.path in algorithm_selected_set
            if photo.ai_selected:
                photo.selection_reason = _selection_reason(photo, lookup, ranks)
            if photo.favorite and request.preserve_favorites:
                photo.ai_selected = True
                photo.selection_reason = "favorite"

        return SelectionSummary(
            selected=tuple(path for path in selected_paths if path in selected_set),
            series=groups,
            target_count=target,
        )

    def analyze_and_select(
        self,
        photos: Iterable[Photo],
        request: SelectionRequest,
        progress_callback: ProgressCallback | None = None,
        cancel_callback: CancelCallback | None = None,
    ) -> SelectionSummary:
        photo_list = list(photos)
        _results, errors = self.analyze(photo_list, progress_callback, cancel_callback)
        summary = self.select(photo_list, request)
        return SelectionSummary(
            selected=summary.selected,
            series=summary.series,
            target_count=summary.target_count,
            errors=errors,
        )

    def _diverse_selection(
        self,
        photos: list[Photo],
        lookup: dict[Path, int],
        target: int,
        profile: SelectionProfile,
    ) -> list[Path]:
        by_series: dict[int, list[Photo]] = defaultdict(list)
        for photo in photos:
            by_series[lookup.get(photo.path, -1)].append(photo)
        for items in by_series.values():
            items.sort(key=lambda photo: photo.ai_score or 0.0, reverse=True)

        if profile == SelectionProfile.BEST_PER_SERIES:
            candidates = [items[0] for items in by_series.values() if items]
            candidates.sort(key=lambda photo: photo.ai_score or 0.0, reverse=True)
            return [photo.path for photo in candidates[:target]]

        selected: list[Path] = []
        ranked_groups = sorted(
            by_series.values(),
            key=lambda items: items[0].ai_score if items else -1.0,
            reverse=True,
        )
        for items in ranked_groups:
            if len(selected) >= target:
                break
            if items and (not selected or _is_distinct_enough(items[0], selected, photos)):
                selected.append(items[0].path)

        skipped_group_winners = [
            items[0]
            for items in ranked_groups
            if items and items[0].path not in selected
        ]

        variant_candidates = [
            photo
            for items in ranked_groups
            for photo in items[1:]
            if photo.path not in selected
        ]
        variant_candidates = skipped_group_winners + variant_candidates
        variant_candidates.sort(key=lambda photo: photo.ai_score or 0.0, reverse=True)
        for photo in variant_candidates:
            if len(selected) >= target:
                break
            if _is_distinct_enough(photo, selected, photos):
                selected.append(photo.path)

        all_candidates = sorted(photos, key=lambda photo: photo.ai_score or 0.0, reverse=True)
        for photo in all_candidates:
            if len(selected) >= target:
                break
            if photo.path not in selected:
                selected.append(photo.path)
        return selected


def _selection_reason(
    photo: Photo,
    lookup: dict[Path, int],
    ranks: dict[Path, int],
) -> str:
    if lookup.get(photo.path, -1) == -1:
        return "quality"
    return "series_best" if ranks.get(photo.path) == 1 else "content_variant"


def _series_ranks(photos: list[Photo], lookup: dict[Path, int]) -> dict[Path, int]:
    by_series: dict[int, list[Photo]] = defaultdict(list)
    for photo in photos:
        by_series[lookup.get(photo.path, -1)].append(photo)
    ranks: dict[Path, int] = {}
    for items in by_series.values():
        items.sort(key=lambda photo: photo.ai_score or 0.0, reverse=True)
        for rank, photo in enumerate(items, start=1):
            ranks[photo.path] = rank
    return ranks


def _is_distinct_enough(candidate: Photo, selected: list[Path], photos: list[Photo]) -> bool:
    by_path = {photo.path: photo for photo in photos}
    for selected_path in selected:
        selected_photo = by_path[selected_path]
        if _near_duplicate(candidate, selected_photo):
            return False
    return True


def _near_duplicate(left: Photo, right: Photo) -> bool:
    if left.ai_analysis is None or right.ai_analysis is None:
        return False
    hash_distance = (
        int(left.ai_analysis.perceptual_hash, 16)
        ^ int(right.ai_analysis.perceptual_hash, 16)
    ).bit_count()
    if hash_distance <= 8:
        return True
    if left.ai_analysis.content == ContentFingerprint.empty() or (
        right.ai_analysis.content == ContentFingerprint.empty()
    ):
        return False
    return _content_distance(left.ai_analysis.content, right.ai_analysis.content) < 0.18


def _content_distance(left: ContentFingerprint, right: ContentFingerprint) -> float:
    values = [
        *_pairwise_differences(left.brightness, right.brightness),
        *_pairwise_differences(left.colors, right.colors),
        *_pairwise_differences(left.edges, right.edges),
        abs(left.warmth - right.warmth),
        abs(left.aspect_ratio - right.aspect_ratio),
    ]
    return sum(values) / max(len(values), 1)


def _pairwise_differences(left: tuple[float, ...], right: tuple[float, ...]) -> list[float]:
    return [abs(a - b) for a, b in zip(left, right, strict=False)]


def _merge_keep_order(primary: list[Path], additions: list[Path]) -> list[Path]:
    result = list(primary)
    seen = set(result)
    for path in additions:
        if path not in seen:
            result.append(path)
            seen.add(path)
    return result
