from __future__ import annotations

import argparse
from pathlib import Path

from .workflow import Workflow


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Literature workflow helper.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create a new workflow job directory.")
    init_parser.add_argument("job_dir", type=Path)
    init_parser.add_argument("--topic", default="")
    init_parser.add_argument("--collection-root", default="")
    init_parser.add_argument("--force", action="store_true")

    prompt_parser = subparsers.add_parser("prompts", help="Regenerate workflow prompt files.")
    prompt_parser.add_argument("job_dir", type=Path)

    normalize_parser = subparsers.add_parser("normalize", help="Normalize raw GS/CNKI records.")
    normalize_parser.add_argument("job_dir", type=Path)

    zotero_parser = subparsers.add_parser("zotero-sync", help="Match candidates against Zotero snapshots.")
    zotero_parser.add_argument("job_dir", type=Path)

    select_parser = subparsers.add_parser("select", help="Select the final paper set.")
    select_parser.add_argument("job_dir", type=Path)

    materialize_parser = subparsers.add_parser("materialize", help="Create queues, prompts, and note stubs.")
    materialize_parser.add_argument("job_dir", type=Path)

    qc_parser = subparsers.add_parser("qc", help="Generate QC reports.")
    qc_parser.add_argument("job_dir", type=Path)

    run_parser = subparsers.add_parser("run", help="Run the pipeline through a chosen stage.")
    run_parser.add_argument("job_dir", type=Path)
    run_parser.add_argument(
        "--through",
        default="qc",
        choices=["prompts", "normalize", "zotero-sync", "select", "materialize", "qc"],
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    workflow = Workflow(args.job_dir)

    if args.command == "init":
        workflow.init_job(topic=args.topic, collection_root=args.collection_root, force=args.force)
    elif args.command == "prompts":
        workflow.generate_prompts()
    elif args.command == "normalize":
        workflow.normalize()
    elif args.command == "zotero-sync":
        workflow.zotero_sync()
    elif args.command == "select":
        workflow.select()
    elif args.command == "materialize":
        workflow.materialize()
    elif args.command == "qc":
        workflow.qc()
    elif args.command == "run":
        workflow.run(through=args.through)
    else:
        parser.error(f"Unsupported command: {args.command}")

    return 0
