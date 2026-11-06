"""Generate tiny original synthetic PNG/WAV bytes using stdlib only."""

from pathlib import Path
import struct
import wave
import zlib


def main():
    root = Path(__file__).resolve().parents[1] / "tests/fixtures/assets"
    root.mkdir(parents=True, exist_ok=True)
    def chunk(kind, content):
        return struct.pack(">I", len(content)) + kind + content + struct.pack(">I", zlib.crc32(kind + content))
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(b"\0\x20\x80\x40")) + chunk(b"IEND", b"")
    (root / "synthetic.png").write_bytes(png)
    with wave.open(str(root / "synthetic.wav"), "wb") as output:
        output.setnchannels(1); output.setsampwidth(2); output.setframerate(8000); output.writeframes(b"\0" * 160)


if __name__ == "__main__": main()
