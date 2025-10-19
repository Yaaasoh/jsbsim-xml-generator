# src/jsbsim_trim_wrapper.py
"""
JSBSim Trim Search Wrapper - Stage 4A of FMS to JSBSim Converter

Provides interface to JSBSim's trim search functionality for automatic
equilibrium flight state calculation.

Technical Basis:
    - JSBSim trim search = 6-DOF steady flight state automatic search
    - Uses Newton-Raphson method to find equilibrium
    - Output: elevator, throttle, alpha equilibrium values
    - Reference: JSBSim Reference Manual Section 5.2 "Trim Analysis"

Usage:
    result = run_trim_search('aircraft.xml', V_m_s=15.0, altitude_m=100)
    if result['converged']:
        print(f"Elevator: {result['elevator_deg']:.2f}°")
        print(f"Throttle: {result['throttle']:.3f}")
        print(f"Alpha: {result['alpha_deg']:.2f}°")
        print(f"L/D: {result['L_D']:.2f}")

Reference:
    - WORK_INSTRUCTION_CONVERTER_IMPLEMENTATION.md: Task 6B-1
    - NEXT_ACTIONS_COMMUNICATION.md: Phase 2 implementation
"""

import jsbsim
import numpy as np
from pathlib import Path
from typing import Dict, Any


