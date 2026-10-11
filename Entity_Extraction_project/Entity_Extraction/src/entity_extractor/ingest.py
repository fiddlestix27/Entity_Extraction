from __future__ import annotations
import hashlib
import re
from pathlib import Path
from urllib.parse import urlparse, urlunparse
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
from .schemas import SourceDocument

DEFAULT_MAX_BYTES = 10 * 1024 * 1024

def _canonical_url(url: str) -> str:
    p = urlparse(url)
    return urlunparse((p.scheme.lower(), p.netloc.lower(), p.path or "/", "", p.query, ""))

def _make_doc(uri: str, title: str, text: str) -> SourceDocument:
    text = text.replace("\x00", "").strip()
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    doc_id = hashlib.sha256(f"{uri}\n{digest}".encode("utf-8")).hexdigest()
    return SourceDocument(uri, title.strip() or uri, text, digest, doc_id)

def ingest_input(value: str, timeout: int = 20, max_bytes: int = DEFAULT_MAX_BYTES) -> SourceDocument:
    if value.lower().startswith(("http://", "https://")):
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("Only valid http(s) URLs are supported.")
        response = requests.get(value, timeout=timeout, stream=True, headers={"User-Agent": "EntityExtraction/0.1"})
        response.raise_for_status()
        chunks, total = [], 0
        for chunk in response.iter_content(chunk_size=65536):
            total += len(chunk)
            if total > max_bytes:
                raise ValueError(f"Input exceeds --max-bytes limit ({max_bytes}).")
            chunks.append(chunk)
        raw = b"".join(chunks)
        content_type = response.headers.get("Content-Type", "").lower()
        encoding = response.encoding or "utf-8"
        decoded = raw.decode(encoding, errors="replace")
        if "pdf" in content_type or urlparse(value).path.lower().endswith(".pdf"):
            import io
            reader = PdfReader(io.BytesIO(raw))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            title = Path(parsed.path).name or parsed.netloc
        elif "html" in content_type or "<html" in decoded[:1000].lower() or "<!doctype" in decoded[:1000].lower():
            soup = BeautifulSoup(decoded, "html.parser")
            for node in soup(["script", "style", "noscript", "svg"]):
                node.decompose()
            title = soup.title.get_text(" ", strip=True) if soup.title else parsed.netloc
            text = soup.get_text(" ", strip=True)
        else:
            title = Path(parsed.path).name or parsed.netloc
            text = decoded
        return _make_doc(_canonical_url(value), title, text)

    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Input file not found: {path}")
    if path.stat().st_size > max_bytes:
        raise ValueError(f"Input exceeds --max-bytes limit ({max_bytes}).")
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(str(path))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    elif suffix in {".html", ".htm"}:
        soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="replace"), "html.parser")
        for node in soup(["script", "style", "noscript", "svg"]):
            node.decompose()
        text = soup.get_text(" ", strip=True)
    elif suffix in {".txt", ".text", ".md", ""}:
        text = path.read_text(encoding="utf-8", errors="replace")
    else:
        raise ValueError(f"Unsupported file extension '{suffix}'. Use TXT, MD, HTML, or PDF.")
    return _make_doc(path.as_uri(), path.name, text)
