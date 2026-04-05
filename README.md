# Literature Workflow

This project turns the workflow we discussed into a small local CLI for:

- job setup and state tracking
- GS and CNKI raw intake
- normalization, deduplication, and scoring
- Zotero library diff from exported snapshot files
- final set selection
- import queue generation
- note stub generation
- QC reporting

## Why this shape

The workflow is built as a staged job runner instead of one giant prompt. That makes it easier to:

- resume after CAPTCHAs or browser login interruptions
- inspect intermediate files before importing into Zotero
- enforce quotas such as recent papers and new-to-Zotero papers
- keep a stable job folder you can revisit the next day

## Install

From this folder:

```bash
python -m pip install -e .
```

You can also run it without installation:

```bash
python -m litflow --help
```

## Quick start

1. Create a job folder:

```bash
python -m litflow init jobs/demo-review --topic "Replace with your topic"
```

2. Edit `config.toml` in the new job folder.

3. Open the generated prompt files:

- `prompts/01-search-prompt.md`
- `prompts/02-zotero-sync-prompt.md`

4. Save raw Google Scholar outputs into `raw/gs/`.

5. Save raw CNKI outputs into `raw/cnki/`.

6. Normalize the pool:

```bash
python -m litflow normalize jobs/demo-review
```

7. Export a Zotero snapshot into `zotero/` and sync:

```bash
python -m litflow zotero-sync jobs/demo-review
```

8. Select the review set:

```bash
python -m litflow select jobs/demo-review
```

9. Materialize note stubs and import queues:

```bash
python -m litflow materialize jobs/demo-review
```

10. Generate the QC report:

```bash
python -m litflow qc jobs/demo-review
```

## Supported raw input formats

For both GS and CNKI folders:

- `.json`
- `.jsonl`
- `.csv`

The parser accepts:

- a list of records
- a single record
- a wrapper object with `results: [...]`

That matches the structures described in the `cookjohn` GS and CNKI skill READMEs.

## Job layout

```text
job-name/
  config.toml
  state.json
  raw/
    gs/
    cnki/
  normalized/
  zotero/
  notes/
  outputs/
  prompts/
```

## Main outputs

- `normalized/candidates.jsonl`
- `normalized/candidates_zotero.jsonl`
- `outputs/selected.csv`
- `outputs/literature_matrix.csv`
- `outputs/zotero_import_queue.json`
- `outputs/analysis_queue.json`
- `outputs/qc_report.md`

## Notes

- The tool does not call GS, CNKI, or Zotero by itself.
- Instead, it keeps the workflow state and generates the files and prompts that Codex can use with those external skills and MCP tools.
- If Zotero snapshot files are missing, the pipeline still runs, but novelty-to-Zotero checks become weaker and QC will surface that gap.
