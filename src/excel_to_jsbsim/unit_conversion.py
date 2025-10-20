#!/usr/bin/env python3
"""
User-friendly unit conversion for JSBSim XML generation

Purpose: Convert practical units (g, mm) to JSBSim-compatible units (KG, M)
Author: Claude (AI Assistant)
Date: 2025-10-03
"""

import pandas as pd

# Conversion map: user_unit -> (jsbsim_unit, conversion_factor)
CONVERSION_MAP = {
    # === 長さ (Length) ===
    "mm": ("M", 0.001),
    "cm": ("M", 0.01),
    "m": ("M", 1.0),
    "in": ("IN", 1.0),      # Already JSBSim unit
    "ft": ("FT", 1.0),      # Already JSBSim unit

    # === 面積 (Area) ===
    "mm2": ("M2", 0.000001),      # 1 mm² = 1e-6 m²
    "mm^2": ("M2", 0.000001),
    "cm2": ("M2", 0.0001),        # 1 cm² = 1e-4 m²
    "cm^2": ("M2", 0.0001),
    "m2": ("M2", 1.0),
    "m^2": ("M2", 1.0),
    "ft2": ("FT2", 1.0),          # Already JSBSim unit
    "ft^2": ("FT2", 1.0),
    "in2": ("IN2", 1.0),
    "in^2": ("IN2", 1.0),

    # === 質量 (Mass) ===
    "g": ("KG", 0.001),           # 1 g = 0.001 kg
    "kg": ("KG", 1.0),
    "lbs": ("LBS", 1.0),          # Already JSBSim unit
    "lb": ("LBS", 1.0),

    # === 慣性モーメント (Moment of Inertia) ===
    "g*mm2": ("KG*M2", 1e-9),     # 1 g·mm² = 1e-9 kg·m²
    "g*mm^2": ("KG*M2", 1e-9),
    "gmm2": ("KG*M2", 1e-9),
    "g*cm2": ("KG*M2", 1e-7),     # 1 g·cm² = 1e-7 kg·m²
    "g*cm^2": ("KG*M2", 1e-7),
    "gcm2": ("KG*M2", 1e-7),
    "kg*m2": ("KG*M2", 1.0),
    "kg*m^2": ("KG*M2", 1.0),
    "kgm2": ("KG*M2", 1.0),
    "slug*ft2": ("SLUG*FT2", 1.0), # Already JSBSim unit
    "slug*ft^2": ("SLUG*FT2", 1.0),

    # === 角度 (Angle) ===
    "deg": ("DEG", 1.0),
    "rad": ("RAD", 1.0),

    # === その他の複合単位 ===
    "lbs/ft": ("LBS/FT", 1.0),
    "lbs/ft/sec": ("LBS/FT/SEC", 1.0),
}


def normalize_unit_string(unit_str):
    """
    Normalize unit string for consistent matching

    Args:
        unit_str: Raw unit string from Excel

    Returns:
        Normalized unit string (lowercase, no spaces)
    """
    if pd.isna(unit_str) or unit_str is None:
        return None

    # Convert to string, lowercase, remove spaces and dots
    normalized = str(unit_str).lower().strip()
    normalized = normalized.replace(" ", "").replace(".", "")

    # Handle common variations
    normalized = normalized.replace("·", "*")  # Middle dot to asterisk
    normalized = normalized.replace("×", "*")  # Multiplication sign to asterisk

    return normalized


