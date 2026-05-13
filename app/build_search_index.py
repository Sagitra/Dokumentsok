#!/usr/bin/env python3
"""Build the document search index used by index.html.

The script scans the workspace for supported documents, extracts text where
possible, optionally OCRs pages/images with little or no embedded text, and
writes search-index.json.
"""

from __future__ import annotations

import argparse
import base64
import html
import json
import os
import re
import shutil
import sys
import zipfile
from html.parser import HTMLParser
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from pypdf import PdfReader


IGNORE_DIRS = {
    ".git",
    ".old-do-not-touch",
    "__pycache__",
    "app",
    "bin",
    "tmp",
    "tools",
}
INDEX_FILE = "search-index.json"
IGNORE_FILES = {"README.md", "Screenshot.png"}
TEXT_THRESHOLD = 24
DOCX_EXTRACTOR_VERSION = 4
IMAGE_EXTENSIONS = {
    ".bmp",
    ".gif",
    ".jpeg",
    ".jpg",
    ".png",
    ".tif",
    ".tiff",
    ".webp",
}
SUPPORTED_EXTENSIONS = {
    ".docx",
    ".pdf",
    ".html",
    ".htm",
    ".txt",
    ".md",
    ".markdown",
} | IMAGE_EXTENSIONS
@dataclass
class OcrState:
    available: bool
    reason: str = ""
    pytesseract: Any = None
    convert_from_path: Any = None
    rapidocr: Any = None
    fitz: Any = None
    np: Any = None
    Image: Any = None
    image_available: bool = False
    image_reason: str = ""
    lang: str = "swe+eng"
    fallback_lang: str = "eng"
    backend: str = ""


class TextExtractingHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "template"}:
            self._skip_depth += 1
        if tag in {"br", "p", "div", "section", "article", "li", "h1", "h2", "h3"}:
            self.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "template"} and self._skip_depth:
            self._skip_depth -= 1
        if tag in {"p", "div", "section", "article", "li", "h1", "h2", "h3"}:
            self.parts.append(" ")

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            self.parts.append(data)


def log(message: str) -> None:
    print(message, flush=True)


