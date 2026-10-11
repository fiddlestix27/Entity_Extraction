from entity_extractor.ingest import ingest_input

def test_ingest_text_file(tmp_path):
    p = tmp_path / "sample.txt"
    p.write_text("Alice founded Acme Corp.", encoding="utf-8")
    doc = ingest_input(str(p))
    assert "Alice founded Acme Corp." in doc.text
    assert doc.document_id
    assert doc.content_sha256
