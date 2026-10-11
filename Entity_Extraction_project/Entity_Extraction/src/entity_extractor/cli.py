from __future__ import annotations
import argparse, logging, os, sys
from pathlib import Path
from .ingest import ingest_input, DEFAULT_MAX_BYTES
from .extraction import extract
from .database import persist
from .exporters import export_csv, export_jsonl, export_graph, export_all

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="entity-extractor",
        description="Extract evidence-linked entities and relationships from a file or HTTP(S) URL."
    )
    parser.add_argument("-i", "--input", required=True, help="Input file path or http(s) URL")
    parser.add_argument("-o", "--output", required=True, choices=["sql", "csv", "jsonl", "graph", "all"],
                        help="Output type: SQLite database, CSV, JSONL, graph node/edge CSVs, or all")
    parser.add_argument("--out-dir", default="results", help="Directory for file-based exports (default: results)")
    parser.add_argument("--database", default="results/entities.db", help="SQLite database path for --output sql/all")
    parser.add_argument("--llm", dest="llm", action="store_true", help="Use configured local LLM for candidate relations")
    parser.add_argument("--no-llm", dest="llm", action="store_false", help="Disable local LLM")
    parser.set_defaults(llm=None)
    parser.add_argument("--llm-base-url", default=os.getenv("LLM_BASE_URL"), help="OpenAI-compatible local API base URL")
    parser.add_argument("--llm-model", default=os.getenv("LLM_MODEL", "local-model"), help="Local model name")
    parser.add_argument("--llm-api-key", default=os.getenv("LLM_API_KEY", "lm-studio"), help="Local API key if required")
    parser.add_argument("--timeout", type=int, default=20, help="Input download timeout in seconds")
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES, help="Maximum input size in bytes")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logs")
    return parser

def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(levelname)s: %(message)s")
    try:
        doc = ingest_input(args.input, timeout=args.timeout, max_bytes=args.max_bytes)
        llm_enabled = args.llm if args.llm is not None else bool(args.llm_base_url)
        result = extract(doc, use_llm=llm_enabled, base_url=args.llm_base_url,
                         model=args.llm_model, api_key=args.llm_api_key, timeout=max(args.timeout, 30))
        if args.output in {"sql", "all"}:
            persist(result, args.database)
            logging.info("SQLite database updated: %s", args.database)
        if args.output == "csv":
            export_csv(result, args.out_dir)
        elif args.output == "jsonl":
            export_jsonl(result, args.out_dir)
        elif args.output == "graph":
            export_graph(result, args.out_dir)
        elif args.output == "all":
            export_all(result, args.out_dir)
        logging.info("Document: %s", doc.document_id)
        logging.info("Extracted %d entities, %d relationships, %d evidence records",
                     len(result.entities), len(result.relationships), len(result.evidence))
        return 0
    except Exception as exc:
        logging.error("%s", exc)
        if args.verbose:
            logging.exception("Extraction failed")
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
