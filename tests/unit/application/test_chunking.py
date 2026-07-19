from uuid import uuid4

from consultant.application.chunking import ChunkingConfig, create_chunks
from consultant.application.parsing import ParsedBlock, parse_document


def test_markdown_headings_are_preserved_as_chunk_sections() -> None:
    blocks = parse_document(
        payload=b"# Current Process\n\nReports are assembled manually.",
        content_type="text/markdown",
    )
    chunks = create_chunks(
        organization_id=uuid4(),
        project_id=uuid4(),
        document_version_id=uuid4(),
        blocks=blocks,
    )

    assert len(chunks) == 1
    assert chunks[0].section == "Current Process"
    assert chunks[0].content == "Reports are assembled manually."


def test_long_blocks_have_stable_ids_and_overlap() -> None:
    version_id = uuid4()
    kwargs = {
        "organization_id": uuid4(),
        "project_id": uuid4(),
        "document_version_id": version_id,
        "blocks": [ParsedBlock(text="word " * 100, section="Scope", page=3)],
        "config": ChunkingConfig(max_characters=160, overlap_characters=20),
    }

    first = create_chunks(**kwargs)
    second = create_chunks(**kwargs)

    assert len(first) > 1
    assert [chunk.id for chunk in first] == [chunk.id for chunk in second]
    assert all(chunk.page_start == 3 for chunk in first)
