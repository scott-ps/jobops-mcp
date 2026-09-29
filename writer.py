"""Saves AI-generated documents (cover letters, prep notes) as Markdown files."""

import logging
import os
import re

import config

logger = logging.getLogger(__name__)

# Generated documents live in the data folder (see config.py)
OUTPUT_DIR = os.path.join(config.data_dir(), "output")


def sanitize_name(name: str) -> str:
    """
    Sanitize folder/file names to prevent Directory Traversal attacks
    and invalid Windows/Linux filesystem characters.
    """
    # Remove path separators (/ \) and characters Windows doesn't allow in names
    clean = re.sub(r'[\/\\:\*\?"<>\|]', '', name)

    # Remove ".." so the name can't point at a parent folder
    clean = clean.replace('..', '').strip()

    # Fall back to a placeholder if nothing is left after cleaning
    return clean or "unknown"


def save_document(company: str, doc_type: str, content: str, output_base: str = OUTPUT_DIR) -> str:
    """
    Save a generated Markdown document into an organized output/<company>/ directory.
    """
    # output_base is a parameter so tests can write to a temporary folder
    safe_company = sanitize_name(company)
    safe_doc_type = sanitize_name(doc_type)

    if not safe_doc_type.endswith(".md"):
        safe_doc_type += ".md"

    # Construct target folder: output/<company>/
    target_dir = os.path.join(output_base, safe_company)
    target_path = os.path.join(target_dir, safe_doc_type)

    # Security Check: Ensure the resolved path stays strictly within the output directory.
    # sanitize_name should already prevent an escape; this is a second line of defense.
    resolved_path = os.path.abspath(target_path)
    resolved_base = os.path.abspath(output_base)
    if not resolved_path.startswith(resolved_base):
        logger.warning(f"SECURITY: Attempted path traversal write blocked: {target_path}")
        return "Error: Security violation - invalid directory path."

    try:
        os.makedirs(target_dir, exist_ok=True)

        # "w" mode overwrites any existing document with the same name
        with open(resolved_path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"AUDIT: Document saved successfully at {resolved_path}")

        # Report the path relative to the output folder (e.g. output/Acme/cover_letter.md)
        # rather than the full path on disk, which varies with JOBOPS_DATA_DIR
        saved_as = os.path.join("output", os.path.relpath(resolved_path, resolved_base))
        return f"Document successfully saved to '{saved_as}'."

    except Exception as e:
        logger.error(f"Failed to write document to {resolved_path}: {e}")
        return f"Error: Could not save document ({str(e)})."
