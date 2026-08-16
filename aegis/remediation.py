from __future__ import annotations

from dataclasses import dataclass

from .models import ActionRisk, DetectionIntent, Finding, RemediationAction, Verdict


@dataclass(frozen=True)
class DependencyGraph:
    dependencies: dict[str, tuple[str, ...]]
    critical_services: tuple[str, ...]

    @classmethod
    def from_dict(cls, value: dict) -> "DependencyGraph":
        return cls(
            dependencies={key: tuple(items) for key, items in value.get("dependencies", {}).items()},
            critical_services=tuple(value.get("critical_services", ())),
        )

    def impacted_services(self, target: str) -> tuple[str, ...]:
        impacted = {target}
        changed = True
        while changed:
            changed = False
            for service, requirements in self.dependencies.items():
                if service not in impacted and impacted.intersection(requirements):
                    impacted.add(service)
                    changed = True
        return tuple(sorted(impacted.intersection(self.critical_services)))


ACTION_CATALOG = {
    "revoke_session": ("identity", "revoke_session", ActionRisk.LOW, True, "restore_session_by_reauthentication"),
    "disable_principal": ("identity", "disable_principal", ActionRisk.HIGH, True, "enable_principal"),
    "isolate_workload": ("network", "isolate_workload", ActionRisk.HIGH, True, "remove_isolation_policy"),
    "preserve_evidence": ("forensics", "preserve_evidence", ActionRisk.LOW, True, "expire_evidence_snapshot"),
}


def plan_remediation(
    intent: DetectionIntent,
    finding: Finding,
    dependency_graph: DependencyGraph,
    target: str,
) -> tuple[RemediationAction, ...]:
    if finding.verdict not in {Verdict.MALICIOUS, Verdict.SUSPICIOUS}:
        return ()

    actions: list[RemediationAction] = []
    impacted = dependency_graph.impacted_services(target)
    for index, action_name in enumerate(intent.remediation_actions, start=1):
        if action_name not in ACTION_CATALOG:
            continue
        adapter, operation, risk, reversible, rollback = ACTION_CATALOG[action_name]
        blocked_reason = None
        status = "requires_human_approval"
        if not reversible:
            blocked_reason = "irreversible actions are prohibited"
            status = "blocked"
        elif impacted and risk in {ActionRisk.HIGH, ActionRisk.IRREVERSIBLE}:
            blocked_reason = f"critical service dependency: {', '.join(impacted)}"
            status = "blocked_pending_continuity_plan"
        actions.append(
            RemediationAction(
                action_id=f"action-{index}",
                adapter=adapter,
                operation=operation,
                target=target,
                risk=risk,
                reversible=reversible,
                preconditions=("human_approval", "fresh_evidence", "rollback_available"),
                rollback=rollback,
                status=status,
                blocked_reason=blocked_reason,
            )
        )
    return tuple(actions)
