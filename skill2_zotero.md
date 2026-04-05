# SKILL 2 - Zotero Dedupe, Import, And Reuse

## Responsibility

Receive verified records from SKILL 1, compare them against the user’s Zotero library, and import only what is missing. Prefer Zotero MCP for reads and writes; use the bundled CNKI or Google Scholar export scripts only when they fit the record better or when MCP write paths are unavailable.

## Read First When Setup Is Unclear

- [Zotero MCP README](zotero-mcp/README.md)
- [Zotero MCP getting started](zotero-mcp/docs/getting-started.md)
- [CNKI export workflow](cnki-skills/skills/cnki-export/SKILL.md)
- [Google Scholar export workflow](gs-skills/skills/gs-export/SKILL.md)

## Preferred Write Stack

1. Zotero MCP
2. Zotero local connector plus bundled export scripts
3. Metadata-only report if neither write path is available

## Recommended Zotero MCP Tools

### Search And Dedupe

- `zotero_search_items`
- `zotero_advanced_search`
- `zotero_get_collections`
- `zotero_search_collections`
- `zotero_get_collection_items`
- `zotero_find_duplicates`

### Import And Update

- `zotero_add_by_doi`
- `zotero_add_by_url`
- `zotero_add_from_file`
- `zotero_create_collection`
- `zotero_manage_collections`
- `zotero_update_item`

### Optional Cleanup

- `zotero_merge_duplicates`

Run merge only after a dry-run preview and only when the user has asked for duplicate cleanup.

## Collection Policy

- If the user names a target collection, search for it first.
- If the collection does not exist, create it before importing.
- If an item already exists in the library but is not in the target collection, reuse the existing item and add it to the collection.
- Do not create a second item just to satisfy a collection placement request.

## Duplicate Logic

### Exact Duplicate

1. DOI exact match:
   treat as existing
2. Normalized title exact match plus author match:
   treat as existing

### Reusable Existing Item

- Existing in library but absent from target collection:
  mark as `exists_add_to_collection`

### Possible Duplicate

- Title highly similar but author mismatch
- Title highly similar but author missing on either side
- Corrected candidate conflicts with an existing record whose authors do not align

These records should not be auto-imported.

## Import Path Selection

Choose the narrowest reliable write path for each item:

1. DOI present and trusted:
   use `zotero_add_by_doi`
2. Stable landing URL present and trusted:
   use `zotero_add_by_url`
3. Local PDF or EPUB available:
   use `zotero_add_from_file`
4. CNKI record without a clean DOI workflow:
   use the bundled [cnki-export](cnki-skills/skills/cnki-export/SKILL.md) path or its `push_to_zotero.py` script
5. Google Scholar record whose best metadata source is BibTeX:
   use the bundled [gs-export](gs-skills/skills/gs-export/SKILL.md) path or its `push_to_zotero.py` script
6. No reliable write path:
   keep the verified metadata in the report and skip import

## Corrected Citation Policy

If SKILL 1 marks an item as `corrected_candidate`, import the canonical record only when:

- the canonical record is DOI-backed, or
- it comes from an official source with strong author match

When doing this:
- add a note, tag, or `extra` field stating that the item was imported from a corrected citation
- report the correction in the final summary

## Fallback When Zotero MCP Is Unavailable

If the current client does not expose Zotero MCP tools:

1. Use local connector or the bundled export scripts for writes.
2. Use local SQLite read-only queries or connector-accessible metadata for duplicate checks when possible.
3. Explicitly state that the workflow fell back from MCP to connector mode.

For Windows plus Chinese metadata, prefer UTF-8-safe Python exporter scripts over direct shell JSON posting when encoding is fragile.

## Batch Workflow

1. Resolve or create target collection.
2. For each verified item, search Zotero by DOI or normalized title.
3. Classify into:
   `new`, `exists_in_collection`, `exists_add_to_collection`, `possible_duplicate`, `not_found`
4. Import only `new` items and approved high-confidence corrected candidates.
5. Reuse existing items instead of recreating them.
6. Tag or annotate imports when the user asked for provenance tracking.
7. Return a report grouped by outcome.

## Output Groups

Return results in these buckets:

```text
new_items
reused_existing_items
already_in_collection
possible_duplicates
not_found_items
corrected_imports
```

Keep the final report concise but explicit about which path was used:
- Zotero MCP
- connector plus exporter script
- metadata-only
