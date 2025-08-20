from PyPDF2 import PdfReader

def extract_pdf_text(local_path: str) -> str:
    """Extract text from a PDF file saved on the server."""
    try:
        reader = PdfReader(local_path)
        parts = []
        for p in reader.pages:
            t = p.extract_text() or ""
            if t:
                parts.append(t)
        return "\n\n".join(parts).strip()
    except Exception as e:
        return f"[PDF read error: {e}]"
