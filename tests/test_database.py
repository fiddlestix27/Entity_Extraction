import sqlite3
from entity_extractor.ingest import ingest_input
from entity_extractor.extraction import extract
from entity_extractor.database import persist

def test_sql_persistence_is_repeatable(tmp_path):
    p = tmp_path / "sample.txt"
    p.write_text("Alice founded Acme Corp.", encoding="utf-8")
    result = extract(ingest_input(str(p)), use_llm=False)
    db = tmp_path / "out.db"
    persist(result, str(db))
    persist(result, str(db))
    con = sqlite3.connect(db)
    assert con.execute("select count(*) from documents").fetchone()[0] == 1
    assert con.execute("select count(*) from relationships").fetchone()[0] == len(result.relationships)
