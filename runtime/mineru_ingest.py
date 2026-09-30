"""Optional MinerU CLI ingestion boundary for Book.

Upstream: opendatalab/MinerU @
ed50cc15bc2c9bfb00520dadfe61979866e62236.

License: Apache-2.0 plus MinerU's additional commercial-threshold terms.
MinerU remains an external tool; no MinerU source is vendored into Book.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import Any, Callable


@dataclass(frozen=True)
class MinerUIngestResult:
    source_path: str
    markdown_path: str
    markdown: str
    tier: str
    backend: str = "mineru-cli"


class MinerUCliIngestor:
    VALID_TIERS = {"flash", "basic", "standard", "advanced"}

    def __init__(
        self,
        *,
        executable: str = "mineru-kit",
        runner: Callable[..., Any] = subprocess.run,
    ) -> None:
        if not str(executable).strip():
            raise ValueError("executable cannot be empty")
        if not callable(runner):
            raise TypeError("runner must be callable")
        self.executable = str(executable)
        self._runner = runner

    def convert_local(
        self,
        source_path: str | Path,
        output_path: str | Path,
        *,
        tier: str = "standard",
    ) -> MinerUIngestResult:
        source = Path(source_path)
        output = Path(output_path)
        if not source.is_file():
            raise FileNotFoundError(source)
        normalized_tier = str(tier).strip().casefold()
        if normalized_tier not in self.VALID_TIERS:
            raise ValueError("tier must be flash, basic, standard or advanced")
        if output.suffix.lower() not in {".md", ".markdown"}:
            raise ValueError("output_path must be a Markdown file")
        output.parent.mkdir(parents=True, exist_ok=True)

        command = [
            self.executable,
            "parse",
            str(source),
            "-o",
            str(output),
            "--tier",
            normalized_tier,
        ]
        completed = self._runner(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
        if not output.is_file():
            raise RuntimeError("MinerU completed without creating the requested Markdown output")
        markdown = output.read_text(encoding="utf-8").strip()
        if not markdown:
            raise ValueError("MinerU returned empty Markdown")
        return MinerUIngestResult(
            source_path=str(source),
            markdown_path=str(output),
            markdown=markdown,
            tier=normalized_tier,
        )
