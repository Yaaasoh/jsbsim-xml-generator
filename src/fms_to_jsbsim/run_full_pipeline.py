# run_full_pipeline.py
"""
FMS to JSBSim Full Conversion Pipeline - Orchestrator

Executes all 3 stages of the conversion pipeline:
    Stage 1: Parse .par file
    Stage 2: Calculate derivatives
    Stage 3: Generate JSBSim XML

Usage:
    python run_full_pipeline.py <input.par> <output_name> [config.yaml]

Example:
    python run_full_pipeline.py examples/sample_aircraft.par SampleAircraft

Reference:
    - WORK_INSTRUCTION_CONVERTER_IMPLEMENTATION.md: Step 6
    - CONVERTER_SPECIFICATION.md: Section 3.1
"""

import sys
import json
from pathlib import Path

# Import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from parse_par_file import parse_par_file, generate_parse_report
from calculate_derivatives import calculate_derived_parameters, load_config, generate_calculation_report
from generate_xml import generate_jsbsim_xml, generate_generation_report


def run_pipeline(par_file: str, output_name: str, config_file: str = "config/aerodynamic_assumptions.yaml"):
    """
    Run full conversion pipeline with comprehensive error handling.

    Args:
        par_file: Path to FMS .par file
        output_name: Output directory name (e.g., "SampleAircraft")
        config_file: Path to aerodynamic assumptions config

    Raises:
        FileNotFoundError: If input files are missing
        ValueError: If data validation fails
        IOError: If file operations fail
    """

    print("=" * 70)
    print(f"FMS to JSBSim Conversion Pipeline")
    print(f"Input: {par_file}")
    print(f"Output: {output_name}.xml")
    print("=" * 70)

    # Validate input file existence before starting
    if not Path(par_file).exists():
        raise FileNotFoundError(
            f"[ERROR] Input .par file not found: {par_file}\n"
            f"Please check the file path and try again."
        )

    # Create output directory
    try:
        output_dir = Path("output") / output_name
        output_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise OSError(
            f"[ERROR] Failed to create output directory: {output_dir}\n"
            f"Error: {e}"
        )

    # Stage 1: Parse
    print("\n[Stage 1] Parsing .par file...")
    try:
        parsed_json = output_dir / "parsed_data.json"
        parsed_data = parse_par_file(par_file, str(parsed_json))
        parse_report = output_dir / "parse_report.txt"
        generate_parse_report(parsed_data, str(parse_report))
        print(f"[OK] Parsed: {parsed_json}")
    except (FileNotFoundError, UnicodeDecodeError, ValueError, IOError) as e:
        print(f"\n[FAILED] Stage 1 failed: {type(e).__name__}")
        print(f"{e}")
        raise

    # Stage 2: Calculate
    print("\n[Stage 2] Calculating derivatives...")
    try:
        config = load_config(config_file)
        derived = calculate_derived_parameters(parsed_data, config)

        derived_json = output_dir / "derived_parameters.json"
        with open(derived_json, 'w', encoding='utf-8') as f:
            json.dump(derived, f, indent=2)

        calc_report = output_dir / "calculation_report.txt"
        generate_calculation_report(parsed_data, derived, config, str(calc_report))
        print(f"[OK] Calculated: {derived_json}")
    except (FileNotFoundError, ValueError, KeyError, ZeroDivisionError) as e:
        print(f"\n[FAILED] Stage 2 failed: {type(e).__name__}")
        print(f"{e}")
        raise

    # Stage 3: Generate XML
    print("\n[Stage 3] Generating JSBSim XML...")
    try:
        xml_output = output_dir / f"{output_name}.xml"
        generate_jsbsim_xml(parsed_data, derived, str(xml_output))

        gen_report = output_dir / "generation_report.txt"
        generate_generation_report(parsed_data, derived, str(xml_output), str(gen_report))
        print(f"[OK] Generated: {xml_output}")
    except (ValueError, IOError, KeyError) as e:
        print(f"\n[FAILED] Stage 3 failed: {type(e).__name__}")
        print(f"{e}")
        raise

    # Generate consolidated summary
    print("\n[Summary] Generating conversion summary...")
    try:
        summary_path = output_dir / "CONVERSION_SUMMARY.txt"
        generate_conversion_summary(parsed_data, derived, str(xml_output), str(summary_path))
    except IOError as e:
        print(f"\n[WARNING] Summary generation failed: {e}")
        # Continue despite summary failure

    print("\n" + "=" * 70)
    print("[OK] CONVERSION COMPLETE")
    print(f"Output directory: {output_dir}")
    print(f"  - {parsed_json.name}")
    print(f"  - {derived_json.name}")
    print(f"  - {xml_output.name}")
    print(f"  - Reports: parse_report.txt, calculation_report.txt, generation_report.txt")
    print(f"  - Summary: CONVERSION_SUMMARY.txt")
    print("=" * 70)


