"""Unified End-to-End Test (Line 1/Line 2 Common)

Phase 3: Unified Test Scripts - Task 3-3

Purpose:
  - Complete E2E test: XML load → XMI → Flight simulation
  - Evidence Level-based performance criteria (L1: strict, L2-L6: relaxed)
  - Line 1/Line 2 common test script

Usage:
  # Line 1 E2E test (FMS data, L1)
  python test_e2e.py --aircraft-dir aircraft/ExampleAircraft \\
      --model ExampleAircraft --evidence-level L2

  # Line 2 E2E test (Excel data, L2)
  python test_e2e.py --aircraft-dir ../phase1_mvp/output/out \\
      --model ExampleAircraft --evidence-level L2

Expected Results:
  - [PASS] XML loads successfully
  - [PASS] XMI initializes
  - [PASS] Flight simulation completes without divergence
  - [PASS] Performance criteria met according to Evidence Level
"""

import sys
import os
from pathlib import Path
import argparse
import math

# Unified XMI interface import
try:
    from unified_xmi_interface import JSBSimXMI
except ImportError:
    # Try adding current directory to path
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        from unified_xmi_interface import JSBSimXMI
    except ImportError:
        print("[ERROR] unified_xmi_interface.py not found in common/")
        print("Please ensure Phase 2 (unified XMI class) is completed")
        sys.exit(1)


