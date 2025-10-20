#!/usr/bin/env python3
"""
Trim Diagnostic Test - 推力テーブルと空力係数の詳細検証

既知のノウハウ確認:
- 推力を適切に絞った低い値からテストしているか？
- 空力係数は適切か？
- initial guessは適切か？

Usage:
    python tests/test_trim_diagnostic.py [aircraft_name] [aircraft_dir]
"""

import sys
import os

def trim_diagnostic(aircraft_name="ExampleAircraft", aircraft_dir="aircraft"):
    """Comprehensive trim diagnostic"""

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

    print("="*70)
    print("TRIM DIAGNOSTIC TEST - 推力テーブルと空力係数の詳細検証")
    print("="*70)
    print(f"Aircraft: {aircraft_name}")
    print(f"Directory: {aircraft_dir}")
    print()

    # ========================================
    # STEP 1: Load Aircraft and Check Basic Properties
    # ========================================
    print("-"*70)
    print("STEP 1: Aircraft Loading and Basic Properties")
    print("-"*70)

    fdm = jsbsim.FGFDMExec('.')
    fdm.set_aircraft_path(os.path.abspath(aircraft_dir))

    try:
        fdm.load_model(aircraft_name)
        print(f"[OK] Aircraft loaded: {aircraft_name}")
    except Exception as e:
        print(f"[ERROR] Failed to load aircraft: {e}")
        return None

    # Initialize throttle (required for External Reactions)
    try:
        fdm['fcs/throttle-cmd-norm'] = 0.0
    except Exception:
        pass

    fdm.run_ic()

    # Get basic properties
    mass_lbs = fdm['inertia/weight-lbs']
    mass_kg = mass_lbs / 2.20462
    wing_area_sqft = fdm['metrics/Sw-sqft']
    wing_area_m2 = wing_area_sqft / 10.7639

    print(f"\n[INFO] Basic Properties:")
    print(f"   Mass: {mass_lbs:.3f} lbs ({mass_kg:.3f} kg)")
    print(f"   Wing Area: {wing_area_sqft:.3f} sqft ({wing_area_m2:.4f} m^2)")
    print(f"   Wing Span: {fdm['metrics/bw-ft']:.3f} ft ({fdm['metrics/bw-ft']*0.3048:.3f} m)")

    # ========================================
    # STEP 2: Thrust Table Verification
    # ========================================
    print("\n" + "-"*70)
    print("STEP 2: Thrust Table Verification - 推力を適切に絞る")
    print("-"*70)

    print("\n[INFO] Testing thrust at various throttle settings...")

    # Set initial conditions for thrust test
    fdm['ic/u-fps'] = 15.0 * 3.28084  # 15 m/s
    fdm['ic/h-sl-ft'] = 100.0
    fdm['ic/alpha-deg'] = 0.0
    fdm['fcs/elevator-cmd-norm'] = 0.0

    thrust_data = []

    # Test throttle from 0% to 100% in 10% increments
    for throttle_pct in range(0, 101, 10):
        throttle_norm = throttle_pct / 100.0
        fdm['fcs/throttle-cmd-norm'] = throttle_norm
        fdm.run_ic()
        fdm.run()

        # Get thrust (External Reactions)
        try:
            thrust_lbs = fdm['forces/fbx-external-lbs']
        except:
            thrust_lbs = 0.0

        thrust_n = thrust_lbs * 4.44822
        thrust_g = thrust_n * 101.972  # N → gf

        thrust_data.append({
            'throttle_pct': throttle_pct,
            'throttle_norm': throttle_norm,
            'thrust_lbs': thrust_lbs,
            'thrust_n': thrust_n,
            'thrust_g': thrust_g
        })

        print(f"   {throttle_pct:3d}%: {thrust_lbs:.4f} lbs = {thrust_n:.4f} N = {thrust_g:.1f} gf")

    # Check if max thrust > weight
    max_thrust_lbs = max([d['thrust_lbs'] for d in thrust_data])
    max_thrust_n = max_thrust_lbs * 4.44822
    weight_n = mass_kg * 9.81

    print(f"\n[INFO] Thrust vs Weight:")
    print(f"   Max thrust: {max_thrust_lbs:.4f} lbs ({max_thrust_n:.3f} N)")
    print(f"   Weight: {mass_lbs:.4f} lbs ({weight_n:.3f} N)")
    print(f"   Thrust/Weight ratio: {max_thrust_n/weight_n:.2f}")

    if max_thrust_n < weight_n:
        print(f"[ERROR] Max thrust < weight! Aircraft cannot sustain level flight.")
        print(f"   Need: {weight_n:.3f} N")
        print(f"   Have: {max_thrust_n:.3f} N")
        print(f"   Deficit: {weight_n - max_thrust_n:.3f} N ({(weight_n - max_thrust_n)*101.972:.1f} gf)")
        return None
    else:
        print(f"[OK] Max thrust > weight (margin: {max_thrust_n - weight_n:.3f} N)")

    # ========================================
    # STEP 3: Aerodynamic Coefficients Check
    # ========================================
    print("\n" + "-"*70)
    print("STEP 3: Aerodynamic Coefficients Verification")
    print("-"*70)

    # Test at 15 m/s, various alphas
    print("\n[INFO] Testing lift/drag at 15 m/s...")

    speed_fps = 15.0 * 3.28084
    fdm['ic/u-fps'] = speed_fps
    fdm['ic/h-sl-ft'] = 100.0
    fdm['fcs/throttle-cmd-norm'] = 0.5
    fdm['fcs/elevator-cmd-norm'] = 0.0

    print(f"\n   Alpha(deg)    CL        CD      L/D     Lift(lbs)  Drag(lbs)")
    print(f"   {'-'*60}")

    for alpha_deg in [0, 2, 4, 6, 8, 10]:
        fdm['ic/alpha-deg'] = alpha_deg
        fdm.run_ic()
        fdm.run()

        CL = fdm['aero/CL']
        CD = fdm['aero/CD']
        lift_lbs = fdm['forces/fz-aero-lbs']
        drag_lbs = fdm['forces/fx-aero-lbs']

        if CD > 0:
            LD = CL / CD
        else:
            LD = 0.0

        print(f"   {alpha_deg:3d}          {CL:6.4f}   {CD:6.4f}  {LD:5.2f}    {-lift_lbs:7.3f}    {-drag_lbs:7.3f}")

    # ========================================
    # STEP 4: Manual Trim Search with Diagnostic Output
    # ========================================
    print("\n" + "-"*70)
    print("STEP 4: Manual Trim Search - 低い推力から開始")
    print("-"*70)

    target_speed_ms = 15.0
    target_speed_fps = target_speed_ms * 3.28084
    altitude_ft = 100.0

    print(f"\n[INFO] Target: {target_speed_ms} m/s ({target_speed_fps:.2f} ft/s) at {altitude_ft} ft")

    # Test multiple initial guesses
    initial_guesses = [
        ([0.0, 0.5], "Low throttle (0%), mid elevator (50%)"),
        ([0.3, 0.0], "Low-medium throttle (30%), neutral elevator"),
        ([0.5, 0.0], "Medium throttle (50%), neutral elevator (test_speed_envelope default)"),
        ([0.7, -0.1], "Medium-high throttle (70%), slight down elevator"),
    ]

    def trim_cost(x, verbose=False):
        """Trim cost function with diagnostic output"""
        elevator_norm, throttle_norm = x
        elevator_norm = max(-1.0, min(1.0, elevator_norm))
        throttle_norm = max(0.0, min(1.0, throttle_norm))

        fdm['fcs/elevator-cmd-norm'] = elevator_norm
        fdm['fcs/throttle-cmd-norm'] = throttle_norm
        fdm.run()

        wdot = fdm['accelerations/wdot-ft_sec2']
        qdot = fdm['accelerations/qdot-rad_sec2']

        if verbose:
            alpha_deg = fdm['aero/alpha-deg']
            pitch_deg = fdm['attitude/theta-deg']
            thrust_lbs = fdm['forces/fbx-external-lbs'] if 'forces/fbx-external-lbs' in fdm.get_property_catalog() else 0.0
            CL = fdm['aero/CL']
            CD = fdm['aero/CD']

            print(f"      Elev={elevator_norm:+.3f} Thr={throttle_norm:.3f}: wdot={wdot:+8.3f} qdot={qdot:+8.5f} alpha={alpha_deg:+5.2f}° pitch={pitch_deg:+5.2f}° thrust={thrust_lbs:.3f}lbs CL={CL:.4f} CD={CD:.4f}")

        return [wdot, qdot]

    best_result = None
    best_convergence = float('inf')

    for initial_guess, description in initial_guesses:
        print(f"\n[INFO] Trying initial guess: {description}")
        print(f"   Initial: elevator={initial_guess[0]:+.3f}, throttle={initial_guess[1]:.3f}")

        # Show initial cost
        print(f"   Initial cost:")
        initial_cost = trim_cost(initial_guess, verbose=True)

        try:
            result = fsolve(trim_cost, initial_guess, full_output=True)
            solution = result[0]
            info = result[1]

            elevator_trim = solution[0]
            throttle_trim = solution[1]

            final_cost = trim_cost(solution)
            wdot_final = abs(final_cost[0])
            qdot_final = abs(final_cost[1])

            convergence_quality = wdot_final + qdot_final * 10.0

            print(f"   Final solution:")
            trim_cost(solution, verbose=True)
            print(f"   Convergence: wdot={wdot_final:.4f} qdot={qdot_final:.6f} quality={convergence_quality:.4f}")

            if convergence_quality < best_convergence:
                best_convergence = convergence_quality
                best_result = {
                    'elevator': elevator_trim,
                    'throttle': throttle_trim,
                    'wdot': wdot_final,
                    'qdot': qdot_final,
                    'initial_guess': initial_guess,
                    'description': description,
                    'converged': (wdot_final < 1.0) and (qdot_final < 0.01)
                }

                if best_result['converged']:
                    print(f"   [OK] CONVERGED!")
                else:
                    print(f"   [WARN] Did not meet convergence criteria")

        except Exception as e:
            print(f"   [ERROR] fsolve failed: {e}")

    # ========================================
    # STEP 5: Summary and Recommendation
    # ========================================
    print("\n" + "="*70)
    print("DIAGNOSTIC SUMMARY")
    print("="*70)

    if best_result:
        print(f"\n[INFO] Best trim found:")
        print(f"   Initial guess: {best_result['description']}")
        print(f"   Elevator: {best_result['elevator']:.4f} norm ({best_result['elevator']*0.35*57.2958:.2f}°)")
        print(f"   Throttle: {best_result['throttle']:.4f} norm ({best_result['throttle']*100:.1f}%)")
        print(f"   wdot: {best_result['wdot']:.4f} ft/s² (target: <1.0)")
        print(f"   qdot: {best_result['qdot']:.6f} rad/s² (target: <0.01)")
        print(f"   Converged: {best_result['converged']}")

        print(f"\n[INFO] Diagnosis:")

        # Check aerodynamic coefficients (PRIORITY 1)
        print(f"\n   [PRIORITY 1] Aerodynamic Coefficients Validation:")
        print(f"   ⚠️  Auto-generated coefficients should be validated")
        print(f"")
        print(f"   Common issues (v3_calculated auto-generation):")
        print(f"      - CL0 too high: Typical range 0.0-0.1 (depends on airfoil)")
        print(f"      - Cmalpha too strong: Typical range -0.3 to -0.8 (pitch stability)")
        print(f"      - Cm_de too strong: Typical range -0.3 to -0.6 (elevator effectiveness)")
        print(f"      - CLalpha too high: Typical range 4.0-5.5 (lift curve slope)")
        print(f"      - Cmq too strong: Typical range -8.0 to -15.0 (pitch damping)")
        print(f"")
        print(f"   RECOMMENDATION:")
        print(f"      Verify coefficients against aerodynamic engineering references")
        print(f"      Excessively strong Cmalpha can prevent trim convergence")

        # Check thrust configuration (PRIORITY 2)
        tw_ratio = max_thrust_n / weight_n
        print(f"\n   [PRIORITY 2] Thrust Configuration:")
        if tw_ratio > 0.5:
            print(f"   ℹ️  High T/W ratio detected (T/W = {tw_ratio:.2f})")
            print(f"      This is acceptable - High T/W is NOT a problem by itself")
            print(f"      IMPORTANT: Test with reduced throttle initial guess (10-30%)")
            print(f"      - In JSBSim simulation: T/W 0.05-0.15 for pure aerodynamic flight model")
            print(f"      - test_trim_manual.py: Automatically tests 10-50% throttle range")
            print(f"      - Avoid starting from throttle 100% (thrust-supported mode)")
        elif tw_ratio >= 0.05:
            print(f"   ✅ Thrust configuration optimal (T/W = {tw_ratio:.2f})")
            print(f"      Pure aerodynamic flight mode (wings generate lift)")
        else:
            print(f"   ⚠️  Very low thrust (T/W = {tw_ratio:.2f})")
            print(f"      Aircraft may have difficulty climbing or accelerating")

        # Check convergence
        if best_result['converged']:
            print(f"   ✅ Trim converged successfully")
        else:
            print(f"   ⚠️ Trim did not converge to strict criteria")
            print(f"      Possible causes:")
            print(f"      1. 空力係数が不適切（CL0, CLalpha, Cmalpha等）")
            print(f"      2. 推力テーブルの非線形性")
            print(f"      3. 重心位置の不適切")
            print(f"      4. Initial guessの選択")

        # Recommendation
        print(f"\n[INFO] Recommendation:")
        if best_result['converged']:
            print(f"   ✅ Use this trim for flight simulation")
            print(f"      Throttle: {best_result['throttle']:.4f}")
            print(f"      Elevator: {best_result['elevator']:.4f}")
        else:
            print(f"   ⚠️ Consider adjusting:")
            print(f"      1. Increase max thrust in thrust table")
            print(f"      2. Adjust Cmalpha (pitch stability)")
            print(f"      3. Try different initial guess: {best_result['initial_guess']}")
    else:
        print(f"\n[ERROR] No trim solution found")
        print(f"\n[INFO] Possible root causes:")
        print(f"   1. Insufficient thrust (max thrust < weight)")
        print(f"   2. Incorrect aerodynamic coefficients")
        print(f"   3. Inappropriate initial guess")

    print("\n" + "="*70)

    return best_result


if __name__ == "__main__":
    if len(sys.argv) > 2:
        aircraft = sys.argv[1]
        aircraft_dir = sys.argv[2]
    elif len(sys.argv) > 1:
        aircraft = sys.argv[1]
        aircraft_dir = "aircraft"
    else:
        aircraft = "ExampleAircraft"
        aircraft_dir = "aircraft"

    result = trim_diagnostic(aircraft, aircraft_dir)

    sys.exit(0 if result and result['converged'] else 1)
