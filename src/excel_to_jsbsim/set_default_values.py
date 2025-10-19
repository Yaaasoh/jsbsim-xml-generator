#!/usr/bin/env python3
"""
Set default values in Excel template for 200g class UAV

Purpose: Populate JSBSim_XML_Authoring_Template_v1.xlsx with typical 200g aircraft values
Author: Claude Code
Date: 2025-10-05
"""

import pandas as pd
from pathlib import Path
import sys

# Default values for 200g class RC UAV (using practical units: g, mm)
DEFAULT_VALUES = {
    "T_01_fileheader": {
        "fileheader/name": {
            "Value": "ExampleAircraft",
            "Unit": "",
            "Note": "200g class RC UAV model name"
        },
        "fileheader/version": {
            "Value": "2.0",
            "Unit": "",
            "Note": "JSBSim format version"
        },
        "fileheader/description": {
            "Value": "200g class fixed-wing aircraft - standard configuration",
            "Unit": "",
            "Note": "Brief description of the aircraft"
        },
    },
    "T_02_metrics": {
        "metrics/wing_area": {
            "Value": 103000,
            "Unit": "mm2",
            "Note": "Wing area: 0.103 m2 = 103,000 mm2. Typical value for 200g class fixed-wing aircraft."
        },
        "metrics/wing_span": {
            "Value": 905,
            "Unit": "mm",
            "Note": "Wingspan: 0.905 m = 905 mm. Typical value for 200g class fixed-wing aircraft."
        },
        "metrics/chord_avg": {
            "Value": 114,
            "Unit": "mm",
            "Note": "Average chord: 0.114 m = 114 mm. wing_area / wing_span = 103000/905"
        },
        "metrics/ref_point/x": {
            "Value": 50,
            "Unit": "mm",
            "Note": "Reference point X: 50mm from nose (placeholder, AERORP auto-generated at 25% chord)"
        },
        "metrics/ref_point/y": {
            "Value": 0,
            "Unit": "mm",
            "Note": "Reference point Y: 0 (centerline)"
        },
        "metrics/ref_point/z": {
            "Value": 0,
            "Unit": "mm",
            "Note": "Reference point Z: 0 (horizontal datum)"
        },
    },
    "T_03_mass_balance": {
        "mass/I/ixx": {
            "Value": 9410000,
            "Unit": "g*mm2",
            "Note": "Roll inertia: 0.00941 kg·m2 = 9,410,000 g·mm2. Typical value for 200g class fixed-wing aircraft."
        },
        "mass/I/iyy": {
            "Value": 7480000,
            "Unit": "g*mm2",
            "Note": "Pitch inertia: 0.00748 kg·m2 = 7,480,000 g·mm2. Typical value for 200g class fixed-wing aircraft."
        },
        "mass/I/izz": {
            "Value": 9220000,
            "Unit": "g*mm2",
            "Note": "Yaw inertia: 0.00922 kg·m2 = 9,220,000 g·mm2. Typical value for 200g class fixed-wing aircraft."
        },
        "mass/empty_weight": {
            "Value": 200,
            "Unit": "g",
            "Note": "Empty weight: 0.2 kg = 200 g. Target weight for 200g class competition"
        },
        "mass/CG/x": {
            "Value": 300,
            "Unit": "mm",
            "Note": "CG X: 300mm from nose. Typical value at approximately 35% MAC for stable flight."
        },
        "mass/CG/y": {
            "Value": 0,
            "Unit": "mm",
            "Note": "CG Y: 0 (centerline)"
        },
        "mass/CG/z": {
            "Value": 0,
            "Unit": "mm",
            "Note": "CG Z: 0 (horizontal datum)"
        },
        "mass/pointmass/name": {
            "Value": "Battery",
            "Unit": "",
            "Note": "Battery pointmass name"
        },
        "mass/pointmass/mass": {
            "Value": 35,
            "Unit": "g",
            "Note": "Battery mass: 35g (LiPo 2S 250mAh typical)"
        },
        "mass/pointmass/x": {
            "Value": 120,
            "Unit": "mm",
            "Note": "Battery X: 120mm (forward of CG for balance)"
        },
        "mass/pointmass/y": {
            "Value": 0,
            "Unit": "mm",
            "Note": "Battery Y: 0 (centerline)"
        },
        "mass/pointmass/z": {
            "Value": 0,
            "Unit": "mm",
            "Note": "Battery Z: 0 (horizontal datum)"
        },
    },
    "T_05_propulsion": {
        "propulsion/engine/type": {
            "Value": "electric",
            "Unit": "",
            "Note": "Electric motor type"
        },
        "propulsion/engine/name": {
            "Value": "Coreless_7mm",
            "Unit": "",
            "Note": "7mm coreless motor (typical for 200g class)"
        },
        "propulsion/engine/file": {
            "Value": "motor_coreless",
            "Unit": "",
            "Note": "Engine definition file (to be created)"
        },
        "propulsion/thruster/type": {
            "Value": "propeller",
            "Unit": "",
            "Note": "Propeller thruster type"
        },
        "propulsion/thruster/name": {
            "Value": "APC_5x3",
            "Unit": "",
            "Note": "APC 5x3 propeller (5 inch diameter, 3 inch pitch)"
        },
        "propulsion/thruster/x": {
            "Value": 20,
            "Unit": "mm",
            "Note": "Thruster X: 20mm (nose area)"
        },
        "propulsion/thruster/y": {
            "Value": 0,
            "Unit": "mm",
            "Note": "Thruster Y: 0 (centerline)"
        },
        "propulsion/thruster/z": {
            "Value": 0,
            "Unit": "mm",
            "Note": "Thruster Z: 0 (horizontal datum)"
        },
    },
    "T_08_output": {
        "output/file": {
            "Value": "rc_uav.csv",
            "Unit": "",
            "Note": "Output CSV file name"
        },
        "output/rate_hz": {
            "Value": 50,
            "Unit": "Hz",
            "Note": "Output rate: 50 Hz (20ms interval)"
        },
        "output/properties": {
            "Value": "velocities/v_ind_mps; aero/alpha_deg",
            "Unit": "",
            "Note": "Output properties (semicolon separated)"
        },
    },
}