def test_e2e(aircraft_dir, model_name, evidence_level='L1',
             speed_ms=15.0, altitude_ft=1000.0,
             throttle=0.70, alpha_deg=4.0, elevator_norm=0.0,
             duration_s=10.0, use_trim=False):
    """Unified E2E test (Line 1/Line 2 common)

    Args:
        aircraft_dir (str): Aircraft directory path
        model_name (str): Aircraft model name
        evidence_level (str): Evidence Level ('L1'-'L6')
        speed_ms (float): Initial/target speed (m/s)
        altitude_ft (float): Initial altitude (ft)
        throttle (float): Initial throttle (0-1)
        alpha_deg (float): Initial angle of attack (deg)
        elevator_norm (float): Initial elevator (-1 to 1)
        duration_s (float): Simulation duration (s)
        use_trim (bool): Use trim search instead of manual IC

    Returns:
        dict: E2E test results
            - passed (bool): Overall test pass/fail
            - steps_completed (list): List of completed steps
            - issues (list): List of issues detected
    """

    print("=" * 70)
    print(f"UNIFIED E2E TEST - Evidence Level {evidence_level}")
    print("=" * 70)
    print(f"Aircraft: {model_name}")
    print(f"Directory: {aircraft_dir}")
    print(f"Evidence Level: {evidence_level}")
    print()
    print("E2E Flow:")
    print("  1. XML Validation")
    print("  2. XMI Initialization")
    print("  3. Initial Conditions Setup")
    print("  4. Flight Simulation")
    print("  5. Results Analysis")
    print()

    completed_steps = []
    issues = []

    # ========================================
    # STEP 1: XML Validation
    # ========================================
    print("-" * 70)
    print("STEP 1: XML Validation")
    print("-" * 70)

    xml_path = Path(aircraft_dir) / f"{model_name}.xml"
    print(f"[INFO] Checking XML existence...")
    print(f"       Expected path: {xml_path}")

    if not xml_path.exists():
        print(f"[FAIL] XML file not found: {xml_path}")
        print()
        print("Please ensure:")
        if evidence_level == 'L1':
            print("  - FMS .par file has been converted to JSBSim XML")
        else:
            print("  - Excel template has been converted to JSBSim XML")
            print("  - Run: python generate_jsbsim_from_gsheet.py")
        return {
            'passed': False,
            'steps_completed': completed_steps,
            'issues': [f"XML not found: {xml_path}"]
        }

    print(f"[OK] XML file exists: {xml_path.name}")
    print(f"     Size: {xml_path.stat().st_size:,} bytes")
    print()
    completed_steps.append("XML validation")

    # ========================================
    # STEP 2: XMI Initialization
    # ========================================
    print("-" * 70)
    print("STEP 2: XMI Initialization")
    print("-" * 70)

    print(f"[INFO] Initializing unified XMI interface...")
    print(f"       Evidence Level: {evidence_level}")

    try:
        xmi = JSBSimXMI(aircraft_dir, model_name, evidence_level)
        print(f"[OK] XMI initialized successfully")

        # Display quality criteria
        criteria = xmi.quality_criteria
        print()
        print(f"Quality Criteria (Evidence Level {evidence_level}):")
        print(f"  - Trim convergence: {criteria['trim_convergence']:.4f} rad/s")
        print(f"  - Altitude drift tolerance: {criteria['alt_drift_tolerance']:.1f} m")
        print(f"  - Speed drift tolerance: {criteria['speed_drift_tolerance']:.1f} m/s")
        print(f"  - Alpha drift tolerance: {criteria['alpha_drift_tolerance']:.1f} deg")

    except Exception as e:
        print(f"[FAIL] XMI initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            'passed': False,
            'steps_completed': completed_steps,
            'issues': [f"XMI init failed: {e}"]
        }

    print()
    completed_steps.append("XMI initialization")

    # ========================================
    # STEP 3: Initial Conditions Setup
    # ========================================
    print("-" * 70)
    print("STEP 3: Initial Conditions Setup")
    print("-" * 70)

    if use_trim:
        print(f"[INFO] Using trim search...")
        print(f"       Target speed: {speed_ms:.1f} m/s")
        print(f"       Target altitude: {altitude_ft:.0f} ft")
        print()

        try:
            trim_result = xmi.set_initial_conditions_from_trim(
                speed_ms=speed_ms,
                altitude_ft=altitude_ft
            )

            if not trim_result.get('converged', False):
                print(f"[WARN] Trim search did not converge")
                print(f"       Falling back to manual initial conditions...")
                use_trim = False
            else:
                print(f"[OK] Trim search converged")
                print(f"     Throttle: {trim_result['throttle'] * 100:.1f}%")
                print(f"     Elevator: {trim_result['elevator_deg']:+.2f} deg")
                print(f"     Alpha: {trim_result['alpha_deg']:+.2f} deg")

        except Exception as e:
            print(f"[WARN] Trim search failed: {e}")
            print(f"       Falling back to manual initial conditions...")
            use_trim = False

    if not use_trim:
        print(f"[INFO] Using manual initial conditions...")
        print(f"       Speed: {speed_ms:.1f} m/s")
        print(f"       Altitude: {altitude_ft:.0f} ft")
        print(f"       Throttle: {throttle * 100:.0f}%")
        print(f"       Alpha: {alpha_deg:.1f} deg")
        print(f"       Elevator: {elevator_norm:+.2f}")
        print()

        try:
            xmi.set_initial_conditions_manual(
                speed_ms=speed_ms,
                altitude_ft=altitude_ft,
                throttle=throttle,
                alpha_deg=alpha_deg,
                elevator_norm=elevator_norm
            )
            print(f"[OK] Manual initial conditions set")
        except Exception as e:
            print(f"[FAIL] Initial conditions setup failed: {e}")
            return {
                'passed': False,
                'steps_completed': completed_steps,
                'issues': [f"IC setup failed: {e}"]
            }

    print()
    completed_steps.append("Initial conditions setup")

    # Get initial state
    initial_state = xmi.get_state()
    initial_altitude_m = initial_state['position']['altitude_m']
    initial_speed_ms = initial_state['velocity']['u_ms']

    # ========================================
    # STEP 4: Flight Simulation
    # ========================================
    print("-" * 70)
    print(f"STEP 4: Flight Simulation ({duration_s:.0f} seconds)")
    print("-" * 70)

    dt = 0.02  # 50 Hz
    steps = int(duration_s / dt)

    print(f"[INFO] Running simulation...")
    print(f"       Duration: {duration_s:.1f} seconds")
    print(f"       Time step: {dt*1000:.0f} ms (50 Hz)")
    print(f"       Steps: {steps}")
    print()

    # Data logging
    time_log = []
    altitude_log = []
    speed_log = []
    pitch_log = []
    roll_log = []
    alpha_log = []

    # Divergence detection
    diverged = False
    divergence_message = ""

    # Get divergence criteria based on Evidence Level
    div_pitch = 60.0 + (ord(evidence_level[1]) - ord('1')) * 5.0  # L1:60, L2:65, ...
    div_roll = 60.0 + (ord(evidence_level[1]) - ord('1')) * 5.0
    min_alt = 100.0 - (ord(evidence_level[1]) - ord('1')) * 15.0  # L1:100, L2:85, ...

    # Display initial state
    print(f"T=  0.0s: Alt={initial_altitude_m:6.1f}m  Spd={initial_speed_ms:5.2f}m/s  "
          f"Pitch={initial_state['attitude']['theta_deg']:+6.2f}deg  "
          f"Alpha={initial_state['attitude']['alpha_deg']:+5.2f}deg")

    # Simulation loop
    for i in range(steps):
        try:
            result = xmi.step(dt=dt)
            if not result:
                diverged = True
                divergence_message = f"Simulation step failed at t={i*dt:.2f}s"
                break

        except Exception as e:
            diverged = True
            divergence_message = f"Exception during simulation: {e}"
            break

        # Get state
        state = xmi.get_state()
        sim_time = i * dt

        # Log data
        time_log.append(sim_time)
        altitude_log.append(state['position']['altitude_m'])
        speed_log.append(state['velocity']['u_ms'])
        pitch_log.append(state['attitude']['theta_deg'])
        roll_log.append(state['attitude']['phi_deg'])
        alpha_log.append(state['attitude']['alpha_deg'])

        # Divergence detection
        if abs(state['attitude']['theta_deg']) > div_pitch:
            diverged = True
            divergence_message = f"Pitch diverged: {state['attitude']['theta_deg']:+.1f} deg at t={sim_time:.2f}s"
            break

        if abs(state['attitude']['phi_deg']) > div_roll:
            diverged = True
            divergence_message = f"Roll diverged: {state['attitude']['phi_deg']:+.1f} deg at t={sim_time:.2f}s"
            break

        if state['position']['altitude_m'] < min_alt:
            diverged = True
            divergence_message = f"Altitude too low: {state['position']['altitude_m']:.1f} m at t={sim_time:.2f}s"
            break

        # Progress display (every 2 seconds)
        if (i+1) % int(2.0 / dt) == 0:
            print(f"T={sim_time:5.1f}s: Alt={state['position']['altitude_m']:6.1f}m  "
                  f"Spd={state['velocity']['u_ms']:5.2f}m/s  "
                  f"Pitch={state['attitude']['theta_deg']:+6.2f}deg  "
                  f"Alpha={state['attitude']['alpha_deg']:+5.2f}deg")

    print()

    if diverged:
        print(f"[FAIL] SIMULATION DIVERGED")
        print(f"  {divergence_message}")
        print()
        issues.append(divergence_message)
        return {
            'passed': False,
            'steps_completed': completed_steps,
            'issues': issues,
            'diverged': True
        }

    print(f"[OK] Simulation completed successfully")
    print()
    completed_steps.append(f"Flight simulation ({duration_s:.0f}s)")

    # ========================================
    # STEP 5: Results Analysis
    # ========================================
    print("-" * 70)
    print(f"STEP 5: Results Analysis (Evidence Level {evidence_level})")
    print("-" * 70)

    final_altitude_m = altitude_log[-1]
    final_speed_ms = speed_log[-1]
    final_pitch_deg = pitch_log[-1]
    final_roll_deg = roll_log[-1]
    final_alpha_deg = alpha_log[-1]

    altitude_drift = final_altitude_m - initial_altitude_m
    speed_drift = final_speed_ms - initial_speed_ms

    print()
    print("Initial State:")
    print(f"  Altitude: {initial_altitude_m:.1f} m")
    print(f"  Speed:    {initial_speed_ms:.2f} m/s")

    print()
    print("Final State:")
    print(f"  Altitude: {final_altitude_m:.1f} m ({altitude_drift:+.1f} m drift)")
    print(f"  Speed:    {final_speed_ms:.2f} m/s ({speed_drift:+.2f} m/s drift)")
    print(f"  Pitch:    {final_pitch_deg:+.2f} deg")
    print(f"  Roll:     {final_roll_deg:+.2f} deg")
    print(f"  Alpha:    {final_alpha_deg:+.2f} deg")

    print()
    print("Range Analysis:")
    pitch_range = max(pitch_log) - min(pitch_log)
    roll_range = max(roll_log) - min(roll_log)
    altitude_range = max(altitude_log) - min(altitude_log)

    print(f"  Pitch range:    {pitch_range:.1f} deg")
    print(f"  Roll range:     {roll_range:.1f} deg")
    print(f"  Altitude range: {altitude_range:.1f} m")

    # Performance criteria
    criteria = xmi.quality_criteria
    alt_tol = criteria['alt_drift_tolerance']
    spd_tol = criteria['speed_drift_tolerance']
    alpha_tol = criteria['alpha_drift_tolerance']

    print()
    print("Performance Evaluation:")

    test_issues = []

    if abs(altitude_drift) > alt_tol:
        test_issues.append(f"Altitude drift: {altitude_drift:+.1f} m (tolerance: +/-{alt_tol:.1f} m)")

    if abs(speed_drift) > spd_tol:
        test_issues.append(f"Speed drift: {speed_drift:+.2f} m/s (tolerance: +/-{spd_tol:.1f} m/s)")

    if abs(final_alpha_deg) > 20.0:  # Stall warning threshold
        test_issues.append(f"High alpha: {final_alpha_deg:+.1f} deg (stall risk)")

    if len(test_issues) > 0:
        print()
        print(f"[WARN] Performance issues detected ({evidence_level} criteria):")
        for issue in test_issues:
            print(f"  - {issue}")
        print()
        if evidence_level != 'L1':
            print(f"Note: These deviations may be acceptable for Evidence Level {evidence_level}")
            print("      (Relaxed criteria compared to L1 measured values)")
        issues.extend(test_issues)
    else:
        print()
        print(f"[PASS] All performance checks passed ({evidence_level} criteria)")
        print()
        print("Flight characteristics:")
        print(f"  - Stable altitude: {altitude_drift:+.1f} m drift in {duration_s:.0f}s")
        print(f"  - Stable speed: {speed_drift:+.2f} m/s drift in {duration_s:.0f}s")
        print(f"  - Safe alpha range: {final_alpha_deg:+.1f} deg")

    print()
    completed_steps.append("Results analysis")

    # ========================================
    # E2E Test Summary
    # ========================================
    print("=" * 70)
    print("E2E TEST SUMMARY")
    print("=" * 70)
    print()
    print(f"Evidence Level: {evidence_level}")
    print()
    print("Completed Steps:")
    for i, step in enumerate(completed_steps, 1):
        print(f"  {i}. {step}")

    print()
    if len(issues) == 0:
        print("[PASS] E2E TEST COMPLETED - ALL CHECKS PASSED")
        print()
        if evidence_level == 'L1':
            print("Recommendation: Ready for production flight tests")
        else:
            print(f"Recommendation: Ready for {evidence_level} integration and validation")
    else:
        print(f"[PARTIAL] E2E TEST COMPLETED - {len(issues)} ISSUE(S) DETECTED")
        print()
        print("Issues:")
        for issue in issues:
            print(f"  - {issue}")
        print()
        if evidence_level != 'L1':
            print(f"Note: Some issues may be acceptable for Evidence Level {evidence_level}")

    print()
    print("Next Steps:")
    if use_trim:
        print("  1. Run FlightGear visualization")
        print("  2. Test with different speeds")
    else:
        print("  1. Try trim search: --use-trim")
        print("  2. Run FlightGear visualization")
        print("  3. Test with different speeds")

    print("=" * 70)

    return {
        'passed': len(issues) == 0,
        'steps_completed': completed_steps,
        'issues': issues,
        'diverged': False,
        'final_state': {
            'altitude_m': final_altitude_m,
            'speed_ms': final_speed_ms,
            'pitch_deg': final_pitch_deg,
            'roll_deg': final_roll_deg,
            'alpha_deg': final_alpha_deg
        },
        'drift': {
            'altitude_m': altitude_drift,
            'speed_ms': speed_drift
        },
        'evidence_level': evidence_level
    }


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Unified E2E Test (Line 1/Line 2 Common)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Line 1 E2E test (FMS data, L1)
  python test_e2e.py --aircraft-dir aircraft/ExampleAircraft \\
      --model ExampleAircraft --evidence-level L2

  # Line 2 E2E test (Excel data, L2)
  python test_e2e.py --aircraft-dir ../phase1_mvp/output/out \\
      --model ExampleAircraft --evidence-level L2

  # E2E test with trim search
  python test_e2e.py --aircraft-dir aircraft/ExampleAircraft \\
      --model ExampleAircraft --evidence-level L2 --use-trim
        """
    )

    parser.add_argument('--aircraft-dir', type=str, required=True,
                       help='Aircraft directory path')
    parser.add_argument('--model', type=str, required=True,
                       help='Aircraft model name')
    parser.add_argument('--evidence-level', type=str, default='L1',
                       choices=['L1', 'L2', 'L3', 'L4', 'L5', 'L6'],
                       help='Evidence Level (default: L1)')
    parser.add_argument('--speed', type=float, default=15.0,
                       help='Initial/target speed in m/s (default: 15.0)')
    parser.add_argument('--altitude', type=float, default=1000.0,
                       help='Initial altitude in ft (default: 1000.0)')
    parser.add_argument('--throttle', type=float, default=0.70,
                       help='Initial throttle 0-1 (default: 0.70)')
    parser.add_argument('--alpha', type=float, default=4.0,
                       help='Initial angle of attack in deg (default: 4.0)')
    parser.add_argument('--elevator', type=float, default=0.0,
                       help='Initial elevator -1 to 1 (default: 0.0)')
    parser.add_argument('--duration', type=float, default=10.0,
                       help='Simulation duration in seconds (default: 10.0)')
    parser.add_argument('--use-trim', action='store_true',
                       help='Use trim search instead of manual IC')

    args = parser.parse_args()

    # Run E2E test
    result = test_e2e(
        aircraft_dir=args.aircraft_dir,
        model_name=args.model,
        evidence_level=args.evidence_level,
        speed_ms=args.speed,
        altitude_ft=args.altitude,
        throttle=args.throttle,
        alpha_deg=args.alpha,
        elevator_norm=args.elevator,
        duration_s=args.duration,
        use_trim=args.use_trim
    )

    # Exit code
    sys.exit(0 if result['passed'] and not result.get('diverged', False) else 1)


if __name__ == '__main__':
    main()
