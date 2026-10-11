from entity_extractor.ingest import ingest_input
from entity_extractor.extraction import extract

def test_rule_relation_is_evidence_grounded(tmp_path):
    p = tmp_path / "sample.txt"
    p.write_text("Alice founded Acme Corp.", encoding="utf-8")
    result = extract(ingest_input(str(p)), use_llm=False)
    assert result.entities
    assert result.relationships
    relation = result.relationships[0]
    assert relation.evidence_text in result.document.text
    assert relation.subject_id in {e.entity_id for e in result.entities}
    assert relation.object_id in {e.entity_id for e in result.entities}
