# SKILL 4 - Structured Reading Notes

## Responsibility

Produce a concise, source-backed reading note for one paper or a small set of papers. Prefer Zotero MCP content access when the item is already in the library; otherwise fall back to the verified metadata gathered during SKILL 1.

## Preferred Inputs

- Zotero item key or item ID
- DOI
- canonical title
- attached PDF or full-text item already present in Zotero

## Preferred Zotero MCP Tools

- `zotero_get_item_metadata`
- `zotero_get_item_fulltext`
- `zotero_get_item_children`
- `zotero_get_annotations`
- `zotero_get_notes`
- `zotero_create_note`

If Scite support is configured and the user asks about influence or reliability, optionally use:
- `scite_enrich_item`

## Evidence Order

1. Full text from Zotero
2. Zotero annotations and notes
3. Verified abstract and metadata
4. Citation or source-page snippets

Do not write claims that are unsupported by the strongest available evidence.

## Workflow

1. Fetch metadata first.
2. If full text exists, read enough of it to extract the research question, method, data, results, and limitations.
3. If annotations exist, use them as priority cues for what the user found important.
4. If only abstract-level evidence exists, produce an abstract-level note and explicitly say that the note is limited by missing full text.
5. If the user wants the note stored back in Zotero, create a note after drafting it.

## Recommended Note Structure

Use sections like these when the evidence supports them:

- Citation
- Research question
- Data or materials
- Method or model
- Key findings
- Limitations
- Relevance to the user’s topic
- What to compare next

## Writing Rules

- Paraphrase instead of copying long passages.
- Keep uncertain fields explicit:
  `not stated in available text`,
  `full text unavailable`,
  `inferred from abstract only`
- Do not invent datasets, metrics, sample sizes, or conclusions.

## Zotero Note Output

If storing the note in Zotero:

- mention whether it was based on full text, annotations, or abstract only
- include DOI and canonical title when available
- keep the note compact enough to remain readable inside Zotero
