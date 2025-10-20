#!/usr/bin/env python3
"""
Manual Trim Search for JSBSim Aircraft (External Reactions Compatible)

This utility performs manual trim search using scipy.optimize, which works
with External Reactions approach (unlike JSBSim built-in trim).

Usage:
    python tests/test_trim_manual.py [aircraft_name] [velocity_mps]

Example:
    python tests/test_trim_manual.py ExampleAircraft 15
"""

import sys
import os

def manual_trim_search(aircraft_name="ExampleAircraft", velocity_mps=15.0, altitude_m=30.5):
    """
    Perform manual trim search using scipy.optimize.

    This method works with External Reactions approach, unlike JSBSim built-in trim.

    Args:
        aircraft_name: Name of the aircraft to trim
        velocity_mps: Target cruise velocity in m/s
        altitude_m: Target altitude in meters (default: 30.5m = 100ft)

    Returns:
        dict: Trim results with elevator, throttle, alpha
    """
    try:
        import jsbsim
    except ImportError:
        print("[ERROR] JSBSim not installed. Run: pip install jsbsim")
        return None

    try:
        from scipy.optimize import fsolve
    except ImportError:
        print("[ERROR] scipy not installed. Run: pip install scipy")
        return None

    print(f"Manual Trim Search: {aircraft_name}")
    print(f"Target velocity: {velocity_mps} m/s ({velocity_mps*3.28084:.2f} ft/s)")
    print(f"Target altitude: {altitude_m} m ({altitude_m*3.28084:.2f} ft)")

    # Initialize JSBSim
    try:
        fdm = jsbsim.FGFDMExec('.')
        fdm.load_model(aircraft_name)

        # Initialize throttle (required for External Reactions)
        try:
            fdm['fcs/throttle-cmd-norm'] = 0.0
        except Exception:
            pass

        fdm.run_ic()
        print("[OK] Aircraft loaded successfully")
    except Exception as e:
        print(f"[ERROR] Failed to load aircraft: {e}")
        return None

    # Set initial conditions
    velocity_fps = velocity_mps * 3.28084  # m/s → ft/s
    altitude_ft = altitude_m * 3.28084     # m → ft

    fdm['ic/u-fps'] = velocity_fps
    fdm['ic/h-sl-ft'] = altitude_ft

    # Define trim cost function
    def trim_cost(x):
        """
        Trim cost function: returns [wdot, qdot] for given [throttle, elevator]

        Goal: Find throttle and elevator such that wdot=0 and qdot=0
        (i.e., no vertical acceleration, no pitch acceleration)

        Parameter order: x = [throttle_norm, elevator_norm]
        """
        throttle_norm, elevator_norm = x

        # Clip to valid ranges
        elevator_norm = max(-1.0, min(1.0, elevator_norm))
        throttle_norm = max(0.0, min(1.0, throttle_norm))

        # Set control inputs
        fdm['fcs/elevator-cmd-norm'] = elevator_norm
        fdm['fcs/throttle-cmd-norm'] = throttle_norm

        # Run one timestep
        fdm.run()

        # Get accelerations
        wdot = fdm['accelerations/wdot-ft_sec2']  # Vertical acceleration
        qdot = fdm['accelerations/qdot-rad_sec2']  # Pitch acceleration

        return [wdot, qdot]

    # Perform trim search
    print("\n[INFO] Running manual trim search (scipy.optimize.fsolve)...")

    # Initial guess: [throttle, elevator]
    # "推力を適切に絞る" approach: Use lower throttle for pure aerodynamic flight
    # Test multiple initial guesses from low to medium throttle
    print("[INFO] Testing with reduced thrust initial guesses...")

    initial_guesses = [
        ([0.1, 0.0], "Very low thrust (10%)"),
        ([0.2, 0.0], "Low thrust (20%)"),
        ([0.3, 0.0], "Medium-low thrust (30%)"),
        ([0.5, 0.0], "Medium thrust (50%)")
    ]

    best_result = None
    best_quality = float('inf')

    for initial_guess, description in initial_guesses:
        print(f"\n  Trying: {description}")
        print(f"    Initial: throttle={initial_guess[0]:.1f}, elevator={initial_guess[1]:.1f}")

        try:
            result = fsolve(trim_cost, initial_guess, full_output=True)
            solution = result[0]
            info = result[1]

            throttle_trim = solution[0]
            elevator_trim = solution[1]

            # Check convergence
            final_cost = trim_cost(solution)
            wdot_final = abs(final_cost[0])
            qdot_final = abs(final_cost[1])

            quality = wdot_final + qdot_final * 10.0

            print(f"    Result: throttle={throttle_trim:.4f}, elevator={elevator_trim:.4f}")
            print(f"    Quality: wdot={wdot_final:.4f}, qdot={qdot_final:.6f}, metric={quality:.4f}")

            if quality < best_quality:
                best_quality = quality
                best_result = {
                    'throttle': throttle_trim,
                    'elevator': elevator_trim,
                    'wdot': wdot_final,
                    'qdot': qdot_final,
                    'quality': quality,
                    'description': description,
                    'converged': (wdot_final < 1.0) and (qdot_final < 0.01)
                }

                if best_result['converged']:
                    print(f"    [OK] CONVERGED!")
                    break
        except Exception as e:
            print(f"    [ERROR] Failed: {e}")

    if best_result is None:
        print("\n[ERROR] All initial guesses failed")
        return None

    # Use best result
    throttle_trim = best_result['throttle']
    elevator_trim = best_result['elevator']
    wdot_final = best_result['wdot']
    qdot_final = best_result['qdot']
    converged = best_result['converged']

    print(f"\n[INFO] Best result from: {best_result['description']}")

    # Use best result for final output
    if converged:
        print("[OK] Trim converged successfully!")

        # Get final state
        alpha_rad = fdm['aero/alpha-rad']
        pitch_rad = fdm['attitude/pitch-rad']
        thrust_lbs = fdm['forces/fbx-external-lbs'] if 'forces/fbx-external-lbs' in fdm.get_property_catalog() else 0.0

        print(f"\n[INFO] Trim Results:")
        print(f"   Elevator: {elevator_trim:.4f} norm ({elevator_trim*0.35*57.2958:.2f}°)")
        print(f"   Throttle: {throttle_trim:.4f} norm ({throttle_trim*100:.1f}%)")
        print(f"   Alpha: {alpha_rad:.4f} rad ({alpha_rad*57.2958:.2f}°)")
        print(f"   Pitch: {pitch_rad:.4f} rad ({pitch_rad*57.2958:.2f}°)")
        if thrust_lbs > 0:
            print(f"   Thrust: {thrust_lbs:.3f} lbs ({thrust_lbs*4.44822:.3f} N)")

        print(f"\n[INFO] Convergence Check:")
        print(f"   wdot: {wdot_final:.4f} ft/s^2 (target: <1.0)")
        print(f"   qdot: {qdot_final:.6f} rad/s^2 (target: <0.01)")

        return {
            'elevator': elevator_trim,
            'throttle': throttle_trim,
            'alpha_rad': alpha_rad,
            'pitch_rad': pitch_rad,
            'converged': True
        }

    else:
        print("[WARN] Trim did not converge to target tolerance")
        print(f"   wdot: {wdot_final:.4f} ft/s^2 (target: <1.0)")
        print(f"   qdot: {qdot_final:.6f} rad/s^2 (target: <0.01)")

        print(f"\n[INFO] Best trim found:")
        print(f"   Elevator: {elevator_trim:.4f} norm")
        print(f"   Throttle: {throttle_trim:.4f} norm")

        return {
            'elevator': elevator_trim,
            'throttle': throttle_trim,
            'converged': False
        }


