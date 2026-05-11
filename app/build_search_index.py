#!/usr/bin/env python3
"""Build the document search index used by index.html.

The script scans the workspace for supported documents, extracts text where
possible, optionally OCRs pages/images with little or no embedded text, and
writes search-index.json.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from html.parser import HTMLParser
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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
IGNORE_FILES = {"README.md"}
TEXT_THRESHOLD = 24
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
    ".pdf",
    ".html",
    ".htm",
    ".txt",
    ".md",
    ".markdown",
} | IMAGE_EXTENSIONS
EMD_FOLDERS = {
    "01_Forelasningar",
    "02_Flikar_Formelblad",
    "03_Labbar",
    "04_Tentor_och_Losningar",
    "05_Kursinfo",
    "06_Ovningar",
}
EIEF10_WRAPPER = "EIEF10"
CATEGORY_FOLDERS = {
    "Föreläsningar": "Föreläsningar",
    "Kurskompendium": "Kurskompendium",
    "Övningar": "Övningar",
    "Formelblad": "Formelblad",
    "Tentor": "Tentor",
    "Lösningsförslag": "Lösningsförslag",
    "Labbar": "Labbar",
    "Kursinfo": "Kursinfo",
}
LEGACY_EMD_WRAPPERS = {"emd"}
LEGACY_EMD_TOP_FOLDERS = EMD_FOLDERS | {"handskriven formel"}
CATEGORY_ORDER = [
    "Föreläsningar",
    "Kurskompendium",
    "Övningar",
    "Formelblad",
    "Tentor",
    "Lösningsförslag",
    "Labbar",
    "Kursinfo",
]


@dataclass
class OcrState:
    available: bool
    reason: str = ""
    pytesseract: Any = None
    convert_from_path: Any = None
    Image: Any = None
    image_available: bool = False
    image_reason: str = ""
    lang: str = "swe+eng"
    fallback_lang: str = "eng"


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


def is_solution_pdf(path: Path) -> bool:
    text = path.stem.casefold()
    return any(token in text for token in ("lösning", "losning", "facit"))


def emd_category(folder: str, filename: str, path: Path) -> str:
    if folder == "01_Forelasningar":
        return "Föreläsningar"
    if folder == "02_Flikar_Formelblad":
        return "Formelblad" if "formelblad" in filename else "Kurskompendium"
    if folder == "03_Labbar":
        return "Labbar"
    if folder == "04_Tentor_och_Losningar":
        return "Lösningsförslag" if is_solution_pdf(path) else "Tentor"
    if folder == "05_Kursinfo":
        return "Kursinfo"
    if folder == "06_Ovningar":
        return "Övningar"
    return clean_folder_name(folder)


def document_metadata(path: Path, root: Path) -> dict[str, str]:
    relative_parts = path.relative_to(root).parts
    top = relative_parts[0] if relative_parts else ""
    filename = path.name.casefold()
    emd_folder = ""
    if top in EMD_FOLDERS:
        emd_folder = top
    elif top == EIEF10_WRAPPER and len(relative_parts) > 1:
        candidate = relative_parts[1]
        if candidate in EMD_FOLDERS:
            emd_folder = candidate

    if top == EIEF10_WRAPPER and len(relative_parts) > 1 and relative_parts[1] in CATEGORY_FOLDERS:
        subject = "EIEF10"
        category = CATEGORY_FOLDERS[relative_parts[1]]
    elif emd_folder:
        subject = "EIEF10"
        category = emd_category(emd_folder, filename, path)
    else:
        subject = clean_folder_name(top) if top else "Dokument"
        category = (
            clean_folder_name(relative_parts[1])
            if len(relative_parts) > 2
            else subject
        )

    return {
        "title": clean_title(path),
        "subject": subject,
        "category": category,
        "path": relpath(path, root),
        "type": document_kind(path),
    }


def should_ignore(path: Path, root: Path) -> bool:
    try:
        relative_parts = path.relative_to(root).parts
    except ValueError:
        return True
    if (
        (root / EIEF10_WRAPPER).is_dir()
        and relative_parts
        and (
            relative_parts[0] in LEGACY_EMD_TOP_FOLDERS
            or relative_parts[0].casefold() in LEGACY_EMD_WRAPPERS
        )
    ):
        return True
    if (
        len(relative_parts) > 1
        and relative_parts[0] == EIEF10_WRAPPER
        and relative_parts[1] in EMD_FOLDERS
        and any((root / EIEF10_WRAPPER / folder).is_dir() for folder in CATEGORY_FOLDERS)
    ):
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
    if not shutil.which("tesseract"):
        return OcrState(
            False,
            "Tesseract saknas i PATH.",
            image_available=False,
            image_reason="Tesseract saknas i PATH.",
        )
    try:
        import pytesseract  # type: ignore
    except ImportError as exc:
        reason = f"Python OCR-paket saknas: {exc.name}."
        return OcrState(False, reason, image_available=False, image_reason=reason)

    try:
        from PIL import Image  # type: ignore

        image_available = True
        image_reason = ""
    except ImportError as exc:
        Image = None
        image_available = False
        image_reason = f"Python bildpaket saknas: {exc.name}."

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
    )


def ocr_page(path: Path, page_number: int, ocr: OcrState, dpi: int) -> str:
    if not ocr.available:
        return ""
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

        if len(text) < TEXT_THRESHOLD and ocr.available:
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


def category_sort_key(category: str) -> tuple[int, str]:
    try:
        return (CATEGORY_ORDER.index(category), category.casefold())
    except ValueError:
        return (len(CATEGORY_ORDER), category.casefold())


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
            else:
                pages = extract_text_document(file_path)
                ocr_pages = 0
            pdf_text_index[relative] = pages
            file_meta[relative] = {
                "signature": signature,
                "pages": len(pages),
                "ocrPages": ocr_pages,
                "type": kind,
            }
        except Exception as exc:
            warnings.append(f"Kunde inte indexera {relative}: {exc}")
            pdf_text_index[relative] = []
            file_meta[relative] = {
                "signature": signature,
                "pages": 0,
                "ocrPages": 0,
                "type": kind,
                "error": str(exc),
            }

    documents.sort(
        key=lambda doc: (
            doc["subject"].casefold(),
            category_sort_key(doc["category"]),
            doc["title"].casefold(),
        )
    )
    categories = sorted(
        {doc["category"] for doc in documents},
        key=category_sort_key,
    )
    subjects = sorted({doc["subject"] for doc in documents}, key=str.casefold)

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
