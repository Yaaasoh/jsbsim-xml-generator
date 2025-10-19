#!/usr/bin/env python3
"""
Unit Conversion Test

Verifies unit conversion accuracy for aviation units
"""

import sys
from pathlib import Path

# Add src/excel_to_jsbsim to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "excel_to_jsbsim"))

from unit_conversion import convert_user_unit_to_jsbsim


def test_length_conversion():
    """Test length conversions: mm, cm, m → M, IN, FT"""
    print("\n" + "="*70)
    print("Test 1: Length Conversion")
    print("="*70)

    test_cases = [
        (1000, "mm", 1.0, "M"),
        (100, "cm", 1.0, "M"),
        (905, "mm", 0.905, "M"),
        (1, "m", 1.0, "M"),
    ]

    passed = 0
    for value, unit, expected_val, expected_unit in test_cases:
        result_val, result_unit = convert_user_unit_to_jsbsim(value, unit)

        if abs(result_val - expected_val) < 1e-6 and result_unit == expected_unit:
            print(f"[OK] {value} {unit} -> {result_val:.6f} {result_unit}")
            passed += 1
        else:
            print(f"[FAIL] {value} {unit} -> {result_val:.6f} {result_unit} (expected {expected_val} {expected_unit})")

    print(f"\nPassed: {passed}/{len(test_cases)}")
    return passed == len(test_cases)


def test_area_conversion():
    """Test area conversions: mm2, cm2, m2 → M2, FT2"""
    print("\n" + "="*70)
    print("Test 2: Area Conversion")
    print("="*70)

    test_cases = [
        (200000, "mm2", 0.2, "M2"),           # 200,000 mm² = 0.2 m²
        (103000, "mm2", 0.103, "M2"),         # 103,000 mm² = 0.103 m²
        (1000000, "mm2", 1.0, "M2"),          # 1,000,000 mm² = 1 m²
        (10000, "cm2", 1.0, "M2"),            # 10,000 cm² = 1 m²
    ]

    passed = 0
    for value, unit, expected_val, expected_unit in test_cases:
        result_val, result_unit = convert_user_unit_to_jsbsim(value, unit)

        if abs(result_val - expected_val) < 1e-6 and result_unit == expected_unit:
            print(f"[OK] {value} {unit} -> {result_val:.6f} {result_unit}")
            passed += 1
        else:
            print(f"[FAIL] {value} {unit} -> {result_val:.6f} {result_unit} (expected {expected_val} {expected_unit})")

    print(f"\nPassed: {passed}/{len(test_cases)}")
    return passed == len(test_cases)


def test_mass_conversion():
    """Test mass conversions: g, kg → KG, LBS"""
    print("\n" + "="*70)
    print("Test 3: Mass Conversion")
    print("="*70)

    test_cases = [
        (200, "g", 0.2, "KG"),               # 200 g = 0.2 kg
        (1000, "g", 1.0, "KG"),              # 1000 g = 1 kg
        (0.5, "kg", 0.5, "KG"),
        (35, "g", 0.035, "KG"),              # Battery mass
    ]

    passed = 0
    for value, unit, expected_val, expected_unit in test_cases:
        result_val, result_unit = convert_user_unit_to_jsbsim(value, unit)

        if abs(result_val - expected_val) < 1e-6 and result_unit == expected_unit:
            print(f"[OK] {value} {unit} -> {result_val:.6f} {result_unit}")
            passed += 1
        else:
            print(f"[FAIL] {value} {unit} -> {result_val:.6f} {result_unit} (expected {expected_val} {expected_unit})")

    print(f"\nPassed: {passed}/{len(test_cases)}")
    return passed == len(test_cases)


