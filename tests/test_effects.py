import copy
import json
import unittest
from pathlib import Path

from aegis.effects import EffectScenario, reconcile_effects
from aegis.io import load_effect_scenario
from aegis.receipts import verify_receipt


FIXTURE = Path(__file__).parents[1] / "examples" / "effect-provenance" / "denied-gitlab-shadow-effect.json"


class EffectReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.value = json.loads(FIXTURE.read_text())

    def reconcile(self, value=None, key=None):
        return reconcile_effects(EffectScenario.from_dict(value or self.value), key)

    def test_external_effect_after_denial_is_critical(self):
        result = reconcile_effects(load_effect_scenario(FIXTURE), "sensor-key")
        self.assertEqual(result.summary, {"denied_but_effect_observed": 1})
        self.assertEqual(result.findings[0].severity, "critical")
        self.assertTrue(verify_receipt(result.receipt, "sensor-key"))
        self.assertTrue(result.receipt.payload["all_effects_externally_verified"])

    def test_effect_without_decision_is_detected(self):
        value = copy.deepcopy(self.value)
        value["observed_effects"][0]["request_id"] = None
        result = self.reconcile(value)
        self.assertEqual(result.findings[0].classification, "effect_without_decision")

    def test_self_reported_effect_is_not_trusted(self):
        value = copy.deepcopy(self.value)
        value["observed_effects"][0]["externally_verified"] = False
        value["observed_effects"][0]["observer_origin"] = "agent_self_report"
        result = self.reconcile(value)
        self.assertEqual(result.findings[0].classification, "untrusted_effect_evidence")

    def test_approved_call_through_different_path_is_shadow_effect(self):
        value = copy.deepcopy(self.value)
        value["authority_topology"]["request"]["path_id"] = "governed-gitlab-adapter"
        value["authority_topology"]["request"]["arguments"] = {
            "title": "Suspicious lateral movement",
            "labels": ["security", "aegis", "auto-generated"],
            "caldera_profile_digest": "sha256:fixture-profile",
        }
        result = self.reconcile(value)
        self.assertEqual(result.authority.decision.decision, "allow")
        self.assertEqual(result.findings[0].classification, "effect_via_shadow_path")

    def test_exact_approved_effect_matches(self):
        value = copy.deepcopy(self.value)
        value["authority_topology"]["request"]["path_id"] = "governed-gitlab-adapter"
        effect = value["observed_effects"][0]
        effect["path_id"] = "governed-gitlab-adapter"
        effect["operation"] = "gitlab_create_incident"
        result = self.reconcile(value)
        self.assertEqual(result.findings[0].classification, "authorized_and_matched")

    def test_changed_arguments_and_duplicate_effects_fail_closed(self):
        changed = copy.deepcopy(self.value)
        changed["authority_topology"]["request"]["path_id"] = "governed-gitlab-adapter"
        changed["observed_effects"][0]["path_id"] = "governed-gitlab-adapter"
        changed["observed_effects"][0]["operation"] = "gitlab_create_incident"
        changed["observed_effects"][0]["arguments_digest"] = "sha256:different"
        self.assertEqual(self.reconcile(changed).findings[0].classification, "authorized_but_arguments_changed")

        duplicate = copy.deepcopy(changed)
        proof_digest = self.reconcile(changed).authority.decision.proof.arguments_digest
        duplicate["observed_effects"][0]["arguments_digest"] = proof_digest
        second = copy.deepcopy(duplicate["observed_effects"][0])
        second["effect_id"] = "gitlab-audit-event-9002"
        duplicate["observed_effects"].append(second)
        result = self.reconcile(duplicate)
        self.assertEqual({item.classification for item in result.findings}, {"authorized_but_duplicate"})

    def test_actor_substitution_and_state_drift_fail_closed(self):
        base = copy.deepcopy(self.value)
        base["authority_topology"]["request"]["path_id"] = "governed-gitlab-adapter"
        base["observed_effects"][0]["path_id"] = "governed-gitlab-adapter"
        base["observed_effects"][0]["operation"] = "gitlab_create_incident"

        actor_changed = copy.deepcopy(base)
        actor_changed["observed_effects"][0]["agent_id"] = "spiffe://a2z-soc/agent/unapproved-child"
        self.assertEqual(self.reconcile(actor_changed).findings[0].classification, "authorized_but_actor_changed")

        stale = copy.deepcopy(base)
        stale["observed_effects"][0]["state_precondition"] = "gitlab-project-suspended:82313809"
        self.assertEqual(self.reconcile(stale).findings[0].classification, "authorized_but_state_stale")


if __name__ == "__main__":
    unittest.main()
