"""
URL Validation Utility Functions
Helper functions for integrating URL validation in various parts of the application
"""

from app.services.url_validator_service import url_validator
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class URLValidationHelper:
    """Helper class for URL validation operations"""

    @staticmethod
    async def validate_and_get_url(user_input: str) -> Optional[str]:
        """
        Validate user input and return authenticated URL, or None if invalid
        
        Args:
            user_input: URL entered by user (with or without protocol)
            
        Returns:
            Authenticated URL if valid, None otherwise
            
        Example:
            authenticated_url = await URLValidationHelper.validate_and_get_url("google.com")
            if authenticated_url:
                print(f"Safe to use: {authenticated_url}")
        """
        try:
            result = await url_validator.validate_and_authenticate_url(user_input)
            if result["is_valid"]:
                logger.info(f"✅ URL validated: {result['authenticated_url']}")
                return result["authenticated_url"]
            else:
                logger.warning(
                    f"❌ URL validation failed for {user_input}: "
                    f"{', '.join(result['errors'])}"
                )
                return None
        except Exception as e:
            logger.error(f"Error validating URL {user_input}: {str(e)}")
            return None

    @staticmethod
    async def validate_batch_urls(urls: List[str]) -> Dict[str, Optional[str]]:
        """
        Validate multiple URLs and return authenticated versions
        
        Args:
            urls: List of URLs to validate
            
        Returns:
            Dictionary mapping original URL to authenticated URL (None if invalid)
            
        Example:
            results = await URLValidationHelper.validate_batch_urls(
                ["google.com", "amazon.com", "invalid-site.tk"]
            )
            # {
            #   "google.com": "https://google.com",
            #   "amazon.com": "https://amazon.com",
            #   "invalid-site.tk": None
            # }
        """
        results = {}
        for url in urls:
            authenticated_url = await URLValidationHelper.validate_and_get_url(url)
            results[url] = authenticated_url
        return results

    @staticmethod
    async def get_validation_details(url: str) -> Dict:
        """
        Get detailed validation information for a URL
        
        Args:
            url: URL to validate
            
        Returns:
            Detailed validation result with all checks
            
        Example:
            details = await URLValidationHelper.get_validation_details("google.com")
            print(f"Domain: {details['domain']}")
            print(f"SSL Valid: {details['ssl_valid']}")
            print(f"Reachable: {details['is_reachable']}")
        """
        return await url_validator.validate_and_authenticate_url(url)

    @staticmethod
    async def is_url_safe(url: str) -> bool:
        """
        Quick check if URL is safe to use
        
        Args:
            url: URL to check
            
        Returns:
            True if URL is valid and reachable, False otherwise
            
        Example:
            if await URLValidationHelper.is_url_safe("microsoft.com"):
                print("URL is safe to use")
        """
        result = await url_validator.validate_and_authenticate_url(url)
        return result["is_valid"]

    @staticmethod
    async def check_suspicious_patterns(url: str) -> List[str]:
        """
        Check if URL has suspicious patterns
        
        Args:
            url: URL to check
            
        Returns:
            List of warnings/suspicious patterns found
            
        Example:
            warnings = await URLValidationHelper.check_suspicious_patterns(url)
            if warnings:
                print("⚠️ Potential issues:")
                for warning in warnings:
                    print(f"  - {warning}")
        """
        result = await url_validator.validate_and_authenticate_url(url)
        return result["warnings"]

    @staticmethod
    async def get_domain_from_url(url: str) -> Optional[str]:
        """
        Safely extract domain from URL
        
        Args:
            url: URL to extract domain from
            
        Returns:
            Domain name if valid, None otherwise
            
        Example:
            domain = await URLValidationHelper.get_domain_from_url("https://www.google.com/search")
            print(domain)  # Output: www.google.com (or google.com depending on URL)
        """
        return url_validator.get_safe_domain(url)


# Usage Examples
async def example_simple_validation():
    """Example 1: Simple URL validation"""
    url = "google.com"
    authenticated = await URLValidationHelper.validate_and_get_url(url)
    if authenticated:
        print(f"✅ Use this URL: {authenticated}")
    else:
        print("❌ URL is not valid or unreachable")


async def example_batch_validation():
    """Example 2: Validate multiple URLs"""
    urls = ["google.com", "amazon.com", "apple.com"]
    results = await URLValidationHelper.validate_batch_urls(urls)
    
    for original, authenticated in results.items():
        if authenticated:
            print(f"✅ {original} → {authenticated}")
        else:
            print(f"❌ {original} → Invalid")


