import httpx
import re
from typing import Optional, List
from urllib.parse import urljoin, urlparse
import logging

logger = logging.getLogger(__name__)


class GoogleSearchService:
    """Service to search Google and extract company URLs"""

    def __init__(self):
        self.timeout = 10
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    async def search_company_url(self, query: str) -> Optional[str]:
        """
        Search for a company URL.
        
        Priority:
          1. If query is already a valid URL/domain → use directly
          2. Try common TLDs directly (.com, .io, .co, .net, .org)
          3. Fall back to Google search HTML scraping
        """
        try:
            # Already a URL/domain?
            if self._is_valid_url(query):
                return self._normalize_url(query)

            # ── Fast path: guess TLD ──────────────────────────────────────────
            # Strip spaces and lowercase; try the most common TLDs
            name = query.strip().lower().replace(" ", "")
            candidate_tlds = [".com", ".io", ".co", ".net", ".org", ".ai", ".app"]

            async with httpx.AsyncClient(
                timeout=5,
                headers=self.headers,
                follow_redirects=True
            ) as client:
                for tld in candidate_tlds:
                    candidate = f"https://{name}{tld}"
                    try:
                        resp = await client.head(candidate)
                        # Accept any 2xx or 3xx — means the site exists
                        if resp.status_code < 500:
                            print(f"✅ [google_search] Direct domain hit: {candidate} ({resp.status_code})")
                            return candidate
                    except Exception:
                        continue  # unreachable → try next TLD

            # ── Fallback: Google search scrape ───────────────────────────────
            print(f"🔍 [google_search] Falling back to Google for: {query}")
            search_url = f"https://www.google.com/search?q={query}+official+website"

            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers, follow_redirects=True) as client:
                response = await client.get(search_url)
                if response.status_code == 200:
                    urls = self._extract_urls_from_html(response.text, query)
                    if urls:
                        return self._normalize_url(urls[0])

            return None

        except Exception as e:
            logger.error(f"Error searching for {query}: {str(e)}")
            return None

    def _is_valid_url(self, url: str) -> bool:
        """Check if string is a valid URL or domain"""
        try:
            url = url.strip().lower()
            
            # Already has scheme
            if url.startswith(('http://', 'https://')):
                return True
            
            # Starts with www
            if url.startswith('www.'):
                return True
            
            # Check for domain pattern (e.g., "akij.com", "example.co.uk")
            # Must have at least one dot and valid domain characters
            if '.' in url:
                parts = url.split('.')
                # Need at least 2 parts (e.g., "akij" and "com")
                if len(parts) >= 2:
                    # Check if parts are valid (alphanumeric and hyphens)
                    for part in parts:
                        if not part or not all(c.isalnum() or c == '-' for c in part):
                            return False
                    return True
            
            return False
        except:
            return False

    def _normalize_url(self, url: str) -> str:
        """Normalize URL to ensure it has a scheme"""
        url = url.strip()
        
        # If it doesn't start with http/https, add https
        if not url.startswith(('http://', 'https://')):
            # If it starts with www, assume https
            if url.startswith('www.'):
                url = 'https://' + url
            else:
                # Try with https first
                url = 'https://' + url
        
        return url

    def _extract_urls_from_html(self, html: str, query: str) -> List[str]:
        """Extract URLs from Google search results HTML.
        
        Stage 1: URLs whose domain matches the query (strict).
        Stage 2: Any first valid non-Google URL (fuzzy fallback for short company names).
        """
        matched_urls: List[str] = []
        fallback_urls: List[str] = []

        url_pattern = r'href="(https?://[^"&<>]*)"'
        matches = re.findall(url_pattern, html)

        SKIP_DOMAINS = [
            'google.com', 'webcache.googleusercontent.com',
            'translate.google', '/url?q=', 'support.google',
            'accounts.google', 'maps.google', 'play.google',
            'youtube.com', 'facebook.com', 'twitter.com',
            'linkedin.com', 'instagram.com', 'wikipedia.org',
            'bing.com', 'yahoo.com', 'amazon.com', 'reddit.com',
        ]

        query_terms = [t.lower() for t in query.split() if len(t) > 2]

        for match in matches:
            if any(skip in match for skip in SKIP_DOMAINS):
                continue

            clean_url = match.split('&')[0] if '&' in match else match

            try:
                parsed = urlparse(clean_url)
                if not parsed.netloc:
                    continue
                domain = parsed.netloc.replace('www.', '').lower()

                # Stage 1: domain contains any query term
                if query_terms and any(term in domain for term in query_terms):
                    if clean_url not in matched_urls:
                        matched_urls.append(clean_url)

                # Stage 2: collect any valid URL as fallback
                if clean_url not in fallback_urls:
                    fallback_urls.append(clean_url)

            except Exception:
                continue

        # Return matched if found, otherwise first few fallback URLs
        return (matched_urls or fallback_urls)[:5]


# Create singleton instance
google_search_service = GoogleSearchService()
