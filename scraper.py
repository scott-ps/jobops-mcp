import logging
import httpx
from bs4 import BeautifulSoup
import ipaddress
import socket
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Standard browser headers so career boards (Greenhouse, Lever) don't block the request
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

MAX_REDIRECTS = 5

def _resolve_and_check(hostname: str) -> bool:
    """Resolve hostname; reject if ANY resolved address is private/internal.

    Checking every address (not just the first) matters because a hostname
    can round-robin between a public and a private IP.
    """
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        return False
    if not infos:
        return False
    for info in infos:
        ip_str = info[4][0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            return False
        if (ip.is_private or ip.is_loopback or ip.is_link_local
                or ip.is_reserved or ip.is_multicast or ip.is_unspecified):
            return False
    return True

def _is_url_allowed(url: str) -> bool:
    """Only allow http(s) URLs that resolve to public, non-internal addresses."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False
    if not parsed.hostname:
        return False
    return _resolve_and_check(parsed.hostname)

def fetch_job_content(url: str, max_chars: int = 8000) -> str:
    """
    Fetch a job posting webpage, strip out navigation/scripts,
    and return clean text content.
    """
    logger.info(f"Fetching URL: {url}")

    if not _is_url_allowed(url):
        logger.warning(f"SECURITY: Blocked request to disallowed URL: {url}")
        return "Error: This URL is not allowed (must be http/https and resolve to a public address)."

    try:
        with httpx.Client(headers=HEADERS, follow_redirects=False, timeout=10.0) as client:
            current_url = url
            for _ in range(MAX_REDIRECTS):
                response = client.get(current_url)
                if response.is_redirect:
                    next_url = str(response.next_request.url)
                    if not _is_url_allowed(next_url):
                        logger.warning(f"SECURITY: Blocked redirect to disallowed URL: {next_url}")
                        return "Error: This URL redirected to a disallowed address."
                    current_url = next_url
                    continue
                response.raise_for_status()
                break
            else:
                logger.warning(f"Too many redirects fetching {url}")
                return "Error: Too many redirects."
    except httpx.HTTPStatusError as e:
        logger.warning(f"HTTP error {e.response.status_code} fetching {url}")
        return f"Error: Server returned HTTP status {e.response.status_code}."
    except httpx.RequestError as e:
        logger.warning(f"Network error fetching {url}: {e}")
        return f"Error: Could not reach URL ({type(e).__name__})."
    except Exception as e:
        logger.error(f"Unexpected error fetching {url}: {e}")
        return f"Error: Failed to fetch webpage ({str(e)})."

    # Parse HTML and strip noisy elements
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Remove scripts, styles, headers, footers, and nav bars
    for element in soup(["script", "style", "nav", "footer", "header", "noscript", "svg"]):
        element.decompose()

    # Extract clean text with newlines
    text = soup.get_text(separator="\n", strip=True)
    
    # Consolidate excessive blank lines
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    cleaned_text = "\n".join(lines)

    if not cleaned_text:
        return "Warning: Webpage was fetched, but no readable text was found."

    # Prevent massive pages from overflowing the model's context window
    if len(cleaned_text) > max_chars:
        cleaned_text = cleaned_text[:max_chars] + f"\n\n[... Truncated: Exceeded {max_chars} characters ...]"

    logger.info(f"Successfully extracted {len(cleaned_text)} characters from {url}")
    return cleaned_text