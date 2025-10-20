# src/calculate_derivatives.py
"""
Aerodynamic Derivatives Calculator - Stage 2 of FMS to JSBSim Converter

Calculates stability derivatives and performs unit conversions.

Evidence Levels:
    - L2: Theoretical calculations (V_H, V_v, Cmalpha, Cmq, etc.)
    - L3: Standard assumptions (eta, deps_dalpha, tau)
    - L6: Provisional estimates (unrealistic control surface deflections)

Usage:
    python calculate_derivatives.py <parsed_data.json> [config.yaml] [output.json]

Reference:
    - WORK_INSTRUCTION_CONVERTER_IMPLEMENTATION.md: Step 3
    - CALCULABLE_VS_INFERENCE_ANALYSIS.md: Section 4 (Formulas)
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any
import math


def load_config(config_path: str = "config/aerodynamic_assumptions.yaml") -> Dict:
    """
    Load aerodynamic assumptions from YAML config.

    Raises:
        FileNotFoundError: If config file does not exist
        yaml.YAMLError: If config file is not valid YAML
        ValueError: If config is missing required fields
    """
    config_path_obj = Path(config_path)

    if not config_path_obj.exists():
        raise FileNotFoundError(
            f"[ERROR] Config file not found: {config_path}\n"
            f"Expected config file at: {config_path_obj.absolute()}\n"
            f"Please create config/aerodynamic_assumptions.yaml"
        )

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise yaml.YAMLError(
            f"[ERROR] Invalid YAML format in {config_path}:\n{e}"
        )

    # Validate required config sections
    required_sections = ['tail_efficiency', 'downwash', 'control_surfaces', 'unit_conversions']
    missing_sections = [s for s in required_sections if s not in config]

    if missing_sections:
        raise ValueError(
            f"[ERROR] Config file missing required sections:\n"
            f"  {', '.join(missing_sections)}\n"
            f"File: {config_path}"
        )

    return config


def calculate_derived_parameters(parsed_data: Dict[str, Any], config: Dict) -> Dict[str, Any]:
    """
    Calculate all derived parameters from parsed .par data.

    Evidence Levels:
        - L2: Theoretical calculations (geometry, stability derivatives)
        - L3: Calculations using standard assumptions (eta, deps_dalpha, tau)
        - L6: Provisional estimates (unrealistic control deflections)

    Raises:
        KeyError: If required parameters are missing from parsed_data
        ValueError: If parameter values are invalid (e.g., division by zero)
    """

    # Extract parsed values for convenience
    try:
        geom = parsed_data["geometry"]
        mass = parsed_data["mass"]
        aero = parsed_data["aerodynamics"]
        ctrl = parsed_data["control"]
        prop = parsed_data["propulsion"]
    except KeyError as e:
        raise KeyError(
            f"[ERROR] Missing required category in parsed_data: {e}\n"
            f"Available categories: {list(parsed_data.keys())}"
        )

    # Validate geometry parameters to prevent division by zero
    if geom.get("wingspan_m", 0) == 0:
        raise ValueError("[ERROR] wingspan_m cannot be zero")
    if geom.get("chord_m", 0) == 0:
        raise ValueError("[ERROR] chord_m cannot be zero")
    if aero.get("clalpha_rad", 0) == 0:
        raise ValueError("[ERROR] clalpha_rad cannot be zero")

    # Get config assumptions
    eta = config["tail_efficiency"]["horizontal_eta"]
    eta_v = config["tail_efficiency"]["vertical_eta_v"]
    deps_dalpha = config["downwash"]["deps_dalpha"]
    tau = config["control_surfaces"]["elevator_tau"]
    e = config["induced_drag"]["oswald_efficiency"]

    # Unit conversions
    m_to_ft = config["unit_conversions"]["m_to_ft"]
    m2_to_ft2 = config["unit_conversions"]["m2_to_ft2"]
    kg_to_lbs = config["unit_conversions"]["kg_to_lbs"]
    kgm2_to_slugft2 = config["unit_conversions"]["kgm2_to_slugft2"]
    n_to_lbf = config["unit_conversions"]["n_to_lbf"]

    derived = {
        "calculated_geometry": {},
        "stability_derivatives": {},
        "control_estimates": {},
        "unit_conversions": {}
    }

    # ===== GEOMETRY CALCULATIONS =====
    # Evidence Level: L2 (Theoretical calculation)

    # Wing area (rectangular approximation)
    S_m2 = geom["wingspan_m"] * geom["chord_m"]
    S_ft2 = S_m2 * m2_to_ft2

    # Aspect ratio
    AR = (geom["wingspan_m"] ** 2) / S_m2

    # Tail volume ratios
    V_H = (geom["tail_arm_m"] * geom["h_tail_area_m2"]) / (geom["chord_m"] * S_m2)
    V_v = (geom["tail_arm_m"] * geom["v_tail_area_m2"]) / (geom["wingspan_m"] * S_m2)

    derived["calculated_geometry"] = {
        "wing_area_m2": S_m2,
        "wing_area_ft2": S_ft2,
        "aspect_ratio": AR,
        "tail_volume_h": V_H,
        "tail_volume_v": V_v
    }

    # ===== STABILITY DERIVATIVES =====
    # Reference: CALCULABLE_VS_INFERENCE_ANALYSIS.md Section 4

    CLalpha = aero["clalpha_rad"]

    # Cmalpha (pitching moment derivative)
    # Formula: -eta * V_H * CLalpha_tail * (1 - deps_dalpha)
    # Evidence Level: L3 (uses eta, deps_dalpha assumptions)
    Cmalpha = -eta * V_H * CLalpha * (1 - deps_dalpha)

    # Cmq (pitch damping)
    # Formula: -2 * V_H * CLalpha_tail * (tail_arm / chord)
    # Evidence Level: L3 (uses eta assumption)
    Cmq = -2 * V_H * CLalpha * (geom["tail_arm_m"] / geom["chord_m"])

    # Cm_de (elevator effectiveness)
    # Formula: -eta * V_H * tau * CLalpha_tail
    # Evidence Level: L3 (uses eta, tau assumptions)
    Cm_de = -eta * V_H * tau * CLalpha

    # Cybeta (side force derivative)
    # Formula: -CLalpha_v * (Sv / S)
    # Evidence Level: L2 (theoretical calculation)
    Cybeta = -CLalpha * (geom["v_tail_area_m2"] / S_m2)

    # Cnbeta (weathercock stability)
    # Formula: eta_v * V_v * CLalpha_v
    # Evidence Level: L3 (uses eta_v assumption)
    Cnbeta = eta_v * V_v * CLalpha

    # Clbeta (dihedral effect) - assume small dihedral
    # Evidence Level: L3 (conservative estimate)
    Clbeta = -0.025  # Small value, conservative

    # Clp (roll damping)
    # Formula: -CLalpha / 12
    # Evidence Level: L3 (empirical formula)
    Clp = -CLalpha / 12

    # Cnr (yaw damping)
    # Formula: -2 * eta_v * V_v * (tail_arm / wingspan)
    # Evidence Level: L3 (uses eta_v assumption)
    Cnr = -2 * eta_v * V_v * (geom["tail_arm_m"] / geom["wingspan_m"])

    derived["stability_derivatives"] = {
        "cmalpha": {
            "value": Cmalpha,
            "unit": "/rad",
            "formula": "-eta * V_H * CLalpha_tail * (1 - deps_dalpha)",
            "assumptions": {"eta": eta, "deps_dalpha": deps_dalpha},
            "uncertainty_percent": 25,
            "evidence_level": "L3"
        },
        "cmq": {
            "value": Cmq,
            "unit": "/rad/s",
            "formula": "-2 * V_H * CLalpha_tail * (tail_arm / chord)",
            "uncertainty_percent": 20,
            "evidence_level": "L3"
        },
        "cm_de": {
            "value": Cm_de,
            "unit": "/rad",
            "formula": "-eta * V_H * tau * CLalpha_tail",
            "assumptions": {"eta": eta, "tau": tau},
            "uncertainty_percent": 25,
            "evidence_level": "L3"
        },
        "cybeta": {
            "value": Cybeta,
            "unit": "/rad",
            "formula": "-CLalpha_v * (Sv / S)",
            "uncertainty_percent": 20,
            "evidence_level": "L2"
        },
        "cnbeta": {
            "value": Cnbeta,
            "unit": "/rad",
            "formula": "eta_v * V_v * CLalpha_v",
            "assumptions": {"eta_v": eta_v},
            "uncertainty_percent": 30,
            "evidence_level": "L3"
        },
        "clbeta": {
            "value": Clbeta,
            "unit": "/rad",
            "formula": "Conservative estimate for small dihedral",
            "uncertainty_percent": 30,
            "evidence_level": "L3"
        },
        "clp": {
            "value": Clp,
            "unit": "/rad/s",
            "formula": "-CLalpha / 12",
            "uncertainty_percent": 30,
            "evidence_level": "L3"
        },
        "cnr": {
            "value": Cnr,
            "unit": "/rad/s",
            "formula": "-2 * eta_v * V_v * (tail_arm / wingspan)",
            "uncertainty_percent": 30,
            "evidence_level": "L3"
        }
    }

    # ===== CONTROL SURFACE ESTIMATES =====
    # Evidence Level: L6 (Provisional estimates for unrealistic data)
    # Check if .par data is realistic

    aileron_max = ctrl.get("aileron_max_rad", 0)
    rudder_max = ctrl.get("rudder_max_rad", 0)
    elevator_max = ctrl.get("elevator_max_rad", 0)

    # Aileron unrealistic check (< 5°)
    if aileron_max < 0.087:
        derived["control_estimates"]["aileron_max_rad"] = {
            "original": aileron_max,
            "estimated": config["control_estimates"]["aileron_max_rad"],
            "reason": f"Original {aileron_max:.4f} rad ({math.degrees(aileron_max):.2f}°) unrealistic, using typical 20°",
            "evidence_level": "L6"
        }

    # Rudder missing check
    if rudder_max == 0:
        derived["control_estimates"]["rudder_max_rad"] = {
            "original": rudder_max,
            "estimated": config["control_estimates"]["rudder_max_rad"],
            "reason": "Missing rudder data (0 rad), using typical 20°",
            "evidence_level": "L6"
        }

    # ===== UNIT CONVERSIONS =====
    # Evidence Level: L1 (Direct conversion from L1 parameters)

    derived["unit_conversions"] = {
        "wingspan_ft": geom["wingspan_m"] * m_to_ft,
        "chord_ft": geom["chord_m"] * m_to_ft,
        "h_tail_area_ft2": geom["h_tail_area_m2"] * m2_to_ft2,
        "v_tail_area_ft2": geom["v_tail_area_m2"] * m2_to_ft2,
        "tail_arm_ft": geom["tail_arm_m"] * m_to_ft,
        "mass_lbs": mass["mass_kg"] * kg_to_lbs,
        "ixx_slugft2": mass["ixx_kgm2"] * kgm2_to_slugft2,
        "iyy_slugft2": mass["iyy_kgm2"] * kgm2_to_slugft2,
        "izz_slugft2": mass["izz_kgm2"] * kgm2_to_slugft2,
        "max_thrust_lbf": prop["max_thrust_n"] * n_to_lbf
    }

    return derived


def generate_calculation_report(parsed_data: Dict, derived: Dict, config: Dict, report_path: str):
    """Generate detailed calculation report."""
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("FMS to JSBSim Calculation Report\n")
        f.write("=" * 70 + "\n\n")

        aircraft = parsed_data["metadata"]["aircraft_name"]
        f.write(f"Aircraft: {aircraft}\n")
        f.write(f"Source: {parsed_data['metadata']['source_file']}\n\n")

        f.write("CALCULATED GEOMETRY\n")
        f.write("-" * 70 + "\n")
        for param, value in derived["calculated_geometry"].items():
            f.write(f"  {param}: {value:.4f}\n")

        f.write("\nSTABILITY DERIVATIVES\n")
        f.write("-" * 70 + "\n")
        for param, data in derived["stability_derivatives"].items():
            f.write(f"\n{param}:\n")
            f.write(f"  Value: {data['value']:.4f} {data.get('unit', '')}\n")
            if "formula" in data:
                f.write(f"  Formula: {data['formula']}\n")
            if "assumptions" in data:
                f.write(f"  Assumptions: {data['assumptions']}\n")
            f.write(f"  Uncertainty: ±{data['uncertainty_percent']}%\n")
            f.write(f"  Evidence Level: {data['evidence_level']}\n")

        if derived["control_estimates"]:
            f.write("\nCONTROL SURFACE ESTIMATES (Data Quality Issues)\n")
            f.write("-" * 70 + "\n")
            for param, data in derived["control_estimates"].items():
                f.write(f"\n{param}:\n")
                f.write(f"  Original: {data['original']:.4f} rad\n")
                f.write(f"  Estimated: {data['estimated']:.4f} rad\n")
                f.write(f"  Reason: {data['reason']}\n")
                f.write(f"  Evidence Level: {data['evidence_level']}\n")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python calculate_derivatives.py <parsed_data.json> [config.yaml] [output.json]")
        sys.exit(1)

    parsed_json = sys.argv[1]
    config_yaml = sys.argv[2] if len(sys.argv) > 2 else "config/aerodynamic_assumptions.yaml"
    output_json = sys.argv[3] if len(sys.argv) > 3 else "derived_parameters.json"

    # Load inputs
    with open(parsed_json, 'r', encoding='utf-8') as f:
        parsed_data = json.load(f)

    config = load_config(config_yaml)

    # Calculate
    derived = calculate_derived_parameters(parsed_data, config)

    # Save outputs
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(derived, f, indent=2)

    report_path = "calculation_report.txt"
    generate_calculation_report(parsed_data, derived, config, report_path)

    print(f"[OK] Calculation complete: {output_json}")
    print(f"[OK] Report generated: {report_path}")
