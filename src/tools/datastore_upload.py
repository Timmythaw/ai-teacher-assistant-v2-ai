# src/tools/datastore_upload.py
"""
Upload curriculum files to Vertex AI Search datastore.

This is a ONE-TIME operation per file. Vertex AI handles indexing,
chunking, and embedding automatically.
"""

from pathlib import Path
from typing import Final

from google.cloud import discoveryengine_v1 as discoveryengine
from google.cloud import storage  # type: ignore[attr-defined]

from src.config.settings import Settings
from src.utils.logger import logger

# Supported file types for Vertex AI Search
SUPPORTED_EXTENSIONS: Final[set[str]] = {
    ".pdf",
    ".pptx",
    ".docx",
    ".txt",
    ".md",
    ".html",
}


class DatastoreUploadError(Exception):
    """Raised when datastore upload operations fail."""

    pass


async def upload_file_to_gcs(
    file_path: Path,
    settings: Settings,
    bucket_name: str = "teacher-assistant-uploads",
) -> str:
    """
    Upload a single file to Google Cloud Storage.

    Args:
        file_path: Local file path
        settings: Application settings
        bucket_name: GCS bucket name

    Returns:
        GCS URI (gs://bucket/path)
    """
    try:
        storage_client = storage.Client(project=settings.google_cloud_project)
        bucket = storage_client.bucket(bucket_name)

        # Use original filename for better organization
        blob_name = f"curriculum/{file_path.name}"
        blob = bucket.blob(blob_name)

        if not blob.exists():
            logger.info("Uploading to GCS", file=file_path.name)
            blob.upload_from_filename(str(file_path))
        else:
            logger.info("File already in GCS", file=file_path.name)

        gcs_uri = f"gs://{bucket_name}/{blob_name}"
        return gcs_uri

    except Exception as e:
        logger.error("GCS upload failed", file=file_path.name, error=str(e))
        raise DatastoreUploadError(f"Failed to upload {file_path.name}: {e}") from e


async def upload_to_datastore(
    files: list[Path],
    settings: Settings,
) -> dict[str, str]:
    """
    Upload files to Vertex AI Search datastore.

    This makes files searchable via the VertexAISearchTool in agents.

    Args:
        files: List of curriculum files (PDFs, DOCX, etc.)
        settings: Application settings

    Returns:
        Dictionary mapping filename to document ID

    Raises:
        DatastoreUploadError: If upload fails

    Example:
        >>> files = [Path("textbook.pdf"), Path("syllabus.docx")]
        >>> result = await upload_to_datastore(files, get_settings())
        >>> # Files are now searchable in Vertex AI Search
    """
    try:
        # Initialize Discovery Engine client
        client = discoveryengine.DocumentServiceClient()

        # Parse datastore ID to get parent path
        # Format: projects/{project}/locations/{location}/collections/{collection}/dataStores/{datastore}
        settings.vertex_ai_search_datastore_id.split("/")
        parent = f"{settings.vertex_ai_search_datastore_id}/branches/default_branch"

        uploaded_docs = {}

        for file_path in files:
            # Validate file
            if not file_path.exists():
                logger.warning("File not found", file=str(file_path))
                continue

            if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                logger.warning(
                    "Unsupported file type",
                    file=file_path.name,
                    type=file_path.suffix,
                )
                continue

            logger.info("Processing file for datastore", file=file_path.name)

            # 1. Upload to GCS (required for Vertex AI Search)
            gcs_uri = await upload_file_to_gcs(file_path, settings)

            # 2. Create document in datastore
            doc_id = file_path.stem  # Use filename without extension as ID

            document = discoveryengine.Document(
                id=doc_id,
                content=discoveryengine.Document.Content(
                    uri=gcs_uri,
                    mime_type=_get_mime_type(file_path),
                ),
                # Optional: Add metadata
                struct_data={
                    "title": file_path.name,
                    "file_type": file_path.suffix,
                },
            )

            # 3. Import into datastore
            request = discoveryengine.CreateDocumentRequest(
                parent=parent,
                document=document,
                document_id=doc_id,
            )

            try:
                response = client.create_document(request=request)
                uploaded_docs[file_path.name] = response.name
                logger.info(
                    "✅ File indexed in datastore",
                    file=file_path.name,
                    doc_id=doc_id,
                )
            except Exception as e:
                # Document might already exist
                if "already exists" in str(e).lower():
                    logger.info("Document already exists", file=file_path.name)
                    uploaded_docs[file_path.name] = doc_id
                else:
                    raise

        logger.info(
            "Datastore upload complete",
            total_files=len(files),
            uploaded=len(uploaded_docs),
        )

        return uploaded_docs

    except Exception as e:
        logger.error("Datastore upload failed", error=str(e))
        raise DatastoreUploadError(f"Upload failed: {e}") from e


def _get_mime_type(file_path: Path) -> str:
    """Get MIME type for file."""
    mime_types = {
        ".pdf": "application/pdf",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".html": "text/html",
    }
    return mime_types.get(file_path.suffix.lower(), "application/octet-stream")
