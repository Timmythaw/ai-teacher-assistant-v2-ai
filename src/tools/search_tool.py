# src/tools/search_tool.py
"""
Web search tools for finding educational resources.

Uses Google Search via ADK to find relevant videos, articles, and
interactive resources to supplement lesson plans.
"""

from typing import Any

from google.adk.tools.google_search_tool import google_search

from src.schemas.lesson_plan import ResourceLink, ResourceType
from src.utils.logger import logger


class ResourceSearchTool:
    """
    Wrapper for Google Search to find educational resources.

    Provides structured search for videos, articles, and interactive content
    relevant to lesson topics.
    """

    def __init__(self) -> None:
        """Initialize the search tool."""
        # google_search is a built-in tool, ready to use
        self._search_tool = google_search
        logger.info("ResourceSearchTool initialized")

    def build_search_query(self, topic: str, grade: str, resource_type: ResourceType) -> str:
        """
        Build optimized search query for resource type.

        Args:
            topic: Subject/topic to search for
            grade: Grade level for appropriate content
            resource_type: Type of resource (video, article, etc.)

        Returns:
            Optimized search query string
        """
        type_keywords = {
            ResourceType.VIDEO: "educational video tutorial",
            ResourceType.ARTICLE: "lesson article guide",
            ResourceType.INTERACTIVE: "interactive simulation game",
            ResourceType.DATASET: "dataset download data",
            ResourceType.TOOL: "educational tool software",
        }

        keywords = type_keywords.get(resource_type, "educational resource")
        query = f"{topic} {grade} {keywords}"

        logger.debug("Built search query", query=query, type=resource_type.value)
        return query

    def parse_search_results(
        self, results: list[dict[str, Any]], resource_type: ResourceType
    ) -> list[ResourceLink]:
        """
        Parse raw search results into ResourceLink objects.

        Args:
            results: Raw search results from google_search tool
            resource_type: Type of resource being searched

        Returns:
            List of parsed ResourceLink objects
        """
        parsed_links: list[ResourceLink] = []

        for result in results[:5]:
            try:
                # Get URL from result (try both common keys)
                url = result.get("url") or result.get("link")
                if not url:
                    logger.warning("Search result missing URL", result_title=result.get("title"))
                    continue

                # Parse based on typical search result structure
                resource = ResourceLink(
                    title=result.get("title", "Untitled Resource"),
                    url=url,
                    type=resource_type,
                    description=result.get("snippet", "")[:200],  # Truncate long descriptions
                    recommended_for=[],  # Agent will assign lecture periods
                )
                parsed_links.append(resource)

            except Exception as e:
                logger.warning(
                    "Failed to parse search result",
                    error=str(e),
                    result_title=result.get("title", "unknown"),
                )

        return parsed_links


# ============================================================================
# Simple function for agent tool usage
# ============================================================================


def create_resource_search_query(
    topic: str,
    grade: str,
    resource_type: str = "video",
) -> str:
    """
    Create a search query for educational resources.

    This function is designed to be called by the agent as a tool.

    Args:
        topic: The subject/topic to search for
        grade: Grade level (e.g., "9th grade", "undergraduate")
        resource_type: Type of resource (video, article, interactive, etc.)

    Returns:
        Optimized search query string

    Example:
        >>> query = create_resource_search_query(
        ...     topic="photosynthesis",
        ...     grade="9th grade",
        ...     resource_type="video"
        ... )
        >>> # Returns: "photosynthesis 9th grade educational video tutorial"
    """
    try:
        rt = ResourceType(resource_type.lower())
    except ValueError:
        rt = ResourceType.VIDEO
        logger.warning(f"Invalid resource type '{resource_type}', defaulting to VIDEO")

    tool = ResourceSearchTool()
    return tool.build_search_query(topic, grade, rt)