def generate_conversion_summary(parsed_data, derived, xml_path, summary_path):
    """Generate consolidated conversion summary."""
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write("FMS to JSBSim Conversion Summary\n")
        f.write("=" * 70 + "\n\n")

        aircraft = parsed_data["metadata"]["aircraft_name"]
        source = parsed_data["metadata"]["source_file"]

        f.write(f"Aircraft: {aircraft}\n")
        f.write(f"Source: {source}\n")
        f.write(f"Output: {xml_path}\n\n")

        f.write("CONVERSION STATISTICS\n")
        f.write("-" * 70 + "\n")
        f.write(f"Parsed parameters:\n")
        f.write(f"  - Geometry: {len(parsed_data['geometry'])} parameters\n")
        f.write(f"  - Mass: {len(parsed_data['mass'])} parameters\n")
        f.write(f"  - Aerodynamics: {len(parsed_data['aerodynamics'])} parameters\n")
        f.write(f"  - Control: {len(parsed_data['control'])} parameters\n")
        f.write(f"  - Propulsion: {len(parsed_data['propulsion'])} parameters\n\n")

        f.write(f"Calculated parameters:\n")
        f.write(f"  - Geometry calculations: {len(derived['calculated_geometry'])} parameters\n")
        f.write(f"  - Stability derivatives: {len(derived['stability_derivatives'])} parameters\n")
        f.write(f"  - Unit conversions: {len(derived['unit_conversions'])} parameters\n")
        f.write(f"  - Control estimates: {len(derived['control_estimates'])} parameters\n\n")

        f.write("KEY STABILITY DERIVATIVES\n")
        f.write("-" * 70 + "\n")
        for param, data in derived["stability_derivatives"].items():
            f.write(f"{param}: {data['value']:.4f} {data.get('unit', '')}\n")
            f.write(f"  Evidence Level: {data['evidence_level']}\n")
            f.write(f"  Uncertainty: ±{data['uncertainty_percent']}%\n")
            if "formula" in data:
                f.write(f"  Formula: {data['formula']}\n")
            f.write("\n")

        if derived["control_estimates"]:
            f.write("CONTROL SURFACE ESTIMATES (Data Quality Issues)\n")
            f.write("-" * 70 + "\n")
            for param, data in derived["control_estimates"].items():
                f.write(f"{param}:\n")
                f.write(f"  Original: {data['original']:.4f} rad\n")
                f.write(f"  Estimated: {data['estimated']:.4f} rad\n")
                f.write(f"  Reason: {data['reason']}\n")
                f.write(f"  Evidence Level: {data['evidence_level']}\n\n")

        f.write("NEXT STEPS\n")
        f.write("-" * 70 + "\n")
        f.write("1. Load XML in JSBSim:\n")
        f.write(f"   import jsbsim\n")
        f.write(f"   fdm = jsbsim.FGFDMExec('.')\n")
        f.write(f"   fdm.load_model('{aircraft}')\n\n")
        f.write("2. Run trim search to find equilibrium state\n")
        f.write("3. Test basic flight simulation\n")
        f.write("4. Integrate with XMI for 50 Hz control\n")
        f.write("5. Integrate with FlightGear for 3D visualization\n")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python run_full_pipeline.py <input.par> <output_name> [config.yaml]")
        print("Example: python run_full_pipeline.py examples/sample_aircraft.par SampleAircraft")
        sys.exit(1)

    par_file = sys.argv[1]
    output_name = sys.argv[2]
    config_file = sys.argv[3] if len(sys.argv) > 3 else "config/aerodynamic_assumptions.yaml"

    # Run pipeline with comprehensive error handling
    try:
        run_pipeline(par_file, output_name, config_file)
        sys.exit(0)  # Success
    except FileNotFoundError as e:
        print("\n" + "=" * 70)
        print("[FATAL ERROR] File Not Found")
        print("=" * 70)
        print(f"{e}")
        print("\nPlease check file paths and try again.")
        sys.exit(1)
    except ValueError as e:
        print("\n" + "=" * 70)
        print("[FATAL ERROR] Validation Failed")
        print("=" * 70)
        print(f"{e}")
        print("\nPlease check input data format.")
        sys.exit(2)
    except (IOError, OSError) as e:
        print("\n" + "=" * 70)
        print("[FATAL ERROR] File I/O Failed")
        print("=" * 70)
        print(f"{e}")
        print("\nPlease check file permissions and disk space.")
        sys.exit(3)
    except Exception as e:
        print("\n" + "=" * 70)
        print("[FATAL ERROR] Unexpected Error")
        print("=" * 70)
        print(f"{type(e).__name__}: {e}")
        print("\nPlease report this error with the full output log.")
        import traceback
        traceback.print_exc()
        sys.exit(99)
