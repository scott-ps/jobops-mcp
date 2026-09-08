from unittest.mock import patch, MagicMock
import httpx
import scraper
import socket
import pytest

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

@patch("scraper._is_url_allowed", return_value=True)
def test_fetch_job_content_success(mock_url_check):
    """Verify that HTML is parsed and noisy tags (nav, footer, script) are removed."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = MOCK_JOB_HTML
    mock_response.raise_for_status = MagicMock()
    mock_response.is_redirect = False

    with patch("httpx.Client.get", return_value=mock_response):
        result = scraper.fetch_job_content("https://example.com/jobs/123")
        
        # Verify core content was extracted
        assert "Senior Automation Engineer" in result
        assert "We are looking for a Python and CI/CD specialist." in result
        
        # Verify noise tags were stripped
        assert "var tracking = true" not in result
        assert "Home | Careers | About" not in result
        assert "Copyright 2026 Acme Corp" not in result

@patch("scraper._is_url_allowed", return_value=True)
def test_fetch_job_content_http_error(mock_url_check):
    """Verify that a 404 response is handled gracefully without crashing."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    http_error = httpx.HTTPStatusError("Not Found", request=MagicMock(), response=mock_response)

    with patch("httpx.Client.get", side_effect=http_error):
        result = scraper.fetch_job_content("https://example.com/jobs/invalid")
        assert "Error: Server returned HTTP status 404" in result

def _mock_addrinfo(ip):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 0))]

@pytest.mark.parametrize("url,resolved_ip,allowed", [
    ("https://boards.greenhouse.io/example", "93.184.216.34", True),   # public IP
    ("http://169.254.169.254/latest/meta-data/", "169.254.169.254", False),  # cloud metadata
    ("http://internal.corp/", "10.0.0.5", False),                      # RFC1918
    ("http://localhost:8080/", "127.0.0.1", False),                    # loopback
])
@patch("socket.getaddrinfo")
def test_is_url_allowed_dns(mock_getaddrinfo, url, resolved_ip, allowed):
    mock_getaddrinfo.return_value = _mock_addrinfo(resolved_ip)
    assert scraper._is_url_allowed(url) == allowed

@pytest.mark.parametrize("url", [
    "ftp://example.com/",
    "file:///etc/passwd",
    "javascript:alert(1)",
])
def test_is_url_allowed_bad_scheme(url):
    # Rejected on scheme alone -- DNS should never even be touched
    with patch("socket.getaddrinfo") as mock_getaddrinfo:
        assert scraper._is_url_allowed(url) is False
        mock_getaddrinfo.assert_not_called()

@patch("scraper._is_url_allowed")
def test_fetch_job_content_blocks_unsafe_redirect(mock_url_check):
    """Initial URL passes, but it 302s to an internal address -- must be blocked."""
    mock_url_check.side_effect = [True, False]  # 1st call: initial url OK, 2nd: redirect target blocked

    redirect_response = MagicMock()
    redirect_response.is_redirect = True
    redirect_response.next_request.url = "http://169.254.169.254/latest/meta-data/"

    with patch("httpx.Client.get", return_value=redirect_response):
        result = scraper.fetch_job_content("https://example.com/jobs/123")
        assert "Error: This URL redirected to a disallowed address." in result