from pathlib import Path
from sqlalchemy import (create_engine, Column, String, Text, Float, Boolean, Integer,
                        ForeignKey, UniqueConstraint)
from sqlalchemy.orm import declarative_base, sessionmaker
from .schemas import ExtractionResult

Base = declarative_base()

class SourceRow(Base):
    __tablename__ = "sources"
    source_uri = Column(String, primary_key=True)
    title = Column(Text, nullable=False)

class DocumentRow(Base):
    __tablename__ = "documents"
    document_id = Column(String, primary_key=True)
    source_uri = Column(String, ForeignKey("sources.source_uri"), nullable=False)
    content_sha256 = Column(String, nullable=False)
    text = Column(Text, nullable=False)

class EntityRow(Base):
    __tablename__ = "entities"
    entity_id = Column(String, primary_key=True)
    name = Column(Text, nullable=False)
    normalized_name = Column(String, nullable=False, index=True)
    entity_type = Column(String, nullable=False)

class AliasRow(Base):
    __tablename__ = "entity_aliases"
    alias_id = Column(String, primary_key=True)
    entity_id = Column(String, ForeignKey("entities.entity_id"), nullable=False)
    alias = Column(Text, nullable=False)
    normalized_alias = Column(String, nullable=False)
    __table_args__ = (UniqueConstraint("entity_id", "normalized_alias"),)

class EvidenceRow(Base):
    __tablename__ = "evidence"
    evidence_id = Column(String, primary_key=True)
    document_id = Column(String, ForeignKey("documents.document_id"), nullable=False)
    quote = Column(Text, nullable=False)
    start_char = Column(Integer)
    end_char = Column(Integer)

class ClaimRow(Base):
    __tablename__ = "claims"
    claim_id = Column(String, primary_key=True)
    document_id = Column(String, ForeignKey("documents.document_id"), nullable=False)
    subject_id = Column(String, ForeignKey("entities.entity_id"), nullable=False)
    predicate = Column(String, nullable=False)
    object_id = Column(String, ForeignKey("entities.entity_id"), nullable=False)
    confidence = Column(Float, nullable=False)
    extraction_method = Column(String, nullable=False)
    accepted = Column(Boolean, nullable=False)

class RelationshipRow(Base):
    __tablename__ = "relationships"
    relationship_id = Column(String, primary_key=True)
    claim_id = Column(String, ForeignKey("claims.claim_id"), nullable=False)
    evidence_id = Column(String, ForeignKey("evidence.evidence_id"), nullable=False)

def persist(result: ExtractionResult, database: str = "results/entities.db") -> None:
    path = Path(database).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{path.as_posix()}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session.begin() as session:
        doc = result.document
        session.merge(SourceRow(source_uri=doc.source_uri, title=doc.title))
        session.merge(DocumentRow(document_id=doc.document_id, source_uri=doc.source_uri,
                                  content_sha256=doc.content_sha256, text=doc.text))
        for entity in result.entities:
            session.merge(EntityRow(entity_id=entity.entity_id, name=entity.name,
                                    normalized_name=entity.normalized_name, entity_type=entity.entity_type))
            for i, alias in enumerate(entity.aliases):
                import hashlib
                alias_id = "alias_" + hashlib.sha256(f"{entity.entity_id}:{alias.casefold()}".encode()).hexdigest()[:24]
                session.merge(AliasRow(alias_id=alias_id, entity_id=entity.entity_id, alias=alias,
                                       normalized_alias=alias.casefold()))
        for ev in result.evidence:
            session.merge(EvidenceRow(evidence_id=ev.evidence_id, document_id=ev.document_id,
                                      quote=ev.quote, start_char=ev.start_char, end_char=ev.end_char))
        for rel in result.relationships:
            session.merge(ClaimRow(claim_id=rel.relationship_id, document_id=rel.document_id,
                                   subject_id=rel.subject_id, predicate=rel.predicate, object_id=rel.object_id,
                                   confidence=rel.confidence, extraction_method=rel.extraction_method,
                                   accepted=rel.accepted))
            session.merge(RelationshipRow(relationship_id=rel.relationship_id, claim_id=rel.relationship_id,
                                          evidence_id=rel.evidence_id))
