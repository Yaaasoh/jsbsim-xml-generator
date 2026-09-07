import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "fms_to_jsbsim"))

from model_provenance import build_model_provenance, write_model_provenance  # noqa: E402


class ModelProvenanceTest(unittest.TestCase):
    def test_manifest_links_inputs_assumptions_and_generated_model(self):
        config = {
            "tail_efficiency": {"horizontal_eta": 0.95, "vertical_eta_v": 0.95},
            "downwash": {"deps_dalpha": 0.4},
            "control_surfaces": {"elevator_tau": 0.35},
            "induced_drag": {"oswald_efficiency": 0.85},
        }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            files = {
                "par": root / "aircraft.par",
                "config": root / "aerodynamic_assumptions.yaml",
                "parsed": root / "parsed_data.json",
                "derived": root / "derived_parameters.json",
                "xml": root / "Aircraft.xml",
            }
            contents = {
                "par": b"PAR\n",
                "config": b"CONFIG\n",
                "parsed": b"{}\n",
                "derived": b'{"stability_derivatives": {}}\n',
                "xml": b"<fdm_config/>\n",
            }
            for key, path in files.items():
                path.write_bytes(contents[key])

            manifest = build_model_provenance(
                str(files["par"]),
                str(files["config"]),
                str(files["parsed"]),
                str(files["derived"]),
                str(files["xml"]),
                config,
            )

            self.assertEqual(manifest["source_input"]["name"], "aircraft.par")
            self.assertEqual(len(manifest["source_input"]["sha256"]), 64)
            self.assertEqual(
                manifest["aerodynamic_assumptions"]["configured_values"]["deps_dalpha"],
                0.4,
            )
            self.assertEqual(
                manifest["pipeline_artifacts"]["generated_xml"]["name"],
                "Aircraft.xml",
            )

            first = root / "MODEL_PROVENANCE.json"
            second = root / "MODEL_PROVENANCE_COPY.json"
            write_model_provenance(manifest, str(first))
            write_model_provenance(manifest, str(second))
            self.assertEqual(first.read_bytes(), second.read_bytes())
            loaded = json.loads(first.read_text(encoding="utf-8"))
            self.assertEqual(loaded, manifest)
            self.assertNotIn(str(root), first.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
