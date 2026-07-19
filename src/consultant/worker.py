from uuid import UUID

from consultant.application.pipeline import DocumentPipeline


async def process_document_job(*, pipeline: DocumentPipeline, version_id: UUID) -> None:
    """Worker entry point kept framework-neutral for queue adapters."""
    await pipeline.process(version_id)