def run_trim_search(xml_path: str, V_m_s: float, altitude_m: float = 0) -> Dict[str, Any]:
    """
    Execute JSBSim trim search for steady flight state.

    Technical Details:
        - Trim mode 2 = Longitudinal trim (elevator + throttle)
        - Searches for: dU/dt = 0, dW/dt = 0, dQ/dt = 0
        - Constraint: gamma = 0 (level flight)

    Args:
        xml_path: JSBSim aircraft XML file path (absolute or relative)
        V_m_s: Target airspeed [m/s]
        altitude_m: Altitude MSL [m] (default: 0)

    Returns:
        Dictionary with trim results:
        {
            'converged': bool,              # True if trim search succeeded
            'elevator_deg': float,          # Elevator deflection [°]
            'throttle': float,              # Throttle setting [0-1]
            'alpha_deg': float,             # Angle of attack [°]
            'pitch_deg': float,             # Pitch angle [°]
            'L_D': float,                   # Lift-to-drag ratio
            'iterations': int,              # Number of iterations
            'speed_m_s': float,             # Actual achieved speed [m/s]
            'error': str                    # Error message (if converged=False)
        }

    Raises:
        FileNotFoundError: If XML file does not exist
        ValueError: If input parameters are invalid
    """

    # Input validation
    xml_path_obj = Path(xml_path)
    if not xml_path_obj.exists():
        raise FileNotFoundError(
            f"[ERROR] Aircraft XML not found: {xml_path}\n"
            f"Expected path: {xml_path_obj.absolute()}"
        )

    if V_m_s <= 0:
        raise ValueError(f"[ERROR] Airspeed must be positive: {V_m_s} m/s")

    if altitude_m < 0:
        raise ValueError(f"[ERROR] Altitude cannot be negative: {altitude_m} m")

    # JSBSim initialization
    try:
        # JSBSim requires this directory structure:
        # jsbsim_root/
        #   aircraft/
        #     aircraft_name/
        #       aircraft_name.xml

        # Check if aircraft directory structure exists
        aircraft_dir = xml_path_obj.parent
        aircraft_name = xml_path_obj.stem

        # JSBSim root should contain 'aircraft' folder
        # If XML is in output/Aircraft_Name/, root should be output/
        jsbsim_root = str(aircraft_dir.parent)

        # Check if we need to create 'aircraft' directory structure
        aircraft_folder = aircraft_dir.parent / "aircraft"
        if not aircraft_folder.exists():
            aircraft_folder.mkdir(parents=True, exist_ok=True)

        # Create symlink or copy to aircraft folder
        target_aircraft_dir = aircraft_folder / aircraft_name
        if not target_aircraft_dir.exists():
            target_aircraft_dir.mkdir(parents=True, exist_ok=True)
            # Copy XML to expected location
            import shutil
            target_xml = target_aircraft_dir / f"{aircraft_name}.xml"
            shutil.copy2(xml_path_obj, target_xml)

        fdm = jsbsim.FGFDMExec(jsbsim_root)

        # Load aircraft model
        success = fdm.load_model(aircraft_name)

        if not success:
            return {
                'converged': False,
                'error': f"Failed to load aircraft model: {aircraft_name}"
            }

        # Set initial conditions
        # JSBSim uses imperial units internally
        fdm['ic/h-sl-ft'] = altitude_m * 3.28084  # m → ft
        fdm['ic/vc-kts'] = V_m_s * 1.94384        # m/s → kts

        # Initialize simulation
        fdm.run_ic()

        # Execute trim search
        # Mode 2 = Longitudinal trim (vtFull)
        # Reference: JSBSim/src/models/FGTrim.cpp
        fdm.do_trim(2)

        # Check convergence
        # JSBSim sets trim status property after trim
        converged = fdm['simulation/trim-completed'] == 1

        if not converged:
            return {
                'converged': False,
                'error': "Trim search did not converge"
            }

        # Extract trim results
        elevator_rad = fdm['fcs/elevator-pos-rad']
        throttle = fdm['fcs/throttle-pos-norm']
        alpha_rad = fdm['aero/alpha-rad']
        pitch_rad = fdm['attitude/theta-rad']

        # Aerodynamic performance
        lift_lbs = fdm['forces/fbz-aero-lbs']
        drag_lbs = fdm['forces/fbx-aero-lbs']

        # Calculate L/D (lift is negative in JSBSim body frame)
        lift_N = abs(lift_lbs) * 4.44822  # lbs → N
        drag_N = abs(drag_lbs) * 4.44822  # lbs → N
        L_D = lift_N / drag_N if drag_N > 0.01 else 0

        # Actual achieved speed
        actual_speed_kts = fdm['velocities/vc-kts']
        actual_speed_m_s = actual_speed_kts / 1.94384

        return {
            'converged': True,
            'elevator_deg': np.rad2deg(elevator_rad),
            'throttle': throttle,
            'alpha_deg': np.rad2deg(alpha_rad),
            'pitch_deg': np.rad2deg(pitch_rad),
            'L_D': L_D,
            'iterations': 0,  # JSBSim doesn't expose iteration count
            'speed_m_s': actual_speed_m_s,
            'error': None
        }

    except Exception as e:
        return {
            'converged': False,
            'error': f"JSBSim exception: {str(e)}"
        }


def run_trim_multiple_speeds(xml_path: str, speeds_m_s: list, altitude_m: float = 0) -> list:
    """
    Run trim search at multiple airspeeds.

    Useful for analyzing trim characteristics across speed envelope.

    Args:
        xml_path: JSBSim aircraft XML file path
        speeds_m_s: List of target airspeeds [m/s]
        altitude_m: Altitude MSL [m]

    Returns:
        List of trim result dictionaries (one per speed)

    Example:
        results = run_trim_multiple_speeds('aircraft.xml', [10, 15, 20])
        for i, result in enumerate(results):
            if result['converged']:
                print(f"Speed {speeds_m_s[i]} m/s: Elevator {result['elevator_deg']:.2f}°")
    """
    results = []

    for V_m_s in speeds_m_s:
        result = run_trim_search(xml_path, V_m_s, altitude_m)
        result['target_speed_m_s'] = V_m_s
        results.append(result)

    return results


