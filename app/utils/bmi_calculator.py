"""
BMI calculation and categorization utilities.
"""
from app.core.constants import BMI_CATEGORIES


def compute_bmi(weight_kg: float, height_cm: float) -> float:
    """
    Compute BMI from weight and height.

    Args:
        weight_kg: Weight in kilograms
        height_cm: Height in centimeters

    Returns:
        BMI value rounded to 2 decimal places
    """
    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)
    return round(bmi, 2)


def get_bmi_category(bmi: float) -> str:
    """
    Determine BMI category from BMI value.

    Args:
        bmi: BMI value

    Returns:
        BMI category string
    """
    for category, (min_bmi, max_bmi) in BMI_CATEGORIES.items():
        if min_bmi <= bmi < max_bmi:
            return category
    return "normal"  # Default fallback


def validate_bmi_category(computed_bmi: float, provided_category: str) -> str:
    """
    Validate provided BMI category against computed BMI.
    Returns computed category if mismatch.

    Args:
        computed_bmi: Calculated BMI value
        provided_category: User-provided category

    Returns:
        Validated BMI category
    """
    computed_category = get_bmi_category(computed_bmi)
    if computed_category != provided_category:
        return computed_category
    return provided_category