def set_defaults(template_path, output_path=None):
    """
    Set default values in Excel template

    Args:
        template_path: Path to input template
        output_path: Path to output template (if None, overwrites input)
    """
    if output_path is None:
        output_path = template_path

    print("=" * 70)
    print("Setting default values in Excel template")
    print("=" * 70)
    print(f"Input:  {template_path}")
    print(f"Output: {output_path}")
    print()

    # Read Excel file
    xl = pd.ExcelFile(template_path)

    # Create ExcelWriter
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Process each sheet
        for sheet_name in xl.sheet_names:
            print(f"Processing: {sheet_name}")

            df = pd.read_excel(template_path, sheet_name=sheet_name)

            # Apply default values if available
            if sheet_name in DEFAULT_VALUES:
                defaults = DEFAULT_VALUES[sheet_name]

                for varname, values in defaults.items():
                    # Find row with this VarName
                    mask = df["VarName (property/tag)"] == varname

                    if mask.any():
                        # Update Value, Unit, Note columns
                        df.loc[mask, "Value"] = values["Value"]
                        if "Unit" in values and values["Unit"]:
                            df.loc[mask, "Unit"] = values["Unit"]
                        if "Note" in values and values["Note"]:
                            df.loc[mask, "Note"] = values["Note"]

                        print(f"  [OK] {varname}: {values['Value']} {values.get('Unit', '')}")
                    else:
                        print(f"  [SKIP] {varname}: not found in sheet")

            # Write sheet to output
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    print()
    print("=" * 70)
    print("[OK] Default values set successfully")
    print("=" * 70)


def main():
    import argparse

    ap = argparse.ArgumentParser(description="Set default values in Excel template")
    ap.add_argument("-i", "--input", required=True, help="Input Excel template path")
    ap.add_argument("-o", "--output", help="Output Excel path (default: overwrite input)")
    args = ap.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else input_path

    if not input_path.exists():
        print(f"[ERROR] Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    set_defaults(input_path, output_path)


if __name__ == "__main__":
    main()
