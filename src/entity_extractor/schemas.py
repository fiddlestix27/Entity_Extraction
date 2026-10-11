from dataclasses import asdict, dataclass, field
from typing import Any

@dataclass
class SourceDocument:
    source_uri: str
    title: str
    text: str
    content_sha256: str
    document_id: str

@dataclass
class Entity:
    entity_id: str
    name: str
    normalized_name: str
    entity_type: str = "UNKNOWN"
    aliases: list[str] = field(default_factory=list)

@dataclass
class Evidence:
    evidence_id: str
    document_id: str
    quote: str
    start_char: int | None = None
    end_char: int | None = None

@dataclass
class Relationship:
    relationship_id: str
    subject_id: str
    predicate: str
    object_id: str
    document_id: str
    evidence_id: str
    evidence_text: str
    confidence: float = 0.5
    extraction_method: str = "rule"
    accepted: bool = True

@dataclass
class ExtractionResult:
    document: SourceDocument
    entities: list[Entity]
    relationships: list[Relationship]
    evidence: list[Evidence]

    def as_dict(self) -> dict[str, Any]:
        return {
            "document": asdict(self.document),
            "entities": [asdict(x) for x in self.entities],
            "relationships": [asdict(x) for x in self.relationships],
            "evidence": [asdict(x) for x in self.evidence],
        }
