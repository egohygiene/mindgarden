"""Create-or-verify public output trees, without replacing caller-owned files."""

from pathlib import Path
import os
import stat

from ..domain.contracts import digest_bytes, safe_path
from ..domain.site import MAX_SITE_BYTES, MAX_SITE_ENTRIES, MAX_SITE_FILE_BYTES, MAX_SITE_FILES, SITE_MARKER, verify_site
from ..domain.validation import ContractError
from .federation_files import explicit_directory


def preview_server(directory, base_uri, port, *, check_live):
    """Serve only checksum-verified manifest members on the loopback interface."""
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    import mimetypes
    from urllib.parse import unquote, urlsplit

    files = read_site(directory)
    manifest = verify_site(files)
    if manifest["kind"] != "site" or manifest["base_uri"] != base_uri:
        raise ContractError("SITE_ROUTE: preview requires the exact rendered public site base")
    allowed = {item["path"]: item for item in manifest["artifacts"]}
    prefix = urlsplit(base_uri).path

    class Handler(BaseHTTPRequestHandler):
        def end_headers(self):
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            super().end_headers()

        def do_GET(self):
            self.respond(True)

        def do_HEAD(self):
            self.respond(False)

        def log_message(self, _format, *arguments):
            pass

        def respond(self, body):
            try:
                check_live()
                path = unquote(urlsplit(self.path).path)
                if path == "/" and prefix != "/":
                    self.send_response(302); self.send_header("Location", prefix); self.end_headers(); return
                if not path.startswith(prefix):
                    self.send_error(404, "Unavailable"); return
                relative = path[len(prefix):]
                names = [relative or "index.html", relative + ".html", relative.rstrip("/") + "/index.html"]
                name = next((candidate for candidate in names if candidate in allowed), None)
                if name is None:
                    self.send_error(404, "Unavailable"); return
                expected = allowed[name]
                content = read_artifact(safe_path(directory, name))
                if len(content) != expected["size_bytes"] or digest_bytes(content) != expected["sha256"]:
                    raise ContractError("SITE_INTEGRITY: preview artifact changed")
                self.send_response(200)
                self.send_header("Content-Type", mimetypes.guess_type(name)[0] or "application/octet-stream")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                if body:
                    self.wfile.write(content)
            except (ContractError, OSError, ValueError):
                self.send_error(403, "Preview unavailable; refresh authorized inputs")

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


def read_artifact(path: Path) -> bytes:
    """Bound every read and reject links, including preview-time replacements."""
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
    with os.fdopen(descriptor, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > MAX_SITE_FILE_BYTES:
            raise ContractError("SITE_PATH: output members must be bounded ordinary files")
        content = stream.read(MAX_SITE_FILE_BYTES + 1)
        if len(content) > MAX_SITE_FILE_BYTES:
            raise ContractError("SITE_BUDGET: output member exceeds the byte limit")
        return content


def read_site(directory: Path) -> dict[str, bytes]:
    if ".." in directory.parts:
        raise ContractError("SITE_PATH: use an explicit directory without traversal")
    directory = explicit_directory(directory)
    result = {}
    try:
        if not directory.is_dir():
            raise ContractError("SITE_UNAVAILABLE: explicit output directory is unavailable")
        entries = total_bytes = 0
        def unavailable(_error):
            raise ContractError("SITE_UNAVAILABLE: complete output coverage is required")
        for root, directories, names in os.walk(directory, onerror=unavailable, followlinks=False):
            entries += len(directories) + len(names)
            if entries > MAX_SITE_ENTRIES:
                raise ContractError("SITE_BUDGET: output exceeds the directory-entry budget")
            for name in directories + names:
                path = Path(root) / name
                if path.is_symlink():
                    raise ContractError("SITE_PATH: output must not contain symlinks")
            for name in sorted(names):
                path = Path(root) / name
                content = read_artifact(path)
                result[path.relative_to(directory).as_posix()] = content
                total_bytes += len(content)
                if len(result) > MAX_SITE_FILES or total_bytes > MAX_SITE_BYTES:
                    raise ContractError("SITE_BUDGET: output exceeds the supported site budget")
        return result
    except OSError as error:
        raise ContractError("SITE_UNAVAILABLE: explicit output cannot be inspected safely") from error


def write_site(directory: Path, files: dict[str, bytes], *, check_live, verify_inputs) -> bool:
    verify_site(files)
    directory = explicit_directory(directory)
    check_live(); verify_inputs()
    if directory.exists():
        if read_site(directory) != files:
            raise ContractError("SITE_OUTPUT_CONFLICT: retain existing output and choose a fresh destination")
        check_live()
        return False
    created = []
    directories = []
    try:
        directory.mkdir(mode=0o700); directories.append(directory)
        for name in sorted(set(files) - {SITE_MARKER}) + [SITE_MARKER]:
            check_live()
            if name == SITE_MARKER:
                verify_inputs()
            target = safe_path(directory, name)
            missing = []
            parent = target.parent
            while parent != directory and not parent.exists():
                missing.append(parent); parent = parent.parent
            for parent in reversed(missing):
                parent.mkdir(mode=0o700); directories.append(parent)
            with target.open("xb") as stream:
                os.chmod(target, 0o600)
                created.append((target, digest_bytes(files[name])))
                stream.write(files[name]); stream.flush(); os.fsync(stream.fileno())
        check_live(); verify_inputs()
        return True
    except BaseException as error:
        for path, expected in reversed(created):
            try:
                if not path.is_symlink() and path.is_file() and (path.stat().st_size == 0 or digest_bytes(path.read_bytes()) == expected):
                    path.unlink()
            except OSError:
                pass
        for parent in reversed(directories):
            try:
                parent.rmdir()
            except OSError:
                pass
        if isinstance(error, OSError):
            raise ContractError("SITE_OUTPUT: creation failed; preserve any incomplete output and choose a fresh destination") from error
        raise
