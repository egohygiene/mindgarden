"""Optional explicit local Poppler tools; bounded execution, no acquisition/OCR."""

from pathlib import Path
import math
import os
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

from ..domain.contracts import digest_bytes
from ..domain.validation import ContractError

MAXIMUM_PDF = 10 * 1024 * 1024
MAXIMUM_OUTPUT = 8 * 1024 * 1024


def child_limits():
    """Resource limits are not a confidential-runtime or network sandbox claim."""
    import resource

    resource.setrlimit(resource.RLIMIT_FSIZE, (MAXIMUM_OUTPUT, MAXIMUM_OUTPUT))
    resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def run_tool(path: Path, arguments: list[str], captured: bytes, workspace: Path):
    environment = {"HOME": str(workspace), "TMPDIR": str(workspace), "TMP": str(workspace),
                   "TEMP": str(workspace), "XDG_CACHE_HOME": str(workspace), "LC_ALL": "C"}
    with tempfile.TemporaryFile(dir=workspace) as output, tempfile.TemporaryFile(dir=workspace) as errors:
        try:
            with subprocess.Popen([str(path), *arguments], stdin=subprocess.PIPE, stdout=output,
                                  stderr=errors, cwd=workspace, env=environment,
                                  preexec_fn=child_limits, start_new_session=True) as process:
                try:
                    process.communicate(captured, timeout=15)
                except subprocess.TimeoutExpired as error:
                    process.kill(); process.communicate()
                    raise ContractError("DOCUMENT_LIMIT: local reader exceeded its time bound") from error
            output.seek(0); errors.seek(0)
            content, diagnostic = output.read(MAXIMUM_OUTPUT + 1), errors.read(MAXIMUM_OUTPUT + 1)
            if len(content) >= MAXIMUM_OUTPUT or len(diagnostic) >= MAXIMUM_OUTPUT or process.returncode < 0:
                raise ContractError("DOCUMENT_LIMIT: local reader exceeded its resource bound")
            return process.returncode, content, diagnostic
        except OSError as error:
            raise ContractError("DOCUMENT_UNAVAILABLE: explicit local reader could not run") from error


def layout_pages(content: bytes, expected: int) -> list[dict]:
    """Normalized word offsets address UTF-8 text, never pretend to be PDF bytes."""
    if b"<!ENTITY" in content or b"<!DOCTYPE" in content and b"[" in content.split(b">", 1)[0]:
        raise ContractError("DOCUMENT_MALFORMED: reader output contains unsupported entities")
    try:
        document = ET.fromstring(content)
        elements = [element for element in document.iter() if element.tag.rsplit("}", 1)[-1] == "page"]
        if len(elements) != expected or not 1 <= expected <= 1000:
            raise ValueError()
        pages = []
        total_words = 0
        for number, element in enumerate(elements, 1):
            width, height = float(element.attrib["width"]), float(element.attrib["height"])
            if not all(math.isfinite(value) and 0 < value <= 100000 for value in (width, height)):
                raise ValueError()
            parts, words, offset = [], [], 0
            for line in element.iter():
                if line.tag.rsplit("}", 1)[-1] != "line": continue
                line_words = [word for word in line if word.tag.rsplit("}", 1)[-1] == "word"]
                for index, word in enumerate(line_words):
                    text = "".join(word.itertext())
                    if not text: continue
                    if index and parts:
                        parts.append(" "); offset += 1
                    bounds = [float(word.attrib[key]) for key in ("xMin", "yMin", "xMax", "yMax")]
                    if (not all(math.isfinite(value) and value >= 0 for value in bounds)
                            or not 0 <= bounds[0] <= bounds[2] <= width
                            or not 0 <= bounds[1] <= bounds[3] <= height): raise ValueError()
                    end = offset + len(text.encode("utf8"))
                    words.append({"text": text, "bbox": bounds, "start_byte": offset, "end_byte": end})
                    parts.append(text); offset = end
                if line_words:
                    parts.append("\n"); offset += 1
            total_words += len(words)
            if total_words > 100000: raise ContractError("DOCUMENT_LIMIT: reader word count exceeds the supported bound")
            pages.append({"page": number, "width": width, "height": height, "text": "".join(parts), "words": words})
        return pages
    except (ET.ParseError, KeyError, TypeError, ValueError, UnicodeError) as error:
        raise ContractError("DOCUMENT_MALFORMED: local reader returned invalid page geometry") from error