def relpath(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def clean_title(path: Path) -> str:
    title = path.stem
    title = re.sub(r"[_]+", " ", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title


def document_kind(path: Path) -> str:
    suffix = path.suffix.casefold()
    if suffix == ".docx":
        return "docx"
    if suffix == ".pdf":
        return "pdf"
    if suffix in IMAGE_EXTENSIONS:
        return "image"
    if suffix in {".html", ".htm"}:
        return "html"
    if suffix in {".md", ".markdown"}:
        return "md"
    if suffix == ".txt":
        return "txt"
    return suffix.lstrip(".") or "fil"


def clean_folder_name(value: str) -> str:
    value = re.sub(r"^\d+[_ -]*", "", value)
    value = value.replace("_", " ")
    value = re.sub(r"\s+", " ", value).strip()
    return value or "Dokument"


def sort_folder_name(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("_", " ")).strip() or "Dokument"


def document_metadata(path: Path, root: Path) -> dict[str, str]:
    relative_parts = path.relative_to(root).parts
    folder_parts = relative_parts[:-1]

    if len(folder_parts) >= 2:
        subject = clean_folder_name(folder_parts[0])
        category = clean_folder_name(folder_parts[1])
        category_sort = sort_folder_name(folder_parts[1])
    elif folder_parts:
        subject = clean_folder_name(folder_parts[0])
        category = subject
        category_sort = sort_folder_name(folder_parts[0])
    else:
        subject = "Dokument"
        category = "Dokument"
        category_sort = "Dokument"

    return {
        "title": clean_title(path),
        "subject": subject,
        "category": category,
        "categorySort": category_sort,
        "path": relpath(path, root),
        "type": document_kind(path),
    }


def should_ignore(path: Path, root: Path) -> bool:
    try:
        relative_parts = path.relative_to(root).parts
    except ValueError:
        return True
    for part in relative_parts[:-1]:
        if part.startswith(".") or part in IGNORE_DIRS:
            return True
    return path.name == INDEX_FILE or path.name in IGNORE_FILES or path.name.startswith(".")


def find_documents(root: Path) -> list[Path]:
    return sorted(
        (
            path
            for path in root.rglob("*")
            if path.is_file() and not should_ignore(path, root)
            and path.suffix.casefold() in SUPPORTED_EXTENSIONS
        ),
        key=lambda item: relpath(item, root).casefold(),
    )


def compact_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def has_meaningful_pdf_text(text: str) -> bool:
    compact = compact_text(text)
    if len(compact) < TEXT_THRESHOLD:
        return False

    meaningful_chars = sum(1 for char in compact if char.isalnum())
    if meaningful_chars < max(8, len(compact) // 4):
        return False

    return True


def read_text_file(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def extract_html_text(path: Path) -> str:
    parser = TextExtractingHtmlParser()
    parser.feed(read_text_file(path))
    parser.close()
    return compact_text(" ".join(parser.parts))


def extract_text_document(path: Path) -> list[dict[str, Any]]:
    if path.suffix.casefold() in {".html", ".htm"}:
        text = extract_html_text(path)
        source = "html"
    else:
        text = compact_text(read_text_file(path))
        source = document_kind(path)
    return [{"page": 1, "text": text, "source": source}]


DOCX_NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}
DOCX_BLOCK_TAGS = {
    f"{{{DOCX_NS['w']}}}p",
    f"{{{DOCX_NS['w']}}}tbl",
}
DOCX_IMAGE_TYPES = {
    ".bmp": "image/bmp",
    ".gif": "image/gif",
    ".jpeg": "image/jpeg",
    ".jpg": "image/jpeg",
    ".png": "image/png",
    ".svg": "image/svg+xml",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
    ".webp": "image/webp",
}


def xml_attr(element: ET.Element, name: str) -> str:
    return element.attrib.get(f"{{{DOCX_NS['w']}}}{name}", "")


def docx_heading_level(paragraph: ET.Element) -> int | None:
    style = paragraph.find("w:pPr/w:pStyle", DOCX_NS)
    value = normalize_style_name(xml_attr(style, "val") if style is not None else "")
    if not value:
        return None
    for prefix in ("heading", "rubrik"):
        if value.startswith(prefix):
            suffix = value[len(prefix) :]
            if suffix[:1].isdigit():
                return max(1, min(3, int(suffix[0])))
    return None


def normalize_style_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def docx_relationships(archive: zipfile.ZipFile) -> dict[str, str]:
    try:
        relationships_xml = archive.read("word/_rels/document.xml.rels")
    except KeyError:
        return {}
    root = ET.fromstring(relationships_xml)
    relationships: dict[str, str] = {}
    for relationship in root.findall("rel:Relationship", DOCX_NS):
        relationship_id = relationship.attrib.get("Id", "")
        target = relationship.attrib.get("Target", "")
        if relationship_id and target:
            relationships[relationship_id] = target
    return relationships


def docx_media_data(
    archive: zipfile.ZipFile,
    relationships: dict[str, str],
) -> dict[str, tuple[str, str]]:
    media: dict[str, tuple[str, str]] = {}
    for relationship_id, target in relationships.items():
        if target.startswith("../") or "://" in target:
            continue
        target_path = Path(target)
        if target_path.parts[:1] != ("media",):
            continue
        archive_path = f"word/{target_path.as_posix()}"
        mime_type = DOCX_IMAGE_TYPES.get(target_path.suffix.casefold())
        if not mime_type:
            continue
        try:
            encoded = base64.b64encode(archive.read(archive_path)).decode("ascii")
        except KeyError:
            continue
        media[relationship_id] = (mime_type, encoded)
    return media


def docx_run_text(
    run: ET.Element,
    media_by_relationship: dict[str, tuple[str, str]],
) -> tuple[str, str, bool, bool]:
    parts: list[str] = []
    image_html: list[str] = []
    for child in run:
        if child.tag == f"{{{DOCX_NS['w']}}}t":
            parts.append(child.text or "")
        elif child.tag == f"{{{DOCX_NS['w']}}}tab":
            parts.append("\t")
        elif child.tag in {
            f"{{{DOCX_NS['w']}}}br",
            f"{{{DOCX_NS['w']}}}cr",
        }:
            parts.append("\n")
    for blip in run.findall(".//a:blip", DOCX_NS):
        relationship_id = blip.attrib.get(f"{{{DOCX_NS['r']}}}embed", "")
        media = media_by_relationship.get(relationship_id)
        if media:
            mime_type, encoded = media
            image_html.append(
                f'<img class="docx-image" alt="" src="data:{mime_type};base64,{encoded}">'
            )
    properties = run.find("w:rPr", DOCX_NS)
    bold = properties is not None and properties.find("w:b", DOCX_NS) is not None
    italic = properties is not None and properties.find("w:i", DOCX_NS) is not None
    return "".join(parts), "".join(image_html), bold, italic


def docx_paragraph_parts(
    paragraph: ET.Element,
    media_by_relationship: dict[str, tuple[str, str]],
) -> tuple[str, str]:
    text_parts: list[str] = []
    html_parts: list[str] = []
    used_math_nodes: set[int] = set()
    for run in paragraph.findall(".//w:r", DOCX_NS):
        text, images, bold, italic = docx_run_text(run, media_by_relationship)
        if not text and not images:
            continue
        for math_text in run.findall(".//m:t", DOCX_NS):
            used_math_nodes.add(id(math_text))
        if text:
            text_parts.append(text)
            escaped = html.escape(text).replace("\n", "<br>")
            if bold:
                escaped = f"<strong>{escaped}</strong>"
            if italic:
                escaped = f"<em>{escaped}</em>"
            html_parts.append(escaped)
        if images:
            html_parts.append(images)
    math_tokens = [
        math_text.text or ""
        for math_text in paragraph.findall(".//m:t", DOCX_NS)
        if id(math_text) not in used_math_nodes and math_text.text
    ]
    if math_tokens:
        math_value = compact_text(" ".join(math_tokens))
        text_parts.append(math_value)
        html_blocks = html.escape(math_value).replace("\n", "<br>")
        html_parts.append(f'<span class="docx-math">{html_blocks}</span>')
    return "".join(text_parts).strip(), "".join(html_parts).strip()


def extract_docx_document(path: Path) -> list[dict[str, Any]]:
    with zipfile.ZipFile(path) as archive:
        media_by_relationship = docx_media_data(archive, docx_relationships(archive))
        document_xml = archive.read("word/document.xml")
    root = ET.fromstring(document_xml)
    body = root.find("w:body", DOCX_NS)
    if body is None:
        return [{"page": 1, "text": "", "html": "", "source": "docx"}]

    text_blocks: list[str] = []
    html_blocks: list[str] = []

    for block in body:
        if block.tag not in DOCX_BLOCK_TAGS:
            continue
        if block.tag == f"{{{DOCX_NS['w']}}}p":
            text, paragraph_html = docx_paragraph_parts(block, media_by_relationship)
            if not text and not paragraph_html:
                continue
            if text:
                text_blocks.append(text)
            heading_level = docx_heading_level(block)
            if heading_level:
                html_blocks.append(f"<h{heading_level}>{paragraph_html}</h{heading_level}>")
            else:
                html_blocks.append(f"<p>{paragraph_html}</p>")
            continue

        rows: list[str] = []
        text_rows: list[str] = []
        for row in block.findall("w:tr", DOCX_NS):
            cells: list[str] = []
            text_cells: list[str] = []
            for cell in row.findall("w:tc", DOCX_NS):
                cell_texts: list[str] = []
                cell_html: list[str] = []
                for paragraph in cell.findall(".//w:p", DOCX_NS):
                    text, paragraph_html = docx_paragraph_parts(
                        paragraph,
                        media_by_relationship,
                    )
                    if text:
                        cell_texts.append(text)
                    if paragraph_html:
                        cell_html.append(paragraph_html)
                cells.append(f"<td>{'<br>'.join(cell_html)}</td>")
                if cell_texts:
                    text_cells.append(" ".join(cell_texts))
            if cells:
                rows.append(f"<tr>{''.join(cells)}</tr>")
            if text_cells:
                text_rows.append(" | ".join(text_cells))
        if rows:
            html_blocks.append(f"<table>{''.join(rows)}</table>")
        if text_rows:
            text_blocks.append("\n".join(text_rows))

    return [
        {
            "page": 1,
            "text": compact_text("\n".join(text_blocks)),
            "html": "".join(html_blocks),
            "source": "docx",
        }
    ]


def load_existing_index(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def file_signature(path: Path) -> dict[str, int]:
    stat = path.stat()
    return {"size": stat.st_size, "mtime_ns": stat.st_mtime_ns}


def init_ocr(lang: str) -> OcrState:
    try:
        from PIL import Image  # type: ignore

        image_available = True
        image_reason = ""
    except ImportError as exc:
        Image = None
        image_available = False
        image_reason = f"Python bildpaket saknas: {exc.name}."

    if shutil.which("tesseract"):
        try:
            import pytesseract  # type: ignore
        except ImportError as exc:
            reason = f"Python OCR-paket saknas: {exc.name}."
            return OcrState(False, reason, Image=Image, image_available=False, image_reason=reason)

        pdf_available = True
        pdf_reason = ""
        convert_from_path = None
        if not shutil.which("pdftoppm"):
            pdf_available = False
            pdf_reason = "Poppler/pdftoppm saknas i PATH."
        else:
            try:
                from pdf2image import convert_from_path as pdf_to_images  # type: ignore

                convert_from_path = pdf_to_images
            except ImportError as exc:
                pdf_available = False
                pdf_reason = f"Python OCR-paket saknas: {exc.name}."

        return OcrState(
            pdf_available,
            pdf_reason,
            pytesseract=pytesseract,
            convert_from_path=convert_from_path,
            Image=Image,
            image_available=image_available,
            image_reason=image_reason,
            lang=lang,
            backend="tesseract",
        )

    try:
        import fitz  # type: ignore
        import numpy as np  # type: ignore
        from rapidocr_onnxruntime import RapidOCR  # type: ignore
    except ImportError as exc:
        reason = "Tesseract saknas i PATH."
        if exc.name:
            reason = f"{reason} RapidOCR-fallback saknas ocksa: {exc.name}."
        return OcrState(False, reason, Image=Image, image_available=False, image_reason=reason)

    if not image_available:
        reason = f"RapidOCR kraver Pillow for bildlasning. {image_reason}"
        return OcrState(False, reason, Image=Image, image_available=False, image_reason=reason)

    return OcrState(
        True,
        "RapidOCR-fallback aktiv.",
        rapidocr=RapidOCR(),
        fitz=fitz,
        np=np,
        Image=Image,
        image_available=True,
        image_reason="RapidOCR-fallback aktiv.",
        lang=lang,
        backend="rapidocr",
    )


def ocr_page(path: Path, page_number: int, ocr: OcrState, dpi: int) -> str:
    if not ocr.available:
        return ""
    if ocr.backend == "rapidocr":
        with ocr.fitz.open(str(path)) as document:
            page = document[page_number - 1]
            pixmap = page.get_pixmap(dpi=dpi, alpha=False)
            image = ocr.np.frombuffer(pixmap.samples, dtype=ocr.np.uint8).reshape(
                pixmap.height,
                pixmap.width,
                pixmap.n,
            )
        result, _ = ocr.rapidocr(image)
        if not result:
            return ""
        return compact_text(" ".join(item[1] for item in result if len(item) > 1))

    images = ocr.convert_from_path(
        str(path),
        dpi=dpi,
        first_page=page_number,
        last_page=page_number,
        fmt="png",
    )
    if not images:
        return ""
    image = images[0]
    try:
        return compact_text(ocr.pytesseract.image_to_string(image, lang=ocr.lang))
    except Exception as first_error:
        if ocr.lang == ocr.fallback_lang:
            raise first_error
        return compact_text(
            ocr.pytesseract.image_to_string(image, lang=ocr.fallback_lang)
        )


def ocr_image(path: Path, ocr: OcrState) -> str:
    if not ocr.image_available:
        return ""
    if ocr.backend == "rapidocr":
        with ocr.Image.open(path) as image:
            rgb_image = image.convert("RGB")
            result, _ = ocr.rapidocr(ocr.np.array(rgb_image))
        if not result:
            return ""
        return compact_text(" ".join(item[1] for item in result if len(item) > 1))

    with ocr.Image.open(path) as image:
        try:
            return compact_text(ocr.pytesseract.image_to_string(image, lang=ocr.lang))
        except Exception as first_error:
            if ocr.lang == ocr.fallback_lang:
                raise first_error
            return compact_text(
                ocr.pytesseract.image_to_string(image, lang=ocr.fallback_lang)
            )


def extract_pdf_pages(path: Path, ocr: OcrState, dpi: int) -> tuple[list[dict[str, Any]], int]:
    reader = PdfReader(str(path))
    pages: list[dict[str, Any]] = []
    ocr_pages = 0

    for index, page in enumerate(reader.pages, start=1):
        text = ""
        source = "pypdf"
        try:
            text = compact_text(page.extract_text())
        except Exception as exc:
            text = ""
            source = f"pypdf-error: {exc.__class__.__name__}"

        if not has_meaningful_pdf_text(text) and ocr.available:
            try:
                ocr_text = ocr_page(path, index, ocr, dpi)
                if ocr_text:
                    text = ocr_text
                    source = "ocr"
                    ocr_pages += 1
            except Exception as exc:
                if not text:
                    source = f"ocr-error: {exc.__class__.__name__}"

        pages.append({"page": index, "text": text, "source": source})

    return pages, ocr_pages


def extract_image_document(path: Path, ocr: OcrState) -> tuple[list[dict[str, Any]], int]:
    text = ""
    source = "image"
    ocr_pages = 0
    if ocr.image_available:
        try:
            text = ocr_image(path, ocr)
            if text:
                source = "ocr"
                ocr_pages = 1
        except Exception as exc:
            source = f"ocr-error: {exc.__class__.__name__}"
    return [{"page": 1, "text": text, "source": source}], ocr_pages


def natural_sort_key(value: str) -> list[int | str]:
    parts = re.split(r"(\d+)", value.casefold())
    return [int(part) if part.isdigit() else part for part in parts]


def build_index(root: Path, output: Path, force: bool, ocr: OcrState, dpi: int) -> dict[str, Any]:
    existing = load_existing_index(output)
    existing_files = existing.get("_meta", {}).get("files", {})
    existing_pages = existing.get("pdfTextIndexByPath", {})

    documents: list[dict[str, str]] = []
    pdf_text_index: dict[str, list[dict[str, Any]]] = {}
    file_meta: dict[str, Any] = {}
    warnings: list[str] = []

    if not ocr.available:
        warnings.append(
            f"PDF-OCR är inte aktivt: {ocr.reason} Textbaserade PDF:er indexeras ändå."
        )
    if not ocr.image_available:
        warnings.append(
            f"Bild-OCR är inte aktivt: {ocr.image_reason} Bilder indexeras via filnamn och mapp."
        )

    files = find_documents(root)
    log(f"Hittade {len(files)} sökbara filer.")

    for file_path in files:
        relative = relpath(file_path, root)
        signature = file_signature(file_path)
        kind = document_kind(file_path)
        documents.append(document_metadata(file_path, root))

        cached = (
            not force
            and existing_files.get(relative, {}).get("signature") == signature
            and relative in existing_pages
            and (
                kind != "docx"
                or existing_files.get(relative, {}).get("extractorVersion")
                == DOCX_EXTRACTOR_VERSION
            )
        )
        if cached:
            pdf_text_index[relative] = existing_pages[relative]
            file_meta[relative] = existing_files[relative]
            log(f"Återanvänder index: {relative}")
            continue

        log(f"Indexerar: {relative}")
        try:
            if kind == "pdf":
                pages, ocr_pages = extract_pdf_pages(file_path, ocr, dpi)
            elif kind == "image":
                pages, ocr_pages = extract_image_document(file_path, ocr)
            elif kind == "docx":
                pages = extract_docx_document(file_path)
                ocr_pages = 0
            else:
                pages = extract_text_document(file_path)
                ocr_pages = 0
            pdf_text_index[relative] = pages
            file_meta[relative] = {
                "signature": signature,
                "pages": len(pages),
                "ocrPages": ocr_pages,
                "type": kind,
                "extractorVersion": DOCX_EXTRACTOR_VERSION if kind == "docx" else 1,
            }
        except Exception as exc:
            warnings.append(f"Kunde inte indexera {relative}: {exc}")
            pdf_text_index[relative] = []
            file_meta[relative] = {
                "signature": signature,
                "pages": 0,
                "ocrPages": 0,
                "type": kind,
                "extractorVersion": DOCX_EXTRACTOR_VERSION if kind == "docx" else 1,
                "error": str(exc),
            }

    documents.sort(
        key=lambda doc: (
            doc["subject"].casefold(),
            natural_sort_key(doc["categorySort"]),
            natural_sort_key(doc["category"]),
            doc["title"].casefold(),
        )
    )
    category_sort_names = {
        doc["category"]: doc["categorySort"]
        for doc in sorted(
            documents,
            key=lambda doc: (
                natural_sort_key(doc["categorySort"]),
                natural_sort_key(doc["category"]),
            ),
        )
    }
    categories = sorted(
        category_sort_names,
        key=lambda category: (
            natural_sort_key(category_sort_names[category]),
            natural_sort_key(category),
        ),
    )
    subjects = sorted({doc["subject"] for doc in documents}, key=natural_sort_key)

    return {
        "version": 1,
        "documents": documents,
        "categories": categories,
        "subjects": subjects,
        "pdfTextIndexByPath": pdf_text_index,
        "warnings": warnings,
        "_meta": {
            "files": file_meta,
            "ocrAvailable": ocr.available,
            "ocrReason": ocr.reason,
            "imageOcrAvailable": ocr.image_available,
            "imageOcrReason": ocr.image_reason,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build search-index.json for the document search app.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Workspace root to scan.")
    parser.add_argument("--output", type=Path, default=None, help="Output JSON path.")
    parser.add_argument("--force", action="store_true", help="Rebuild all documents even when cached.")
    parser.add_argument("--ocr-lang", default=os.environ.get("OCR_LANG", "swe+eng"))
    parser.add_argument("--ocr-dpi", type=int, default=int(os.environ.get("OCR_DPI", "200")))
    args = parser.parse_args()

    root = args.root.resolve()
    output = (args.output or root / INDEX_FILE).resolve()
    ocr = init_ocr(args.ocr_lang)

    try:
        index = build_index(root, output, args.force, ocr, args.ocr_dpi)
        output.write_text(
            json.dumps(index, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except KeyboardInterrupt:
        log("Avbrutet.")
        return 130
    except Exception as exc:
        print(f"Fel: {exc}", file=sys.stderr)
        return 1

    log(f"Skrev {output}")
    for warning in index.get("warnings", []):
        log(f"Varning: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
