from consultant.ports.exporter import ExportDocument, ExportedFile


class MarkdownExporter:
    def export(self, document: ExportDocument) -> ExportedFile:
        notice = "" if document.approved else "> **草稿：未经审批，不得对外使用**\n\n"
        citations = (
            "\n\n## 引用\n\n" + "\n".join(document.citation_lines)
            if document.citation_lines
            else ""
        )
        content = f"# {document.title}\n\n{notice}{document.body_markdown}{citations}\n"
        return ExportedFile(content.encode(), "text/markdown; charset=utf-8", "md")
