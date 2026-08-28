"""Compliance module: ROPA, DSR, document versioning.

This module owns the Record of Processing Activities (ROPA), the Data
Subject Rights (DSR) intake and workflow, the published-document
registry used by ``apps.tenancy`` for versioned legal acceptances,
and the platform-side helpers that the legal policies describe.

It does not produce legal text; it is the platform surface that legal
text binds to.
"""
