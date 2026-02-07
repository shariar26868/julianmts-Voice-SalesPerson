


import os
import httpx
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional
import re
import json
from app.config.settings import settings
from openai import AsyncOpenAI


class CompanyScraper:
    """AI-powered company data scraper"""
    
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
    
    
    async def scrape_company_data(self, company_url: str) -> Dict[str, Any]:
        """AI-powered data collection from multiple sources"""
        
        domain = company_url.replace("https://", "").replace("http://", "").split("/")[0]
        company_name = self._extract_company_name(domain)
        
        company_data = {
            "company_size": None,
            "headquarters": None,
            "revenue": None,
            "industry": None,
            "tech_stack": [],
            "open_positions": None,
            "founded_year": None,
            "description": None,
            "social_links": {},
            "data_sources": []
        }
        
        print(f"\n{'='*60}")
        print(f"🔍 Scraping: {domain} ({company_name})")
        print(f"{'='*60}\n")
        
        # Step 1: Scrape website content
        print("📌 Step 1: Scraping website content...")
        raw_content = await self._scrape_website_content(company_url)
        
        if raw_content:
            company_data["data_sources"].append("Company Website")
        
        # Step 2: Tech stack from PageSpeed
        print("\n📌 Step 2: Fetching tech stack...")
        tech_data = await self._fetch_from_pagespeed(company_url)
        company_data["tech_stack"] = tech_data.get("tech_stack", [])
        if company_data["tech_stack"]:
            company_data["data_sources"].append("PageSpeed API")
        
        # Step 3: Google search results
        print("\n📌 Step 3: Google search...")
        search_results = await self._fetch_google_search_results(company_name, domain)
        
        # Step 4: Use ChatGPT to extract structured data
        if self.openai_client and (raw_content or search_results):
            print("\n📌 Step 4: Using AI to extract company data...")
            ai_extracted_data = await self._extract_with_chatgpt(
                company_name=company_name,
                domain=domain,
                website_content=raw_content,
                search_results=search_results
            )
            
            if ai_extracted_data:
                self._merge_data(company_data, ai_extracted_data, "AI Extraction")
        else:
            print("\n⚠️ OpenAI API key not found or no content to process")
        
        # Step 5: Basic extraction fallback
        if raw_content:
            print("\n📌 Step 5: Basic extraction from website...")
            basic_data = await self._basic_extraction(raw_content)
            self._merge_data(company_data, basic_data, "Basic Extraction")
        
        print(f"\n{'='*60}")
        print(f"✅ Data Collection Complete!")
        print(f"📊 Sources: {', '.join(company_data['data_sources'])}")
        print(f"📈 Quality: {self._calculate_completeness(company_data)}%")
        print(f"{'='*60}\n")
        
        return company_data
    
    
    def _extract_company_name(self, domain: str) -> str:
        """Extract company name from domain"""
        name = domain.replace("www.", "").split(".")[0]
        return name.title()
    
    
    def _merge_data(self, target: dict, source: dict, source_name: str):
        """Merge data intelligently"""
        added = False
        for key, value in source.items():
            if key not in ["data_sources"] and value:
                if not target.get(key):
                    target[key] = value
                    added = True
                    print(f"  ✅ {key}: {str(value)[:70]}...")
        
        if added and source_name not in target["data_sources"]:
            target["data_sources"].append(source_name)
    
    
    def _calculate_completeness(self, data: dict) -> int:
        """Calculate data completeness percentage"""
        fields = ["company_size", "headquarters", "industry", "description", "tech_stack", "founded_year"]
        filled = sum(1 for field in fields if data.get(field))
        return round((filled / len(fields)) * 100)
    
    
    async def _scrape_website_content(self, company_url: str) -> str:
        """Scrape website and extract meaningful content"""
        
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(
                    company_url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                )
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Remove noise
                    for tag in soup(["script", "style", "noscript", "nav", "footer"]):
                        tag.decompose()
                    
                    # Extract text content
                    text_content = soup.get_text(separator=" ", strip=True)
                    
                    # Limit to first 3000 chars for AI processing
                    content = text_content[:3000]
                    
                    print(f"  📄 Extracted {len(content)} characters from website")
                    return content
        
        except Exception as e:
            print(f"  ⚠️ Website scraping error: {e}")
        
        return ""
    
    
    async def _fetch_google_search_results(self, company_name: str, domain: str) -> str:
        """Fetch Google search results"""
        
        api_key = settings.GOOGLE_API_KEY
        search_engine_id = settings.GOOGLE_SEARCH_ENGINE_ID
        
        if not api_key or not search_engine_id:
            print("  ⚠️ Google API keys not configured")
            return ""
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://www.googleapis.com/customsearch/v1",
                    params={
                        "key": api_key,
                        "cx": search_engine_id,
                        "q": f"{company_name} {domain} company information"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("items"):
                        # Combine snippets
                        snippets = [item.get("snippet", "") for item in data["items"][:5]]
                        combined = " ".join(snippets)
                        
                        print(f"  📄 Got {len(combined)} characters from Google Search")
                        return combined
                else:
                    print(f"  ⚠️ Google Search error: {response.status_code}")
        
        except Exception as e:
            print(f"  ⚠️ Google Search error: {e}")
        
        return ""
    
    
    async def _extract_with_chatgpt(
        self,
        company_name: str,
        domain: str,
        website_content: str,
        search_results: str
    ) -> Dict[str, Any]:
        """Use ChatGPT to extract structured company data"""
        
        if not self.openai_client:
            return {}
        
        try:
            # Combine all available content
            combined_content = f"""
Website Content:
{website_content[:2000]}

Google Search Results:
{search_results[:1000]}
            """.strip()
            
            prompt = f"""
You are a company data extraction expert. Extract accurate information about the company "{company_name}" (website: {domain}) from the provided content.

Extract the following information:
1. company_size: Number of employees (extract number only, e.g., "500" or "1000-5000")
2. headquarters: City, Country (e.g., "Singapore" or "Dhaka, Bangladesh")
3. revenue: Annual revenue if mentioned (e.g., "$10M" or "$1.5B")
4. industry: Primary industry/sector (e.g., "E-commerce", "Technology", "Finance")
5. founded_year: Year company was founded (e.g., "2012")
6. description: Brief 1-2 sentence description of what the company does

Content to analyze:
{combined_content}

IMPORTANT RULES:
- Only extract information that is CLEARLY stated in the content
- If information is not found, use null
- For company_size, extract numbers only (remove commas)
- For headquarters, use format: "City, Country"
- Be concise and accurate
- Make intelligent inferences when data is implied but not explicit

Return ONLY a valid JSON object with these exact keys:
{{
  "company_size": "value or null",
  "headquarters": "value or null", 
  "revenue": "value or null",
  "industry": "value or null",
  "founded_year": "value or null",
  "description": "value or null"
}}
"""
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",  # or "gpt-4" if you have access
                messages=[
                    {"role": "system", "content": "You are a precise data extraction assistant. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistency
                max_tokens=500
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Clean up response (remove markdown code blocks if present)
            if result_text.startswith("```json"):
                result_text = result_text.replace("```json", "").replace("```", "").strip()
            elif result_text.startswith("```"):
                result_text = result_text.replace("```", "").strip()
            
            # Parse JSON
            extracted_data = json.loads(result_text)
            
            # Convert "null" strings to None
            for key, value in extracted_data.items():
                if value == "null" or value == "None" or value == "":
                    extracted_data[key] = None
            
            print(f"  🤖 AI extracted {sum(1 for v in extracted_data.values() if v)} fields")
            
            return extracted_data
        
        except json.JSONDecodeError as e:
            print(f"  ⚠️ AI response was not valid JSON: {e}")
            print(f"  Response was: {result_text[:200]}")
        except Exception as e:
            print(f"  ⚠️ ChatGPT extraction error: {e}")
        
        return {}
    
    
    async def _basic_extraction(self, content: str) -> Dict[str, Any]:
        """Basic regex-based extraction as fallback"""
        
        result = {}
        
        # Company size
        emp_patterns = [
            r"(\d{1,3}(?:,\d{3})*|\d+)\+?\s*(?:employees|team members|staff)",
            r"team\s+of\s+(\d+)",
            r"(\d+-\d+)\s*employees"
        ]
        
        for pattern in emp_patterns:
            match = re.search(pattern, content, re.I)
            if match:
                result["company_size"] = match.group(1).replace(",", "")
                break
        
        # Revenue
        rev_match = re.search(r"\$(\d+(?:\.\d+)?)\s*([BMK])", content, re.I)
        if rev_match:
            result["revenue"] = f"${rev_match.group(1)}{rev_match.group(2)}"
        
        # Founded year
        year_match = re.search(r"(?:founded|established|since)\s+(?:in\s+)?(\d{4})", content, re.I)
        if year_match:
            result["founded_year"] = year_match.group(1)
        
        # Headquarters
        hq_patterns = [
            r"(?:headquartered|based|located)\s+in\s+([A-Z][a-z]+(?:,\s*[A-Z][a-z]+)*)",
            r"headquarters:\s*([A-Z][a-z]+(?:,\s*[A-Z][a-z]+)*)"
        ]
        
        for pattern in hq_patterns:
            match = re.search(pattern, content, re.I)
            if match:
                result["headquarters"] = match.group(1)
                break
        
        # Industry detection
        industries = {
            "E-commerce": ["ecommerce", "e-commerce", "online shopping", "marketplace"],
            "Technology": ["software", "saas", "cloud", "ai", "tech"],
            "Finance": ["fintech", "banking", "financial"],
            "Healthcare": ["health", "medical", "pharma"],
            "Education": ["education", "edtech", "learning"]
        }
        
        content_lower = content.lower()
        for industry, keywords in industries.items():
            if any(keyword in content_lower for keyword in keywords):
                result["industry"] = industry
                break
        
        return result
    
    
    async def _fetch_from_pagespeed(self, company_url: str) -> Dict[str, Any]:
        """PageSpeed API for tech stack"""
        
        api_key = settings.PAGESPEED_API_KEY
        result = {"tech_stack": []}
        
        if not api_key:
            return result
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(
                    "https://www.googleapis.com/pagespeedonline/v5/runPagespeed",
                    params={"url": company_url, "key": api_key, "category": "PERFORMANCE"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    audits = data.get("lighthouseResult", {}).get("audits", {})
                    
                    tech_stack = set()
                    if "network-requests" in audits:
                        items = audits["network-requests"].get("details", {}).get("items", [])
                        
                        tech_mapping = {
                            "react": "React",
                            "vue": "Vue.js",
                            "angular": "Angular",
                            "jquery": "jQuery",
                            "bootstrap": "Bootstrap",
                            "tailwind": "Tailwind CSS",
                            "next": "Next.js",
                            "wordpress": "WordPress",
                            "shopify": "Shopify",
                            "cloudflare": "Cloudflare",
                            "amazonaws": "AWS",
                            "stripe": "Stripe",
                            "gtag": "Google Analytics"
                        }
                        
                        for item in items:
                            url = item.get("url", "").lower()
                            for key, tech in tech_mapping.items():
                                if key in url:
                                    tech_stack.add(tech)
                    
                    result["tech_stack"] = list(tech_stack)
                    print(f"  🔧 Found tech stack: {result['tech_stack']}")
        
        except Exception as e:
            print(f"  ⚠️ PageSpeed error: {e}")
        
        return result


# Singleton
scraper = CompanyScraper()