#!/usr/bin/env python3
"""
JSBSim Trim and Stability Test

Tests trim convergence and basic stability for JSBSim aircraft.
"""

import sys
import os

def test_trim_stability(aircraft_name="ExampleAircraft", velocity_mps=15.0):
    """
    Test JSBSim aircraft trim and stability.

    Args:
        aircraft_name: Name of the aircraft to test
        velocity_mps: Cruise velocity in m/s (default: 15.0)
    """
    try:
        import jsbsim
    except ImportError:
        print("ERROR: JSBSim not installed. Run: pip install jsbsim")
        return False

    print(f"Testing Trim and Stability: {aircraft_name}")
    print(f"Cruise velocity: {velocity_mps} m/s ({velocity_mps*3.28084:.2f} ft/s)")

    # Initialize JSBSim
    try:
        fdm = jsbsim.FGFDMExec('.')
        fdm.load_model(aircraft_name)

        # Initialize throttle (required for External Reactions approach)
        try:
            fdm['fcs/throttle-cmd-norm'] = 0.0
        except Exception:
            pass  # Not all aircraft use External Reactions

        fdm.run_ic()
        print("[OK] Aircraft loaded successfully")
    except Exception as e:
        print(f"[ERROR] Failed to load aircraft: {e}")
        return False

    # Set initial conditions
    try:
        velocity_fps = velocity_mps * 3.28084  # m/s → ft/s
        fdm['ic/u-fps'] = velocity_fps
        fdm['ic/h-sl-ft'] = 100.0  # Altitude: 100ft

        print(f"\n[INFO] Initial Conditions:")
        print(f"   Velocity: {velocity_fps:.2f} ft/s ({velocity_mps:.2f} m/s)")
        print(f"   Altitude: 100 ft (30.5 m)")

    except Exception as e:
        print(f"[ERROR] Failed to set initial conditions: {e}")
        return False

    # Run trim
    print(f"\n[INFO] Running trim (mode=2, longitudinal)...")
    try:
        fdm.do_trim(2)  # 2 = Longitudinal trim

        if fdm['simulation/trim-completed']:
            print("[OK] Trim converged successfully!")

            # Display trim results
            elevator = fdm['fcs/elevator-pos-rad']
            throttle = fdm['fcs/throttle-cmd-norm']
            alpha = fdm['aero/alpha-rad']

            print(f"\n[INFO] Trim Results:")
            print(f"   Elevator: {elevator:.4f} rad ({elevator*57.2958:.2f}°)")
            print(f"   Throttle: {throttle:.4f}")
            print(f"   Alpha: {alpha:.4f} rad ({alpha*57.2958:.2f}°)")

        else:
            print("[ERROR] Trim did not converge")
            print("   Possible causes:")
            print("   - Aerodynamic coefficients inappropriate (CD0, Cmalpha)")
            print("   - Insufficient thrust")
            print("   - CG position inappropriate")
            return False

    except Exception as e:
        print(f"[ERROR] Exception during trim: {e}")
        return False

    # Stability test: Run for 10 seconds
    print(f"\n[INFO] Running 10-second stability test...")
    try:
        dt = 0.01  # 10ms timestep
        steps = int(10.0 / dt)  # 10 seconds

        # Record initial state
        initial_pitch = fdm['attitude/pitch-rad']
        initial_alt = fdm['position/h-sl-ft']

        # Run simulation
        for i in range(steps):
            fdm.run()

        # Check final state
        final_pitch = fdm['attitude/pitch-rad']
        final_alt = fdm['position/h-sl-ft']

        pitch_change = abs(final_pitch - initial_pitch) * 57.2958  # rad → deg
        alt_change = abs(final_alt - initial_alt) * 0.3048  # ft → m

        print(f"\n[INFO] Stability Results (10 seconds):")
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

    except Exception as e:
        print(f"[ERROR] Exception during stability test: {e}")
        return False


if __name__ == "__main__":
    aircraft = sys.argv[1] if len(sys.argv) > 1 else "ExampleAircraft"
    velocity = float(sys.argv[2]) if len(sys.argv) > 2 else 15.0

    success = test_trim_stability(aircraft, velocity)
    sys.exit(0 if success else 1)
