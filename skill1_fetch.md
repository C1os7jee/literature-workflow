# SKILL 1 - Search, Verification, And Citation Resolution

## Responsibility

Turn a topic, DOI, title list, or noisy reference list into verified paper metadata. This module is responsible for source selection, title lookup, author matching, confidence labeling, and correction detection before any Zotero write happens.

## Source Routing

| Request pattern | Primary bundle | Supporting evidence |
|---|---|---|
| Chinese journal article | CNKI search and detail pages | Journal search or index, DOI page, publisher page |
| Chinese core-journal verification | CNKI journal search and journal index | Official journal site |
| Chinese thesis or dissertation | CNKI first | Official thesis repository or university record |
| English journal or conference paper | Google Scholar | DOI resolution, publisher page, Crossref |
| Citation expansion, “cited by”, influence tracing | Google Scholar cited-by | Publisher page, Crossref |
| Mixed list with Chinese and English items | Route each item independently | Merge evidence at the end |

## Load These Bundled Docs Only When Needed

- Chinese retrieval:
  [cnki-search](cnki-skills/skills/cnki-search/SKILL.md),
  [cnki-advanced-search](cnki-skills/skills/cnki-advanced-search/SKILL.md),
  [cnki-paper-detail](cnki-skills/skills/cnki-paper-detail/SKILL.md),
  [cnki-journal-search](cnki-skills/skills/cnki-journal-search/SKILL.md),
  [cnki-journal-index](cnki-skills/skills/cnki-journal-index/SKILL.md)
- English retrieval:
  [gs-search](gs-skills/skills/gs-search/SKILL.md),
  [gs-advanced-search](gs-skills/skills/gs-advanced-search/SKILL.md),
  [gs-cited-by](gs-skills/skills/gs-cited-by/SKILL.md),
  [gs-fulltext](gs-skills/skills/gs-fulltext/SKILL.md)

## Mode A: Topic-Based Collection

1. Normalize the topic into 2-6 search expressions.
2. Decide the source mix:
   Chinese-heavy topic -> CNKI first;
   English-heavy topic -> Google Scholar first;
   mixed topic -> parallel source coverage.
3. Run source-native search:
   CNKI via `cnki-search` or `cnki-advanced-search`;
   Google Scholar via `gs-search` or `gs-advanced-search`.
4. For shortlisted papers, open detail-level evidence:
   CNKI via `cnki-paper-detail`;
   English papers via DOI or publisher metadata, plus `gs-fulltext` when full text matters.
5. Expand only when needed:
   use `gs-cited-by` for high-value seed papers;
   use CNKI journal tools when the user explicitly asks about core status or indexing.
6. Produce a verified candidate list with confidence labels before sending anything to Zotero.

## Mode B: Citation List Resolution

### Parse Each Raw Citation Into Target Fields

Extract, when present:
- `doi`
- `title`
- `authors`
- `year`
- `venue`
- `volume_issue_pages`
- `type`

Do not trust the raw citation as a whole string. It may contain title errors, journal errors, or author omissions.

### Search Order

1. If DOI exists:
   verify DOI metadata first, then use source-specific search only to fill gaps or confirm language variants.
2. If no DOI and the item is Chinese:
   search by exact title in CNKI first, then confirm with author match, then use journal-search or journal-index if venue verification is needed.
3. If no DOI and the item is English:
   search by title in Google Scholar first, then confirm with author match, then resolve DOI or publisher landing page.
4. Use the full raw reference string only as a last fallback after title-based search fails.

### Matching Rules

- Exact or near-exact title plus matching first author and no venue conflict:
  `confirmed`
- Official source record exists but differs from the user-supplied citation while authors and topic clearly match:
  `corrected_candidate`
- Title is similar but author match is weak, absent, or conflicting:
  `possible_duplicate`
- No reliable official or DOI-backed record found:
  `not_found`

### Correction Policy

A corrected candidate may be auto-promoted to importable only when the evidence is strong:
- DOI-backed canonical metadata, or
- official CNKI or publisher record with strong author match and no major conflict

When auto-promoting a corrected candidate, always report the correction in plain language.

## CAPTCHA Handling

- CNKI and Google Scholar browser flows assume Chrome DevTools MCP is available.
- If either site shows CAPTCHA, stop and ask the user to solve it manually in the browser.
- Resume from the same page after the user confirms.

## Tool Availability Fallback

If the current Codex session does not expose the browser MCP tools required by the bundled CNKI or Google Scholar docs:

1. Keep the same source priority and verification rules.
2. Use official web pages, DOI content negotiation, Crossref, or publisher pages as fallback evidence.
3. Preserve the same confidence labels:
   `confirmed`, `corrected_candidate`, `possible_duplicate`, `not_found`.

## Output Schema

Return each resolved item in a structure equivalent to:

```json
{
  "input_title": "",
  "canonical_title": "",
  "authors": [],
  "year": "",
  "venue": "",
  "type": "",
  "doi": "",
  "url": "",
  "source_used": "",
  "status": "confirmed",
  "confidence": 0.0,
  "correction_note": "",
  "evidence": []
}
```

Keep `evidence` short and source-backed. Do not include invented abstracts or guesses.
