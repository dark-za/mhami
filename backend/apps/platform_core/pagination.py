"""Shared pagination for keyed list envelopes.

The platform's list endpoints return keyed envelopes (``{"instances":
[...]}``, ``{"items": [...]}``) rather than bare arrays or DRF's default
``{count, next, previous, results}`` shape, so the frontend contract is
preserved while still bounding how many rows a single request can fetch.
"""

from __future__ import annotations

from typing import Any, Sequence

from rest_framework.pagination import PageNumberPagination

DEFAULT_API_PAGE_SIZE = 50


def paginate_sequence(
    items: Sequence[Any],
    request,
    *,
    page_size: int = DEFAULT_API_PAGE_SIZE,
) -> tuple[list[Any], dict[str, int]]:
    """Slice ``items`` to the requested page.

    Args:
        items: A queryset or any sized, sliceable sequence.
        request: The current DRF request (``?page=`` is honoured).
        page_size: Rows per page (defaults to :data:`DEFAULT_API_PAGE_SIZE`).

    Returns:
        ``(page_items, stats)`` where ``stats`` carries ``page``,
        ``pages``, and ``total`` to merge into the response envelope.

    Raises:
        NotFound: If ``?page=`` is out of range (DRF default behaviour).
    """
    paginator = PageNumberPagination()
    paginator.page_size = page_size
    page = paginator.paginate_queryset(items, request)
    return list(page), {
        "page": paginator.page.number,
        "pages": paginator.page.paginator.num_pages,
        "total": paginator.page.paginator.count,
    }
