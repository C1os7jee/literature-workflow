from __future__ import annotations

from collections.abc import Iterable
import csv
import json
import math
from pathlib import Path
import re


CANDIDATE_FIELDS = [
    "candidate_id",
    "title",
    "title_normalized",
    "authors",
    "first_author",
    "year",
    "venue",
    "abstract",
    "keywords",
    "doi",
    "doi_normalized",
    "source_url",
    "full_text_url",
    "source",
    "source_record_ids",
    "source_queries",
    "source_files",
    "source_count",
    "citation_count",
    "download_count",
    "pdf_available",
    "validation_status",
    "validation_notes",
    "zotero_status",
    "zotero_item_key",
    "in_zotero",
    "score_relevance",
    "score_citation",
    "score_recency",
    "score_novelty",
    "score_fulltext",
    "score_total",
    "selected",
    "selection_reason",
    "analysis_status",
]


def slugify(value: str, limit: int = 48) -> str:
    base = re.sub(r"[^0-9A-Za-z]+", "-", value).strip("-").lower()
    if not base:
        base = "paper"
    return base[:limit].rstrip("-")


def normalize_text(value: str) -> str:
    return re.sub(r"[\W_]+", "", value.lower(), flags=re.UNICODE)


def normalize_doi(value: str) -> str:
    value = (value or "").strip().lower()
    value = value.replace("https://doi.org/", "").replace("http://doi.org/", "")
    value = value.replace("doi:", "").strip()
    return value


def extract_year(*parts: str) -> int | None:
    for part in parts:
        if not part:
            continue
        match = re.search(r"(19|20)\d{2}", str(part))
        if match:
            return int(match.group(0))
    return None


def parse_count(value: str | int | None) -> int:
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    digits = re.findall(r"\d[\d,]*", str(value))
    if not digits:
        return 0
    return int(digits[0].replace(",", ""))


def maybe_list_to_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "; ".join(str(item).strip() for item in value if str(item).strip())
    return str(value).strip()


def derive_validation_status(record: dict[str, object]) -> tuple[str, str]:
    has_title = bool(record.get("title"))
    has_source = bool(record.get("source_url"))
    has_anchor = bool(record.get("doi") or record.get("full_text_url") or record.get("source_url"))
    if has_title and has_source and has_anchor:
        return "verified-source", ""
    notes = []
    if not has_title:
        notes.append("missing title")
    if not has_source:
        notes.append("missing source url")
    if not has_anchor:
        notes.append("missing doi/full text/source anchor")
    return "needs-review", ", ".join(notes)


