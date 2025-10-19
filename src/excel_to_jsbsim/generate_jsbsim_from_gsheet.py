#!/usr/bin/env python3
"""
Minimal generator: Excel (GSheet-compatible) -> JSON IR -> JSBSim XML (skeleton)
- Reads the provided Excel template
- Builds a normalized JSON intermediate representation
- Emits a minimal fdm_config XML using metrics/mass_balance/propulsion/output
Notes:
- No external internet access required.
- Requires: pandas, openpyxl
Usage (PowerShell one-line):
python .\generate_jsbsim_from_gsheet.py -i .\JSBSim_XML_Authoring_Template_v1.xlsx -o .\out
"""
import argparse, json
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
import xml.etree.ElementTree as ET
from unit_conversion import convert_user_unit_to_jsbsim

# JSBSim unit conversion constants
# JSBSim strictly requires English units
M2_TO_FT2 = 10.7639      # Square meters to square feet
M_TO_FT = 3.28084        # Meters to feet
M_TO_IN = 39.3701        # Meters to inches
KGM2_TO_SLUGFT2 = 0.73756  # kg·m² to slug·ft²
KG_TO_LBS = 2.20462      # Kilograms to pounds

def read_sheet(df):
    # Standardize column names - remove newlines, normalize spaces, and strip whitespace
    import re
    df = df.rename(columns={c: re.sub(r'\s+', ' ', c.replace('\n', ' ')).strip() for c in df.columns})

    # Also normalize VarName column values (v3_calculated has newlines in VarName values)
    # Example: 'aero/\nCmalpha' → 'aero/ Cmalpha' → 'aero/Cmalpha'
    if "VarName (property/tag)" in df.columns:
        df["VarName (property/tag)"] = df["VarName (property/tag)"].apply(
            lambda x: re.sub(r'\s*/\s*', '/', re.sub(r'\s+', ' ', str(x).replace('\n', ' ')).strip()) if pd.notna(x) else x
        )

    return df

def collect_first(df, varname):
    rows = df[df["VarName (property/tag)"]==varname]
    if rows.empty:
        return None
    row = rows.iloc[0]
    # Convert NaN to None for cleaner handling
    value = row["Value"]
    unit = row["Unit"]
    if pd.isna(value):
        value = None
    if pd.isna(unit):
        unit = None

    # Apply unit conversion if both value and unit are present
    if value is not None and unit is not None:
        converted_value, jsbsim_unit = convert_user_unit_to_jsbsim(value, unit)
        # Convert numpy types to Python native types for JSON serialization
        if isinstance(converted_value, (np.integer, np.floating)):
            converted_value = converted_value.item()
        if isinstance(value, (np.integer, np.floating)):
            value = value.item()
        return dict(
            value = converted_value,
            unit  = jsbsim_unit,
            original_value = value,  # Store for debugging
            original_unit = unit,    # Store for debugging
            required = str(row.get("Required","")).upper()=="YES"
        )
    else:
        # Convert numpy types to Python native types for JSON serialization
        if isinstance(value, (np.integer, np.floating)):
            value = value.item()
        return dict(
            value = value,
            unit  = unit,
            required = str(row.get("Required","")).upper()=="YES"
        )

def build_ir(xlsx_path):
    xl = pd.ExcelFile(xlsx_path)
    ir = {"fileheader":{}, "metrics":{}, "mass_balance":{}, "ground_reactions":[], "propulsion":{}, "aerodynamics":{}, "output":{}, "tables":{}}

    # fileheader
    if "T_01_fileheader" in xl.sheet_names or "T_01_ファイルヘッダー" in xl.sheet_names:
        sheet_name = "T_01_ファイルヘッダー" if "T_01_ファイルヘッダー" in xl.sheet_names else "T_01_fileheader"
        df = read_sheet(pd.read_excel(xlsx_path, sheet_name=sheet_name))
        name = collect_first(df,"fileheader/name") or {}
        version = collect_first(df,"fileheader/version") or {}
        desc = collect_first(df,"fileheader/description") or {}
        ir["fileheader"] = {
            "name": name.get("value") or "MyAircraft",
            "version": version.get("value") or "2.0",
            "desc": desc.get("value") or ""
        }

    # metrics
    if "T_02_metrics" in xl.sheet_names or "T_02_機体寸法" in xl.sheet_names:
        sheet_name = "T_02_機体寸法" if "T_02_機体寸法" in xl.sheet_names else "T_02_metrics"
        df = read_sheet(pd.read_excel(xlsx_path, sheet_name=sheet_name))
        ir["metrics"] = {
            "wing_area": collect_first(df,"metrics/wing_area"),
            "wing_span": collect_first(df,"metrics/wing_span"),
            "chord_avg": collect_first(df,"metrics/chord_avg"),
            "ref_point": {
                "x": collect_first(df,"metrics/ref_point/x"),
                "y": collect_first(df,"metrics/ref_point/y"),
                "z": collect_first(df,"metrics/ref_point/z"),
            }
        }

    # mass_balance
    if "T_03_mass_balance" in xl.sheet_names or "T_03_質量バランス" in xl.sheet_names:
        sheet_name = "T_03_質量バランス" if "T_03_質量バランス" in xl.sheet_names else "T_03_mass_balance"
        df = read_sheet(pd.read_excel(xlsx_path, sheet_name=sheet_name))
        ir["mass_balance"] = {
            "I": {
                "ixx": collect_first(df,"mass/I/ixx"),
                "iyy": collect_first(df,"mass/I/iyy"),
                "izz": collect_first(df,"mass/I/izz"),
            },
            "empty_weight": collect_first(df,"mass/empty_weight"),
            "CG": {
                "x": collect_first(df,"mass/CG/x"),
                "y": collect_first(df,"mass/CG/y"),
                "z": collect_first(df,"mass/CG/z"),
            },
            "pointmasses": []
        }
        # multiple pointmasses
        pm_rows = df[df["Section"]=="mass_balance.pointmass"]
        for _, r in pm_rows.iterrows():
            pm_value = r.get("Value")
            pm_name = "" if pd.isna(pm_value) else str(pm_value)
            ir["mass_balance"]["pointmasses"].append({
                "name": pm_name if r.get("VarName (property/tag)")=="mass/pointmass/name" else "",
                "mass": None,
                "x": None,"y": None,"z": None
            })

    # ground_reactions (NEW for Phase 2)
    if "T_04_ground_reactions" in xl.sheet_names or "T_04_地上反力" in xl.sheet_names:
        sheet_name = "T_04_地上反力" if "T_04_地上反力" in xl.sheet_names else "T_04_ground_reactions"
        df = read_sheet(pd.read_excel(xlsx_path, sheet_name=sheet_name))
        contact = {
            "type": collect_first(df,"ground/type"),
            "name": collect_first(df,"ground/name"),
            "location": {
                "x": collect_first(df,"ground/x"),
                "y": collect_first(df,"ground/y"),
                "z": collect_first(df,"ground/z"),
            },
            "k_spring": collect_first(df,"ground/k_spring"),
            "c_damper": collect_first(df,"ground/c_damper"),
            "mu_static": collect_first(df,"ground/mu_static"),
            "mu_kinetic": collect_first(df,"ground/mu_kinetic"),
        }
        # データがある場合のみ追加
        if contact["type"] and contact["type"].get("value"):
            ir["ground_reactions"].append(contact)

    # propulsion
    if "T_05_propulsion" in xl.sheet_names or "T_05_推進系" in xl.sheet_names:
        sheet_name = "T_05_推進系" if "T_05_推進系" in xl.sheet_names else "T_05_propulsion"
        df = read_sheet(pd.read_excel(xlsx_path, sheet_name=sheet_name))
        ir["propulsion"] = {
            "engine": {
                "type": collect_first(df,"prop/engine/type"),
                "name": collect_first(df,"prop/engine/name"),
                "file": collect_first(df,"prop/engine/file"),
            },
            "thruster": {
                "type": collect_first(df,"prop/thruster/type"),
                "name": collect_first(df,"prop/thruster/name"),
                "x": collect_first(df,"prop/thruster/x"),
                "y": collect_first(df,"prop/thruster/y"),
                "z": collect_first(df,"prop/thruster/z"),
            },
            "prop_static_map": []
        }
    if "T_05a_prop_static_thrust_map" in xl.sheet_names:
        dfm = pd.read_excel(xlsx_path, sheet_name="T_05a_prop_static_thrust_map")
        for _, r in dfm.iterrows():
            rpm = r.get("rpm")
            th  = r.get("thrust_N")
            if pd.notna(rpm) and pd.notna(th):
                ir["propulsion"]["prop_static_map"].append({"rpm": float(rpm), "thrust_N": float(th)})

    # aerodynamics (NEW for Phase 3 Phase B)
    if "T_06_空力係数" in xl.sheet_names or "T_06_aerodynamics_functions" in xl.sheet_names:
        sheet_name = "T_06_空力係数" if "T_06_空力係数" in xl.sheet_names else "T_06_aerodynamics_functions"
        df = read_sheet(pd.read_excel(xlsx_path, sheet_name=sheet_name))
        ir["aerodynamics"] = {
            # v2_complete basic parameters
            "CL0": collect_first(df,"aero/CL0"),
            "CLalpha": collect_first(df,"aero/CLalpha"),
            "CLmax": collect_first(df,"aero/CLmax"),
            "CLmin": collect_first(df,"aero/CLmin"),
            "CD0": collect_first(df,"aero/CD0"),
            "K": collect_first(df,"aero/K"),
            "Cm0": collect_first(df,"aero/Cm0"),
            "Cmalpha": collect_first(df,"aero/Cmalpha"),
            "CLde": collect_first(df,"aero/CLde"),
            "Cmde": collect_first(df,"aero/Cmde"),
            # v3_calculated additional stability derivatives (8 parameters)
            "Cmq": collect_first(df,"aero/Cmq"),        # Pitch damping
            "Cm_de": collect_first(df,"aero/Cm_de"),    # Elevator effectiveness
            "Cybeta": collect_first(df,"aero/Cybeta"),  # Side force derivative
            "Cnbeta": collect_first(df,"aero/Cnbeta"),  # Weathercock stability
            "Clbeta": collect_first(df,"aero/Clbeta"),  # Dihedral effect
            "Clp": collect_first(df,"aero/Clp"),        # Roll damping
            "Cnr": collect_first(df,"aero/Cnr"),        # Yaw damping
            "CLalpha": collect_first(df,"aero/CLalpha"), # Lift curve slope (v3 stores separately)
        }

    # output
    if "T_08_output" in xl.sheet_names:
        df = read_sheet(pd.read_excel(xlsx_path, sheet_name="T_08_output"))
        ir["output"] = {
            "file": collect_first(df,"output/file_name"),
            "rate_hz": collect_first(df,"output/rate_hz"),
            "properties": collect_first(df,"output/properties"),
        }

    return ir

