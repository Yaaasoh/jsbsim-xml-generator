# src/generate_xml.py
"""
JSBSim XML Generator - Stage 3 of FMS to JSBSim Converter

Generates JSBSim XML aircraft configuration from derived parameters.

Evidence Level: Inherits from derived_parameters.json (L1/L2/L3/L6)

Usage:
    python generate_xml.py <derived_parameters.json> <parsed_data.json> <output.xml>

Reference:
    - WORK_INSTRUCTION_CONVERTER_IMPLEMENTATION.md: Step 5
    - JSBSim template structure reference
"""

import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime


def generate_jsbsim_xml(parsed_data: Dict[str, Any], derived: Dict[str, Any], output_path: str):
    """
    Generate JSBSim XML from parsed and derived parameters.

    Phase 1 Implementation: Direct XML string generation (no Jinja2)

    Raises:
        ValueError: If required data fields are missing
        IOError: If XML file cannot be written
    """

    # Validate input data structure
    if "metadata" not in parsed_data:
        raise ValueError("[ERROR] parsed_data missing 'metadata' section")
    if "stability_derivatives" not in derived:
        raise ValueError("[ERROR] derived missing 'stability_derivatives' section")
    if "unit_conversions" not in derived:
        raise ValueError("[ERROR] derived missing 'unit_conversions' section")

    # Extract values
    try:
        aircraft_name = parsed_data["metadata"]["aircraft_name"]
        source_file = parsed_data["metadata"]["source_file"]
    except KeyError as e:
        raise ValueError(
            f"[ERROR] Missing required metadata field: {e}\n"
            f"Available metadata: {list(parsed_data.get('metadata', {}).keys())}"
        )

    # Geometry (converted to ft)
    geom_conv = derived["unit_conversions"]
    wingspan_ft = geom_conv["wingspan_ft"]
    chord_ft = geom_conv["chord_ft"]
    wing_area_ft2 = derived["calculated_geometry"]["wing_area_ft2"]
    h_tail_area_ft2 = geom_conv["h_tail_area_ft2"]
    v_tail_area_ft2 = geom_conv["v_tail_area_ft2"]
    tail_arm_ft = geom_conv["tail_arm_ft"]

    # Mass (converted to lbs, slug·ft²)
    mass_lbs = geom_conv["mass_lbs"]
    ixx_slugft2 = geom_conv["ixx_slugft2"]
    iyy_slugft2 = geom_conv["iyy_slugft2"]
    izz_slugft2 = geom_conv["izz_slugft2"]

    # Propulsion (converted to lbf)
    max_thrust_lbf = geom_conv["max_thrust_lbf"]

    # Aerodynamics
    clalpha = parsed_data["aerodynamics"]["clalpha_rad"]
    cl_max = parsed_data["aerodynamics"]["cl_max"]
    cd0 = parsed_data["aerodynamics"]["cf"]  # CD0 from FMS "cf" parameter

    # Stability derivatives
    stab = derived["stability_derivatives"]
    cmalpha = stab["cmalpha"]["value"]
    cmq = stab["cmq"]["value"]
    cm_de = stab["cm_de"]["value"]
    cybeta = stab["cybeta"]["value"]
    cnbeta = stab["cnbeta"]["value"]
    clbeta = stab["clbeta"]["value"]
    clp = stab["clp"]["value"]
    cnr = stab["cnr"]["value"]

    # Control surface deflections
    elevator_max = parsed_data["control"].get("elevator_max_rad", 0.35)
    aileron_max = parsed_data["control"].get("aileron_max_rad", 0.35)
    rudder_max = parsed_data["control"].get("rudder_max_rad", 0.35)

    # Use estimated values if original data unrealistic
    if "aileron_max_rad" in derived["control_estimates"]:
        aileron_max = derived["control_estimates"]["aileron_max_rad"]["estimated"]
    if "rudder_max_rad" in derived["control_estimates"]:
        rudder_max = derived["control_estimates"]["rudder_max_rad"]["estimated"]

    # CG location (simplified: at AERORP for Phase 1)
    cg_x_in = tail_arm_ft * 12 * 0.4  # Approximate: 40% of tail arm
    cg_y_in = 0.0
    cg_z_in = 0.0

    # Generate XML
    xml_content = f"""<?xml version='1.0' encoding='utf-8'?>
<fdm_config name="{aircraft_name}" version="2.0">
  <fileheader>
    <description>FMS {aircraft_name} converted to JSBSim (Phase 1 - Automatic Conversion)</description>
    <author>FMS to JSBSim Converter v1.0</author>
    <filecreationdate>{datetime.now().strftime('%Y-%m-%d')}</filecreationdate>
    <version>0.1</version>
    <reference refID="source_par" author="FMS" title="Source Parameter File" date="{datetime.now().year}">
      {source_file}
    </reference>
    <note>
      Automatically generated from FMS .par file.
      Evidence Levels: L1 (direct), L2 (calculated), L3 (assumptions), L6 (estimated).
      Cmalpha: {cmalpha:.4f} (L3, eta={stab['cmalpha']['assumptions']['eta']}, deps_dalpha={stab['cmalpha']['assumptions']['deps_dalpha']})
      Cmq: {cmq:.4f} (L3)
    </note>
  </fileheader>

  <metrics>
    <wingarea unit="FT2">{wing_area_ft2:.4f}</wingarea>
    <wingspan unit="FT">{wingspan_ft:.4f}</wingspan>
    <chord unit="FT">{chord_ft:.4f}</chord>

    <location name="AERORP" unit="IN">
      <x>{cg_x_in:.2f}</x>
      <y>{cg_y_in:.2f}</y>
      <z>{cg_z_in:.2f}</z>
    </location>
  </metrics>

  <mass_balance>
    <emptywt unit="LBS">{mass_lbs:.4f}</emptywt>

    <ixx unit="SLUG*FT2">{ixx_slugft2:.6f}</ixx>
    <iyy unit="SLUG*FT2">{iyy_slugft2:.6f}</iyy>
    <izz unit="SLUG*FT2">{izz_slugft2:.6f}</izz>
    <ixy unit="SLUG*FT2">0.0</ixy>
    <ixz unit="SLUG*FT2">0.0</ixz>
    <iyz unit="SLUG*FT2">0.0</iyz>

    <location name="CG" unit="IN">
      <x>{cg_x_in:.2f}</x>
      <y>{cg_y_in:.2f}</y>
      <z>{cg_z_in:.2f}</z>
    </location>
  </mass_balance>

  <ground_reactions />

  <propulsion>
    <tank type="FUEL">
      <location unit="IN">
        <x>{cg_x_in:.2f}</x>
        <y>0.0</y>
        <z>0.0</z>
      </location>
      <capacity unit="LBS">0.1</capacity>
      <contents unit="LBS">0.1</contents>
    </tank>
  </propulsion>

  <flight_control name="FCS: {aircraft_name}">
    <channel name="Pitch">
      <summer name="Pitch_Trim_Sum">
        <input>fcs/elevator-cmd-norm</input>
        <input>fcs/pitch-trim-cmd-norm</input>
        <clipto>
          <min>-1</min>
          <max>1</max>
        </clipto>
        <output>fcs/pitch-trim-sum</output>
      </summer>

      <aerosurface_scale name="Elevator_Control">
        <input>fcs/pitch-trim-sum</input>
        <range>
          <min>{-elevator_max:.4f}</min>
          <max>{elevator_max:.4f}</max>
        </range>
        <output>fcs/elevator-pos-rad</output>
      </aerosurface_scale>

      <aerosurface_scale name="Elevator_Normalized">
        <input>fcs/elevator-pos-rad</input>
        <domain>
          <min>{-elevator_max:.4f}</min>
          <max>{elevator_max:.4f}</max>
        </domain>
        <range>
          <min>-1</min>
          <max>1</max>
        </range>
        <output>fcs/elevator-pos-norm</output>
      </aerosurface_scale>
    </channel>

    <channel name="Roll">
      <summer name="Roll_Trim_Sum">
        <input>fcs/aileron-cmd-norm</input>
        <input>fcs/roll-trim-cmd-norm</input>
        <clipto>
          <min>-1</min>
          <max>1</max>
        </clipto>
        <output>fcs/roll-trim-sum</output>
      </summer>

      <aerosurface_scale name="Aileron_Control">
        <input>fcs/roll-trim-sum</input>
        <range>
          <min>{-aileron_max:.4f}</min>
          <max>{aileron_max:.4f}</max>
        </range>
        <output>fcs/aileron-pos-rad</output>
      </aerosurface_scale>

      <aerosurface_scale name="Aileron_Normalized">
        <input>fcs/aileron-pos-rad</input>
        <domain>
          <min>{-aileron_max:.4f}</min>
          <max>{aileron_max:.4f}</max>
        </domain>
        <range>
          <min>-1</min>
          <max>1</max>
        </range>
        <output>fcs/aileron-pos-norm</output>
      </aerosurface_scale>
    </channel>

    <channel name="Yaw">
      <summer name="Yaw_Trim_Sum">
        <input>fcs/rudder-cmd-norm</input>
        <input>fcs/yaw-trim-cmd-norm</input>
        <clipto>
          <min>-1</min>
          <max>1</max>
        </clipto>
        <output>fcs/yaw-trim-sum</output>
      </summer>

      <aerosurface_scale name="Rudder_Control">
        <input>fcs/yaw-trim-sum</input>
        <range>
          <min>{-rudder_max:.4f}</min>
          <max>{rudder_max:.4f}</max>
        </range>
        <output>fcs/rudder-pos-rad</output>
      </aerosurface_scale>

      <aerosurface_scale name="Rudder_Normalized">
        <input>fcs/rudder-pos-rad</input>
        <domain>
          <min>{-rudder_max:.4f}</min>
          <max>{rudder_max:.4f}</max>
        </domain>
        <range>
          <min>-1</min>
          <max>1</max>
        </range>
        <output>fcs/rudder-pos-norm</output>
      </aerosurface_scale>
    </channel>
  </flight_control>

  <aerodynamics>
    <axis name="LIFT">
      <function name="aero/force/Lift_alpha">
        <description>Lift due to angle of attack</description>
        <product>
          <property>aero/qbar-psf</property>
          <property>metrics/Sw-sqft</property>
          <product>
            <value>{clalpha:.4f}</value>
            <property>aero/alpha-rad</property>
          </product>
        </product>
      </function>
    </axis>

    <axis name="DRAG">
      <function name="aero/force/Drag_basic">
        <description>Basic drag (CD0 + induced drag)</description>
        <product>
          <property>aero/qbar-psf</property>
          <property>metrics/Sw-sqft</property>
          <sum>
            <value>{cd0:.4f}</value>
            <product>
              <value>0.10</value>
              <property>aero/cl-squared</property>
            </product>
          </sum>
        </product>
      </function>
    </axis>

    <axis name="SIDE">
      <function name="aero/force/Side_beta">
        <description>Side force due to sideslip (Cybeta)</description>
        <product>
          <property>aero/qbar-psf</property>
          <property>metrics/Sw-sqft</property>
          <property>aero/beta-rad</property>
          <value>{cybeta:.4f}</value>
        </product>
      </function>
    </axis>

    <axis name="PITCH">
      <function name="aero/moment/Pitch_alpha">
        <description>Pitching moment due to alpha (Cmalpha)</description>
        <product>
          <property>aero/qbar-psf</property>
          <property>metrics/Sw-sqft</property>
          <property>metrics/cbarw-ft</property>
          <product>
            <value>{cmalpha:.4f}</value>
            <property>aero/alpha-rad</property>
          </product>
        </product>
      </function>

      <function name="aero/moment/Pitch_rate">
        <description>Pitching moment due to pitch rate (Cmq)</description>
        <product>
          <property>aero/qbar-psf</property>
          <property>metrics/Sw-sqft</property>
          <property>metrics/cbarw-ft</property>
          <value>{cmq:.4f}</value>
          <property>aero/ci2vel</property>
          <property>velocities/q-rad_sec</property>
        </product>
      </function>

      <function name="aero/moment/Pitch_elevator">
        <description>Pitching moment due to elevator (Cm_de)</description>
        <product>
          <property>aero/qbar-psf</property>
          <property>metrics/Sw-sqft</property>
          <property>metrics/cbarw-ft</property>
          <value>{cm_de:.4f}</value>
          <property>fcs/elevator-pos-rad</property>
        </product>
      </function>
    </axis>

    <axis name="ROLL">
      <function name="aero/moment/Roll_beta">
        <description>Roll moment due to sideslip (Clbeta)</description>
        <product>
          <property>aero/qbar-psf</property>
          <property>metrics/Sw-sqft</property>
          <property>metrics/bw-ft</property>
          <property>aero/beta-rad</property>
          <value>{clbeta:.4f}</value>
        </product>
      </function>

      <function name="aero/moment/Roll_damp">
        <description>Roll damping (Clp)</description>
        <product>
          <property>aero/qbar-psf</property>
          <property>metrics/Sw-sqft</property>
          <property>metrics/bw-ft</property>
          <value>{clp:.4f}</value>
          <property>aero/bi2vel</property>
          <property>velocities/p-rad_sec</property>
        </product>
      </function>

      <function name="aero/moment/Roll_aileron">
        <description>Roll control power (Cl_da)</description>
        <product>
          <property>aero/qbar-psf</property>
          <property>metrics/Sw-sqft</property>
          <property>metrics/bw-ft</property>
          <value>0.15</value>
          <property>fcs/aileron-pos-rad</property>
        </product>
      </function>
    </axis>

    <axis name="YAW">
      <function name="aero/moment/Yaw_beta">
        <description>Weathercock stability (Cnbeta)</description>
        <product>
          <property>aero/qbar-psf</property>
          <property>metrics/Sw-sqft</property>
          <property>metrics/bw-ft</property>
          <property>aero/beta-rad</property>
          <value>{cnbeta:.4f}</value>
        </product>
      </function>

      <function name="aero/moment/Yaw_damp">
        <description>Yaw damping (Cnr)</description>
        <product>
          <property>aero/qbar-psf</property>
          <property>metrics/Sw-sqft</property>
          <property>metrics/bw-ft</property>
          <value>{cnr:.4f}</value>
          <property>aero/bi2vel</property>
          <property>velocities/r-rad_sec</property>
        </product>
      </function>

      <function name="aero/moment/Yaw_rudder">
        <description>Yaw control power (Cn_dr)</description>
        <product>
          <property>aero/qbar-psf</property>
          <property>metrics/Sw-sqft</property>
          <property>metrics/bw-ft</property>
          <value>-0.10</value>
          <property>fcs/rudder-pos-rad</property>
        </product>
      </function>
    </axis>
  </aerodynamics>

  <external_reactions>
    <force name="propeller-thrust" frame="BODY">
      <location unit="IN">
        <x>0.00</x>
        <y>0.0</y>
        <z>0.0</z>
      </location>
      <direction>
        <x>1.0</x>
        <y>0.0</y>
        <z>0.0</z>
      </direction>
      <function>
        <table>
          <independentVar lookup="row">fcs/throttle-cmd-norm</independentVar>
          <tableData>
            0.00   0.0000
            0.10   {max_thrust_lbf * 0.1:.4f}
            0.20   {max_thrust_lbf * 0.2:.4f}
            0.30   {max_thrust_lbf * 0.3:.4f}
            0.40   {max_thrust_lbf * 0.4:.4f}
            0.50   {max_thrust_lbf * 0.5:.4f}
            0.60   {max_thrust_lbf * 0.6:.4f}
            0.70   {max_thrust_lbf * 0.7:.4f}
            0.80   {max_thrust_lbf * 0.8:.4f}
            0.90   {max_thrust_lbf * 0.9:.4f}
            1.00   {max_thrust_lbf:.4f}
          </tableData>
        </table>
      </function>
    </force>
  </external_reactions>
</fdm_config>
"""

    # Write XML file
    try:
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
    except IOError as e:
        raise IOError(
            f"[ERROR] Failed to write XML file: {output_path}\n"
            f"Error: {e}"
        )