def evaluate_trim_quality(trim_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate trim result quality based on physical realism.

    Quality Criteria:
        - Elevator: -25° to +25° (realistic control authority)
        - Throttle: 0.1 to 0.9 (avoid saturation)
        - Alpha: 0° to 15° (typical flight range)
        - L/D: > 5 (reasonable efficiency)

    Args:
        trim_result: Output from run_trim_search()

    Returns:
        {
            'overall': str,           # 'GOOD', 'ACCEPTABLE', 'POOR'
            'elevator_ok': bool,
            'throttle_ok': bool,
            'alpha_ok': bool,
            'L_D_ok': bool,
            'issues': list            # List of identified issues
        }
    """
    if not trim_result['converged']:
        return {
            'overall': 'POOR',
            'elevator_ok': False,
            'throttle_ok': False,
            'alpha_ok': False,
            'L_D_ok': False,
            'issues': ['Trim search did not converge']
        }

    issues = []

    # Elevator check
    elevator_deg = trim_result['elevator_deg']
    elevator_ok = -25 <= elevator_deg <= 25
    if not elevator_ok:
        issues.append(f"Elevator {elevator_deg:.2f}° out of realistic range [-25°, +25°]")

    # Throttle check
    throttle = trim_result['throttle']
    throttle_ok = 0.1 <= throttle <= 0.9
    if not throttle_ok:
        if throttle < 0.1:
            issues.append(f"Throttle {throttle:.3f} too low (< 0.1)")
        else:
            issues.append(f"Throttle {throttle:.3f} saturated (> 0.9)")

    # Alpha check
    alpha_deg = trim_result['alpha_deg']
    alpha_ok = 0 <= alpha_deg <= 15
    if not alpha_ok:
        if alpha_deg < 0:
            issues.append(f"Alpha {alpha_deg:.2f}° negative (unusual)")
        else:
            issues.append(f"Alpha {alpha_deg:.2f}° too high (> 15°, near stall)")

    # L/D check
    L_D = trim_result['L_D']
    L_D_ok = L_D > 5
    if not L_D_ok:
        issues.append(f"L/D {L_D:.2f} too low (< 5, poor efficiency)")

    # Overall assessment
    if len(issues) == 0:
        overall = 'GOOD'
    elif len(issues) <= 2:
        overall = 'ACCEPTABLE'
    else:
        overall = 'POOR'

    return {
        'overall': overall,
        'elevator_ok': elevator_ok,
        'throttle_ok': throttle_ok,
        'alpha_ok': alpha_ok,
        'L_D_ok': L_D_ok,
        'issues': issues
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python jsbsim_trim_wrapper.py <aircraft.xml> <speed_m_s> [altitude_m]")
        print("\nExample:")
        print("  python jsbsim_trim_wrapper.py ../output/SampleAircraft/aircraft.xml 15.0 100")
        sys.exit(1)

    xml_path = sys.argv[1]
    V_m_s = float(sys.argv[2])
    altitude_m = float(sys.argv[3]) if len(sys.argv) > 3 else 0

    print(f"\n[JSBSim Trim Search]")
    print(f"Aircraft: {xml_path}")
    print(f"Target speed: {V_m_s} m/s")
    print(f"Altitude: {altitude_m} m MSL")
    print("-" * 70)

    # Run trim search
    result = run_trim_search(xml_path, V_m_s, altitude_m)

    # Display results
    if result['converged']:
        print("\n[OK] Trim converged successfully\n")
        print(f"Elevator:  {result['elevator_deg']:>8.3f} °")
        print(f"Throttle:  {result['throttle']:>8.3f}")
        print(f"Alpha:     {result['alpha_deg']:>8.3f} °")
        print(f"Pitch:     {result['pitch_deg']:>8.3f} °")
        print(f"L/D:       {result['L_D']:>8.2f}")
        print(f"Speed:     {result['speed_m_s']:>8.2f} m/s")

        # Quality assessment
        quality = evaluate_trim_quality(result)
        print(f"\nTrim Quality: {quality['overall']}")
        if quality['issues']:
            print("Issues:")
            for issue in quality['issues']:
                print(f"  - {issue}")
    else:
        print(f"\n[FAILED] Trim did not converge")
        print(f"Error: {result['error']}")
        sys.exit(1)
