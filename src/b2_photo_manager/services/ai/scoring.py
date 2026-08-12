from b2_photo_manager.services.ai.models import AnalysisResult, SelectionProfile

PROFILE_WEIGHTS: dict[SelectionProfile, dict[str, float]] = {
    SelectionProfile.BALANCED: {"technical": 0.50, "aesthetic": 0.36, "people": 0.14},
    SelectionProfile.TECHNICAL: {"technical": 0.78, "aesthetic": 0.18, "people": 0.04},
    SelectionProfile.PEOPLE: {"technical": 0.34, "aesthetic": 0.24, "people": 0.42},
    SelectionProfile.EVENT: {"technical": 0.42, "aesthetic": 0.34, "people": 0.24},
    SelectionProfile.BEST_PER_SERIES: {"technical": 0.56, "aesthetic": 0.34, "people": 0.10},
    SelectionProfile.CUSTOM: {"technical": 0.50, "aesthetic": 0.36, "people": 0.14},
}


def score_result(
    result: AnalysisResult,
    profile: SelectionProfile,
    custom_weights: dict[str, float] | None = None,
) -> float:
    weights = custom_weights if profile == SelectionProfile.CUSTOM and custom_weights else None
    if weights is None:
        weights = PROFILE_WEIGHTS[profile]
    total_weight = sum(max(value, 0.0) for value in weights.values()) or 1.0
    score = (
        result.technical.overall * max(weights.get("technical", 0.0), 0.0)
        + result.aesthetic.overall * max(weights.get("aesthetic", 0.0), 0.0)
        + result.people.overall * max(weights.get("people", 0.0), 0.0)
    ) / total_weight
    return max(0.0, min(1.0, score))


def recommendation_for_score(score: float) -> str:
    if score >= 0.74:
        return "Empfohlen"
    if score >= 0.55:
        return "Prüfen"
    return "Eher aussortieren"