def generate_generation_report(parsed_data: Dict, derived: Dict, xml_path: str, report_path: str):
    """Generate XML generation report."""
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("FMS to JSBSim XML Generation Report\n")
        f.write("=" * 70 + "\n\n")

        aircraft = parsed_data["metadata"]["aircraft_name"]
        f.write(f"Aircraft: {aircraft}\n")
        f.write(f"Output XML: {xml_path}\n")
        f.write(f"Generation Date: {datetime.now().isoformat()}\n\n")

        f.write("GENERATED SECTIONS\n")
        f.write("-" * 70 + "\n")
        f.write("  ✅ fileheader\n")
        f.write("  ✅ metrics\n")
        f.write("  ✅ mass_balance\n")
        f.write("  ✅ flight_control (3 channels: Pitch, Roll, Yaw)\n")
        f.write("  ✅ aerodynamics (5 axes: LIFT, DRAG, SIDE, PITCH, ROLL, YAW)\n")
        f.write("  ✅ external_reactions (propeller thrust)\n\n")

        f.write("EVIDENCE LEVELS SUMMARY\n")
        f.write("-" * 70 + "\n")
        f.write(f"  L1 (Direct): Geometry, Mass, Aerodynamics from .par\n")
        f.write(f"  L2 (Calculated): Wing area, Aspect ratio, Tail volumes\n")
        f.write(f"  L3 (Assumptions): Cmalpha, Cmq, Cm_de, Cnbeta, Clp, Cnr\n")
        if derived["control_estimates"]:
            f.write(f"  L6 (Estimated): Control surface deflections\n")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 4:
        print("Usage: python generate_xml.py <derived_parameters.json> <parsed_data.json> <output.xml>")
        sys.exit(1)

    derived_json = sys.argv[1]
    parsed_json = sys.argv[2]
    output_xml = sys.argv[3]

    # Load inputs
    with open(derived_json, 'r', encoding='utf-8') as f:
        derived = json.load(f)

    with open(parsed_json, 'r', encoding='utf-8') as f:
        parsed_data = json.load(f)

    # Generate XML
    generate_jsbsim_xml(parsed_data, derived, output_xml)

    # Generate report
    report_path = "generation_report.txt"
    generate_generation_report(parsed_data, derived, output_xml, report_path)

    print(f"[OK] XML generated: {output_xml}")
    print(f"[OK] Report generated: {report_path}")
