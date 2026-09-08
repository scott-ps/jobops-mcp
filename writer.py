import os
import re
import logging

logger = logging.getLogger(__name__)

# Anchor the output directory to the project root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

def sanitize_name(name: str) -> str:
    """
    Sanitize folder/file names to prevent Directory Traversal attacks
    and invalid Windows/Linux filesystem characters.
    """
    # Remove any path traversal sequences and special characters
    clean = re.sub(r'[\/\\:\*\?"<>\|]', '', name)
    clean = clean.replace('..', '').strip()
    # Replace spaces with underscores for clean CLI compatibility
    return clean or "unknown"

def save_document(company: str, doc_type: str, content: str, output_base: str = OUTPUT_DIR) -> str:
    """
    Save a generated Markdown document into an organized output/<company>/ directory.
    """
    safe_company = sanitize_name(company)
    safe_doc_type = sanitize_name(doc_type)

    if not safe_doc_type.endswith(".md"):
        safe_doc_type += ".md"

    # Construct target folder: output/<company>/
    target_dir = os.path.join(output_base, safe_company)
    target_path = os.path.join(target_dir, safe_doc_type)

    # Security Check: Ensure the resolved path stays strictly within the output directory
    resolved_path = os.path.abspath(target_path)
    resolved_base = os.path.abspath(output_base)
    if not resolved_path.startswith(resolved_base):
        logger.warning(f"SECURITY: Attempted path traversal write blocked: {target_path}")
        return "Error: Security violation - invalid directory path."

    try:
        os.makedirs(target_dir, exist_ok=True)
        with open(resolved_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"AUDIT: Document saved successfully at {resolved_path}")
        return f"Document successfully saved to '{os.path.relpath(resolved_path, BASE_DIR)}'."

    except Exception as e:
        logger.error(f"Failed to write document to {resolved_path}: {e}")
        return f"Error: Could not save document ({str(e)})."