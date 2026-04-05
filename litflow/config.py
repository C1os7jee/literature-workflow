from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
import tomllib


@dataclass(slots=True)
class Keywords:
    core: list[str] = field(default_factory=list)
    expanded: list[str] = field(default_factory=list)
    mechanisms: list[str] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)
    exclusions: list[str] = field(default_factory=list)

    @property
    def all_terms(self) -> list[str]:
        return [*self.core, *self.expanded, *self.mechanisms, *self.methods]


@dataclass(slots=True)
class Collections:
    root: str
    candidates: str = "00_candidates"
    selected: str = "01_selected"
    fulltext: str = "02_fulltext"
    notes: str = "03_notes"


@dataclass(slots=True)
class Weights:
    topic_relevance: int = 40
    citation_value: int = 20
    recency_value: int = 20
    novelty_to_local_library: int = 10
    fulltext_availability: int = 10


@dataclass(slots=True)
class JobConfig:
    job_name: str
    topic: str
    description: str
    target_final_count: int
    target_recent_count: int
    target_new_to_zotero_count: int
    target_classic_count: int
    candidate_pool_min: int
    recent_year_cutoff: int
    analysis_template_name: str
    keywords: Keywords
    collections: Collections
    weights: Weights

    @classmethod
    def from_path(cls, path: Path) -> "JobConfig":
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        keywords = Keywords(**data.get("keywords", {}))
        collections = Collections(**data.get("collections", {}))
        weights = Weights(**data.get("weights", {}))
        return cls(
            job_name=data["job_name"],
            topic=data.get("topic", ""),
            description=data.get("description", ""),
            target_final_count=int(data.get("target_final_count", 40)),
            target_recent_count=int(data.get("target_recent_count", 25)),
            target_new_to_zotero_count=int(data.get("target_new_to_zotero_count", 10)),
            target_classic_count=int(data.get("target_classic_count", 5)),
            candidate_pool_min=int(data.get("candidate_pool_min", 80)),
            recent_year_cutoff=int(data.get("recent_year_cutoff", date.today().year - 9)),
            analysis_template_name=data.get("analysis_template_name", "empirical-paper-brief"),
            keywords=keywords,
            collections=collections,
            weights=weights,
        )


def build_default_config(job_name: str, topic: str = "", collection_root: str = "") -> str:
    recent_cutoff = date.today().year - 9
    topic_line = topic or "Replace with your research topic"
    collection = collection_root or f"{job_name}_{date.today().isoformat()}"
    return f"""job_name = "{job_name}"
topic = "{topic_line}"
description = "Describe scope, population, methods, and why this review matters."
target_final_count = 40
target_recent_count = 25
target_new_to_zotero_count = 10
target_classic_count = 5
candidate_pool_min = 80
recent_year_cutoff = {recent_cutoff}
analysis_template_name = "empirical-paper-brief"

[keywords]
core = ["primary construct A", "primary construct B"]
expanded = ["synonym A", "synonym B"]
mechanisms = ["mechanism A", "mechanism B"]
methods = ["difference in differences", "panel data", "instrumental variables"]
exclusions = ["book review", "news report"]

[collections]
root = "{collection}"
candidates = "00_candidates"
selected = "01_selected"
fulltext = "02_fulltext"
notes = "03_notes"

[weights]
topic_relevance = 40
citation_value = 20
recency_value = 20
novelty_to_local_library = 10
fulltext_availability = 10
"""