def safe_value(v, default=""):
    """Convert value to safe string, handling None, NaN, and numpy types"""
    if v is None:
        return default
    # Handle numpy types
    if isinstance(v, (np.floating, np.integer)):
        if np.isnan(v) or np.isinf(v):
            return default
        v = v.item()  # Convert to Python native type
    if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
        return default
    return str(v)

def text(v):
    """Convert value to string, handling None and NaN"""
    return safe_value(v, "")

def add_text(parent, tag, value, unit=None):
    el = ET.SubElement(parent, tag)
    # Handle NaN in unit attribute as well
    if unit and not (isinstance(unit, float) and (np.isnan(unit) if isinstance(unit, (float, np.floating)) else False)):
        el.set("unit", safe_value(unit))
    el.text = text(value)
    return el

def get_default_aero_data():
    """デフォルト空力係数（典型的な小型固定翼機の値）"""
    return {
        'CL0': 0.25,        # ゼロ迎角揚力係数（キャンバー翼の典型値）
        'CLalpha': 5.0,     # 揚力傾斜（アスペクト比6-8の翼の典型値）
        'CD0': 0.028,       # 零揚力抗力係数（小型機の典型値）- トリム収束に重要
        'K': 0.0796,        # 誘導抗力係数
        'Cm0': 0.0,         # ゼロ迎角ピッチモーメント係数（中立）
        'Cmalpha': -0.50,   # ピッチモーメント傾斜（縦安定性）- トリム収束に重要
    }

def validate_aero_data(data):
    """空力係数の妥当性チェック"""
    import logging

    if not (3.0 <= data['CLalpha'] <= 7.0):
        logging.warning(f"CLalpha={data['CLalpha']}が妥当範囲外（3.0-7.0）")

    if not (0.02 <= data['CD0'] <= 0.10):
        logging.warning(f"CD0={data['CD0']}が妥当範囲外（0.02-0.10）")

    if data['Cmalpha'] >= 0:
        logging.error(f"Cmalpha={data['Cmalpha']}が正（縦不安定）")
        raise ValueError("Cmalphaは負である必要があります（縦安定性）")

