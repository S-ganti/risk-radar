import importlib.util
import unittest
from pathlib import Path


SPEC = importlib.util.spec_from_file_location("risk_validate", Path(__file__).parents[1] / "scripts" / "validate.py")
risk_validate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(risk_validate)


class ValidationGateTests(unittest.TestCase):
    def test_current_repository_passes_without_publication_errors(self):
        gate, health = risk_validate.validate_all()
        self.assertEqual([], gate.errors)
        self.assertIn(health["overall"], {"healthy", "degraded"})

    def test_every_model_has_required_governance_fields(self):
        registry = risk_validate.read_json(risk_validate.DATA / "model-registry.json")
        required = {"id", "version", "status", "decision_ready", "outputs", "metrics_required", "limitations"}
        for model in registry["models"]:
            self.assertTrue(required.issubset(model), model.get("id"))

    def test_evidence_urls_are_https(self):
        registry = risk_validate.read_json(risk_validate.DATA / "evidence-registry.json")
        for evidence in registry["evidence"]:
            self.assertTrue(evidence["source_url"].startswith("https://"), evidence["id"])

    def test_invalid_candidate_is_blocked_in_memory(self):
        history = risk_validate.read_json(risk_validate.DATA / "history.json")
        gate, health = risk_validate.validate_all(
            latest_override={"generated": "2026-08-30T00:00:00+00:00", "spot": {}, "vols": {}, "corr": {}},
            history_override=history,
        )
        self.assertGreater(len(gate.errors), 0)
        self.assertEqual("blocked", health["overall"])


if __name__ == "__main__":
    unittest.main()
