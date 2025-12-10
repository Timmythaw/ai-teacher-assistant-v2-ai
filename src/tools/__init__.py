"""
AI Teaching Assistant Tools.

This module contains specialized tools for the agents:
- datastore_upload: Tool to upload curriculum files to Vertex AI Search datastore.
- google_search: Tool to perform Google searches for supplementary resources.
"""

from src.tools.datastore_upload import upload_to_datastore
from src.tools.search_tool import create_resource_search_query

__all__ = [
    "create_resource_search_query",
    "upload_to_datastore",
]
