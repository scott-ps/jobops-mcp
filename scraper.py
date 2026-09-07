import logging
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Standard browser headers so career boards (Greenhouse, Lever) don't block the request
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def fetch_job_content(url: str, max_chars: int = 8000) -> str:
    """
    Fetch a job posting webpage, strip out navigation/scripts,
    and return clean text content.
    """
    logger.info(f"Fetching URL: {url}")
    
    try:
        with httpx.Client(headers=HEADERS, follow_redirects=True, timeout=10.0) as client:
            response = client.get(url)
            response.raise_for_status()
            
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