def generate_aerodynamics(root, ir):
    """aerodynamics要素を生成 (v3_calculated対応: 6軸完全モデル)"""
    # aerodynamicsデータ取得
    aero_ir = ir.get("aerodynamics", {})

    # デフォルト値準備
    defaults = get_default_aero_data()

    # IRから値を取得（なければデフォルト）
    aero_data = {
        'CL0': aero_ir.get('CL0', {}).get('value', defaults['CL0']) if aero_ir.get('CL0') else defaults['CL0'],
        'CLalpha': aero_ir.get('CLalpha', {}).get('value', defaults['CLalpha']) if aero_ir.get('CLalpha') else defaults['CLalpha'],
        'CD0': aero_ir.get('CD0', {}).get('value', defaults['CD0']) if aero_ir.get('CD0') else defaults['CD0'],
        'K': aero_ir.get('K', {}).get('value', defaults['K']) if aero_ir.get('K') else defaults['K'],
        'Cm0': aero_ir.get('Cm0', {}).get('value', defaults['Cm0']) if aero_ir.get('Cm0') else defaults['Cm0'],
        'Cmalpha': aero_ir.get('Cmalpha', {}).get('value', defaults['Cmalpha']) if aero_ir.get('Cmalpha') else defaults['Cmalpha'],
    }

    # v3_calculated追加パラメータ（あれば使用、なければNone）
    v3_data = {}
    for key in ['Cmq', 'Cm_de', 'Cybeta', 'Cnbeta', 'Clbeta', 'Clp', 'Cnr']:
        param = aero_ir.get(key)
        if param and param.get('value') is not None:
            v3_data[key] = param.get('value')
        else:
            v3_data[key] = None

    # 検証
    validate_aero_data(aero_data)

    # aerodynamics要素作成
    aero = ET.SubElement(root, 'aerodynamics')

    # コメント追加
    if any(v is not None for v in v3_data.values()):
        comment_text = """
  v3_calculated Full Aerodynamics Implementation
  6-axis model: LIFT, DRAG, SIDE, ROLL, PITCH, YAW
  Stability derivatives from automated calculation (Roskam 1979)
  """
    else:
        comment_text = """
  Phase 3-1 Minimal Aerodynamics Implementation
  Linear model: LIFT, DRAG, PITCH axes only
  Based on FMS 200g aircraft estimation
  """
    aero.append(ET.Comment(comment_text))

    # LIFT AXIS
    axis_lift = ET.SubElement(aero, 'axis', name='LIFT')
    generate_lift_alpha(axis_lift, aero_data)

    # DRAG AXIS
    axis_drag = ET.SubElement(aero, 'axis', name='DRAG')
    generate_drag_basic(axis_drag, aero_data)

    # PITCH AXIS
    axis_pitch = ET.SubElement(aero, 'axis', name='PITCH')
    generate_pitch_alpha(axis_pitch, aero_data)

    # Cmq: v3があれば使用、なければデフォルト-12.0
    cmq_value = v3_data.get('Cmq') if v3_data.get('Cmq') is not None else -12.0
    generate_pitch_rate(axis_pitch, cmq=cmq_value)

    # Cm_de: Elevator効果（v3のみ）
    if v3_data.get('Cm_de') is not None:
        generate_pitch_elevator(axis_pitch, cm_de=v3_data['Cm_de'])

    # SIDE AXIS (v3のみ)
    if v3_data.get('Cybeta') is not None:
        axis_side = ET.SubElement(aero, 'axis', name='SIDE')
        generate_side_beta(axis_side, cybeta=v3_data['Cybeta'])

    # ROLL AXIS (v3のみ)
    if v3_data.get('Clbeta') is not None or v3_data.get('Clp') is not None:
        axis_roll = ET.SubElement(aero, 'axis', name='ROLL')
        if v3_data.get('Clbeta') is not None:
            generate_roll_beta(axis_roll, clbeta=v3_data['Clbeta'])
        if v3_data.get('Clp') is not None:
            generate_roll_rate(axis_roll, clp=v3_data['Clp'])

    # YAW AXIS (v3のみ)
    if v3_data.get('Cnbeta') is not None or v3_data.get('Cnr') is not None:
        axis_yaw = ET.SubElement(aero, 'axis', name='YAW')
        if v3_data.get('Cnbeta') is not None:
            generate_yaw_beta(axis_yaw, cnbeta=v3_data['Cnbeta'])
        if v3_data.get('Cnr') is not None:
            generate_yaw_rate(axis_yaw, cnr=v3_data['Cnr'])

    return aero

def generate_lift_alpha(axis, data):
    """揚力 - 迎角依存 (CL = CL0 + CLalpha * alpha)"""
    func = ET.SubElement(axis, 'function', name='aero/force/Lift_alpha')
    desc = ET.SubElement(func, 'description')
    desc.text = 'Lift due to angle of attack (CL = CL0 + CLalpha * alpha)'

    product = ET.SubElement(func, 'product')
    prop1 = ET.SubElement(product, 'property')
    prop1.text = 'aero/qbar-psf'
    prop2 = ET.SubElement(product, 'property')
    prop2.text = 'metrics/Sw-sqft'

    sum_cl = ET.SubElement(product, 'sum')
    val_cl0 = ET.SubElement(sum_cl, 'value')
    val_cl0.text = str(data['CL0'])

    prod_alpha = ET.SubElement(sum_cl, 'product')
    val_cla = ET.SubElement(prod_alpha, 'value')
    val_cla.text = str(data['CLalpha'])
    prop_alpha = ET.SubElement(prod_alpha, 'property')
    prop_alpha.text = 'aero/alpha-rad'

def generate_drag_basic(axis, data):
    """抗力 - 基本 (CD = CD0 + K*CL²)"""
    func = ET.SubElement(axis, 'function', name='aero/force/Drag_basic')
    desc = ET.SubElement(func, 'description')
    desc.text = 'Total drag (CD = CD0 + K*CL²)'

    product = ET.SubElement(func, 'product')
    prop1 = ET.SubElement(product, 'property')
    prop1.text = 'aero/qbar-psf'
    prop2 = ET.SubElement(product, 'property')
    prop2.text = 'metrics/Sw-sqft'

    sum_cd = ET.SubElement(product, 'sum')
    val_cd0 = ET.SubElement(sum_cd, 'value')
    val_cd0.text = str(data['CD0'])

    prod_cdi = ET.SubElement(sum_cd, 'product')
    val_k = ET.SubElement(prod_cdi, 'value')
    val_k.text = str(data['K'])
    prop_cl2 = ET.SubElement(prod_cdi, 'property')
    prop_cl2.text = 'aero/cl-squared'

def generate_pitch_alpha(axis, data):
    """ピッチモーメント - 迎角依存 (Cm = Cm0 + Cmalpha * alpha)"""
    func = ET.SubElement(axis, 'function', name='aero/moment/Pitch_alpha')
    desc = ET.SubElement(func, 'description')
    desc.text = 'Pitching moment due to angle of attack (Cm = Cm0 + Cmalpha * alpha)'

    product = ET.SubElement(func, 'product')
    prop1 = ET.SubElement(product, 'property')
    prop1.text = 'aero/qbar-psf'
    prop2 = ET.SubElement(product, 'property')
    prop2.text = 'metrics/Sw-sqft'
    prop3 = ET.SubElement(product, 'property')
    prop3.text = 'metrics/cbarw-ft'

    sum_cm = ET.SubElement(product, 'sum')
    val_cm0 = ET.SubElement(sum_cm, 'value')
    val_cm0.text = str(data['Cm0'])

    prod_alpha = ET.SubElement(sum_cm, 'product')
    val_cma = ET.SubElement(prod_alpha, 'value')
    val_cma.text = str(data['Cmalpha'])
    prop_alpha = ET.SubElement(prod_alpha, 'property')
    prop_alpha.text = 'aero/alpha-rad'

def generate_pitch_rate(axis, cmq=-12.0):
    """ピッチモーメント - ピッチレート依存 (Cmq: pitch rate damping)"""
    func = ET.SubElement(axis, 'function', name='aero/moment/Pitch_rate')
    desc = ET.SubElement(func, 'description')
    desc.text = 'Pitching moment due to pitch rate (Cmq: pitch rate damping)'

    product = ET.SubElement(func, 'product')
    prop1 = ET.SubElement(product, 'property')
    prop1.text = 'aero/qbar-psf'
    prop2 = ET.SubElement(product, 'property')
    prop2.text = 'metrics/Sw-sqft'
    prop3 = ET.SubElement(product, 'property')
    prop3.text = 'metrics/cbarw-ft'
    val_cmq = ET.SubElement(product, 'value')
    val_cmq.text = str(cmq)  # v3: Excelから、v2: デフォルト-12.0
    prop4 = ET.SubElement(product, 'property')
    prop4.text = 'aero/ci2vel'
    prop5 = ET.SubElement(product, 'property')
    prop5.text = 'velocities/q-rad_sec'

