from __future__ import annotations

import csv
from datetime import datetime, timezone
import json
from pathlib import Path

from .config import JobConfig, build_default_config
from .records import (
    CANDIDATE_FIELDS,
    build_note_filename,
    dedupe_candidates,
    flatten_for_csv,
    iter_data_files,
    load_records,
    load_zotero_snapshot,
    match_zotero,
    normalize_cnki,
    normalize_gs,
    parse_count,
    score_candidate,
)


STAGES = [
    "INIT",
    "PROMPTS_READY",
    "NORMALIZED",
    "ZOTERO_SYNCED",
    "SELECTED",
    "MATERIALIZED",
    "QC_DONE",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class Workflow:
    def __init__(self, job_dir: Path):
        self.job_dir = job_dir.resolve()
        self.config_path = self.job_dir / "config.toml"
        self.state_path = self.job_dir / "state.json"
        self.paths = {
            "raw_gs": self.job_dir / "raw" / "gs",
            "raw_cnki": self.job_dir / "raw" / "cnki",
            "normalized": self.job_dir / "normalized",
            "zotero": self.job_dir / "zotero",
            "notes": self.job_dir / "notes",
            "outputs": self.job_dir / "outputs",
            "prompts": self.job_dir / "prompts",
        }

    def ensure_layout(self) -> None:
        self.job_dir.mkdir(parents=True, exist_ok=True)
        for path in self.paths.values():
            path.mkdir(parents=True, exist_ok=True)

    def init_job(self, topic: str = "", collection_root: str = "", force: bool = False) -> None:
        self.ensure_layout()
        if self.config_path.exists() and not force:
            raise FileExistsError(f"Config already exists: {self.config_path}")
        self.config_path.write_text(
            build_default_config(self.job_dir.name, topic=topic, collection_root=collection_root),
            encoding="utf-8",
        )
        self.write_state(
            {
                "job_name": self.job_dir.name,
                "created_at": now_iso(),
                "updated_at": now_iso(),
                "current_stage": "INIT",
                "completed_stages": [],
                "artifacts": {},
            }
        )
        self.generate_prompts()

    def load_config(self) -> JobConfig:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Missing config file: {self.config_path}")
        return JobConfig.from_path(self.config_path)

    def load_state(self) -> dict[str, object]:
        if not self.state_path.exists():
            return {
                "job_name": self.job_dir.name,
                "created_at": now_iso(),
                "updated_at": now_iso(),
                "current_stage": "INIT",
                "completed_stages": [],
                "artifacts": {},
            }
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def write_state(self, state: dict[str, object]) -> None:
        state["updated_at"] = now_iso()
        self.state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    def mark_stage(self, stage: str, **artifacts: str) -> None:
        state = self.load_state()
        completed = list(state.get("completed_stages", []))
        if stage not in completed:
            completed.append(stage)
        state["completed_stages"] = completed
        state["current_stage"] = stage
        artifact_map = dict(state.get("artifacts", {}))
        artifact_map.update({key: value for key, value in artifacts.items() if value})
        state["artifacts"] = artifact_map
        self.write_state(state)

    def write_json(self, path: Path, payload: object) -> None:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def write_jsonl(self, path: Path, rows: list[dict[str, object]]) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    def load_jsonl(self, path: Path) -> list[dict[str, object]]:
        if not path.exists():
            return []
        rows: list[dict[str, object]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
        return rows

    def write_csv(self, path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)

    def generate_prompts(self) -> None:
        self.ensure_layout()
        config = self.load_config()
        search_prompt = f"""# Search Prompt

You are running the retrieval phase for the literature workflow at:
{self.job_dir}

Goal:
- Topic: {config.topic}
- Build at least {config.candidate_pool_min} candidates across Google Scholar and CNKI.
- Keep a balance of high-citation foundations and recent literature.
- Prefer sources with DOI, detail page, or full text link.

Instructions:
1. Expand the query using the configured keyword buckets below.
2. Use GS and CNKI skills to retrieve candidates in batches.
3. Save raw GS outputs to:
   - {self.paths["raw_gs"]}
4. Save raw CNKI outputs to:
   - {self.paths["raw_cnki"]}
5. Preserve the original skill fields whenever possible.
6. Do not invent papers. Every record must keep its source URL or record identifier.

Keyword buckets:
- Core: {", ".join(config.keywords.core) or "fill in config.toml"}
- Expanded: {", ".join(config.keywords.expanded) or "fill in config.toml"}
- Mechanisms: {", ".join(config.keywords.mechanisms) or "fill in config.toml"}
- Methods: {", ".join(config.keywords.methods) or "fill in config.toml"}
- Exclusions: {", ".join(config.keywords.exclusions) or "none"}
"""
        zotero_prompt = f"""# Zotero Sync Prompt

You are running the Zotero diff phase for the literature workflow at:
{self.job_dir}

Inputs:
- Normalized candidates file: {self.paths["normalized"] / "candidates.jsonl"}
- Target snapshot folder: {self.paths["zotero"]}

Instructions:
1. Use Zotero MCP to inspect the local library and selected collection targets.
2. Export a lightweight snapshot of relevant Zotero items into the Zotero folder above.
3. Keep at least: title, DOI, key/itemKey, year, creators/authors.
4. Use JSON, JSONL, or CSV.
5. After the snapshot exists, run:
   python -m litflow zotero-sync "{self.job_dir}"
"""
        self.paths["prompts"].joinpath("01-search-prompt.md").write_text(search_prompt, encoding="utf-8")
        self.paths["prompts"].joinpath("02-zotero-sync-prompt.md").write_text(zotero_prompt, encoding="utf-8")
        self.mark_stage(
            "PROMPTS_READY",
            search_prompt=str(self.paths["prompts"] / "01-search-prompt.md"),
            zotero_prompt=str(self.paths["prompts"] / "02-zotero-sync-prompt.md"),
        )

    def _score_records(self, records: list[dict[str, object]]) -> None:
        config = self.load_config()
        keyword_map = {
            "core": config.keywords.core,
            "expanded": config.keywords.expanded,
            "mechanisms": config.keywords.mechanisms,
            "methods": config.keywords.methods,
        }
        weight_map = {
            "topic_relevance": config.weights.topic_relevance,
            "citation_value": config.weights.citation_value,
            "recency_value": config.weights.recency_value,
            "novelty_to_local_library": config.weights.novelty_to_local_library,
            "fulltext_availability": config.weights.fulltext_availability,
        }
        for record in records:
            score_candidate(record, keyword_map, weight_map, config.recent_year_cutoff)

    def normalize(self) -> list[dict[str, object]]:
        self.ensure_layout()
        gs_records = [normalize_gs(item) for item in load_records(iter_data_files(self.paths["raw_gs"]))]
        cnki_records = [normalize_cnki(item) for item in load_records(iter_data_files(self.paths["raw_cnki"]))]
        merged = dedupe_candidates([*gs_records, *cnki_records])
        self._score_records(merged)

        candidates_jsonl = self.paths["normalized"] / "candidates.jsonl"
        candidates_csv = self.paths["normalized"] / "candidates.csv"
        self.write_jsonl(candidates_jsonl, merged)
        self.write_csv(candidates_csv, [flatten_for_csv(item) for item in merged], CANDIDATE_FIELDS)
        self.write_json(
            self.paths["normalized"] / "summary.json",
            {
                "candidate_count": len(merged),
                "gs_raw_files": len(iter_data_files(self.paths["raw_gs"])),
                "cnki_raw_files": len(iter_data_files(self.paths["raw_cnki"])),
            },
        )
        self.mark_stage(
            "NORMALIZED",
            candidates_jsonl=str(candidates_jsonl),
            candidates_csv=str(candidates_csv),
        )
        return merged

    def zotero_sync(self) -> list[dict[str, object]]:
        candidates = self.load_jsonl(self.paths["normalized"] / "candidates.jsonl")
        if not candidates:
            candidates = self.normalize()

        snapshot = load_zotero_snapshot(iter_data_files(self.paths["zotero"]))
        if snapshot:
            match_zotero(candidates, snapshot)
        else:
            for candidate in candidates:
                candidate["zotero_status"] = "unknown"
                candidate["in_zotero"] = ""
                candidate["zotero_item_key"] = ""

        self._score_records(candidates)

        synced_jsonl = self.paths["normalized"] / "candidates_zotero.jsonl"
        synced_csv = self.paths["normalized"] / "candidates_zotero.csv"
        self.write_jsonl(synced_jsonl, candidates)
        self.write_csv(synced_csv, [flatten_for_csv(item) for item in candidates], CANDIDATE_FIELDS)
        self.mark_stage(
            "ZOTERO_SYNCED",
            zotero_candidates_jsonl=str(synced_jsonl),
            zotero_candidates_csv=str(synced_csv),
        )
        return candidates

    def select(self) -> list[dict[str, object]]:
        candidates = self.load_jsonl(self.paths["normalized"] / "candidates_zotero.jsonl")
        if not candidates:
            candidates = self.zotero_sync()
        config = self.load_config()
        ranked = sorted(candidates, key=lambda item: float(item.get("score_total", 0.0)), reverse=True)

        recent = [
            item for item in ranked
            if str(item.get("year", "")).isdigit() and int(item["year"]) >= config.recent_year_cutoff
        ]
        classic = [
            item for item in ranked
            if str(item.get("year", "")).isdigit() and int(item["year"]) < config.recent_year_cutoff
        ]
        new_items = [item for item in ranked if item.get("zotero_status") == "missing"]

        selected: list[dict[str, object]] = []
        seen_ids: set[str] = set()

        def add_batch(items: list[dict[str, object]], limit: int, reason: str) -> None:
            for item in items:
                if len(selected) >= config.target_final_count or limit <= 0:
                    return
                candidate_id = str(item["candidate_id"])
                if candidate_id in seen_ids:
                    continue
                item["selected"] = True
                item["selection_reason"] = reason
                selected.append(item)
                seen_ids.add(candidate_id)
                limit -= 1

        add_batch(classic, config.target_classic_count, "classic-anchor")
        add_batch(recent, config.target_recent_count, "recent-priority")
        needed_new = max(
            0,
            config.target_new_to_zotero_count - sum(1 for item in selected if item.get("zotero_status") == "missing"),
        )
        add_batch(new_items, needed_new, "new-to-zotero")
        add_batch(ranked, config.target_final_count - len(selected), "best-remaining")

        for item in ranked:
            if item.get("candidate_id") not in seen_ids:
                item["selected"] = False
                item["selection_reason"] = ""

        selected_jsonl = self.paths["outputs"] / "selected.jsonl"
        selected_csv = self.paths["outputs"] / "selected.csv"
        matrix_csv = self.paths["outputs"] / "literature_matrix.csv"
        self.write_jsonl(selected_jsonl, selected)
        self.write_csv(selected_csv, [flatten_for_csv(item) for item in selected], CANDIDATE_FIELDS)

        matrix_rows = []
        for item in selected:
            matrix_rows.append(
                {
                    "candidate_id": item["candidate_id"],
                    "title": item["title"],
                    "authors": item["authors"],
                    "year": item["year"],
                    "venue": item["venue"],
                    "source": item["source"],
                    "zotero_status": item["zotero_status"],
                    "pdf_available": "true" if item.get("pdf_available") else "false",
                    "score_total": item["score_total"],
                    "research_question": "",
                    "data_sample": "",
                    "method_model": "",
                    "identification_strategy": "",
                    "core_finding": "",
                    "mechanism": "",
                    "limitation": "",
                    "relevance_to_topic": "",
                }
            )
        self.write_csv(
            matrix_csv,
            matrix_rows,
            [
                "candidate_id",
                "title",
                "authors",
                "year",
                "venue",
                "source",
                "zotero_status",
                "pdf_available",
                "score_total",
                "research_question",
                "data_sample",
                "method_model",
                "identification_strategy",
                "core_finding",
                "mechanism",
                "limitation",
                "relevance_to_topic",
            ],
        )
        self.mark_stage(
            "SELECTED",
            selected_jsonl=str(selected_jsonl),
            selected_csv=str(selected_csv),
            matrix_csv=str(matrix_csv),
        )
        return selected

    def materialize(self) -> None:
        selected = self.load_jsonl(self.paths["outputs"] / "selected.jsonl")
        if not selected:
            selected = self.select()
        config = self.load_config()

        import_queue = []
        analysis_queue = []
        for index, item in enumerate(selected, start=1):
            note_path = self.paths["notes"] / build_note_filename(index, str(item.get("title", "")))
            note_body = f"""# {item.get("title", "")}

Metadata
- Candidate ID: {item.get("candidate_id", "")}
- Authors: {item.get("authors", "")}
- Year: {item.get("year", "")}
- Venue: {item.get("venue", "")}
- Source: {item.get("source", "")}
- DOI: {item.get("doi", "")}
- Source URL: {item.get("source_url", "")}
- Full Text URL: {item.get("full_text_url", "")}
- Zotero Status: {item.get("zotero_status", "")}

Reading Mode
- {"Full text available" if item.get("pdf_available") else "Abstract or metadata only until PDF is attached"}

Structured Notes
## Research Question

## Theory Lens

## Data or Sample

## Method or Model

## Identification Strategy

## Core Findings

## Mechanism

## Limitations

## Relevance To Topic

## Verification Notes
- Do not fill unverifiable details.
- Mark any inference clearly.
"""
            note_path.write_text(note_body, encoding="utf-8")
            item["analysis_status"] = "stub-created"

            if item.get("zotero_status") == "missing":
                import_queue.append(
                    {
                        "candidate_id": item.get("candidate_id"),
                        "title": item.get("title"),
                        "source": item.get("source"),
                        "source_record_ids": item.get("source_record_ids"),
                        "source_url": item.get("source_url"),
                        "full_text_url": item.get("full_text_url"),
                        "collections": [
                            config.collections.root,
                            config.collections.selected,
                            config.collections.fulltext if item.get("pdf_available") else "",
                        ],
                        "tags": [
                            f"source:{item.get('source')}",
                            "selected",
                            "new-to-zotero",
                            "fulltext" if item.get("pdf_available") else "abstract-only",
                        ],
                    }
                )

            analysis_queue.append(
                {
                    "candidate_id": item.get("candidate_id"),
                    "title": item.get("title"),
                    "note_path": str(note_path),
                    "zotero_status": item.get("zotero_status"),
                    "source_url": item.get("source_url"),
                }
            )

        import_queue_path = self.paths["outputs"] / "zotero_import_queue.json"
        analysis_queue_path = self.paths["outputs"] / "analysis_queue.json"
        self.write_json(import_queue_path, import_queue)
        self.write_json(analysis_queue_path, analysis_queue)
        self.write_jsonl(self.paths["outputs"] / "selected.jsonl", selected)

        import_prompt = f"""# Import Prompt

You are importing selected papers into Zotero for the workflow at:
{self.job_dir}

Inputs:
- Import queue: {import_queue_path}

Instructions:
1. Create or open the collection root: {config.collections.root}
2. Use subcollections:
   - {config.collections.candidates}
   - {config.collections.selected}
   - {config.collections.fulltext}
   - {config.collections.notes}
3. Import only papers whose Zotero status is missing.
4. Preserve DOI, source links, and PDFs when available.
5. If PDF download fails, keep the metadata item and add an "abstract-only" tag.
"""
        analysis_prompt = f"""# Analysis Prompt

You are running structured literature reading for the workflow at:
{self.job_dir}

Inputs:
- Selected papers: {self.paths["outputs"] / "selected.jsonl"}
- Analysis queue: {analysis_queue_path}
- Note folder: {self.paths["notes"]}

Instructions:
1. Open each selected paper from Zotero or the stored source URL.
2. Fill the matching note file.
3. Required sections:
   - Research Question
   - Theory Lens
   - Data or Sample
   - Method or Model
   - Identification Strategy
   - Core Findings
   - Mechanism
   - Limitations
   - Relevance To Topic
4. If only abstract or metadata is available, say so explicitly and do not infer hidden details.
5. Keep wording concise and comparable across notes.
"""
        self.paths["prompts"].joinpath("03-import-prompt.md").write_text(import_prompt, encoding="utf-8")
        self.paths["prompts"].joinpath("04-analysis-prompt.md").write_text(analysis_prompt, encoding="utf-8")
        self.mark_stage(
            "MATERIALIZED",
            import_queue=str(import_queue_path),
            analysis_queue=str(analysis_queue_path),
            import_prompt=str(self.paths["prompts"] / "03-import-prompt.md"),
            analysis_prompt=str(self.paths["prompts"] / "04-analysis-prompt.md"),
        )

    def qc(self) -> dict[str, object]:
        selected = self.load_jsonl(self.paths["outputs"] / "selected.jsonl")
        if not selected:
            self.materialize()
            selected = self.load_jsonl(self.paths["outputs"] / "selected.jsonl")
        config = self.load_config()

        total = len(selected)
        recent = sum(
            1
            for item in selected
            if str(item.get("year", "")).isdigit() and int(item["year"]) >= config.recent_year_cutoff
        )
        classics = sum(
            1
            for item in selected
            if str(item.get("year", "")).isdigit() and int(item["year"]) < config.recent_year_cutoff
        )
        new_to_zotero = sum(1 for item in selected if item.get("zotero_status") == "missing")
        missing_pdf = sum(1 for item in selected if not item.get("pdf_available"))
        missing_doi = sum(1 for item in selected if not item.get("doi"))
        missing_source_url = sum(1 for item in selected if not item.get("source_url"))
        needs_review = [item for item in selected if item.get("validation_status") != "verified-source"]
        average_score = round(sum(float(item.get("score_total", 0.0)) for item in selected) / total, 2) if total else 0.0

        report = {
            "job_dir": str(self.job_dir),
            "topic": config.topic,
            "selected_count": total,
            "target_final_count": config.target_final_count,
            "recent_count": recent,
            "target_recent_count": config.target_recent_count,
            "classic_count": classics,
            "target_classic_count": config.target_classic_count,
            "new_to_zotero_count": new_to_zotero,
            "target_new_to_zotero_count": config.target_new_to_zotero_count,
            "missing_pdf_count": missing_pdf,
            "missing_doi_count": missing_doi,
            "missing_source_url_count": missing_source_url,
            "needs_review_count": len(needs_review),
            "average_score": average_score,
            "checks": {
                "selected_target_met": total >= config.target_final_count,
                "recent_target_met": recent >= config.target_recent_count,
                "classic_target_met": classics >= config.target_classic_count,
                "new_to_zotero_target_met": new_to_zotero >= config.target_new_to_zotero_count,
                "no_invalid_records": len(needs_review) == 0,
            },
        }
        report_path = self.paths["outputs"] / "qc_report.json"
        self.write_json(report_path, report)

        next_actions = []
        if total < config.target_final_count:
            next_actions.append("Retrieve more candidates before finalizing the review set.")
        if recent < config.target_recent_count:
            next_actions.append("Add more recent papers to meet the recency quota.")
        if new_to_zotero < config.target_new_to_zotero_count:
            next_actions.append("Find more papers not yet stored in Zotero.")
        if missing_pdf:
            next_actions.append("Use GS/CNKI export or Zotero to attach more PDFs.")
        if missing_source_url or missing_doi or needs_review:
            next_actions.append("Review records missing DOI or source anchors.")
        if not next_actions:
            next_actions.append("Proceed to detailed reading and synthesis.")

        markdown = [
            "# QC Report",
            "",
            f"- Topic: {config.topic}",
            f"- Selected / target: {total} / {config.target_final_count}",
            f"- Recent / target: {recent} / {config.target_recent_count}",
            f"- Classic / target: {classics} / {config.target_classic_count}",
            f"- New to Zotero / target: {new_to_zotero} / {config.target_new_to_zotero_count}",
            f"- Missing PDFs: {missing_pdf}",
            f"- Missing DOI: {missing_doi}",
            f"- Missing source URL: {missing_source_url}",
            f"- Needs review: {len(needs_review)}",
            f"- Average score: {average_score}",
            "",
            "## Next Actions",
            "",
        ]
        markdown.extend(f"- {item}" for item in next_actions)
        markdown_path = self.paths["outputs"] / "qc_report.md"
        markdown_path.write_text("\n".join(markdown) + "\n", encoding="utf-8")
        self.mark_stage(
            "QC_DONE",
            qc_json=str(report_path),
            qc_markdown=str(markdown_path),
        )
        return report

    def run(self, through: str = "qc") -> None:
        stage_order = [
            ("prompts", self.generate_prompts),
            ("normalize", self.normalize),
            ("zotero-sync", self.zotero_sync),
            ("select", self.select),
            ("materialize", self.materialize),
            ("qc", self.qc),
        ]
        valid = {name for name, _ in stage_order}
        if through not in valid:
            raise ValueError(f"Unknown stage: {through}. Expected one of {sorted(valid)}")
        for name, action in stage_order:
            action()
            if name == through:
                break