def flatten_payload(payload: object, source_name: str = "") -> list[dict[str, object]]:
    if isinstance(payload, list):
        return [dict(item) for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        shared = {k: v for k, v in payload.items() if k != "results"}
        results = payload.get("results")
        if isinstance(results, list):
            flattened: list[dict[str, object]] = []
            for result in results:
                if not isinstance(result, dict):
                    continue
                item = dict(result)
                if "query" not in item and "query" in shared:
                    item["query"] = shared["query"]
                if "currentUrl" not in item and "currentUrl" in shared:
                    item["currentUrl"] = shared["currentUrl"]
                item.setdefault("_source_name", source_name)
                flattened.append(item)
            return flattened
        wrapped = dict(payload)
        wrapped.setdefault("_source_name", source_name)
        return [wrapped]
    return []


def _load_json_payload(path: Path) -> list[dict[str, object]]:
    return flatten_payload(json.loads(path.read_text(encoding="utf-8")), path.name)


def _load_jsonl_payload(path: Path) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        items.extend(flatten_payload(json.loads(stripped), path.name))
    return items


def _load_csv_payload(path: Path) -> list[dict[str, object]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def load_records(paths: Iterable[Path]) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    for path in paths:
        suffix = path.suffix.lower()
        if suffix == ".json":
            loaded = _load_json_payload(path)
        elif suffix == ".jsonl":
            loaded = _load_jsonl_payload(path)
        elif suffix == ".csv":
            loaded = _load_csv_payload(path)
        else:
            continue
        for item in loaded:
            item.setdefault("_source_name", path.name)
        items.extend(loaded)
    return items


def iter_data_files(folder: Path) -> list[Path]:
    if not folder.exists():
        return []
    return sorted(
        path
        for path in folder.iterdir()
        if path.is_file() and path.suffix.lower() in {".json", ".jsonl", ".csv"}
    )


def normalize_gs(record: dict[str, object]) -> dict[str, object]:
    title = maybe_list_to_text(record.get("title"))
    authors = maybe_list_to_text(record.get("authors"))
    venue_text = maybe_list_to_text(record.get("journalYear") or record.get("journal"))
    year = extract_year(maybe_list_to_text(record.get("year")), venue_text)
    doi = normalize_doi(maybe_list_to_text(record.get("doi")))
    validation_status, validation_notes = derive_validation_status(
        {
            "title": title,
            "source_url": maybe_list_to_text(record.get("href") or record.get("source_url")),
            "doi": doi,
            "full_text_url": maybe_list_to_text(record.get("fullTextUrl")),
        }
    )
    return {
        "candidate_id": "",
        "title": title,
        "title_normalized": normalize_text(title),
        "authors": authors,
        "first_author": authors.split(",")[0].split(";")[0].strip() if authors else "",
        "year": year or "",
        "venue": venue_text,
        "abstract": maybe_list_to_text(record.get("abstract") or record.get("snippet")),
        "keywords": maybe_list_to_text(record.get("keywords")),
        "doi": doi,
        "doi_normalized": doi,
        "source_url": maybe_list_to_text(record.get("href") or record.get("source_url")),
        "full_text_url": maybe_list_to_text(record.get("fullTextUrl") or record.get("pdfUrl")),
        "source": "gs",
        "source_record_ids": [maybe_list_to_text(record.get("dataCid") or record.get("source_record_id"))],
        "source_queries": [maybe_list_to_text(record.get("query"))],
        "source_files": [maybe_list_to_text(record.get("_source_name"))],
        "source_count": 1,
        "citation_count": parse_count(record.get("citedBy") or record.get("citation_count")),
        "download_count": 0,
        "pdf_available": bool(maybe_list_to_text(record.get("fullTextUrl") or record.get("pdfUrl"))),
        "validation_status": validation_status,
        "validation_notes": validation_notes,
        "zotero_status": "unknown",
        "zotero_item_key": "",
        "in_zotero": "",
        "score_relevance": 0.0,
        "score_citation": 0.0,
        "score_recency": 0.0,
        "score_novelty": 0.0,
        "score_fulltext": 0.0,
        "score_total": 0.0,
        "selected": False,
        "selection_reason": "",
        "analysis_status": "pending",
    }


def normalize_cnki(record: dict[str, object]) -> dict[str, object]:
    title = maybe_list_to_text(record.get("title"))
    authors = maybe_list_to_text(record.get("authors"))
    year = extract_year(maybe_list_to_text(record.get("date")), maybe_list_to_text(record.get("year")))
    doi = normalize_doi(maybe_list_to_text(record.get("doi")))
    validation_status, validation_notes = derive_validation_status(
        {
            "title": title,
            "source_url": maybe_list_to_text(record.get("href") or record.get("pageUrl")),
            "doi": doi,
            "full_text_url": maybe_list_to_text(record.get("pdfUrl") or record.get("full_text_url")),
        }
    )
    return {
        "candidate_id": "",
        "title": title,
        "title_normalized": normalize_text(title),
        "authors": authors,
        "first_author": authors.split(";")[0].split(",")[0].strip() if authors else "",
        "year": year or "",
        "venue": maybe_list_to_text(record.get("journal") or record.get("source")),
        "abstract": maybe_list_to_text(record.get("abstract") or record.get("summary") or record.get("snippet")),
        "keywords": maybe_list_to_text(record.get("keywords")),
        "doi": doi,
        "doi_normalized": doi,
        "source_url": maybe_list_to_text(record.get("href") or record.get("pageUrl")),
        "full_text_url": maybe_list_to_text(record.get("pdfUrl") or record.get("full_text_url")),
        "source": "cnki",
        "source_record_ids": [maybe_list_to_text(record.get("exportId") or record.get("filename"))],
        "source_queries": [maybe_list_to_text(record.get("query"))],
        "source_files": [maybe_list_to_text(record.get("_source_name"))],
        "source_count": 1,
        "citation_count": parse_count(record.get("citations") or record.get("citation_count")),
        "download_count": parse_count(record.get("downloads") or record.get("download_count")),
        "pdf_available": bool(maybe_list_to_text(record.get("pdfUrl") or record.get("full_text_url"))),
        "validation_status": validation_status,
        "validation_notes": validation_notes,
        "zotero_status": "unknown",
        "zotero_item_key": "",
        "in_zotero": "",
        "score_relevance": 0.0,
        "score_citation": 0.0,
        "score_recency": 0.0,
        "score_novelty": 0.0,
        "score_fulltext": 0.0,
        "score_total": 0.0,
        "selected": False,
        "selection_reason": "",
        "analysis_status": "pending",
    }


def dedupe_candidates(candidates: list[dict[str, object]]) -> list[dict[str, object]]:
    merged: dict[str, dict[str, object]] = {}
    counter = 1
    for candidate in candidates:
        doi_key = str(candidate.get("doi_normalized") or "")
        title_key = str(candidate.get("title_normalized") or "")
        author_year_key = normalize_text(f"{candidate.get('first_author', '')}{candidate.get('year', '')}")
        key = doi_key or title_key or author_year_key or f"candidate-{counter}"
        if key not in merged:
            item = dict(candidate)
            item["candidate_id"] = f"P{counter:03d}"
            merged[key] = item
            counter += 1
            continue

        current = merged[key]
        for field in ["title", "authors", "venue", "abstract", "keywords", "doi", "doi_normalized", "source_url", "full_text_url", "first_author"]:
            if not current.get(field) and candidate.get(field):
                current[field] = candidate[field]
        current["year"] = current.get("year") or candidate.get("year") or ""
        current["citation_count"] = max(parse_count(current.get("citation_count")), parse_count(candidate.get("citation_count")))
        current["download_count"] = max(parse_count(current.get("download_count")), parse_count(candidate.get("download_count")))
        current["pdf_available"] = bool(current.get("pdf_available")) or bool(candidate.get("pdf_available"))
        current["source_count"] = int(current.get("source_count", 1)) + 1
        current["source"] = ";".join(sorted(set(str(current.get("source", "")).split(";") + [str(candidate.get("source", ""))]) - {""}))
        for list_field in ["source_record_ids", "source_queries", "source_files"]:
            existing = [str(item).strip() for item in current.get(list_field, []) if str(item).strip()]
            incoming = [str(item).strip() for item in candidate.get(list_field, []) if str(item).strip()]
            current[list_field] = sorted(set(existing + incoming))
        if current.get("validation_status") != "verified-source" and candidate.get("validation_status") == "verified-source":
            current["validation_status"] = "verified-source"
            current["validation_notes"] = candidate.get("validation_notes", "")

    return list(merged.values())


def load_zotero_snapshot(paths: Iterable[Path]) -> list[dict[str, object]]:
    return load_records(paths)


def match_zotero(candidates: list[dict[str, object]], snapshot: list[dict[str, object]]) -> None:
    by_doi: dict[str, dict[str, object]] = {}
    by_title: dict[str, dict[str, object]] = {}
    for item in snapshot:
        doi = normalize_doi(maybe_list_to_text(item.get("doi") or item.get("DOI")))
        if doi:
            by_doi[doi] = item
        title = normalize_text(maybe_list_to_text(item.get("title")))
        if title:
            by_title[title] = item

    for candidate in candidates:
        doi = str(candidate.get("doi_normalized") or "")
        title = str(candidate.get("title_normalized") or "")
        match = None
        if doi and doi in by_doi:
            match = by_doi[doi]
        elif title and title in by_title:
            match = by_title[title]

        if match:
            candidate["zotero_status"] = "matched"
            candidate["zotero_item_key"] = maybe_list_to_text(
                match.get("key") or match.get("itemKey") or match.get("zotero_item_key")
            )
            candidate["in_zotero"] = True
        else:
            candidate["zotero_status"] = "missing"
            candidate["zotero_item_key"] = ""
            candidate["in_zotero"] = False


def flatten_for_csv(record: dict[str, object]) -> dict[str, object]:
    row: dict[str, object] = {}
    for field in CANDIDATE_FIELDS:
        value = record.get(field, "")
        if isinstance(value, list):
            row[field] = "; ".join(str(item) for item in value if str(item))
        elif isinstance(value, bool):
            row[field] = "true" if value else "false"
        else:
            row[field] = value
    return row


def score_candidate(record: dict[str, object], config_keywords: dict[str, list[str]], weights: dict[str, int], recent_cutoff: int) -> None:
    title = str(record.get("title", "")).lower()
    abstract = str(record.get("abstract", "")).lower()
    venue = str(record.get("venue", "")).lower()
    term_weights = {"core": 4.0, "expanded": 2.5, "mechanisms": 1.5, "methods": 1.0}
    raw_relevance = 0.0
    max_relevance = 1.0

    for group, terms in config_keywords.items():
        group_weight = term_weights[group]
        for term in terms:
            normalized = term.strip().lower()
            if not normalized:
                continue
            max_relevance += group_weight * 3
            if normalized in title:
                raw_relevance += group_weight * 3
            elif normalized in abstract:
                raw_relevance += group_weight * 2
            elif normalized in venue:
                raw_relevance += group_weight

    score_relevance = weights["topic_relevance"] * min(1.0, raw_relevance / max_relevance)
    citation_ratio = min(1.0, math.log1p(parse_count(record.get("citation_count"))) / math.log1p(500))
    score_citation = weights["citation_value"] * citation_ratio

    year = int(record["year"]) if str(record.get("year", "")).isdigit() else None
    if year is None:
        recency_ratio = 0.25
    elif year >= recent_cutoff:
        recency_ratio = 1.0
    else:
        recency_ratio = max(0.15, 1 - ((recent_cutoff - year) / 15))
    score_recency = weights["recency_value"] * recency_ratio

    zotero_status = str(record.get("zotero_status", "unknown"))
    if zotero_status == "missing":
        novelty_ratio = 1.0
    elif zotero_status == "unknown":
        novelty_ratio = 0.5
    else:
        novelty_ratio = 0.0
    score_novelty = weights["novelty_to_local_library"] * novelty_ratio

    fulltext_ratio = 1.0 if record.get("pdf_available") else 0.25 if record.get("source_url") else 0.0
    score_fulltext = weights["fulltext_availability"] * fulltext_ratio

    record["score_relevance"] = round(score_relevance, 2)
    record["score_citation"] = round(score_citation, 2)
    record["score_recency"] = round(score_recency, 2)
    record["score_novelty"] = round(score_novelty, 2)
    record["score_fulltext"] = round(score_fulltext, 2)
    record["score_total"] = round(
        score_relevance + score_citation + score_recency + score_novelty + score_fulltext,
        2,
    )


def build_note_filename(index: int, title: str) -> str:
    return f"{index:03d}-{slugify(title)}.md"
