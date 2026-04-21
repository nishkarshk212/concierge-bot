# Font mapping - temporarily restored for compatibility
def apply_font(text: str) -> str:
    """Returns text as-is (font styling disabled)."""
    return str(text) if text else ""
