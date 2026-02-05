import httpx
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional
import re


class CompanyScraper:
    """Scrape company data from website"""
    
    async def scrape_company_data(self, company_url: str) -> Dict[str, Any]:
        """
        Scrape company information from website
        
        Returns company data dictionary with available information
        """
        
        company_data = {
            "company_size": None,
            "headquarters": None,
            "revenue": None,
            "industry": None,
            "tech_stack": [],
            "open_positions": None,
            "customer_reviews": None,
            "latest_news": [],
            "financial_growth": None
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Fetch main page
                response = await client.get(company_url, follow_redirects=True)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Extract basic info
                    company_data = await self._extract_basic_info(soup, company_data)
                    
                    # Try to find about page
                    about_url = await self._find_about_page(company_url, soup)
                    if about_url:
                        about_data = await self._scrape_about_page(about_url)
                        company_data.update(about_data)
                    
                    # Try to find careers/jobs page
                    careers_url = await self._find_careers_page(company_url, soup)
                    if careers_url:
                        jobs_count = await self._scrape_job_openings(careers_url)
                        company_data["open_positions"] = jobs_count
        
        except Exception as e:
            print(f"Error scraping company data: {e}")
        
        return company_data
    
    async def _extract_basic_info(
        self,
        soup: BeautifulSoup,
        company_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract basic information from homepage"""
        
        # Try to find industry from meta tags
        meta_description = soup.find("meta", {"name": "description"})
        if meta_description:
            description = meta_description.get("content", "")
            company_data["industry"] = self._extract_industry_from_text(description)
        
        # Try to find location/headquarters
        address_patterns = [
            soup.find("address"),
            soup.find(text=re.compile(r"headquarters", re.I)),
            soup.find(text=re.compile(r"location", re.I))
        ]
        
        for pattern in address_patterns:
            if pattern:
                company_data["headquarters"] = str(pattern)[:200]
                break
        
        # Extract latest news from blog/news section
        news_section = soup.find("section", class_=re.compile(r"news|blog", re.I))
        if news_section:
            headlines = news_section.find_all(["h2", "h3", "h4"], limit=5)
            company_data["latest_news"] = [h.get_text().strip() for h in headlines]
        
        return company_data
    
    async def _find_about_page(
        self,
        base_url: str,
        soup: BeautifulSoup
    ) -> Optional[str]:
        """Find about page URL"""
        
        about_links = soup.find_all("a", href=re.compile(r"about|company", re.I))
        
        if about_links:
            href = about_links[0].get("href")
            if href.startswith("http"):
                return href
            else:
                return f"{base_url.rstrip('/')}/{href.lstrip('/')}"
        
        return None
    
    async def _scrape_about_page(self, about_url: str) -> Dict[str, Any]:
        """Scrape about page for company details"""
        
        data = {}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(about_url)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    text = soup.get_text()
                    
                    # Extract company size
                    size_match = re.search(r"(\d+[\+]?)\s*(employees|team members)", text, re.I)
                    if size_match:
                        data["company_size"] = size_match.group(1)
                    
                    # Extract revenue if mentioned
                    revenue_match = re.search(r"\$(\d+[BMK]?)\s*(revenue|sales)", text, re.I)
                    if revenue_match:
                        data["revenue"] = f"${revenue_match.group(1)}"
        
        except Exception as e:
            print(f"Error scraping about page: {e}")
        
        return data
    
    async def _find_careers_page(
        self,
        base_url: str,
        soup: BeautifulSoup
    ) -> Optional[str]:
        """Find careers/jobs page URL"""
        
        careers_links = soup.find_all("a", href=re.compile(r"careers|jobs|hiring", re.I))
        
        if careers_links:
            href = careers_links[0].get("href")
            if href.startswith("http"):
                return href
            else:
                return f"{base_url.rstrip('/')}/{href.lstrip('/')}"
        
        return None
    
    async def _scrape_job_openings(self, careers_url: str) -> int:
        """Count open job positions"""
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(careers_url)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Try to find job listings
                    job_elements = soup.find_all(["article", "div"], class_=re.compile(r"job|position|role", re.I))
                    
                    if job_elements:
                        return len(job_elements)
                    
                    # Try to find text like "25 open positions"
                    text = soup.get_text()
                    match = re.search(r"(\d+)\s*(open|available)?\s*(positions?|jobs?|roles?)", text, re.I)
                    if match:
                        return int(match.group(1))
        
        except Exception as e:
            print(f"Error scraping job openings: {e}")
        
        return 0
    
    def _extract_industry_from_text(self, text: str) -> Optional[str]:
        """Extract industry from text using keywords"""
        
        industries = {
            "technology": ["software", "saas", "cloud", "ai", "ml", "tech"],
            "finance": ["fintech", "banking", "investment", "financial"],
            "healthcare": ["health", "medical", "pharma", "biotech"],
            "ecommerce": ["ecommerce", "e-commerce", "retail", "marketplace"],
            "education": ["education", "edtech", "learning", "training"],
            "manufacturing": ["manufacturing", "industrial", "production"],
            "consulting": ["consulting", "advisory", "services"]
        }
        
        text_lower = text.lower()
        
        for industry, keywords in industries.items():
            if any(keyword in text_lower for keyword in keywords):
                return industry.title()
        
        return None
    
    async def fetch_tech_stack(self, company_url: str) -> List[str]:
        """
        Fetch technology stack using BuiltWith or Wappalyzer API
        This is a placeholder - integrate actual API
        """
        
        # TODO: Integrate with Wappalyzer API or BuiltWith API
        # For now, returning common tech based on website inspection
        
        tech_stack = []
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(company_url)
                
                if response.status_code == 200:
                    html = response.text.lower()
                    
                    # Detect common technologies
                    tech_patterns = {
                        "React": "react",
                        "Vue.js": "vue",
                        "Angular": "angular",
                        "WordPress": "wp-content",
                        "Shopify": "shopify",
                        "Google Analytics": "google-analytics",
                        "AWS": "amazonaws",
                        "Cloudflare": "cloudflare"
                    }
                    
                    for tech, pattern in tech_patterns.items():
                        if pattern in html:
                            tech_stack.append(tech)
        
        except Exception as e:
            print(f"Error fetching tech stack: {e}")
        
        return tech_stack


# Singleton instance
scraper = CompanyScraper()