def generate_pitch_elevator(axis, cm_de):
    """ピッチモーメント - エレベーター依存 (Cm_de: elevator effectiveness)"""
    func = ET.SubElement(axis, 'function', name='aero/moment/Pitch_elevator')
    desc = ET.SubElement(func, 'description')
    desc.text = 'Pitching moment due to elevator (Cm_de: elevator effectiveness)'

    product = ET.SubElement(func, 'product')
    prop1 = ET.SubElement(product, 'property')
    prop1.text = 'aero/qbar-psf'
    prop2 = ET.SubElement(product, 'property')
    prop2.text = 'metrics/Sw-sqft'
    prop3 = ET.SubElement(product, 'property')
    prop3.text = 'metrics/cbarw-ft'
    val_cmde = ET.SubElement(product, 'value')
    val_cmde.text = str(cm_de)
    prop4 = ET.SubElement(product, 'property')
    prop4.text = 'fcs/elevator-pos-rad'

def generate_side_beta(axis, cybeta):
    """横力 - 横滑り角依存 (Cybeta: side force derivative)"""
    func = ET.SubElement(axis, 'function', name='aero/force/Side_beta')
    desc = ET.SubElement(func, 'description')
    desc.text = 'Side force due to sideslip (Cybeta: side force derivative)'

    product = ET.SubElement(func, 'product')
    prop1 = ET.SubElement(product, 'property')
    prop1.text = 'aero/qbar-psf'
    prop2 = ET.SubElement(product, 'property')
    prop2.text = 'metrics/Sw-sqft'
    val_cy = ET.SubElement(product, 'value')
    val_cy.text = str(cybeta)
    prop3 = ET.SubElement(product, 'property')
    prop3.text = 'aero/beta-rad'

def generate_roll_beta(axis, clbeta):
    """ロールモーメント - 横滑り角依存 (Clbeta: dihedral effect)"""
    func = ET.SubElement(axis, 'function', name='aero/moment/Roll_beta')
    desc = ET.SubElement(func, 'description')
    desc.text = 'Rolling moment due to sideslip (Clbeta: dihedral effect)'

    product = ET.SubElement(func, 'product')
    prop1 = ET.SubElement(product, 'property')
    prop1.text = 'aero/qbar-psf'
    prop2 = ET.SubElement(product, 'property')
    prop2.text = 'metrics/Sw-sqft'
    prop3 = ET.SubElement(product, 'property')
    prop3.text = 'metrics/bw-ft'
    val_cl = ET.SubElement(product, 'value')
    val_cl.text = str(clbeta)
    prop4 = ET.SubElement(product, 'property')
    prop4.text = 'aero/beta-rad'

def generate_roll_rate(axis, clp):
    """ロールモーメント - ロールレート依存 (Clp: roll damping)"""
    func = ET.SubElement(axis, 'function', name='aero/moment/Roll_rate')
    desc = ET.SubElement(func, 'description')
    desc.text = 'Rolling moment due to roll rate (Clp: roll damping)'

    product = ET.SubElement(func, 'product')
    prop1 = ET.SubElement(product, 'property')
    prop1.text = 'aero/qbar-psf'
    prop2 = ET.SubElement(product, 'property')
    prop2.text = 'metrics/Sw-sqft'
    prop3 = ET.SubElement(product, 'property')
    prop3.text = 'metrics/bw-ft'
    val_clp = ET.SubElement(product, 'value')
    val_clp.text = str(clp)
    prop4 = ET.SubElement(product, 'property')
    prop4.text = 'aero/bi2vel'
    prop5 = ET.SubElement(product, 'property')
    prop5.text = 'velocities/p-rad_sec'

def generate_yaw_beta(axis, cnbeta):
    """ヨーモーメント - 横滑り角依存 (Cnbeta: weathercock stability)"""
    func = ET.SubElement(axis, 'function', name='aero/moment/Yaw_beta')
    desc = ET.SubElement(func, 'description')
    desc.text = 'Yawing moment due to sideslip (Cnbeta: weathercock stability)'

    product = ET.SubElement(func, 'product')
    prop1 = ET.SubElement(product, 'property')
    prop1.text = 'aero/qbar-psf'
    prop2 = ET.SubElement(product, 'property')
    prop2.text = 'metrics/Sw-sqft'
    prop3 = ET.SubElement(product, 'property')
    prop3.text = 'metrics/bw-ft'
    val_cn = ET.SubElement(product, 'value')
    val_cn.text = str(cnbeta)
    prop4 = ET.SubElement(product, 'property')
    prop4.text = 'aero/beta-rad'

def generate_yaw_rate(axis, cnr):
    """ヨーモーメント - ヨーレート依存 (Cnr: yaw damping)"""
    func = ET.SubElement(axis, 'function', name='aero/moment/Yaw_rate')
    desc = ET.SubElement(func, 'description')
    desc.text = 'Yawing moment due to yaw rate (Cnr: yaw damping)'

    product = ET.SubElement(func, 'product')
    prop1 = ET.SubElement(product, 'property')
    prop1.text = 'aero/qbar-psf'
    prop2 = ET.SubElement(product, 'property')
    prop2.text = 'metrics/Sw-sqft'
    prop3 = ET.SubElement(product, 'property')
    prop3.text = 'metrics/bw-ft'
    val_cnr = ET.SubElement(product, 'value')
    val_cnr.text = str(cnr)
    prop4 = ET.SubElement(product, 'property')
    prop4.text = 'aero/bi2vel'
    prop5 = ET.SubElement(product, 'property')
    prop5.text = 'velocities/r-rad_sec'

def generate_external_reactions(root, aerorp_x_in):
    """
    External Reactions推力モデル生成

    ExampleAircraft_reference.xml互換の推力定義を生成
    T-Motor AT2203 2300KV実測データベース（7x3.5" prop, 2S=7.4V）
    最大推力: 338g = 0.745 lbs @ 100% throttle

    Args:
        root: XML root element
        aerorp_x_in: AERORP X位置 (IN) - プロペラ位置計算の基準
    """
    ext_react = ET.SubElement(root, 'external_reactions')

    # コメント追加
    comment_text = """
    Propulsion: Direct thrust model based on T-Motor AT2203 2300KV real-world data

    Real-world specifications (2S = 7.4V, 7x3.5" propeller):
      Max thrust: 338g = 0.745 lbs @ 100% throttle
      Max power: 57W
      Cruise thrust: ~100g @ 30-40% throttle

    Thrust curve (estimated from typical brushless motor characteristics):
      0%: 0g
      30%: 100g = 0.220 lbs
      50%: 170g = 0.375 lbs
      70%: 250g = 0.551 lbs
      100%: 338g = 0.745 lbs
  """
    ext_react.append(ET.Comment(comment_text))

    # 推力force定義
    force = ET.SubElement(ext_react, 'force', name='propeller-thrust', frame='BODY')

    # 推力位置（機首、プロペラ位置）
    # ExampleAircraft_reference: AERORP=12.12 IN, propeller=0.787402 IN
    # → propeller is 0.0649 * AERORP forward
    # This ratio applies to similar aircraft geometry
    PROPELLER_TO_AERORP_RATIO = 0.0649  # 0.787402 / 12.12 = 0.0649
    propeller_x_in = PROPELLER_TO_AERORP_RATIO * aerorp_x_in

    location = ET.SubElement(force, 'location', unit='IN')
    add_text(location, 'x', propeller_x_in)  # Propeller location (nose), scaled from AERORP
    add_text(location, 'y', 0.0)
    add_text(location, 'z', 0.0)

    # 推力方向（前方）
    direction = ET.SubElement(force, 'direction')
    add_text(direction, 'x', 1.0)  # Forward thrust
    add_text(direction, 'y', 0.0)
    add_text(direction, 'z', 0.0)

    # 推力テーブル（throttle-cmd-norm → thrust LBS）
    function = ET.SubElement(force, 'function')
    table = ET.SubElement(function, 'table')
    indep_var = ET.SubElement(table, 'independentVar', lookup='row')
    indep_var.text = 'fcs/throttle-cmd-norm'

    # テーブルデータ（ExampleAircraft_reference.xml Line 89-101）
    table_data = ET.SubElement(table, 'tableData')
    table_data.text = """
            0.00   0.000
            0.10   0.050
            0.20   0.110
            0.30   0.220
            0.40   0.290
            0.50   0.375
            0.60   0.450
            0.70   0.551
            0.80   0.620
            0.90   0.685
            1.00   0.745
          """

    return ext_react