class LocalPDFReader:
    """Selected by the caller, never discovered from PATH or installed implicitly."""

    def __init__(self, tool_directory: Path, work_root: Path):
        self.tool_directory, self.work_root = tool_directory, work_root
        self.source_checks = []

    def read(self, captured: bytes) -> dict:
        if not sys.platform.startswith("linux"):
            raise ContractError("DOCUMENT_UNAVAILABLE: this bounded tool runner supports Linux only")
        if len(captured) > MAXIMUM_PDF:
            raise ContractError("DOCUMENT_LIMIT: captured PDF exceeds the supported bound")
        if not captured.startswith(b"%PDF-"):
            return {"status": "unsupported", "pages": [], "parser": None}
        # The application validates the selected vault before constructing us.
        directory = self.tool_directory
        if not directory.is_absolute() or any(p.is_symlink() for p in (directory, *directory.parents)):
            raise ContractError("DOCUMENT_UNAVAILABLE: supply an explicit regular tool directory")
        tools = {name: directory / name for name in ("pdfinfo", "pdftotext")}
        for path in tools.values():
            if path.is_symlink() or not path.is_file() or not os.access(path, os.X_OK):
                raise ContractError("DOCUMENT_UNAVAILABLE: selected optional reader is unavailable")
        self.source_checks = [(path, digest_bytes(path.read_bytes())) for path in tools.values()]
        profile = {"name": "poppler-bbox-layout", "adapter_version": "1.0.0", "tools": [],
                   "normalization": "word-order-space-separated-lines-lf/1",
                   "limits": {"capture_bytes": MAXIMUM_PDF, "output_bytes": MAXIMUM_OUTPUT,
                              "timeout_seconds": 15, "pages": 1000, "words": 100000}}
        with tempfile.TemporaryDirectory(prefix=".document-work-", dir=self.work_root) as temporary:
            workspace = Path(temporary); workspace.chmod(0o700)
            for name, path in tools.items():
                code, output, errors = run_tool(path, ["-v"], b"", workspace)
                match = re.search(rb"\bversion ([0-9]+\.[0-9]+\.[0-9]+)\b", output + errors)
                if code or not match:
                    raise ContractError("DOCUMENT_UNAVAILABLE: selected reader version is unrecognized")
                profile["tools"].append({"name": name, "version": match.group(1).decode(),
                                         "sha256": dict(self.source_checks)[path]})
            code, info, errors = run_tool(tools["pdfinfo"], ["-"], captured, workspace)
            if b"password" in errors.lower() or re.search(rb"^Encrypted:\s+yes", info, re.M):
                return {"status": "encrypted", "pages": [], "parser": profile}
            # Warnings indicate potentially incomplete parsing: do not accept a repaired file silently.
            if code or errors.strip(): return {"status": "malformed", "pages": [], "parser": profile}
            count = re.search(rb"^Pages:\s+([0-9]+)\s*$", info, re.M)
            if not count or not 1 <= int(count.group(1)) <= 1000:
                raise ContractError("DOCUMENT_LIMIT: page count is unavailable or outside the supported bound")
            code, xml, errors = run_tool(tools["pdftotext"], ["-bbox-layout", "-enc", "UTF-8", "-", "-"], captured, workspace)
            if code or errors.strip(): return {"status": "malformed", "pages": [], "parser": profile}
            pages = layout_pages(xml, int(count.group(1)))
            readable = sum(bool(page["text"].strip()) for page in pages)
            status = "complete" if readable == len(pages) else ("ocr-needed" if not readable else "partial")
            if any(digest_bytes(path.read_bytes()) != digest for path, digest in self.source_checks):
                raise ContractError("DOCUMENT_CHANGED: selected reader changed during extraction")
            return {"status": status, "pages": pages, "parser": profile}
