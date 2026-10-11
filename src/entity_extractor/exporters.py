import csv, json
from pathlib import Path
from dataclasses import asdict
from .schemas import ExtractionResult

def _write_csv(path: Path, rows: list[dict]):
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v
                             for k, v in row.items()})

def export_csv(result: ExtractionResult, out_dir: str):
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    _write_csv(out / "entities.csv", [asdict(x) for x in result.entities])
    _write_csv(out / "relationships.csv", [asdict(x) for x in result.relationships])
    _write_csv(out / "evidence.csv", [asdict(x) for x in result.evidence])

def export_jsonl(result: ExtractionResult, out_dir: str):
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    groups = {"entities": result.entities, "relationships": result.relationships, "evidence": result.evidence}
    for name, objects in groups.items():
        with (out / f"{name}.jsonl").open("w", encoding="utf-8") as f:
            for obj in objects:
                f.write(json.dumps(asdict(obj), ensure_ascii=False) + "\n")

def export_graph(result: ExtractionResult, out_dir: str):
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    _write_csv(out / "nodes.csv", [asdict(x) for x in result.entities])
    _write_csv(out / "edges.csv", [asdict(x) for x in result.relationships])

def export_all(result: ExtractionResult, out_dir: str):
    export_csv(result, out_dir)
    export_jsonl(result, out_dir)
    export_graph(result, out_dir)
