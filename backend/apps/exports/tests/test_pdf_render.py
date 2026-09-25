"""Render tests for the Arabic-capable PDF summary artifact."""

from __future__ import annotations

from apps.exports.services import _pdf_bytes


def test_pdf_bytes_is_valid_pdf_with_embedded_unicode_font():
    pdf = _pdf_bytes("تقرير المهام", ["عدد المهام: 12", "حالة التنفيذ: مكتمل"])
    assert pdf.startswith(b"%PDF")
    assert b"%%EOF" in pdf
    assert b"/FontFile2" in pdf


def test_pdf_bytes_renders_latin_lines_too():
    pdf = _pdf_bytes("Export ABC", ["Rows: 3", "Branches: 1"])
    assert pdf.startswith(b"%PDF")
    assert b"/FontFile2" in pdf
    assert len(pdf) > 5000


def test_pdf_bytes_embeds_arabic_glyphs_not_replacement_chars():
    arabic = _pdf_bytes("مصرف النور", ["تحويل الحساب"])
    assert "�".encode("utf-16-be") not in arabic
    assert len(arabic) > 5000