async def example_detailed_check():
    """Example 3: Detailed validation check"""
    url = "microsoft.com"
    details = await URLValidationHelper.get_validation_details(url)
    
    print(f"URL: {url}")
    print(f"Valid: {details['is_valid']}")
    print(f"Authenticated URL: {details['authenticated_url']}")
    print(f"Domain: {details['domain']}")
    print(f"SSL Valid: {details['ssl_valid']}")
    print(f"Reachable: {details['is_reachable']}")
    print(f"HTTP Status: {details['status_code']}")
    
    if details['errors']:
        print(f"Errors: {details['errors']}")
    if details['warnings']:
        print(f"Warnings: {details['warnings']}")


async def example_safety_check():
    """Example 4: Quick safety check"""
    suspicious_urls = [
        "google.com",  # Safe
        "bit.ly/fake",  # Suspicious (shortened URL)
        "bank-lookalike.tk",  # Suspicious (phishing TLD)
    ]
    
    for url in suspicious_urls:
        is_safe = await URLValidationHelper.is_url_safe(url)
        warnings = await URLValidationHelper.check_suspicious_patterns(url)
        
        print(f"\n{url}:")
        print(f"  Safe: {is_safe}")
        if warnings:
            print(f"  Warnings: {', '.join(warnings)}")


async def example_domain_extraction():
    """Example 5: Extract domain safely"""
    urls = [
        "https://www.google.com/search?q=test",
        "amazon.com",
        "invalid://bad-url"
    ]
    
    for url in urls:
        domain = await URLValidationHelper.get_domain_from_url(url)
        print(f"{url} → {domain if domain else 'Invalid'}")


# Decorators for automatic URL validation
def validate_company_url(func):
    """Decorator to automatically validate company URL parameter"""
    async def wrapper(*args, company_url=None, **kwargs):
        if company_url:
            authenticated_url = await URLValidationHelper.validate_and_get_url(company_url)
            if not authenticated_url:
                raise ValueError(f"Invalid or unreachable company URL: {company_url}")
            kwargs['company_url'] = authenticated_url
        return await func(*args, **kwargs)
    return wrapper


# Example usage with decorator
@validate_company_url
async def create_company(company_id: str, company_url: str = None):
    """
    Create company with automatic URL validation
    
    Usage:
        await create_company("c_123", company_url="google.com")
    """
    print(f"Creating company {company_id} with URL: {company_url}")


# Integration with FastAPI
def create_url_validation_middleware():
    """
    Create middleware for URL validation
    Can be integrated with FastAPI app for automatic validation
    """
    async def validate_company_urls_middleware(request, call_next):
        # Check if request contains company_url
        if hasattr(request, 'json'):
            try:
                body = await request.json()
                if 'company_url' in body:
                    authenticated = await URLValidationHelper.validate_and_get_url(
                        body['company_url']
                    )
                    if not authenticated:
                        return {
                            "error": "Invalid company URL",
                            "original_url": body['company_url']
                        }
                    body['company_url'] = authenticated
            except:
                pass
        
        response = await call_next(request)
        return response
    
    return validate_company_urls_middleware


# Logging helper
class URLValidationLogger:
    """Helper for logging URL validations"""
    
    @staticmethod
    def log_validation(url: str, result: Dict):
        """Log URL validation result"""
        if result['is_valid']:
            logger.info(
                f"✅ URL validated | Original: {url} | "
                f"Authenticated: {result['authenticated_url']} | "
                f"Domain: {result['domain']}"
            )
        else:
            logger.warning(
                f"❌ URL validation failed | URL: {url} | "
                f"Errors: {', '.join(result['errors'])}"
            )
    
    @staticmethod
    def log_batch_validation(urls: List[str], results: Dict[str, Optional[str]]):
        """Log batch URL validation results"""
        valid_count = sum(1 for v in results.values() if v)
        logger.info(
            f"Batch validation completed | Total: {len(urls)} | "
            f"Valid: {valid_count} | Invalid: {len(urls) - valid_count}"
        )


if __name__ == "__main__":
    # Run examples
    import asyncio
    
    print("URL Validation Examples\n" + "="*50)
    
    asyncio.run(example_simple_validation())
    print("\n" + "="*50)
    
    asyncio.run(example_batch_validation())
    print("\n" + "="*50)
    
    asyncio.run(example_detailed_check())
