from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .authority import analyze_authority
from .effects import reconcile_effects
from .io import load_authority_topology, load_effect_scenario, load_events, load_intent, load_json
from .remediation import DependencyGraph
from .runtime import AegisRuntime


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Aegis governed detection and remediation compiler")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run", help="evaluate evidence and produce portable detections")
    run.add_argument("--intent", required=True)
    run.add_argument("--events", required=True)
    run.add_argument("--dependencies", required=True)
    run.add_argument("--backends", default="splunk,kql,esql,sigma")
    run.add_argument("--target", required=True)
    run.add_argument("--output")
    authority = subparsers.add_parser("authority", help="analyze privileged action paths and bind a decision proof")
    authority.add_argument("--topology", required=True)
    authority.add_argument("--output")
    effects = subparsers.add_parser("effects", help="reconcile external effects with authority decisions")
    effects.add_argument("--scenario", required=True)
    effects.add_argument("--output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "run":
        result = AegisRuntime().run(
            intent=load_intent(args.intent),
            events=load_events(args.events),
            dependencies=DependencyGraph.from_dict(load_json(args.dependencies)),
            backends=tuple(item.strip() for item in args.backends.split(",") if item.strip()),
            target=args.target,
            signing_key=os.getenv("AEGIS_RECEIPT_KEY"),
        )
        rendered = json.dumps(result.to_dict(), indent=2, sort_keys=True)
        if args.output:
            Path(args.output).write_text(rendered + "\n", encoding="utf-8")
        else:
            print(rendered)
        return 0
    if args.command == "effects":
        result = reconcile_effects(
            load_effect_scenario(args.scenario),
            signing_key=os.getenv("AEGIS_RECEIPT_KEY"),
        )
        rendered = json.dumps(result.to_dict(), indent=2, sort_keys=True)
        if args.output:
            Path(args.output).write_text(rendered + "\n", encoding="utf-8")
        else:
            print(rendered)
        return 0
    if args.command == "authority":
        result = analyze_authority(
            load_authority_topology(args.topology),
            signing_key=os.getenv("AEGIS_RECEIPT_KEY"),
        )
        rendered = json.dumps(result.to_dict(), indent=2, sort_keys=True)
        if args.output:
            Path(args.output).write_text(rendered + "\n", encoding="utf-8")
        else:
            print(rendered)
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
