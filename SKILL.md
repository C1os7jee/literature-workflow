---
name: literature-workflow
description: 真实学术文献检索、题录纠错、Zotero 去重入库和结构化阅读工作流。Use when Codex needs to search or verify Chinese or English papers, resolve DOI/title/citation lists into canonical metadata, compare them against a Zotero library, import missing items, reuse existing entries, or draft literature-review notes. This skill orchestrates the bundled CNKI workflows, Google Scholar workflows, and Zotero MCP package in this folder.
---

# Literature Workflow

Use this skill as the top-level orchestrator for literature work. Prefer the bundled packages in this folder over ad-hoc browsing or hand-written import logic.

## Start Here

Read [skill3_batch.md](skill3_batch.md) first. Let it choose mode A or mode B and decide which bundled package docs to load.
For reusable user-facing prompt templates, see [references/trigger-prompts.md](references/trigger-prompts.md).

## Bundled Packages

- [CNKI workflows](cnki-skills/README.md)
  Use for Chinese papers, official Chinese journal pages, journal indexing checks, and CNKI export metadata.
- [Google Scholar workflows](gs-skills/README.md)
  Use for English or international discovery, citation expansion, BibTeX export, and open full-text links.
- [Zotero MCP](zotero-mcp/README.md)
  Use for library reads and writes, duplicate checks, collection management, notes, annotations, semantic search, and DOI or URL import.

## Primary Routing

- Chinese title, Chinese journal, core-journal verification, or Chinese thesis:
  prefer CNKI first.
- English title, DOI lookup, cited-by expansion, or broad international discovery:
  prefer Google Scholar first, then DOI or publisher metadata.
- Zotero library search, dedupe, collection operations, note creation, metadata updates:
  prefer Zotero MCP first.
- If Zotero MCP is unavailable in the current client but Zotero local connector works:
  use connector or bundled export scripts as fallback and say that MCP was unavailable.

## Non-Negotiable Rules

1. Never invent papers, DOIs, abstracts, citations, or PDF availability.
2. In citation-list mode, do not default to the full raw reference string. Prefer DOI first; otherwise search by title and then confirm with author match.
3. Treat year, journal, pages, issue, and publisher as supporting evidence rather than the primary key.
4. If the canonical record differs from the user-supplied citation, mark it as a correction and report the difference clearly.
5. Pause when CNKI or Google Scholar surfaces CAPTCHA and ask the user to solve it manually before continuing.
6. Reuse existing Zotero items instead of creating duplicates.
7. Keep the workflow moving if one source fails. Switch sources or downgrade to a verified metadata-only report.
8. For theses or dissertations, do not guess the school, degree type, or city. Leave the item unresolved until an official thesis record is found.

## Modules

- [skill3_batch.md](skill3_batch.md): dispatcher and execution policy
- [skill1_fetch.md](skill1_fetch.md): search, verification, and citation-resolution flow
- [skill2_zotero.md](skill2_zotero.md): dedupe, import, reuse, and fallback write logic
- [skill4_review.md](skill4_review.md): structured reading notes and Zotero note output

## Load On Demand

- CNKI search stack:
  [cnki-search](cnki-skills/skills/cnki-search/SKILL.md),
  [cnki-advanced-search](cnki-skills/skills/cnki-advanced-search/SKILL.md),
  [cnki-paper-detail](cnki-skills/skills/cnki-paper-detail/SKILL.md),
  [cnki-journal-search](cnki-skills/skills/cnki-journal-search/SKILL.md),
  [cnki-journal-index](cnki-skills/skills/cnki-journal-index/SKILL.md),
  [cnki-export](cnki-skills/skills/cnki-export/SKILL.md)
- Google Scholar stack:
  [gs-search](gs-skills/skills/gs-search/SKILL.md),
  [gs-advanced-search](gs-skills/skills/gs-advanced-search/SKILL.md),
  [gs-cited-by](gs-skills/skills/gs-cited-by/SKILL.md),
  [gs-fulltext](gs-skills/skills/gs-fulltext/SKILL.md),
  [gs-export](gs-skills/skills/gs-export/SKILL.md)
- Zotero MCP references:
  [README](zotero-mcp/README.md),
  [getting started](zotero-mcp/docs/getting-started.md)

## Default Behavior

- Topic search, literature review, and source screening default to mode A.
- DOI lists, title lists, reference lists, and “导入 Zotero” requests default to mode B.
- Prefer Chinese output when the user works in Chinese, but keep titles and DOIs in their canonical language.
- Report three buckets whenever relevant: confirmed import, corrected candidate, unresolved item.
