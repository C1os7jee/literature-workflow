from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from litflow.workflow import Workflow


class WorkflowTest(unittest.TestCase):
    def test_end_to_end_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            job_dir = Path(temp_dir) / "demo-job"
            workflow = Workflow(job_dir)
            workflow.init_job(topic="digital finance and firm innovation")

            config_path = job_dir / "config.toml"
            config_path.write_text(
                """job_name = "demo-job"
topic = "digital finance and firm innovation"
description = "demo"
target_final_count = 3
target_recent_count = 2
target_new_to_zotero_count = 1
target_classic_count = 1
candidate_pool_min = 4
recent_year_cutoff = 2017
analysis_template_name = "empirical-paper-brief"

[keywords]
core = ["digital finance", "firm innovation"]
expanded = ["credit access", "innovation"]
mechanisms = ["constraint", "mechanism"]
methods = ["did", "panel"]
exclusions = []

[collections]
root = "demo-root"
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
""",
                encoding="utf-8",
            )

            gs_payload = {
                "query": "digital finance firm innovation",
                "results": [
                    {
                        "title": "Digital Finance and Firm Innovation",
                        "authors": "Li, Wang",
                        "journalYear": "Journal of Finance, 2024",
                        "citedBy": "180",
                        "dataCid": "CID-001",
                        "href": "https://example.com/gs-1",
                        "fullTextUrl": "https://example.com/gs-1.pdf",
                        "snippet": "Digital finance improves firm innovation through credit access.",
                    },
                    {
                        "title": "Finance Constraints and Innovation",
                        "authors": "Zhao, Sun",
                        "journalYear": "Economic Review, 2011",
                        "citedBy": "240",
                        "dataCid": "CID-002",
                        "href": "https://example.com/gs-2",
                        "fullTextUrl": "",
                        "snippet": "A classic paper on financing constraints and innovation.",
                    },
                ],
            }
            cnki_payload = {
                "query": "digital finance innovation",
                "results": [
                    {
                        "title": "Mechanisms of Digital Finance on Innovation",
                        "authors": "Zhang; Liu",
                        "journal": "Management World",
                        "date": "2021-06-01",
                        "citations": "95",
                        "downloads": "500",
                        "href": "https://kns.cnki.net/detail/1",
                        "exportId": "EXP-001",
                    },
                    {
                        "title": "Digital Finance and Firm Innovation",
                        "authors": "Li; Wang",
                        "journal": "Management Science",
                        "date": "2024-01-01",
                        "citations": "110",
                        "downloads": "1200",
                        "href": "https://kns.cnki.net/detail/duplicate",
                        "exportId": "EXP-002",
                    },
                ],
            }

            (job_dir / "raw" / "gs" / "page1.json").write_text(json.dumps(gs_payload), encoding="utf-8")
            (job_dir / "raw" / "cnki" / "page1.json").write_text(json.dumps(cnki_payload), encoding="utf-8")

            zotero_snapshot = [
                {
                    "title": "Finance Constraints and Innovation",
                    "doi": "",
                    "key": "ZT-001",
                    "year": "2011",
                }
            ]
            (job_dir / "zotero" / "snapshot.json").write_text(json.dumps(zotero_snapshot), encoding="utf-8")

            workflow.normalize()
            workflow.zotero_sync()
            selected = workflow.select()
            workflow.materialize()
            report = workflow.qc()

            self.assertEqual(len(selected), 3)
            self.assertTrue((job_dir / "outputs" / "selected.csv").exists())
            self.assertTrue((job_dir / "outputs" / "zotero_import_queue.json").exists())
            self.assertTrue((job_dir / "outputs" / "qc_report.md").exists())
            self.assertEqual(report["selected_count"], 3)
            self.assertGreaterEqual(report["recent_count"], 2)


if __name__ == "__main__":
    unittest.main()
