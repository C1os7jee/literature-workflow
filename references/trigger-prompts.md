# Trigger Prompts

Use these prompt templates when you want to trigger `literature-workflow` quickly and consistently.

## General Trigger

```text
Use $literature-workflow to handle this literature task.
```

## Mode A - Topic Search And Screening

### 1. Topic search plus import

```text
Use $literature-workflow to search literature on “路面裂缝检测”.
中文文献优先走 CNKI，英文文献优先走 Google Scholar。
先去重，再把 Zotero 里没有的文献导入当前 collection。
最后给我一份按主题分组的结果摘要。
```

### 2. Recent papers plus core classics

```text
Use $literature-workflow to collect papers on “pavement crack segmentation”.
Find at least 20 papers, including recent work from the last 5 years and a few foundational classics.
Import only verified missing items into Zotero and tell me which ones were newly added.
```

### 3. Chinese core journals first

```text
Use $literature-workflow to search this topic in Chinese first:
“道路病害检测与分割”.
Prioritize CNKI and check journal status when relevant.
Then supplement with international papers from Google Scholar.
Do not import duplicates into Zotero.
```

### 4. Cited-by expansion

```text
Use $literature-workflow to start from these seed papers, expand cited-by chains in Google Scholar,
screen out weakly related results, and import only the verified relevant papers into Zotero.
Also show me which papers are high-citation anchors.
```

## Mode B - Citation List Resolution And Import

### 5. Batch import by title and author check

```text
Use $literature-workflow to resolve and import the following references into Zotero.
Do not search with the full raw citation by default.
Prefer DOI first; otherwise search by title and confirm by author match.
Reuse existing Zotero items instead of creating duplicates.

[paste citation list here]
```

### 6. Re-check unresolved items

```text
Use $literature-workflow to re-check the following unresolved references.
Only import items that can be verified from official or DOI-backed sources.
If a citation is wrong, import the corrected canonical record and mark it as a correction in the report.

[paste unresolved list here]
```

### 7. Chinese citation correction

```text
Use $literature-workflow to verify these Chinese references with CNKI first.
Search by title, then confirm with author names.
If the official record differs from my citation, show me the corrected title, authors, journal, and year before import.

[paste Chinese references here]
```

### 8. Thesis-safe import

```text
Use $literature-workflow to verify these theses or dissertations.
Do not guess the school, city, or degree type.
Only import a thesis when an official thesis record is found; otherwise leave it unresolved.

[paste thesis list here]
```

## Zotero Maintenance

### 9. Library dedupe without risky auto-merge

```text
Use $literature-workflow to check whether these papers already exist in Zotero.
Show me exact duplicates, reusable existing items, and possible duplicates separately.
Do not merge or overwrite anything automatically.
```

### 10. Collection backfill

```text
Use $literature-workflow to compare this paper list against Zotero.
If an item already exists in the library but not in the target collection, reuse it and add it to that collection.
Do not create duplicate records.

Target collection: [collection name]
[paste paper list here]
```

### 11. Environment self-check before work

```text
Use $literature-workflow to first check whether CNKI browser workflow, Google Scholar browser workflow,
and Zotero MCP are available.
Then tell me which retrieval/import path you will use before starting the batch job.
```

## Review And Notes

### 12. Reading notes for imported papers

```text
Use $literature-workflow to generate structured reading notes for these Zotero items.
Prefer Zotero full text and annotations when available.
For each paper, summarize the research question, method, data, findings, limitations, and relevance to my topic.
```

### 13. Abstract-only fallback notes

```text
Use $literature-workflow to make lightweight reading notes for these papers.
If full text is unavailable, fall back to verified metadata and abstracts, and clearly mark the note as abstract-based.
```

## Recommended Short Forms

These shorter prompts work well when you do not need to spell out the whole workflow:

```text
Use $literature-workflow to search this topic and import missing verified papers into Zotero.
```

```text
Use $literature-workflow to resolve this citation list by title and author match, then import only the missing items.
```

```text
Use $literature-workflow to re-check unresolved Chinese references with CNKI first.
```

```text
Use $literature-workflow to generate structured notes for the papers I just imported.
```

## Prompting Tips

- Mention the target collection if collection placement matters.
- Say `do not use the full raw citation by default` when you are giving noisy references.
- Say `mark corrected canonical records explicitly` when citation correction matters.
- Say `do not auto-merge duplicates` when you want a safe review-first flow.
- Say `Chinese first via CNKI` or `English first via Google Scholar` when source priority matters.
