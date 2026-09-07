from unittest.mock import patch, MagicMock
import httpx
import scraper

# Sample mock HTML representing a typical job board
MOCK_JOB_HTML = """
<!DOCTYPE html>
<html>
<head><title>Job Posting</title><script>var tracking = true;</script></head>
<body>
    <header><nav>Home | Careers | About</nav></header>
    <main>
        <h1>Senior Automation Engineer</h1>
        <p>Location: Remote</p>
        <h2>About the Role</h2>
        <p>We are looking for a Python and CI/CD specialist.</p>
    </main>
    <footer>Copyright 2026 Acme Corp</footer>
</body>
</html>
"""

def test_fetch_job_content_success():
    """Verify that HTML is parsed and noisy tags (nav, footer, script) are removed."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = MOCK_JOB_HTML
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.Client.get", return_value=mock_response):
        result = scraper.fetch_job_content("https://example.com/jobs/123")
        
        # Verify core content was extracted
        assert "Senior Automation Engineer" in result
        assert "We are looking for a Python and CI/CD specialist." in result
        
        # Verify noise tags were stripped
        assert "var tracking = true" not in result
        assert "Home | Careers | About" not in result
        assert "Copyright 2026 Acme Corp" not in result

def test_fetch_job_content_http_error():
    """Verify that a 404 response is handled gracefully without crashing."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    http_error = httpx.HTTPStatusError("Not Found", request=MagicMock(), response=mock_response)

    with patch("httpx.Client.get", side_effect=http_error):
        result = scraper.fetch_job_content("https://example.com/jobs/invalid")
        assert "Error: Server returned HTTP status 404" in result