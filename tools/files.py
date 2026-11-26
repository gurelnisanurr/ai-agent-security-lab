from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent / "workspace"


def read_file(path: str) -> str:
    """Çalışma alanındaki bir dosyanın içeriğini döndürür."""
    hedef = WORKSPACE / path
    return hedef.read_text(encoding="utf-8")