def test_inertia_conversion():
    """Test inertia conversions: g*mm2, g*cm2, kg*m2 → KG*M2, SLUG*FT2"""
    print("\n" + "="*70)
    print("Test 4: Moment of Inertia Conversion")
    print("="*70)

    test_cases = [
        (3000000, "g*mm2", 0.003, "KG*M2"),        # 3,000,000 g·mm² = 0.003 kg·m²
        (9410000, "g*mm2", 0.00941, "KG*M2"),      # Ixx from defaults
        (7480000, "g*mm2", 0.00748, "KG*M2"),      # Iyy from defaults
        (9220000, "g*mm2", 0.00922, "KG*M2"),      # Izz from defaults
        (1000000000, "g*mm2", 1.0, "KG*M2"),       # 1e9 g·mm² = 1 kg·m²
    ]

    passed = 0
    for value, unit, expected_val, expected_unit in test_cases:
        result_val, result_unit = convert_user_unit_to_jsbsim(value, unit)

        if abs(result_val - expected_val) < 1e-9 and result_unit == expected_unit:
            print(f"[OK] {value} {unit} -> {result_val:.9f} {result_unit}")
            passed += 1
        else:
            print(f"[FAIL] {value} {unit} -> {result_val:.9f} {result_unit} (expected {expected_val} {expected_unit})")

    print(f"\nPassed: {passed}/{len(test_cases)}")
    return passed == len(test_cases)


def test_unit_normalization():
    """Test unit string normalization variations"""
    print("\n" + "="*70)
    print("Test 5: Unit String Normalization")
    print("="*70)

    test_cases = [
        (100, "mm2", 0.0001, "M2"),       # mm2
        (100, "mm^2", 0.0001, "M2"),      # mm^2 (caret)
        (1000, "g*mm2", 1e-6, "KG*M2"),   # g*mm2 (asterisk)
        (1000, "g*mm^2", 1e-6, "KG*M2"),  # g*mm^2 (caret)
    ]

    passed = 0
    for value, unit, expected_val, expected_unit in test_cases:
        result_val, result_unit = convert_user_unit_to_jsbsim(value, unit)

        if abs(result_val - expected_val) < 1e-9 and result_unit == expected_unit:
            print(f"[OK] {value} {unit!r} -> {result_val:.9f} {result_unit}")
            passed += 1
        else:
            print(f"[FAIL] {value} {unit!r} -> {result_val:.9f} {result_unit} (expected {expected_val} {expected_unit})")

    print(f"\nPassed: {passed}/{len(test_cases)}")
    return passed == len(test_cases)


def test_practical_aircraft_values():
    """Test practical values from 200g UAV"""
    print("\n" + "="*70)
    print("Test 6: Practical Aircraft Values (200g UAV)")
    print("="*70)

    test_cases = [
        (103000, "mm2", 0.103, "M2", "Wing area"),
        (905, "mm", 0.905, "M", "Wingspan"),
        (200, "g", 0.2, "KG", "Empty weight"),
        (35, "g", 0.035, "KG", "Battery mass"),
        (300, "mm", 0.3, "M", "CG X position"),
        (9410000, "g*mm2", 0.00941, "KG*M2", "Ixx (roll inertia)"),
    ]

    passed = 0
    for value, unit, expected_val, expected_unit, description in test_cases:
        result_val, result_unit = convert_user_unit_to_jsbsim(value, unit)

        if abs(result_val - expected_val) < 1e-9 and result_unit == expected_unit:
            print(f"[OK] {description}: {value} {unit} -> {result_val:.6f} {result_unit}")
            passed += 1
        else:
            print(f"[FAIL] {description}: {value} {unit} -> {result_val:.6f} {result_unit}")
            print(f"      Expected: {expected_val} {expected_unit}")

    print(f"\nPassed: {passed}/{len(test_cases)}")
    return passed == len(test_cases)


def main():
    """Run all unit conversion tests"""
    print("\n" + "="*70)
    print("UNIT CONVERSION TEST SUITE")
    print("="*70)

    tests = [
        test_length_conversion,
        test_area_conversion,
        test_mass_conversion,
        test_inertia_conversion,
        test_unit_normalization,
        test_practical_aircraft_values,
    ]

    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"[ERROR] {test.__name__}: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n[OK] ALL TESTS PASSED")
        return 0
    else:
        print("\n[FAIL] SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
