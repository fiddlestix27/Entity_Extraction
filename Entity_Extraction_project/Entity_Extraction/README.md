# Entity Extraction

Standalone Python command-line tool for extracting entities and evidence-linked relationships from local text files, PDFs, and public web pages. It combines optional spaCy NER, an optional local LLM endpoint (LM Studio/OpenAI-compatible API), and deterministic validation. Extracted data can be written to SQLite, CSV, JSONL, and graph node/edge files.

## Install

Python 3.10+ recommended.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

python -m pip install -e ".[nlp,dev]"
python -m spacy download en_core_web_sm
```

The spaCy model is optional. If spaCy or its model is unavailable, the tool still performs conservative rule-based entity extraction.

## Local LLM (optional)

Start LM Studio's local server and load a model. Configure the endpoint using environment variables:

```bash
# Linux/macOS
export LLM_BASE_URL=http://localhost:1234/v1
export LLM_MODEL=your-loaded-model
export LLM_API_KEY=lm-studio

# PowerShell
$env:LLM_BASE_URL="http://localhost:1234/v1"
$env:LLM_MODEL="your-loaded-model"
$env:LLM_API_KEY="lm-studio"
```

The LLM is optional. Without it, the baseline NER/rule-based pipeline runs. Treat model-produced relations as candidate claims, not verified facts; each accepted relation must be grounded in source text.

## CLI

```bash
entity-extractor --input ./report.txt --output jsonl
entity-extractor --input ./report.pdf --output csv --out-dir ./results
entity-extractor --input "https://example.org/report" --output graph --out-dir ./results
entity-extractor --input ./report.txt --output sql --database ./data/entities.db
entity-extractor --input ./report.txt --output all --out-dir ./results
```

Arguments:

- `--input`, required: path to `.txt`, `.html`/`.htm`, `.pdf`, or `http(s)://` URL.
- `--output`, required: `sql`, `csv`, `jsonl`, `graph`, or `all`.
- `--out-dir`: directory for file exports (default `results`).
- `--database`: SQLite path (default `results/entities.db`).
- `--llm` / `--no-llm`: enable/disable local LLM relation extraction (default enabled if `LLM_BASE_URL` is configured).
- `--llm-model`, `--llm-base-url`: override local endpoint configuration.
- `--timeout`: HTTP timeout in seconds (default 20).
- `--max-bytes`: maximum downloaded/local input size in bytes (default 10 MB).
- `--verbose`: log extraction details.

`sql` writes to a persistent SQLite database. `csv` creates entities, relationships, and evidence CSVs. `jsonl` creates one JSON object per line for entities, relationships, and evidence. `graph` creates `nodes.csv` and `edges.csv`. `all` writes every format.

## Data and confidence boundaries

- Every document has a stable ID derived from its canonical source and content hash.
- Entity IDs are stable from normalized type/name, but are not identity proof.
- Relationships are source-grounded claims, not automatically confirmed real-world facts.
- The same relation may be asserted differently by multiple documents; evidence/provenance is retained.
- Entity resolution is conservative: matching labels may link to one entity record, but names alone should not be treated as proof that two people are the same.
- The SQL schema includes sources, documents, entities, aliases, claims, relationships, and evidence. Relationship rows reference entities and claim/evidence rows.
- Web ingestion only fetches the supplied URL. It does not crawl links or bypass access controls.

## Development

```bash
pytest
```

See `examples/sample_document.txt` for a small example.