def generate_flight_control(root, aircraft_name="ExampleAircraft"):
    """
    Flight Control System (FCS) generation

    Based on par_to_jsbsim_converter/src/generate_xml.py (Lines 164-266)
    Complete 3-channel FCS: Pitch, Roll, Yaw

    JSBSim REQUIRES a <flight_control> section even with External Reactions.
    This FCS enables:
    - Trim computation (elevator, aileron, rudder trim)
    - Control surface position output (fcs/elevator-pos-rad, etc.)
    - Normalized position output (fcs/elevator-pos-norm, etc.)

    Args:
        root: XML root element
        aircraft_name: Aircraft name for FCS identifier
    """
    # Estimated control surface deflections (±30 deg = ±0.524 rad)
    # Based on typical RC aircraft control surface ranges
    ELEVATOR_MAX_RAD = 0.35  # ±20 degrees (conservative)
    AILERON_MAX_RAD = 0.35   # ±20 degrees
    RUDDER_MAX_RAD = 0.35    # ±20 degrees

    fcs = ET.SubElement(root, 'flight_control', name=f'FCS: {aircraft_name}')

    # ========== PITCH CHANNEL ==========
    ch_pitch = ET.SubElement(fcs, 'channel', name='Pitch')

    # Pitch Trim Sum
    summer_pitch = ET.SubElement(ch_pitch, 'summer', name='Pitch_Trim_Sum')
    ET.SubElement(summer_pitch, 'input').text = 'fcs/elevator-cmd-norm'
    ET.SubElement(summer_pitch, 'input').text = 'fcs/pitch-trim-cmd-norm'
    clipto_pitch = ET.SubElement(summer_pitch, 'clipto')
    ET.SubElement(clipto_pitch, 'min').text = '-1'
    ET.SubElement(clipto_pitch, 'max').text = '1'
    ET.SubElement(summer_pitch, 'output').text = 'fcs/pitch-trim-sum'

    # Elevator Control (normalized to radians)
    scale_elevator = ET.SubElement(ch_pitch, 'aerosurface_scale', name='Elevator_Control')
    ET.SubElement(scale_elevator, 'input').text = 'fcs/pitch-trim-sum'
    range_elev = ET.SubElement(scale_elevator, 'range')
    ET.SubElement(range_elev, 'min').text = f'{-ELEVATOR_MAX_RAD:.4f}'
    ET.SubElement(range_elev, 'max').text = f'{ELEVATOR_MAX_RAD:.4f}'
    ET.SubElement(scale_elevator, 'output').text = 'fcs/elevator-pos-rad'

    # Elevator Normalized (radians to normalized)
    scale_elev_norm = ET.SubElement(ch_pitch, 'aerosurface_scale', name='Elevator_Normalized')
    ET.SubElement(scale_elev_norm, 'input').text = 'fcs/elevator-pos-rad'
    domain_elev = ET.SubElement(scale_elev_norm, 'domain')
    ET.SubElement(domain_elev, 'min').text = f'{-ELEVATOR_MAX_RAD:.4f}'
    ET.SubElement(domain_elev, 'max').text = f'{ELEVATOR_MAX_RAD:.4f}'
    range_elev_norm = ET.SubElement(scale_elev_norm, 'range')
    ET.SubElement(range_elev_norm, 'min').text = '-1'
    ET.SubElement(range_elev_norm, 'max').text = '1'
    ET.SubElement(scale_elev_norm, 'output').text = 'fcs/elevator-pos-norm'

    # ========== ROLL CHANNEL ==========
    ch_roll = ET.SubElement(fcs, 'channel', name='Roll')

    # Roll Trim Sum
    summer_roll = ET.SubElement(ch_roll, 'summer', name='Roll_Trim_Sum')
    ET.SubElement(summer_roll, 'input').text = 'fcs/aileron-cmd-norm'
    ET.SubElement(summer_roll, 'input').text = 'fcs/roll-trim-cmd-norm'
    clipto_roll = ET.SubElement(summer_roll, 'clipto')
    ET.SubElement(clipto_roll, 'min').text = '-1'
    ET.SubElement(clipto_roll, 'max').text = '1'
    ET.SubElement(summer_roll, 'output').text = 'fcs/roll-trim-sum'

    # Aileron Control
    scale_aileron = ET.SubElement(ch_roll, 'aerosurface_scale', name='Aileron_Control')
    ET.SubElement(scale_aileron, 'input').text = 'fcs/roll-trim-sum'
    range_ail = ET.SubElement(scale_aileron, 'range')
    ET.SubElement(range_ail, 'min').text = f'{-AILERON_MAX_RAD:.4f}'
    ET.SubElement(range_ail, 'max').text = f'{AILERON_MAX_RAD:.4f}'
    ET.SubElement(scale_aileron, 'output').text = 'fcs/aileron-pos-rad'

    # Aileron Normalized
    scale_ail_norm = ET.SubElement(ch_roll, 'aerosurface_scale', name='Aileron_Normalized')
    ET.SubElement(scale_ail_norm, 'input').text = 'fcs/aileron-pos-rad'
    domain_ail = ET.SubElement(scale_ail_norm, 'domain')
    ET.SubElement(domain_ail, 'min').text = f'{-AILERON_MAX_RAD:.4f}'
    ET.SubElement(domain_ail, 'max').text = f'{AILERON_MAX_RAD:.4f}'
    range_ail_norm = ET.SubElement(scale_ail_norm, 'range')
    ET.SubElement(range_ail_norm, 'min').text = '-1'
    ET.SubElement(range_ail_norm, 'max').text = '1'
    ET.SubElement(scale_ail_norm, 'output').text = 'fcs/aileron-pos-norm'

    # ========== YAW CHANNEL ==========
    ch_yaw = ET.SubElement(fcs, 'channel', name='Yaw')

    # Yaw Trim Sum
    summer_yaw = ET.SubElement(ch_yaw, 'summer', name='Yaw_Trim_Sum')
    ET.SubElement(summer_yaw, 'input').text = 'fcs/rudder-cmd-norm'
    ET.SubElement(summer_yaw, 'input').text = 'fcs/yaw-trim-cmd-norm'
    clipto_yaw = ET.SubElement(summer_yaw, 'clipto')
    ET.SubElement(clipto_yaw, 'min').text = '-1'
    ET.SubElement(clipto_yaw, 'max').text = '1'
    ET.SubElement(summer_yaw, 'output').text = 'fcs/yaw-trim-sum'

    # Rudder Control
    scale_rudder = ET.SubElement(ch_yaw, 'aerosurface_scale', name='Rudder_Control')
    ET.SubElement(scale_rudder, 'input').text = 'fcs/yaw-trim-sum'
    range_rud = ET.SubElement(scale_rudder, 'range')
    ET.SubElement(range_rud, 'min').text = f'{-RUDDER_MAX_RAD:.4f}'
    ET.SubElement(range_rud, 'max').text = f'{RUDDER_MAX_RAD:.4f}'
    ET.SubElement(scale_rudder, 'output').text = 'fcs/rudder-pos-rad'

    # Rudder Normalized
    scale_rud_norm = ET.SubElement(ch_yaw, 'aerosurface_scale', name='Rudder_Normalized')
    ET.SubElement(scale_rud_norm, 'input').text = 'fcs/rudder-pos-rad'
    domain_rud = ET.SubElement(scale_rud_norm, 'domain')
    ET.SubElement(domain_rud, 'min').text = f'{-RUDDER_MAX_RAD:.4f}'
    ET.SubElement(domain_rud, 'max').text = f'{RUDDER_MAX_RAD:.4f}'
    range_rud_norm = ET.SubElement(scale_rud_norm, 'range')
    ET.SubElement(range_rud_norm, 'min').text = '-1'
    ET.SubElement(range_rud_norm, 'max').text = '1'
    ET.SubElement(scale_rud_norm, 'output').text = 'fcs/rudder-pos-norm'

    return fcs

