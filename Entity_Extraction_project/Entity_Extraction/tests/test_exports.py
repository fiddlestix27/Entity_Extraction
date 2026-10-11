import json
from entity_extractor.ingest import ingest_input
from entity_extractor.extraction import extract
from entity_extractor.exporters import export_csv, export_jsonl, export_graph

def test_exports(tmp_path):
    p = tmp_path / "sample.txt"
    p.write_text("Alice founded Acme Corp.", encoding="utf-8")
    result = extract(ingest_input(str(p)), use_llm=False)
    export_csv(result, str(tmp_path / "csv"))
    export_jsonl(result, str(tmp_path / "jsonl"))
    export_graph(result, str(tmp_path / "graph"))
    assert (tmp_path / "csv" / "entities.csv").exists()
    rows = [json.loads(x) for x in (tmp_path / "jsonl" / "relationships.jsonl").read_text().splitlines()]
    assert all(row["evidence_id"] for row in rows)
    assert (tmp_path / "graph" / "nodes.csv").exists()
    assert (tmp_path / "graph" / "edges.csv").exists()
