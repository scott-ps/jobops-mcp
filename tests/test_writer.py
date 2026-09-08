import os
import writer

def test_save_document_success(tmp_path):
    """Verify that documents are saved correctly to disk in the company subfolder."""
    test_output_dir = str(tmp_path / "output")
    content = "# Cover Letter for Acme Corp\n\nI am excited to apply..."
    
    result = writer.save_document(
        company="Acme Corp", 
        doc_type="cover_letter", 
        content=content, 
        output_base=test_output_dir
    )
    
    # Verify success response
    assert "Document successfully saved" in result
    
    # Verify file exists on disk and content matches
    expected_file = os.path.join(test_output_dir, "Acme Corp", "cover_letter.md")
    assert os.path.exists(expected_file)
    with open(expected_file, "r", encoding="utf-8") as f:
        assert f.read() == content

def test_save_document_path_traversal_protection(tmp_path):
    """Verify that dangerous directory traversal inputs are sanitized or blocked."""
    test_output_dir = str(tmp_path / "output")
    content = "Malicious content"
    
    # Attempt to break out of the directory with traversal characters
    result = writer.save_document(
        company="../../../etc", 
        doc_type="passwd", 
        content=content, 
        output_base=test_output_dir
    )
    
    # Sanitization should clean the name and keep it safely inside the test output directory
    assert "Document successfully saved" in result
    escaped_file = os.path.join(test_output_dir, "etc", "passwd.md")
    assert os.path.exists(escaped_file)
    
    # Ensure it did NOT write to the root filesystem
    assert not os.path.exists("/etc/passwd.md")