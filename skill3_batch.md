# SKILL 3 - Batch Dispatcher And Execution Policy

## Responsibility

Parse the user request, choose mode A or mode B, load only the necessary bundled package docs, orchestrate the fetch and Zotero stages, and produce a clean final report.

## Mode Selection

### Mode A: Topic Search, Screening, And Optional Review

Use mode A when the user:
- gives a research topic
- asks for literature search or source screening
- wants a literature review, reading notes, or structured summaries

### Mode B: Citation Resolution And Zotero Import

Use mode B when the user:
- gives a DOI list, title list, or formatted reference list
- asks to “导入 Zotero”, “补齐未入库文献”, or “精确查找这些文献”
- mainly wants metadata correction, duplicate handling, and import

## Default Parameters

- `collection_name`:
  use the user’s target collection if provided; otherwise default to the currently selected Zotero collection or library root
- `need_review`:
  mode A = `true`
  mode B = `false`
- `language_mix`:
  infer from the user’s titles, journals, and query language

## Package Loading Order

1. Read [skill1_fetch.md](skill1_fetch.md).
2. Load CNKI docs only if Chinese-source work is needed.
3. Load Google Scholar docs only if English or international work is needed.
4. Read [skill2_zotero.md](skill2_zotero.md) before any write or duplicate operation.
5. Read [skill4_review.md](skill4_review.md) only when the user wants notes, summaries, or review output.

## Mode A Pipeline

1. Normalize the topic and define source mix.
2. Search with the bundled source workflows:
   CNKI for Chinese materials;
   Google Scholar for international discovery.
3. Verify shortlisted papers with title, author, and source evidence.
4. Pass verified items to the Zotero stage.
5. If review output is requested, generate structured notes for imported or selected items.
6. Return a final report with imports, reuse, corrections, and unresolved items.

## Mode B Pipeline

1. Parse the raw citation list into per-item fields.
2. Resolve each item using the source routing from SKILL 1:
   DOI first;
   otherwise title search plus author confirmation.
3. Separate results into:
   `confirmed`, `corrected_candidate`, `possible_duplicate`, `not_found`
4. Send only confirmed items and high-confidence corrected candidates into the Zotero stage.
5. Reuse existing Zotero items where possible.
6. Return a final report that distinguishes newly added items from corrected imports and unresolved citations.

## Tool Availability Policy

The bundled CNKI and Google Scholar workflows assume Chrome DevTools MCP access, and the Zotero stage assumes Zotero MCP access.

If the current session lacks one of these tool surfaces:

- keep the same source priority and decision rules
- use browsing, DOI metadata, publisher pages, local connector, or exporter scripts as fallback
- say clearly which part ran in fallback mode

Do not silently change the verification standard just because the preferred tool is unavailable.

## Progress Reporting

- For batch jobs, report progress every 10 items.
- Also report when the workflow switches sources or changes from verification to import.
- Keep progress updates short and operational:
  what source is being used, what has been confirmed, and what remains unresolved.

## Final Report Format

Always separate the outcomes:

- newly imported
- reused existing items
- already in target collection
- corrected canonical imports
- possible duplicates awaiting confirmation
- unresolved or not found

When corrections occurred, show the canonical title used for import and state that it differs from the user-supplied citation.
