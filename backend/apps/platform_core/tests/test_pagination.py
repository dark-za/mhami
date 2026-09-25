"""Unit tests for the keyed-envelope pagination helper."""

from __future__ import annotations

import pytest
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from apps.platform_core.pagination import paginate_sequence


def _request(path: str = "/", data: dict | None = None) -> Request:
    return Request(APIRequestFactory().get(path, data or {}))


def test_first_page_caps_at_page_size():
    request = _request()
    page, stats = paginate_sequence(list(range(120)), request)
    assert len(page) == 50
    assert stats == {"page": 1, "pages": 3, "total": 120}


def test_second_page_slice():
    request = _request(data={"page": 2})
    page, stats = paginate_sequence(list(range(120)), request)
    assert page[0] == 50
    assert len(page) == 50
    assert stats["page"] == 2


def test_final_partial_page():
    request = _request(data={"page": 3})
    page, stats = paginate_sequence(list(range(120)), request)
    assert len(page) == 20
    assert stats == {"page": 3, "pages": 3, "total": 120}


def test_empty_sequence_has_single_empty_page():
    request = _request()
    page, stats = paginate_sequence([], request)
    assert page == []
    assert stats == {"page": 1, "pages": 1, "total": 0}


def test_out_of_range_page_raises_not_found():
    request = _request(data={"page": 99})
    with pytest.raises(NotFound):
        paginate_sequence(list(range(10)), request)
