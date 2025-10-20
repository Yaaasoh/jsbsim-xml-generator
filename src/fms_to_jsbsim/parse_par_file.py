# src/parse_par_file.py
"""
FMS .par File Parser - Stage 1 of FMS to JSBSim Converter

Parses Flying Model Simulator (FMS) .par files and extracts structured parameters.

Evidence Level: L1 (Direct measurement from .par file)

Usage:
    python parse_par_file.py <input.par> [output.json]

Reference:
    - WORK_INSTRUCTION_CONVERTER_IMPLEMENTATION.md: Step 1
    - CONVERTER_SPECIFICATION.md: Section 2.2
"""

import json
import re
from pathlib import Path
from typing import Dict, Any
from datetime import datetime


def parse_par_file(par_path: str, output_json: str = None) -> Dict[str, Any]:
    """
    Parse FMS .par file and extract structured parameters.

    Args:
        par_path: Path to .par file
        output_json: Path to output JSON (optional)

    Returns:
        Structured parameter dictionary

    Evidence Level: L1 (Direct extraction from .par file)

    Raises:
        FileNotFoundError: If .par file does not exist
        UnicodeDecodeError: If file encoding is not Shift-JIS
        ValueError: If .par file format is invalid
    """
    par_path = Path(par_path)

    # Validate file existence
    if not par_path.exists():
        raise FileNotFoundError(
            f"[ERROR] .par file not found: {par_path}\n"
            f"Please check the file path and try again."
        )

    # Validate file extension
    if par_path.suffix.lower() != '.par':
        raise ValueError(
            f"[ERROR] Invalid file extension: {par_path.suffix}\n"
            f"Expected .par file, got {par_path.name}"
        )

    # Read file with Shift-JIS encoding (FMS standard)
    try:
        with open(par_path, 'r', encoding='shift-jis') as f:
            lines = f.readlines()
    except UnicodeDecodeError as e:
        raise UnicodeDecodeError(
            e.encoding, e.object, e.start, e.end,
            f"[ERROR] Failed to decode {par_path.name} with Shift-JIS encoding.\n"
            f"FMS .par files must use Shift-JIS encoding.\n"
            f"Original error: {e.reason}"
        )

    # Parse pattern: value  line_num:name(unit)  description
    pattern = r'^(\S+)\s+(\d+):(\w+)\(([^)]+)\)\s+(.*)$'

    parsed_data = {
        "metadata": {
            "source_file": str(par_path),
            "encoding": "shift-jis",
            "parse_date": datetime.now().isoformat(),
            "aircraft_name": par_path.stem  # e.g., "sample_aircraft" from "sample_aircraft.par"
        },
        "geometry": {},
        "mass": {},
        "aerodynamics": {},
        "control": {},
        "propulsion": {},
        "raw_lines": []
    }

    for line in lines:
        line = line.strip()
        if not line:
            continue

        parsed_data["raw_lines"].append(line)

        match = re.match(pattern, line)
        if not match:
            continue

        value_str, line_num, param_name, unit, description = match.groups()

        # Convert value to float
        try:
            value = float(value_str)
        except ValueError:
            value = value_str  # Keep as string if not numeric

        # Categorize parameters
        # Reference: CALCULABLE_VS_INFERENCE_ANALYSIS.md Table in Section 5

        if line_num in ['16', '17', '23', '24', '25']:  # Geometry
            if line_num == '16':
                parsed_data["geometry"]["wingspan_m"] = value
            elif line_num == '17':
                parsed_data["geometry"]["chord_m"] = value
            elif line_num == '23':
                parsed_data["geometry"]["h_tail_area_m2"] = value
            elif line_num == '24':
                parsed_data["geometry"]["v_tail_area_m2"] = value
            elif line_num == '25':
                parsed_data["geometry"]["tail_arm_m"] = value

        elif line_num in ['19', '20', '21', '22']:  # Mass
            if line_num == '19':
                parsed_data["mass"]["mass_kg"] = value
            elif line_num == '20':
                parsed_data["mass"]["ixx_kgm2"] = value
            elif line_num == '21':
                parsed_data["mass"]["iyy_kgm2"] = value
            elif line_num == '22':
                parsed_data["mass"]["izz_kgm2"] = value

        elif line_num in ['8', '10', '11', '12', '14']:  # Aerodynamics
            if line_num == '8':
                parsed_data["aerodynamics"]["clalpha_rad"] = value
            elif line_num == '10':
                parsed_data["aerodynamics"]["cf"] = value
            elif line_num == '11':
                parsed_data["aerodynamics"]["cdb"] = value
            elif line_num == '12':
                parsed_data["aerodynamics"]["cl_max"] = value
            elif line_num == '14':
                parsed_data["aerodynamics"]["cm"] = value

        elif line_num in ['3', '4', '5']:  # Control surfaces
            if line_num == '3':
                parsed_data["control"]["rudder_max_rad"] = value
            elif line_num == '4':
                parsed_data["control"]["elevator_max_rad"] = value
            elif line_num == '5':
                parsed_data["control"]["aileron_max_rad"] = value

        elif line_num == '2':  # Propulsion
            parsed_data["propulsion"]["max_thrust_n"] = value

    # Validate that essential parameters were extracted
    required_geometry = ['wingspan_m', 'chord_m', 'h_tail_area_m2', 'v_tail_area_m2', 'tail_arm_m']
    required_mass = ['mass_kg', 'ixx_kgm2', 'iyy_kgm2', 'izz_kgm2']
    required_aero = ['clalpha_rad']

    missing_params = []
    for param in required_geometry:
        if param not in parsed_data["geometry"]:
            missing_params.append(f"geometry.{param}")
    for param in required_mass:
        if param not in parsed_data["mass"]:
            missing_params.append(f"mass.{param}")
    for param in required_aero:
        if param not in parsed_data["aerodynamics"]:
            missing_params.append(f"aerodynamics.{param}")

    if missing_params:
        raise ValueError(
            f"[ERROR] Missing required parameters in {par_path.name}:\n"
            f"  {', '.join(missing_params)}\n"
            f"The .par file may be incomplete or in an unsupported format."
        )

    # Save to JSON if output path specified
    if output_json:
        try:
            output_path = Path(output_json)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(parsed_data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            raise IOError(
                f"[ERROR] Failed to write output JSON: {output_json}\n"
                f"Error: {e}"
            )

    return parsed_data


def generate_parse_report(parsed_data: Dict[str, Any], report_path: str):
    """Generate human-readable parse report."""
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("FMS .par File Parse Report\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Source File: {parsed_data['metadata']['source_file']}\n")
        f.write(f"Aircraft Name: {parsed_data['metadata']['aircraft_name']}\n")
        f.write(f"Parse Date: {parsed_data['metadata']['parse_date']}\n\n")

        f.write("Extracted Parameters:\n")
        f.write("-" * 50 + "\n")
        f.write(f"Geometry: {len(parsed_data['geometry'])} parameters\n")
        f.write(f"Mass: {len(parsed_data['mass'])} parameters\n")
        f.write(f"Aerodynamics: {len(parsed_data['aerodynamics'])} parameters\n")
        f.write(f"Control: {len(parsed_data['control'])} parameters\n")
        f.write(f"Propulsion: {len(parsed_data['propulsion'])} parameters\n\n")

        # List all extracted values
        for category, params in parsed_data.items():
            if category in ['metadata', 'raw_lines']:
                continue
            f.write(f"\n{category.upper()}:\n")
            for param, value in params.items():
                f.write(f"  {param}: {value}\n")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python parse_par_file.py <input.par> [output.json]")
        sys.exit(1)

    par_file = sys.argv[1]
    output_json = sys.argv[2] if len(sys.argv) > 2 else "parsed_data.json"

    parsed = parse_par_file(par_file, output_json)

    report_path = "parse_report.txt"
    generate_parse_report(parsed, report_path)

    print(f"[OK] Parse complete: {output_json}")
    print(f"[OK] Report generated: {report_path}")
