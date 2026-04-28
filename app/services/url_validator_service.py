import httpx
import ssl
import socket
from typing import Dict, Any, Optional
from urllib.parse import urlparse, urljoin
import re


class URLValidator:
    """Service to validate and authenticate company URLs"""

    def __init__(self):
        self.timeout = 15.0

    async def validate_and_authenticate_url(self, url: str) -> Dict[str, Any]:
        """
        Comprehensive URL validation and authentication check
        
        Returns:
            {
                "is_valid": bool,
                "authenticated_url": str (normalized URL with https),
                "is_reachable": bool,
                "status_code": int,
                "ssl_valid": bool,
                "domain": str,
                "errors": [list of issues],
                "warnings": [list of warnings]
            }
        """
        result = {
            "is_valid": False,
            "authenticated_url": None,
            "is_reachable": False,
            "status_code": None,
            "ssl_valid": False,
            "domain": None,
            "errors": [],
            "warnings": [],
            "response_headers": {}
        }

        try:
            # Step 1: Normalize URL
            normalized_url = self._normalize_url(url)
            if not normalized_url:
                result["errors"].append("Invalid URL format")
                return result

            result["authenticated_url"] = normalized_url

            # Step 2: Extract domain
            parsed = urlparse(normalized_url)
            domain = parsed.netloc
            result["domain"] = domain

            # Step 3: Check SSL certificate validity
            ssl_valid = await self._check_ssl_certificate(domain)
            result["ssl_valid"] = ssl_valid
            if not ssl_valid:
                result["warnings"].append("SSL certificate invalid or self-signed")

            # Step 4: Check if URL is reachable
            is_reachable, status_code, headers = await self._check_url_reachable(normalized_url)
            result["is_reachable"] = is_reachable
            result["status_code"] = status_code
            result["response_headers"] = headers

            if not is_reachable:
                result["errors"].append(f"URL not reachable (Status: {status_code})")
                return result

            # Step 5: Check for redirect chains (potential phishing)
            redirect_issues = await self._check_redirect_chain(normalized_url)
            if redirect_issues:
                result["warnings"].extend(redirect_issues)

            # Step 6: Validate domain reputation
            domain_check = self._check_domain_reputation(domain)
            if domain_check["suspicious"]:
                result["warnings"].extend(domain_check["issues"])

            # Step 7: Final validation
            result["is_valid"] = (
                is_reachable and
                (ssl_valid or self._is_localhost_or_internal(domain))
            )

            if result["is_valid"]:
                result["message"] = "✅ URL authenticated successfully"
            else:
                if not is_reachable:
                    result["message"] = "❌ URL is not reachable"
                elif not ssl_valid and not self._is_localhost_or_internal(domain):
                    result["message"] = "⚠️ SSL certificate issue detected"

            return result

        except Exception as e:
            result["errors"].append(f"Validation error: {str(e)}")
            return result

    def _normalize_url(self, url: str) -> Optional[str]:
        """
        Normalize URL to ensure it's properly formatted
        - Add https:// if protocol is missing
        - Remove whitespace
        - Validate format
        """
        if not url:
            return None

        url = url.strip()

        # Check for valid URL format
        if not re.match(r"^https?://|^www\.|^[a-zA-Z0-9]", url):
            return None

        # Add https:// if no protocol
        if not url.startswith(("http://", "https://")):
            if url.startswith("www."):
                url = "https://" + url
            else:
                url = "https://" + url

        # Basic URL format validation
        try:
            parsed = urlparse(url)
            if not parsed.netloc:
                return None
            return url
        except:
            return None

    async def _check_ssl_certificate(self, domain: str) -> bool:
        """Check if SSL certificate is valid for the domain"""
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    return cert is not None
        except (ssl.SSLError, socket.gaierror, socket.timeout, ConnectionRefusedError):
            return False
        except Exception:
            return False

    async def _check_url_reachable(self, url: str) -> tuple:
        """
        Check if URL is reachable and returns status code
        Returns: (is_reachable, status_code, headers)
        """
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                verify=False  # Allow self-signed certs for now
            ) as client:
                response = await client.head(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                )

                # If HEAD fails, try GET
                if response.status_code >= 400:
                    response = await client.get(
                        url,
                        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
                        follow_redirects=True
                    )

                is_reachable = 200 <= response.status_code < 400
                return (
                    is_reachable,
                    response.status_code,
                    dict(response.headers)
                )

        except Exception as e:
            return False, None, {}

    async def _check_redirect_chain(self, url: str) -> list:
        """Check for suspicious redirect chains"""
        warnings = []
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                verify=False
            ) as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0"},
                    follow_redirects=False
                )

                if response.status_code in [301, 302, 303, 307, 308]:
                    redirect_url = response.headers.get("location", "")
                    if redirect_url:
                        original_domain = urlparse(url).netloc
                        redirect_domain = urlparse(redirect_url).netloc

                        if original_domain != redirect_domain:
                            warnings.append(
                                f"⚠️ Redirects to different domain: {redirect_domain}"
                            )

        except Exception:
            pass

        return warnings

    def _check_domain_reputation(self, domain: str) -> Dict[str, Any]:
        """
        Basic domain reputation check
        Returns: {"suspicious": bool, "issues": [list]}
        """
        issues = []
        suspicious = False

        # Check for suspicious patterns
        suspicious_patterns = [
            r"bit\.ly",
            r"short\.link",
            r"tinyurl",
            r"-[a-z0-9]{10,}\.",
            r"xn--",  # IDN homoglyph attacks
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, domain, re.IGNORECASE):
                issues.append(f"Suspicious domain pattern detected: {pattern}")
                suspicious = True

        # Check for common phishing TLDs
        phishing_tlds = [".tk", ".ml", ".ga", ".cf"]
        for tld in phishing_tlds:
            if domain.endswith(tld):
                issues.append(f"Domain uses commonly abused TLD: {tld}")
                suspicious = True

        return {"suspicious": suspicious, "issues": issues}

    def _is_localhost_or_internal(self, domain: str) -> bool:
        """Check if domain is localhost or internal network"""
        internal_patterns = [
            "localhost",
            "127.0.0.1",
            "192.168.",
            "10.",
            "172.16.",
            ".local",
            ".internal",
        ]
        return any(pattern in domain.lower() for pattern in internal_patterns)

    async def get_authenticated_url(self, url: str) -> Optional[str]:
        """
        Validate URL and return authenticated URL
        Returns None if URL is not authentic
        """
        result = await self.validate_and_authenticate_url(url)
        if result["is_valid"]:
            return result["authenticated_url"]
        return None

    def get_safe_domain(self, url: str) -> Optional[str]:
        """Extract domain from URL safely"""
        try:
            normalized = self._normalize_url(url)
            if normalized:
                parsed = urlparse(normalized)
                return parsed.netloc
            return None
        except:
            return None


# Create singleton instance
url_validator = URLValidator()
