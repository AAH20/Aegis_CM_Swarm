import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from aegis.compilers import compile_detection
from aegis.evidence import build_evidence_graph, evaluate_intent
from aegis.io import load_events, load_intent
from aegis.models import SecurityEvent, Verdict
from aegis.receipts import verify_receipt
from aegis.remediation import DependencyGraph
from aegis.runtime import AegisRuntime


FIXTURE_ROOT = Path(__file__).parents[1] / "examples" / "identity-intrusion"


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.intent = load_intent(FIXTURE_ROOT / "intent.json")
        self.events = load_events(FIXTURE_ROOT / "events.json")
        self.dependencies = DependencyGraph.from_dict(json.loads((FIXTURE_ROOT / "dependencies.json").read_text()))

    def test_complete_chain_is_malicious(self):
        finding = evaluate_intent(self.intent, build_evidence_graph(self.events))
        self.assertEqual(finding.verdict, Verdict.MALICIOUS)
        self.assertEqual(finding.confidence, 1.0)

    def test_missing_chain_abstains(self):
        finding = evaluate_intent(self.intent, build_evidence_graph(self.events[:2]))
        self.assertEqual(finding.verdict, Verdict.INSUFFICIENT_EVIDENCE)
        self.assertIn("lateral_movement", finding.missing_evidence)

    def test_unrelated_entities_do_not_form_attack_chain(self):
        unrelated = [
            replace(event, actor=f"actor-{index}", target=f"target-{index}")
            for index, event in enumerate(self.events)
        ]
        finding = evaluate_intent(self.intent, build_evidence_graph(unrelated))
        self.assertEqual(finding.verdict, Verdict.INSUFFICIENT_EVIDENCE)
        self.assertLess(finding.confidence, self.intent.min_confidence)

    def test_sequence_outside_window_does_not_match(self):
        delayed = [*self.events[:-1], replace(self.events[-1], timestamp="2026-08-16T10:14:00Z")]
        finding = evaluate_intent(self.intent, build_evidence_graph(delayed))
        self.assertEqual(finding.verdict, Verdict.INSUFFICIENT_EVIDENCE)
        self.assertTrue(any("outside" in item for item in finding.missing_evidence))

    def test_benign_context_prevents_malicious_verdict(self):
        value = self.events[0].to_dict()
        value["attributes"]["known_benign"] = True
        events = [SecurityEvent.from_dict(value), *self.events[1:]]
        finding = evaluate_intent(self.intent, build_evidence_graph(events))
        self.assertEqual(finding.verdict, Verdict.SUSPICIOUS)

    def test_compilers_preserve_semantics(self):
        outputs = [compile_detection(self.intent, backend) for backend in ("splunk", "kql", "esql", "sigma")]
        self.assertTrue(all(output.semantic_fingerprint == self.intent.sequence for output in outputs))

    def test_dependency_blocks_high_risk_action(self):
        result = AegisRuntime().run(self.intent, self.events, self.dependencies, ("splunk",), "build-runner-01", "test-key")
        statuses = {action.operation: action.status for action in result.remediation_plan}
        self.assertEqual(statuses["preserve_evidence"], "requires_human_approval")
        self.assertEqual(statuses["disable_principal"], "blocked_pending_continuity_plan")
        self.assertEqual(statuses["isolate_workload"], "blocked_pending_continuity_plan")
        self.assertTrue(verify_receipt(result.receipt, "test-key"))
        self.assertEqual(result.receipt.payload["production_actions_executed"], 0)

    def test_output_is_serializable(self):
        result = AegisRuntime().run(self.intent, self.events, self.dependencies, ("splunk", "sigma"), "build-runner-01")
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "result.json"
            destination.write_text(json.dumps(result.to_dict()))
            self.assertEqual(json.loads(destination.read_text())["finding"]["verdict"], "malicious")


if __name__ == "__main__":
    unittest.main()
