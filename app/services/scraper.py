
import os
import httpx
from bs4 import BeautifulSoup
from typing import Dict, Any
import re
import json
from app.config.settings import settings
from openai import AsyncOpenAI


class CompanyScraper:
    """AI-powered company data scraper (OpenAI Web Search Version)"""

    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None

    async def scrape_company_data(self, company_url: str) -> Dict[str, Any]:

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

        # Step 1: Website scraping
        print("📌 Step 1: Scraping website content...")
        raw_content = await self._scrape_website_content(company_url)

        if raw_content:
            company_data["data_sources"].append("Company Website")

        # Step 2: Tech stack
        print("\n📌 Step 2: Fetching tech stack...")
        tech_data = await self._fetch_from_pagespeed(company_url)
        company_data["tech_stack"] = tech_data.get("tech_stack", [])
        if company_data["tech_stack"]:
            company_data["data_sources"].append("PageSpeed API")

        # Step 3: Wikipedia + OpenAI Web Search
        print("\n📌 Step 3: Wikipedia + OpenAI Web Search...")

        wiki_content = await self._fetch_wikipedia(company_name)
        if wiki_content:
            company_data["data_sources"].append("Wikipedia")

        ai_search_results = await self._fetch_ai_search_results(company_name, domain)
        if ai_search_results:
            company_data["data_sources"].append("OpenAI Web Search")

        # Step 4: AI extraction
        if self.openai_client and (raw_content or ai_search_results or wiki_content):
            print("\n📌 Step 4: Using AI to extract company data...")

            ai_extracted_data = await self._extract_with_chatgpt(
                company_name=company_name,
                domain=domain,
                website_content=raw_content,
                search_results=ai_search_results,
                wiki_content=wiki_content
            )

            if ai_extracted_data:
                self._merge_data(company_data, ai_extracted_data, "AI Extraction")
        else:
            print("\n⚠️ OpenAI API key not found or no content to process")

        # Step 5: Basic fallback extraction
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
        name = domain.replace("www.", "").split(".")[0]
        return name.title()

    def _merge_data(self, target: dict, source: dict, source_name: str):
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
        fields = ["company_size", "headquarters", "industry", "description", "tech_stack", "founded_year"]
        filled = sum(1 for field in fields if data.get(field))
        return round((filled / len(fields)) * 100)

    async def _scrape_website_content(self, company_url: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(
                    company_url,
                    headers={"User-Agent": "Mozilla/5.0"}
                )

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")

                    for tag in soup(["script", "style", "noscript", "nav", "footer"]):
                        tag.decompose()

                    text_content = soup.get_text(separator=" ", strip=True)
                    content = text_content[:3000]

                    print(f"  📄 Extracted {len(content)} characters from website")
                    return content

        except Exception as e:
            print(f"  ⚠️ Website scraping error: {e}")

        return ""

    async def _fetch_wikipedia(self, company_name: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.get(
                    f"https://en.wikipedia.org/api/rest_v1/page/summary/{company_name}"
                )
                if response.status_code == 200:
                    data = response.json()
                    extract = data.get("extract", "")
                    if extract:
                        print(f"  📚 Got {len(extract)} characters from Wikipedia")
                    return extract
        except Exception as e:
            print(f"  ⚠️ Wikipedia fetch error: {e}")
        return ""

    async def _fetch_ai_search_results(self, company_name: str, domain: str) -> str:

        if not self.openai_client:
            return ""

        try:
            prompt = f"""
Search the web and gather reliable information about:

Company: {company_name}
Website: {domain}

Find:
- Company size
- Headquarters
- Revenue
- Industry
- Founded year
- Brief company description

Prefer Wikipedia, Crunchbase, LinkedIn, and reputable news sources.
Return a detailed plain text summary.
"""

            response = await self.openai_client.responses.create(
                model="gpt-4.1",
                tools=[{"type": "web_search"}],
                input=prompt,
                temperature=0.2,
            )

            text_output = ""

            for output in response.output:
                if output.type == "message":
                    for content in output.content:
                        if content.type == "output_text":
                            text_output += content.text

            if text_output:
                print(f"  🌍 AI Web Search returned {len(text_output)} characters")

            return text_output

        except Exception as e:
            print(f"  ⚠️ OpenAI search error: {e}")
            return ""

    async def _extract_with_chatgpt(
        self,
        company_name: str,
        domain: str,
        website_content: str,
        search_results: str,
        wiki_content: str
    ) -> Dict[str, Any]:

        if not self.openai_client:
            return {}

        try:
            combined_content = f"""
Website Content:
{website_content[:2000]}

Wikipedia Content:
{wiki_content[:1500]}

AI Web Search Results:
{search_results[:2000]}
""".strip()

            prompt = f"""
You are a company data extraction expert.

Extract ALL available information about this company from the content below.

Content:
{combined_content}

IMPORTANT RULES:
- Extract the best possible estimate from available content
- Use reasonable inference when strongly implied
- Return null if genuinely not found

Return ONLY valid JSON:
{{
  "company_size": "e.g. 500 employees or null",
  "headquarters": "City, Country or null",
  "revenue": "e.g. $50M ARR or null",
  "industry": "e.g. SaaS, FinTech or null",
  "founded_year": "e.g. 2015 or null",
  "description": "1-2 sentence company description or null",
  "wappalyzer_tech_stack": ["tech1", "tech2"],
  "hiring_data": {{
    "open_positions": 10,
    "hiring_summary": "Actively hiring engineers and sales reps"
  }},
  "customer_reviews": {{
    "rating": 4.5,
    "total_reviews": 200,
    "summary": "Customers praise ease of use but note pricing concerns"
  }},
  "latest_news": ["News item 1", "News item 2"],
  "financial_statements": {{
    "yoy_growth": "35% YoY",
    "arr": "$12M ARR",
    "burn_rate": null
  }},
  "product_documentation": {{
    "api_docs_available": true,
    "integration_guides_available": true,
    "video_tutorials_available": false,
    "documentation_url": "https://docs.example.com or null"
  }}
}}
"""

            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a precise data extraction assistant. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1200
            )

            result_text = response.choices[0].message.content.strip()

            if result_text.startswith("```"):
                result_text = result_text.replace("```json", "").replace("```", "").strip()

            extracted_data = json.loads(result_text)

            for key, value in extracted_data.items():
                if value in ["null", "None", ""]:
                    extracted_data[key] = None

            print(f"  🤖 AI extracted {sum(1 for v in extracted_data.values() if v)} fields")

            return extracted_data

        except Exception as e:
            print(f"  ⚠️ ChatGPT extraction error: {e}")

        return {}

    async def _basic_extraction(self, content: str) -> Dict[str, Any]:

        result = {}

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

        rev_match = re.search(r"\$(\d+(?:\.\d+)?)\s*([BMK])", content, re.I)
        if rev_match:
            result["revenue"] = f"${rev_match.group(1)}{rev_match.group(2)}"

        year_match = re.search(r"(?:founded|established|since)\s+(?:in\s+)?(\d{4})", content, re.I)
        if year_match:
            result["founded_year"] = year_match.group(1)

        return result

    async def _fetch_from_pagespeed(self, company_url: str) -> Dict[str, Any]:

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