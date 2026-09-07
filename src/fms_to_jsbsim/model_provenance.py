"""Owner-local provenance helpers for FMS-to-JSBSim generated models."""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict


def sha256_file(path: str) -> str:
    """Return the SHA-256 digest for one file without loading it all at once."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_identity(path: str) -> Dict[str, str]:
    """Return a portable name plus content identity for a pipeline file."""
    file_path = Path(path)
    return {
        "name": file_path.name,
        "sha256": sha256_file(str(file_path)),
    }


def configured_assumption_snapshot(config: Dict[str, Any]) -> Dict[str, Any]:
    """Capture selected current FMS aerodynamic config values without asserting authority."""
    return {
        "horizontal_eta": config["tail_efficiency"]["horizontal_eta"],
        "vertical_eta_v": config["tail_efficiency"]["vertical_eta_v"],
        "deps_dalpha": config["downwash"]["deps_dalpha"],
        "elevator_tau": config["control_surfaces"]["elevator_tau"],
        "oswald_efficiency": config["induced_drag"]["oswald_efficiency"],
    }


def build_model_provenance(
    par_file: str,
    config_file: str,
    parsed_json: str,
    derived_json: str,
    xml_file: str,
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """Build a local provenance manifest for one completed conversion run."""
    return {
        "format": "fms_to_jsbsim_model_provenance",
        "format_version": 1,
        "source_input": file_identity(par_file),
        "aerodynamic_assumptions": {
            "file": file_identity(config_file),
            "configured_values": configured_assumption_snapshot(config),
            "evidence_note": (
                "Selected configured values available to the conversion are recorded for traceability. "
                "This manifest does not assert that every recorded value affects every generated result, "
                "or that any value is aircraft-specific or source-validated."
            ),
        },
        "pipeline_artifacts": {
            "parsed_data": file_identity(parsed_json),
            "derived_parameters": file_identity(derived_json),
            "generated_xml": file_identity(xml_file),
        },
    }


def write_model_provenance(manifest: Dict[str, Any], output_path: str) -> None:
    """Write stable UTF-8 JSON without timestamps or machine-specific absolute paths."""
    with Path(output_path).open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(manifest, stream, indent=2, sort_keys=True, ensure_ascii=False)
        stream.write("\n")