def emit_xml(ir, out_xml):
    # Ensure all root attributes are safe strings
    root_name = safe_value(ir["fileheader"].get("name", "MyAircraft"), "MyAircraft")
    root_version = safe_value(ir["fileheader"].get("version", "2.0"), "2.0")

    # Create fdm_config root element with JSBSim official attributes
    root = ET.Element("fdm_config", name=root_name, version=root_version, release="BETA")

    # Add XML Schema namespace declaration (JSBSim official format)
    # Reference: http://jsbsim.sourceforge.net/JSBSim.xsd
    root.set("{http://www.w3.org/2001/XMLSchema-instance}noNamespaceSchemaLocation",
             "http://jsbsim.sourceforge.net/JSBSim.xsd")
    fh = ET.SubElement(root, "fileheader")

    # Add Evidence Level to description (for v3_calculated templates)
    # Detect v3_calculated by checking for stability derivatives in aerodynamics
    aero_ir = ir.get("aerodynamics", {})
    has_v3_derivatives = any(aero_ir.get(key) and aero_ir.get(key).get('value') is not None
                             for key in ['Cmq', 'Cm_de', 'Cybeta', 'Cnbeta', 'Clbeta', 'Clp', 'Cnr'])

    description = ir["fileheader"].get("desc","")
    if has_v3_derivatives:
        # Add Evidence Level information for v3_calculated templates
        # Format: CRITICAL_CORRECTION.md Line 580-592 recommended format
        evidence_level_note = (
            "\n\n"
            "Evidence Level: L2-L3 (Theoretical calculation with engineering assumptions)\n"
            f"Source: v3_calculated (auto-calculated stability derivatives from Roskam 1979)\n"
            f"Generated: {datetime.now().isoformat()}"
        )
        description = (description + evidence_level_note) if description else evidence_level_note.strip()

    add_text(fh, "description", description)

    # metrics (JSBSim requires English units and specific tag names)
    m = ET.SubElement(root, "metrics")

    # Wing area: M2 → FT2 (tag: wingarea)
    if ir["metrics"].get("wing_area"):
        value = ir["metrics"]["wing_area"]["value"]
        if value and str(value).strip():
            try:
                wing_area_m2 = float(value)
                wing_area_ft2 = wing_area_m2 * M2_TO_FT2
                add_text(m, "wingarea", wing_area_ft2, unit="FT2")
            except (ValueError, TypeError) as e:
                print(f"Warning: Invalid wing_area '{value}': {e}")

    # Wing span: M → FT (tag: wingspan)
    if ir["metrics"].get("wing_span"):
        value = ir["metrics"]["wing_span"]["value"]
        if value and str(value).strip():
            try:
                wing_span_m = float(value)
                wing_span_ft = wing_span_m * M_TO_FT
                add_text(m, "wingspan", wing_span_ft, unit="FT")
            except (ValueError, TypeError) as e:
                print(f"Warning: Invalid wing_span '{value}': {e}")

    # Average chord: M → FT (tag: chord)
    if ir["metrics"].get("chord_avg"):
        value = ir["metrics"]["chord_avg"]["value"]
        if value and str(value).strip():
            try:
                chord_avg_m = float(value)
                chord_avg_ft = chord_avg_m * M_TO_FT
                add_text(m, "chord", chord_avg_ft, unit="FT")
            except (ValueError, TypeError) as e:
                print(f"Warning: Invalid chord_avg '{value}': {e}")

    # Reference point: M → IN
    rp = ET.SubElement(m, "ref_point")
    if ir["metrics"]["ref_point"].get("x"):
        value = ir["metrics"]["ref_point"]["x"]["value"]
        if value is not None and str(value).strip():
            try:
                rp_x_m = float(value)
                rp_x_in = rp_x_m * M_TO_IN
                add_text(rp, "x", rp_x_in, unit="IN")
            except (ValueError, TypeError) as e:
                print(f"Warning: Invalid ref_point.x '{value}': {e}")

    if ir["metrics"]["ref_point"].get("y"):
        value = ir["metrics"]["ref_point"]["y"]["value"]
        if value is not None and str(value).strip():
            try:
                rp_y_m = float(value)
                rp_y_in = rp_y_m * M_TO_IN
                add_text(rp, "y", rp_y_in, unit="IN")
            except (ValueError, TypeError) as e:
                print(f"Warning: Invalid ref_point.y '{value}': {e}")

    if ir["metrics"]["ref_point"].get("z"):
        value = ir["metrics"]["ref_point"]["z"]["value"]
        if value is not None and str(value).strip():
            try:
                rp_z_m = float(value)
                rp_z_in = rp_z_m * M_TO_IN
                add_text(rp, "z", rp_z_in, unit="IN")
            except (ValueError, TypeError) as e:
                print(f"Warning: Invalid ref_point.z '{value}': {e}")

    # AERORP (空力中心): 典型的な小型固定翼機の推定値
    # 200g級機体の典型値: 約12 in (機首から約300mm)
    #
    # 注意: JSBSimのAERORP Xは「機首からの絶対位置」を指定する必要がある。
    # 翼弦の25%位置ではなく、機首からの距離を指定。
    #
    # 小型機の一般的な範囲: 10-15 in (質量とスケールに応じて調整)
    aerorp_x_in = 12.12  # 200g級固定翼機の典型値 (約300mm)

    aerorp = ET.SubElement(m, "location", name="AERORP", unit="IN")
    add_text(aerorp, "x", aerorp_x_in)
    add_text(aerorp, "y", 0)
    add_text(aerorp, "z", 0)

    # mass_balance (JSBSim requires SLUG*FT2, LBS, IN)
    mb = ET.SubElement(root, "mass_balance")

    # Empty weight: KG → LBS (must come BEFORE inertia in JSBSim)
    if ir["mass_balance"].get("empty_weight"):
        value = ir["mass_balance"]["empty_weight"]["value"]
        if value is not None and str(value).strip():
            try:
                empty_weight_kg = float(value)
                empty_weight_lbs = empty_weight_kg * KG_TO_LBS
                add_text(mb, "emptywt", empty_weight_lbs, unit="LBS")
            except (ValueError, TypeError) as e:
                print(f"Warning: Invalid empty_weight '{value}': {e}")

    # Inertia: KG*M2 → SLUG*FT2
    # NOTE: JSBSim requires ixx/iyy/izz as DIRECT children of mass_balance (NOT wrapped in <inertia>)
    if ir["mass_balance"]["I"].get("ixx"):
        value = ir["mass_balance"]["I"]["ixx"]["value"]
        if value is not None and str(value).strip():
            try:
                ixx_kgm2 = float(value)
                ixx_slugft2 = ixx_kgm2 * KGM2_TO_SLUGFT2
                add_text(mb, "ixx", ixx_slugft2, unit="SLUG*FT2")
            except (ValueError, TypeError) as e:
                print(f"Warning: Invalid ixx '{value}': {e}")

    if ir["mass_balance"]["I"].get("iyy"):
        value = ir["mass_balance"]["I"]["iyy"]["value"]
        if value is not None and str(value).strip():
            try:
                iyy_kgm2 = float(value)
                iyy_slugft2 = iyy_kgm2 * KGM2_TO_SLUGFT2
                add_text(mb, "iyy", iyy_slugft2, unit="SLUG*FT2")
            except (ValueError, TypeError) as e:
                print(f"Warning: Invalid iyy '{value}': {e}")

    if ir["mass_balance"]["I"].get("izz"):
        value = ir["mass_balance"]["I"]["izz"]["value"]
        if value is not None and str(value).strip():
            try:
                izz_kgm2 = float(value)
                izz_slugft2 = izz_kgm2 * KGM2_TO_SLUGFT2
                add_text(mb, "izz", izz_slugft2, unit="SLUG*FT2")
            except (ValueError, TypeError) as e:
                print(f"Warning: Invalid izz '{value}': {e}")

    # CG location: M → IN
    loc = ET.SubElement(mb, "location", name="CG")
    if ir["mass_balance"]["CG"].get("x"):
        value = ir["mass_balance"]["CG"]["x"]["value"]
        if value is not None and str(value).strip():
            try:
                cg_x_m = float(value)
                cg_x_in = cg_x_m * M_TO_IN
                add_text(loc, "x", cg_x_in, unit="IN")
            except (ValueError, TypeError) as e:
                print(f"Warning: Invalid CG.x '{value}': {e}")

    if ir["mass_balance"]["CG"].get("y"):
        value = ir["mass_balance"]["CG"]["y"]["value"]
        if value is not None and str(value).strip():
            try:
                cg_y_m = float(value)
                cg_y_in = cg_y_m * M_TO_IN
                add_text(loc, "y", cg_y_in, unit="IN")
            except (ValueError, TypeError) as e:
                print(f"Warning: Invalid CG.y '{value}': {e}")

    if ir["mass_balance"]["CG"].get("z"):
        value = ir["mass_balance"]["CG"]["z"]["value"]
        if value is not None and str(value).strip():
            try:
                cg_z_m = float(value)
                cg_z_in = cg_z_m * M_TO_IN
                add_text(loc, "z", cg_z_in, unit="IN")
            except (ValueError, TypeError) as e:
                print(f"Warning: Invalid CG.z '{value}': {e}")

    # ground_reactions (NEW for Phase 2)
    # Always create ground_reactions element (required by JSBSim)
    gr = ET.SubElement(root, "ground_reactions")
    if ir.get("ground_reactions") and len(ir["ground_reactions"]) > 0:
        for contact in ir["ground_reactions"]:
            if contact.get("type") and contact["type"].get("value"):
                cont = ET.SubElement(gr, "contact", type=safe_value(contact["type"]["value"]), name=safe_value(contact["name"]["value"] if contact.get("name") else "CONTACT"))

                # Ground contact location: M → IN
                if contact.get("location"):
                    loc_x_m = 0.0
                    loc_y_m = 0.0
                    loc_z_m = 0.0

                    if contact["location"].get("x"):
                        value = contact["location"]["x"]["value"]
                        if value is not None and str(value).strip():
                            try:
                                loc_x_m = float(value)
                            except (ValueError, TypeError) as e:
                                print(f"Warning: Invalid ground_reactions.location.x '{value}': {e}")

                    if contact["location"].get("y"):
                        value = contact["location"]["y"]["value"]
                        if value is not None and str(value).strip():
                            try:
                                loc_y_m = float(value)
                            except (ValueError, TypeError) as e:
                                print(f"Warning: Invalid ground_reactions.location.y '{value}': {e}")

                    if contact["location"].get("z"):
                        value = contact["location"]["z"]["value"]
                        if value is not None and str(value).strip():
                            try:
                                loc_z_m = float(value)
                            except (ValueError, TypeError) as e:
                                print(f"Warning: Invalid ground_reactions.location.z '{value}': {e}")

                    loc_x_in = loc_x_m * M_TO_IN
                    loc_y_in = loc_y_m * M_TO_IN
                    loc_z_in = loc_z_m * M_TO_IN
                    add_text(cont, "location", f"{loc_x_in} {loc_y_in} {loc_z_in}", unit="IN")

                # spring/damper properties
                if contact.get("k_spring") and contact["k_spring"].get("value"):
                    add_text(cont, "spring_coeff", contact["k_spring"]["value"], unit=contact["k_spring"].get("unit"))
                if contact.get("c_damper") and contact["c_damper"].get("value"):
                    add_text(cont, "damping_coeff", contact["c_damper"]["value"], unit=contact["c_damper"].get("unit"))

                # friction
                if contact.get("mu_static") and contact["mu_static"].get("value"):
                    add_text(cont, "static_friction", contact["mu_static"]["value"])
                if contact.get("mu_kinetic") and contact["mu_kinetic"].get("value"):
                    add_text(cont, "dynamic_friction", contact["mu_kinetic"]["value"])

    # propulsion
    # Check if engine/thruster data is empty (v3_calculated template has no propulsion data)
    has_engine_data = False
    if ir["propulsion"].get("engine"):
        eng_file = ir["propulsion"]["engine"].get("file")
        eng_type = ir["propulsion"]["engine"].get("type")
        if eng_file and eng_file.get("value") and str(eng_file["value"]).strip():
            has_engine_data = True
        if eng_type and eng_type.get("value") and str(eng_type["value"]).strip():
            has_engine_data = True

    prop = ET.SubElement(root, "propulsion")

    if has_engine_data:
        # Traditional engine/thruster approach (for templates with propulsion data)
        eng_name = safe_value(ir["propulsion"]["engine"]["name"]["value"] if ir["propulsion"]["engine"].get("name") else "E1", "E1")
        eng = ET.SubElement(prop, "engine", name=eng_name)
        if ir["propulsion"]["engine"].get("file"):
            f = ET.SubElement(eng, "file")
            f.text = safe_value(ir["propulsion"]["engine"]["file"]["value"])
        if ir["propulsion"]["engine"].get("type"):
            add_text(eng, "type", ir["propulsion"]["engine"]["type"]["value"])
        if ir["propulsion"].get("thruster"):
            thr_name = safe_value(ir["propulsion"]["thruster"]["name"]["value"] if ir["propulsion"]["thruster"].get("name") else "Prop1", "Prop1")
            thr_type = safe_value(ir["propulsion"]["thruster"]["type"]["value"] if ir["propulsion"]["thruster"].get("type") else "propeller", "propeller")
            thr = ET.SubElement(prop, "thruster", name=thr_name, type=thr_type)

            # Thruster location: M → IN
            tx_m = 0.0
            ty_m = 0.0
            tz_m = 0.0

            if ir['propulsion']['thruster'].get('x'):
                value = ir['propulsion']['thruster']['x']['value']
                if value is not None and str(value).strip():
                    try:
                        tx_m = float(value)
                    except (ValueError, TypeError) as e:
                        print(f"Warning: Invalid propulsion.thruster.x '{value}': {e}")

            if ir['propulsion']['thruster'].get('y'):
                value = ir['propulsion']['thruster']['y']['value']
                if value is not None and str(value).strip():
                    try:
                        ty_m = float(value)
                    except (ValueError, TypeError) as e:
                        print(f"Warning: Invalid propulsion.thruster.y '{value}': {e}")

            if ir['propulsion']['thruster'].get('z'):
                value = ir['propulsion']['thruster']['z']['value']
                if value is not None and str(value).strip():
                    try:
                        tz_m = float(value)
                    except (ValueError, TypeError) as e:
                        print(f"Warning: Invalid propulsion.thruster.z '{value}': {e}")

            tx_in = tx_m * M_TO_IN
            ty_in = ty_m * M_TO_IN
            tz_in = tz_m * M_TO_IN
            add_text(thr, "location", f"{tx_in} {ty_in} {tz_in}", unit="IN")
    else:
        # Minimal FUEL tank approach (for v3_calculated and templates without propulsion data)
        # This allows JSBSim to load the model without engine/thruster errors
        # Note: All thrust must come from External Reactions (defined separately)
        prop.append(ET.Comment("""
    No engine/propeller - all thrust from External Reactions below.
    IMPORTANT: JSBSim built-in trim (FGTrim) does NOT work with this configuration.
    SOLUTION: Use manual trim search (scipy.optimize)
  """))

        # Use AERORP location for fuel tank (co-located with aerodynamic center)
        fuel_x_in = aerorp_x_in  # Already calculated above (line 500)

        tank = ET.SubElement(prop, "tank", type="FUEL")
        tank_loc = ET.SubElement(tank, "location", unit="IN")
        add_text(tank_loc, "x", fuel_x_in)
        add_text(tank_loc, "y", 0.0)
        add_text(tank_loc, "z", 0.0)
        add_text(tank, "capacity", 0.1, unit="LBS")
        add_text(tank, "contents", 0.1, unit="LBS")

    # external_reactions (NEW for v3_calculated: External Reactions推力モデル)
    # Minimal FUEL tank approach使用時のみ生成（v3_calculated テンプレート等）
    if not has_engine_data:
        generate_external_reactions(root, aerorp_x_in)

    # flight_control (FCS) - REQUIRED by JSBSim even with External Reactions
    # Based on par_to_jsbsim_converter successful implementation
    model_name = safe_value(ir["fileheader"].get("name", "MyAircraft"), "MyAircraft")
    generate_flight_control(root, aircraft_name=model_name)

    # aerodynamics (NEW for Phase 3 Phase B)
    generate_aerodynamics(root, ir)

    # output (add required attributes for JSBSim)
    out = ET.SubElement(root, "output", name="dataout", type="CSV")
    if ir["output"].get("file"):
        add_text(out, "file", ir["output"]["file"]["value"])
    else:
        add_text(out, "file", "output.csv")
    if ir["output"].get("rate_hz"):
        add_text(out, "rate", ir["output"]["rate_hz"]["value"])
    else:
        add_text(out, "rate", "10")
    if ir["output"].get("properties"):
        props = ir["output"]["properties"]["value"]
        if isinstance(props, str):
            for p in [s.strip() for s in props.split(";") if s.strip()]:
                add_text(out, "property", p)

    # NEW: Create JSBSim-compatible directory structure
    # JSBSim expects: aircraft_path/model_name/model_name.xml
    model_name = safe_value(ir["fileheader"].get("name", "MyAircraft"), "MyAircraft")

    # Determine parent directory from out_xml path
    parent_dir = out_xml.parent
    model_dir = parent_dir / model_name
    model_dir.mkdir(parents=True, exist_ok=True)

    # Create XML file in correct location
    model_xml = model_dir / f"{model_name}.xml"

    # Format XML tree with proper indentation
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ", level=0)

    # Write XML with JSBSim official declarations
    # Reference: JSBSim sample aircraft XMLs (https://github.com/JSBSim-Team/jsbsim/tree/master/aircraft)
    with open(model_xml, 'w', encoding='utf-8') as f:
        # XML declaration
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        # XSL stylesheet processing instruction (for browser rendering)
        # Reference: http://jsbsim.sourceforge.net/JSBSim.xsl
        f.write('<?xml-stylesheet type="text/xsl" href="http://jsbsim.sourceforge.net/JSBSim.xsl"?>\n')
        # Write the XML tree (without duplicate XML declaration)
        tree.write(f, encoding='unicode', xml_declaration=False)

    return model_xml  # Return actual path for reporting

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-i","--input", required=True, help="Excel template path (.xlsx)")
    ap.add_argument("-o","--outdir", required=True, help="Output directory")
    args = ap.parse_args()
    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)

    # Build intermediate representation
    ir = build_ir(args.input)

    # Save JSON IR
    ir_json_path = outdir / "model_ir.json"
    ir_json_path.write_text(json.dumps(ir, indent=2, ensure_ascii=False), encoding="utf-8")

    # Generate XML (with new directory structure)
    # Note: out_xml is a dummy path - parent directory is used
    xml_path = emit_xml(ir, outdir / "dummy.xml")

    # Report results
    print(f"[OK] Wrote IR: {ir_json_path}")
    print(f"[OK] Wrote XML: {xml_path}")
    print()

    # Print JSBSim loading instructions
    model_name = safe_value(ir["fileheader"].get("name", "MyAircraft"), "MyAircraft")
    print("JSBSim loading test:")
    print(f"  import jsbsim, os")
    print(f"  fdm = jsbsim.FGFDMExec(None)")
    print(f"  fdm.set_aircraft_path(os.path.abspath('{outdir}'))")
    print(f"  result = fdm.load_model('{model_name}')")

if __name__ == "__main__":
    main()
