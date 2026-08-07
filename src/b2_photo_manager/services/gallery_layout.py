def calculate_columns(
    viewport_width: int,
    card_width: int,
    spacing: int,
    minimum: int = 1,
) -> int:
    if viewport_width <= 0 or card_width <= 0:
        return minimum

    usable_width = viewport_width + spacing
    required_width = card_width + spacing
    return max(minimum, usable_width // required_width)
