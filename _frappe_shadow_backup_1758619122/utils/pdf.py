"""PDF utilities for the frappe shim."""

from __future__ import annotations


def get_pdf(html: str) -> bytes:
	"""Return bytes representing the rendered PDF.

	Generating actual PDFs is unnecessary for the unit tests; returning the
	encoded HTML keeps the behaviour deterministic and sufficient for code
	that merely verifies that ``get_pdf`` was invoked.
	"""

	return html.encode("utf-8")
