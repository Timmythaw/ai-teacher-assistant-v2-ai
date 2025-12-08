"""
Context caching for uploaded lecture materials.

Handles file uploads and creates Vertex AI context caches for efficient
processing of large documents (textbooks, lecture slides, etc.).
"""

from datetime import timedelta
import hashlib
from pathlib import Path
from typing import Final

from google.cloud import storage  # type: ignore[attr-defined]
import vertexai
from vertexai.generative_models import Content, Part
from vertexai.preview import caching

from src.config.settings import Settings
from src.utils.logger import logger

# Supported file types
SUPPORTED_EXTENSIONS: Final[set[str]] = {".pdf", ".pptx", ".docx", ".txt", ".md"}

# Default cache TTL (1 hour - adjustable based on use case)
DEFAULT_CACHE_TTL: Final[timedelta] = timedelta(hours=1)


class ContextCacheError(Exception):
    """Raised when context caching operations fail."""

    pass


def _compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA256 hash of file for cache deduplication.

    Args:
        file_path: Path to file

    Returns:
        Hex digest of file content
    """
    sha256_hash = hashlib.sha256()
    with file_path.open("rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


async def upload_files_to_gcs(
    files: list[Path],
    settings: Settings,
    bucket_name: str = "teacher-assistant-uploads",
) -> list[str]:
    """
    Upload files to Google Cloud Storage.

    Args:
        files: List of local file paths
        settings: Application settings
        bucket_name: GCS bucket name

    Returns:
        List of GCS URIs (gs://bucket/path)

    Raises:
        ContextCacheError: If upload fails
    """
    try:
        storage_client = storage.Client(project=settings.google_cloud_project)
        bucket = storage_client.bucket(bucket_name)

        gcs_uris = []
        for file_path in files:
            # Validate file
            if not file_path.exists():
                raise ContextCacheError(f"File not found: {file_path}")

            if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                raise ContextCacheError(
                    f"Unsupported file type: {file_path.suffix}. "
                    f"Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
                )

            # Generate unique blob name using hash
            file_hash = _compute_file_hash(file_path)
            blob_name = f"lesson-materials/{file_hash}/{file_path.name}"

            # Check if already uploaded
            blob = bucket.blob(blob_name)
            if not blob.exists():
                logger.info("Uploading file to GCS", file=str(file_path), blob=blob_name)
                blob.upload_from_filename(str(file_path))
            else:
                logger.info("File already exists in GCS", blob=blob_name)

            gcs_uri = f"gs://{bucket_name}/{blob_name}"
            gcs_uris.append(gcs_uri)

        logger.info("All files uploaded", count=len(gcs_uris))
        return gcs_uris

    except Exception as e:
        logger.error("Failed to upload files to GCS", error=str(e))
        raise ContextCacheError(f"GCS upload failed: {e}") from e


async def create_context_cache(
    files: list[Path],
    settings: Settings,
    system_instruction: str | None = None,
    ttl: timedelta = DEFAULT_CACHE_TTL,
) -> str:
    """
    Upload files and create a Vertex AI context cache.

    This allows the agent to reference large documents without re-processing
    them in every request, reducing cost by up to 75%.

    Args:
        files: List of PDF/PPTX/DOCX file paths
        settings: Application settings
        system_instruction: Optional system instruction for the cache
        ttl: Time-to-live for cache (default: 1 hour)

    Returns:
        Cache name/identifier for use in agent requests

    Raises:
        ContextCacheError: If caching fails

    Example:
        >>> cache_id = await create_context_cache(
        ...     files=[Path("lecture_01.pdf"), Path("textbook.pdf")],
        ...     settings=get_settings()
        ... )
        >>> # Now agent can reference this cache
    """
    try:
        # 1. Upload files to GCS
        logger.info("Creating context cache", file_count=len(files))
        gcs_uris = await upload_files_to_gcs(files, settings)

        # 2. Initialize Vertex AI if not already done
        vertexai.init(
            project=settings.google_cloud_project,
            location=settings.google_cloud_region,
        )

        # 3. Create context cache
        default_instruction = (
            "You are analyzing course materials including lecture slides, "
            "textbooks, and curriculum documents. Use these documents to "
            "generate detailed, accurate lesson plans that align with the "
            "content and learning objectives presented in the materials."
        )

        # Convert GCS URIs to Content objects with file_data parts
        contents = [
            Content(parts=[Part.from_uri(uri, mime_type="application/pdf")]) for uri in gcs_uris
        ]

        # Prepare system instruction as Content if provided
        instruction_text = system_instruction or default_instruction
        instruction_content = Content(parts=[Part.from_text(instruction_text)])

        cache = caching.CachedContent.create(
            model_name=settings.specialist_model,
            system_instruction=instruction_content,
            contents=contents,
            ttl=ttl,
            display_name=f"lesson-materials-{Path(files[0]).stem}",
        )

        logger.info(
            "Context cache created successfully",
            cache_name=cache.name,
            file_count=len(files),
            ttl=ttl,
        )

        return cache.name

    except Exception as e:
        logger.error("Failed to create context cache", error=str(e))
        raise ContextCacheError(f"Cache creation failed: {e}") from e


async def get_cache_info(cache_name: str, settings: Settings) -> dict[str, str]:
    """
    Get information about an existing cache.

    Args:
        cache_name: Cache identifier
        settings: Application settings

    Returns:
        Dictionary with cache metadata
    """
    try:
        vertexai.init(
            project=settings.google_cloud_project,
            location=settings.google_cloud_region,
        )

        cache = caching.CachedContent(cached_content_name=cache_name)

        return {
            "name": cache.name,
            "model": cache.model_name,
            "expire_time": str(cache.expire_time),
            "display_name": cache.display_name or "N/A",
        }
    except Exception as e:
        logger.error("Failed to get cache info", cache_name=cache_name, error=str(e))
        raise ContextCacheError(f"Failed to retrieve cache info: {e}") from e


async def delete_cache(cache_name: str, settings: Settings) -> None:
    """
    Delete a context cache.

    Args:
        cache_name: Cache identifier
        settings: Application settings
    """
    try:
        vertexai.init(
            project=settings.google_cloud_project,
            location=settings.google_cloud_region,
        )

        cache = caching.CachedContent(cached_content_name=cache_name)
        cache.delete()  # type: ignore[no-untyped-call]

        logger.info("Context cache deleted", cache_name=cache_name)
    except Exception as e:
        logger.error("Failed to delete cache", cache_name=cache_name, error=str(e))
        raise ContextCacheError(f"Cache deletion failed: {e}") from e