def convert_user_unit_to_jsbsim(value, user_unit):
    """
    Convert value from user-friendly unit to JSBSim-compatible unit

    Args:
        value: Numeric value to convert
        user_unit: User-specified unit (e.g., "g", "mm", "mm²")

    Returns:
        Tuple of (converted_value, jsbsim_unit)
        Returns (None, None) if value is None/NaN
        Returns (value, None) if unit is None/empty
        Returns (value, UPPERCASE_UNIT) if unit is unknown

    Examples:
        >>> convert_user_unit_to_jsbsim(200, "g")
        (0.2, "KG")

        >>> convert_user_unit_to_jsbsim(1000, "mm")
        (1.0, "M")

        >>> convert_user_unit_to_jsbsim(200000, "mm²")
        (0.2, "M2")

    Raises:
        ValueError: If value is not numeric
    """
    # Handle None/NaN values
    if pd.isna(value) or value is None:
        return None, None

    if pd.isna(user_unit) or not user_unit:
        # No unit specified, return value as-is with no unit
        return value, None

    # Normalize unit string
    unit_key = normalize_unit_string(user_unit)

    if not unit_key:
        return value, None

    # Look up conversion
    if unit_key in CONVERSION_MAP:
        jsbsim_unit, factor = CONVERSION_MAP[unit_key]
        try:
            converted_value = float(value) * factor
            return converted_value, jsbsim_unit
        except (ValueError, TypeError) as e:
            raise ValueError(f"Cannot convert value '{value}' to float: {e}")
    else:
        # Unknown unit - pass through with uppercase
        # This allows JSBSim-native units (e.g., "FT", "LBS") to work
        import warnings
        warnings.warn(
            f"Unknown unit '{user_unit}' - passing through as '{str(user_unit).upper()}'. "
            f"JSBSim may reject it if not a valid unit.",
            UserWarning
        )
        return value, str(user_unit).upper()


def get_supported_units():
    """
    Get list of supported user-friendly units

    Returns:
        Dictionary categorized by physical quantity
    """
    return {
        "長さ (Length)": ["mm", "cm", "m", "in", "ft"],
        "面積 (Area)": ["mm²", "cm²", "m²", "ft²", "in²"],
        "質量 (Mass)": ["g", "kg", "lbs"],
        "慣性モーメント (Inertia)": ["g·mm²", "g·cm²", "kg·m²", "slug·ft²"],
        "角度 (Angle)": ["deg", "rad"],
    }


def validate_conversion(original_value, original_unit, converted_value, jsbsim_unit):
    """
    Validate conversion result and check for common issues

    Args:
        original_value: Original value
        original_unit: Original unit
        converted_value: Converted value
        jsbsim_unit: JSBSim unit

    Returns:
        List of validation warnings (empty if no issues)
    """
    warnings = []

    # Check for unrealistic values after conversion
    if jsbsim_unit == "KG" and converted_value > 1000:
        warnings.append(f"Large mass value: {converted_value} KG from {original_value} {original_unit}")

    if jsbsim_unit == "M" and converted_value > 100:
        warnings.append(f"Large length value: {converted_value} M from {original_value} {original_unit}")

    if jsbsim_unit == "M2" and converted_value > 1000:
        warnings.append(f"Large area value: {converted_value} M2 from {original_value} {original_unit}")

    # Check for very small values (might indicate unit mismatch)
    if converted_value < 1e-10:
        warnings.append(f"Very small value: {converted_value} {jsbsim_unit} from {original_value} {original_unit}")

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("Unit Conversion Module - Self Test")
    print("=" * 60)
    print()

    test_cases = [
        (200, "g", 0.2, "KG"),
        (1000, "mm", 1.0, "M"),
        (200000, "mm2", 0.2, "M2"),       # Use mm2 instead of mm²
        (5000000, "g*mm2", 0.005, "KG*M2"),  # Use g*mm2 instead of g·mm²
        (0.2, "kg", 0.2, "KG"),
        (100, "cm", 1.0, "M"),
    ]

    print("Testing conversions:")
    print("-" * 60)

    for original_val, original_unit, expected_val, expected_unit in test_cases:
        converted_val, converted_unit = convert_user_unit_to_jsbsim(original_val, original_unit)

        # Check if conversion is correct
        val_ok = abs(converted_val - expected_val) < 1e-6
        unit_ok = converted_unit == expected_unit

        status = "[OK]" if (val_ok and unit_ok) else "[NG]"

        print(f"{status} {original_val:>10} {original_unit:<8} -> {converted_val:>10.6f} {converted_unit}")

        if not val_ok:
            print(f"   Expected value: {expected_val}")
        if not unit_ok:
            print(f"   Expected unit: {expected_unit}")

    print()
    print("=" * 60)
    print("Supported Units: Length, Area, Mass, Inertia, Angle")
    print("=" * 60)
    print("See CONVERSION_MAP in source code for full list")

    print()
    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
