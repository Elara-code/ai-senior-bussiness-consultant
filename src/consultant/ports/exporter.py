from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ExportDocument:
    title: str
    body_markdown: str
    approved: bool
    citation_lines: list[str]


@dataclass(frozen=True, slots=True)
class ExportedFile:
    content: bytes
    content_type: str
    extension: str


class DocumentExporter(Protocol):
    def export(self, document: ExportDocument) -> ExportedFile: ...