def stability_test(fdm, elevator_trim, throttle_trim, duration=10.0):
    """
    Run stability test with trim settings.

    Args:
        fdm: JSBSim FDM object
        elevator_trim: Trim elevator position (normalized)
        throttle_trim: Trim throttle position (normalized)
        duration: Test duration in seconds (default: 10.0)

    Returns:
        bool: True if stable, False otherwise
    """
    print(f"\n[INFO] Running {duration}-second stability test...")

    # Set trim settings
    fdm['fcs/elevator-cmd-norm'] = elevator_trim
    fdm['fcs/throttle-cmd-norm'] = throttle_trim

    # Record initial state
    initial_pitch = fdm['attitude/pitch-rad']
    initial_alt = fdm['position/h-sl-ft']

    # Run simulation
    dt = 0.01  # 10ms timestep
    steps = int(duration / dt)

    for i in range(steps):
        fdm.run()

    # Check final state
    final_pitch = fdm['attitude/pitch-rad']
    final_alt = fdm['position/h-sl-ft']

    pitch_change = abs(final_pitch - initial_pitch) * 57.2958  # rad → deg
    alt_change = abs(final_alt - initial_alt) * 0.3048  # ft → m

    print(f"\n[INFO] Stability Results ({duration} seconds):")
    print(f"   Initial pitch: {initial_pitch*57.2958:.2f}°")
    print(f"   Final pitch: {final_pitch*57.2958:.2f}°")
    print(f"   Pitch change: {pitch_change:.2f}°")
    print(f"   Altitude change: {alt_change:.2f} m")

    # Check stability criteria
    if pitch_change < 5.0 and alt_change < 10.0:
        print("[PASS] Aircraft is stable!")
        return True
    else:
        print("[WARN] Aircraft may be unstable")
        print("   (pitch change > 5° or altitude change > 10m)")
        return False


if __name__ == "__main__":
    aircraft = sys.argv[1] if len(sys.argv) > 1 else "ExampleAircraft"
    velocity = float(sys.argv[2]) if len(sys.argv) > 2 else 15.0

    # Perform manual trim search
    trim_result = manual_trim_search(aircraft, velocity)

    if trim_result and trim_result['converged']:
        # If trim converged, run stability test
        import jsbsim
        fdm = jsbsim.FGFDMExec('.')
        fdm.load_model(aircraft)
        try:
            fdm['fcs/throttle-cmd-norm'] = 0.0
        except Exception:
            pass
        fdm.run_ic()

        velocity_fps = velocity * 3.28084
        fdm['ic/u-fps'] = velocity_fps
        fdm['ic/h-sl-ft'] = 100.0

        stable = stability_test(fdm, trim_result['elevator'], trim_result['throttle'])

        sys.exit(0 if stable else 1)
    else:
        sys.exit(1)
