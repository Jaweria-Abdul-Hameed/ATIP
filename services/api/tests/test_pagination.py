"""Tests for pagination calculations, headers, and metadata."""

from atip_api.core.pagination import PaginationMetadata, PaginationParams


def test_pagination_params_offset_limit() -> None:
    p1 = PaginationParams(page=1, page_size=20)
    assert p1.offset == 0
    assert p1.limit == 20

    p2 = PaginationParams(page=3, page_size=15)
    assert p2.offset == 30
    assert p2.limit == 15


def test_pagination_metadata_first_page() -> None:
    meta = PaginationMetadata.create(page=1, page_size=20, total_items=45)
    assert meta.page == 1
    assert meta.page_size == 20
    assert meta.total_items == 45
    assert meta.total_pages == 3
    assert meta.has_next is True
    assert meta.has_prev is False


def test_pagination_metadata_last_page() -> None:
    meta = PaginationMetadata.create(page=3, page_size=20, total_items=45)
    assert meta.page == 3
    assert meta.total_pages == 3
    assert meta.has_next is False
    assert meta.has_prev is True


def test_pagination_metadata_empty() -> None:
    meta = PaginationMetadata.create(page=1, page_size=20, total_items=0)
    assert meta.total_items == 0
    assert meta.total_pages == 0
    assert meta.has_next is False
    assert meta.has_prev is False
