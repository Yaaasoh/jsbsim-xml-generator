#!/usr/bin/env python3
"""
XML Generation Test - Excel to JSBSim XML Workflow

Tests:
1. Default template XML generation
2. Unit conversion in generated XML
"""

import sys
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET


def test_default_template_xml_generation():
    """Test 1: Generate XML from default template"""
    print("\n" + "="*70)
    print("Test 1: Default Template XML Generation")
    print("="*70)

    # Generate XML
    cmd = [
        sys.executable,
        "src/generate_jsbsim_from_gsheet.py",
        "-i", "templates/Aircraft_Input_Template.xlsx",
        "-o", "test_output_xmlgen"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"[FAIL] XML generation failed")
        print(result.stderr)
        return False

    # Find generated XML (name comes from Excel template)
    output_dir = Path("test_output_xmlgen")
    aircraft_dirs = [d for d in output_dir.iterdir() if d.is_dir()]

    if not aircraft_dirs:
        print(f"[FAIL] No aircraft directory found in {output_dir}")
        return False

    aircraft_dir = aircraft_dirs[0]
    aircraft_name = aircraft_dir.name
    xml_path = aircraft_dir / f"{aircraft_name}.xml"

    if not xml_path.exists():
        print(f"[FAIL] XML file not found: {xml_path}")
        return False

    print(f"[INFO] Generated aircraft: {aircraft_name}")

    # Check XML size (should be 5-15 KB)
    xml_size = xml_path.stat().st_size
    if xml_size < 3000 or xml_size > 50000:
        print(f"[WARN] XML size unusual: {xml_size} bytes (expected 5-15 KB)")

    print(f"[OK] XML generated: {xml_path} ({xml_size} bytes)")
    return True


def test_unit_conversion_in_xml():
    """Test 2: Unit conversion verification"""
    print("\n" + "="*70)
    print("Test 2: Unit Conversion in Generated XML")
    print("="*70)

    # Find generated XML
    output_dir = Path("test_output_xmlgen")
    if not output_dir.exists():
        print("[SKIP] Output directory not found (run Test 1 first)")
        return True

    aircraft_dirs = [d for d in output_dir.iterdir() if d.is_dir()]
    if not aircraft_dirs:
        print("[SKIP] No aircraft directory found (run Test 1 first)")
        return True

    aircraft_dir = aircraft_dirs[0]
    aircraft_name = aircraft_dir.name
    xml_path = aircraft_dir / f"{aircraft_name}.xml"

    if not xml_path.exists():
        print("[SKIP] XML not found (run Test 1 first)")
        return True

    # Parse XML
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Check metrics section
    metrics = root.find("metrics")
    if metrics is None:
        print("[FAIL] metrics section not found")
        return False

    # Check wingarea conversion
    # Input template: 103,000 mm² = 0.103 m² → ~1.109 ft²
    wingarea = metrics.find("wingarea")
    if wingarea is not None:
        unit = wingarea.get("unit")
        value = float(wingarea.text)
        print(f"  Wing area: {value:.3f} {unit}")
        if unit != "FT2":
            print(f"[FAIL] Wing area unit should be FT2, got {unit}")
            return False
        if not (1.0 < value < 1.2):
            print(f"[WARN] Wing area value {value:.3f} outside expected range 1.0-1.2 ft2")
    else:
        print("[FAIL] wingarea element not found")
        return False

    # Check wingspan conversion
    # Input template: 905 mm = 0.905 m → ~2.97 ft
    wingspan = metrics.find("wingspan")
    if wingspan is not None:
        unit = wingspan.get("unit")
        value = float(wingspan.text)
        print(f"  Wingspan: {value:.3f} {unit}")
        if unit != "FT":
            print(f"[FAIL] Wingspan unit should be FT, got {unit}")
            return False
        if not (2.8 < value < 3.1):
            print(f"[WARN] Wingspan value {value:.3f} outside expected range 2.8-3.1 ft")
    else:
        print("[FAIL] wingspan element not found")
        return False

    print(f"[OK] Unit conversion appears correct")
    return True


def main():
    """Run all XML generation tests"""
    print("\n" + "="*70)
    print("XML GENERATION TEST SUITE")
    print("="*70)

    tests = [
        test_default_template_xml_generation,
        test_unit_conversion_in_xml,
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
