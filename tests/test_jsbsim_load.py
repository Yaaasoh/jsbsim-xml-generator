#!/usr/bin/env python3
"""
JSBSim Aircraft Loading Test

Tests basic JSBSim XML loading functionality.
"""

import sys
import os

def test_jsbsim_load(aircraft_name="ExampleAircraft"):
    """
    Test JSBSim aircraft loading.

    Args:
        aircraft_name: Name of the aircraft to load (default: ExampleAircraft)
    """
    try:
        import jsbsim
    except ImportError:
        print("ERROR: JSBSim not installed. Run: pip install jsbsim")
        return False

    print(f"Testing JSBSim aircraft loading: {aircraft_name}")
    print(f"JSBSim version: {jsbsim.__version__}")

    # Initialize JSBSim
    try:
        fdm = jsbsim.FGFDMExec('.')
        print("[OK] JSBSim initialized successfully")
    except Exception as e:
        print(f"[ERROR] Failed to initialize JSBSim: {e}")
        return False

    # Load aircraft model
    try:
        success = fdm.load_model(aircraft_name)
        if not success:
            print(f"[ERROR] Failed to load aircraft: {aircraft_name}")
            print(f"   Check that aircraft/{aircraft_name}/{aircraft_name}.xml exists")
            return False
        print(f"[OK] Aircraft '{aircraft_name}' loaded successfully")
    except Exception as e:
        print(f"[ERROR] Exception while loading aircraft: {e}")
        return False

    # Initialize throttle (required for External Reactions approach)
    try:
        fdm['fcs/throttle-cmd-norm'] = 0.0
    except Exception:
        pass  # Not all aircraft use External Reactions

    # Run initial conditions
    try:
        fdm.run_ic()
        print("[OK] Initial conditions executed successfully")
    except Exception as e:
        print(f"[ERROR] Failed to run initial conditions: {e}")
        return False

    # Check basic properties
    try:
        mass = fdm['inertia/weight-lbs']
        wingarea = fdm['metrics/Sw-sqft']
        wingspan = fdm['metrics/bw-ft']

        print(f"\n[INFO] Aircraft Properties:")
        print(f"   Mass: {mass:.2f} lbs ({mass*0.453592:.2f} kg)")
        print(f"   Wing Area: {wingarea:.2f} sqft ({wingarea*0.092903:.4f} m^2)")
        print(f"   Wing Span: {wingspan:.2f} ft ({wingspan*0.3048:.2f} m)")

    except Exception as e:
        print(f"[WARN] Warning: Could not read aircraft properties: {e}")

    print(f"\n[PASS] All tests passed for '{aircraft_name}'!")
    return True


if __name__ == "__main__":
    aircraft = sys.argv[1] if len(sys.argv) > 1 else "ExampleAircraft"

    success = test_jsbsim_load(aircraft)
    sys.exit(0 if success else 1)
