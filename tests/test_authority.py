import json
import tempfile
import unittest
from pathlib import Path

from aegis.authority import AuthorityTopology, analyze_authority
from aegis.io import load_authority_topology
from aegis.receipts import verify_receipt


FIXTURE = Path(__file__).parents[1] / "examples" / "authority-mesh" / "gitlab-shadow-path.json"


class AuthorityMeshTests(unittest.TestCase):
    def setUp(self):
        self.topology = load_authority_topology(FIXTURE)

    def test_detects_equivalent_effect_bypass_and_standing_authority(self):
        result = analyze_authority(self.topology, "test-key")
        finding_types = {finding.finding_type for finding in result.findings}
        self.assertIn("equivalent_effect_bypass", finding_types)
        self.assertIn("standing_privileged_authority", finding_types)
        self.assertEqual(result.coverage["gitlab://project/82313809/issues::create"], 0.5)
        self.assertTrue(verify_receipt(result.receipt, "test-key"))

    def test_denies_swarm2_direct_api_path(self):
        result = analyze_authority(self.topology)
        self.assertEqual(result.decision.decision, "deny")
        self.assertIn("no authoritative enforcement point", result.decision.reason)
        self.assertEqual(result.decision.proof.policy_generation, "7")
        self.assertTrue(result.decision.proof.arguments_digest.startswith("sha256:"))
        self.assertEqual(result.receipt.payload["production_actions_executed"], 0)

    def test_allows_protected_ephemeral_approved_path(self):
        value = json.loads(FIXTURE.read_text())
        value["request"]["path_id"] = "governed-gitlab-adapter"
        topology = AuthorityTopology.from_dict(value)
        result = analyze_authority(topology)
        self.assertEqual(result.decision.decision, "allow")

    def test_missing_approval_fails_closed(self):
        value = json.loads(FIXTURE.read_text())
        value["request"]["path_id"] = "governed-gitlab-adapter"
        value["request"]["approved"] = False
        result = analyze_authority(AuthorityTopology.from_dict(value))
        self.assertEqual(result.decision.decision, "deny")
        self.assertIn("approval is absent", result.decision.reason)

    def test_output_is_serializable(self):
        rendered = analyze_authority(self.topology).to_dict()
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "authority.json"
            destination.write_text(json.dumps(rendered))
            self.assertEqual(json.loads(destination.read_text())["decision"]["decision"], "deny")


if __name__ == "__main__":
    unittest.main()
