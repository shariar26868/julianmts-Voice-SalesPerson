from fastapi import APIRouter, HTTPException, Body, Query
from starlette.responses import RedirectResponse
from typing import List
from pydantic import BaseModel
from app.models.schemas import (
    CompanyCreate, CompanyResponse, RepresentativeCreate,
    RepresentativeResponse, MeetingMode
)
from app.config.database import (
    get_company_collection, get_representative_collection,
    get_meeting_collection, get_conversation_collection
)
from app.services.scraper import scraper, linkedin_scraper
from app.services.openai_service import openai_service
from app.services.url_validator_service import url_validator
from app.services.google_search_service import google_search_service
from app.utils.helpers import generate_id, current_timestamp, build_api_response

router = APIRouter(prefix="/api/company", tags=["Company"])


# Request/Response models
class URLValidationRequest(BaseModel):
    url: str


class URLValidationResponse(BaseModel):
    is_valid: bool
    authenticated_url: str = None
    is_reachable: bool
    status_code: int = None
    ssl_valid: bool
    domain: str = None
    errors: list
    warnings: list
    message: str = None


@router.post("/validate-url", response_model=dict)
async def validate_company_url(request: URLValidationRequest):
    """
    Validate and authenticate a company URL
    
    This endpoint checks:
    - URL format and validity
    - SSL certificate validity
    - Website reachability
    - Domain reputation
    - Redirect chains
    
    Returns the authenticated URL if valid
    """
    try:
        validation_result = await url_validator.validate_and_authenticate_url(request.url)

        return build_api_response(
            success=validation_result["is_valid"],
            data={
                "is_valid": validation_result["is_valid"],
                "authenticated_url": validation_result["authenticated_url"],
                "is_reachable": validation_result["is_reachable"],
                "status_code": validation_result["status_code"],
                "ssl_valid": validation_result["ssl_valid"],
                "domain": validation_result["domain"],
                "errors": validation_result["errors"],
                "warnings": validation_result["warnings"],
            },
            message=validation_result.get("message", "URL validation completed")
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/redirect")
async def redirect_to_authenticated_url(url: str = Query(..., description="The company URL to redirect to")):
    """
    Validate URL and redirect to authenticated website
    
    Usage: /api/company/redirect?url=example.com
    
    The system will:
    1. Validate the URL
    2. Add https:// if needed
    3. Verify it's authentic and reachable
    4. Redirect to the authenticated URL if valid
    """
    try:
        authenticated_url = await url_validator.get_authenticated_url(url)

        if authenticated_url:
            return RedirectResponse(url=authenticated_url, status_code=307)
        else:
            raise HTTPException(
                status_code=400,
                detail="URL validation failed. The website is not reachable or has security issues."
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create", response_model=dict)
async def create_company_data(company_data: CompanyCreate):
    """
    Create company profile with AI-powered data extraction
    
    The endpoint accepts any input for company_url:
    - If it's a valid URL or domain, uses it directly
    - If it's a search term, searches Google and auto-fills the URL
    - Proceeds even if URL has SSL issues or is temporarily unreachable
    """
    
    try:
        company_url_input = str(company_data.company_url).strip()
        
        # Step 1: Check if input is already a valid URL or domain
        is_url = google_search_service._is_valid_url(company_url_input)
        
        company_url_to_use = company_url_input
        search_query = None
        
        # Step 2: If not a URL/domain, search Google
        if not is_url:
            print(f"🔍 Searching Google for: {company_url_input}")
            search_query = company_url_input
            found_url = await google_search_service.search_company_url(company_url_input)
            
            if found_url:
                company_url_to_use = found_url
                print(f"✅ Found URL: {company_url_to_use}")
            else:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "message": f"We searched everywhere but couldn't find a company called \"{company_url_input}\". Please double-check the name or try entering their website URL directly (e.g. betopia.com).",
                        "search_query": company_url_input,
                        "suggestion": "Try entering the full website URL instead of just the company name."
                    }
                )
        
        # Step 3: Normalize and validate the URL
        print(f"🔐 Validating URL: {company_url_to_use}")
        company_url_to_use = google_search_service._normalize_url(company_url_to_use)
        
        # Attempt validation, but don't fail if URL is unreachable or has SSL issues
        validation_result = await url_validator.validate_and_authenticate_url(company_url_to_use)
        
        # Use the authenticated URL from validation, or fall back to normalized URL
        authenticated_url = validation_result.get("authenticated_url") or company_url_to_use
        
        company_id = generate_id()
        
        # Step 4: Scrape company data if auto_fetch is enabled
        scraped_data = {}
        if company_data.auto_fetch:
            # Only scrape if URL is reachable
            if validation_result.get("is_reachable"):
                print(f"📊 Scraping company data from: {authenticated_url}")
                try:
                    scraped_data = await scraper.scrape_company_data(authenticated_url)
                except Exception as e:
                    print(f"⚠️ Could not scrape data: {str(e)}")
                    # Continue anyway - don't fail if scraping fails
            else:
                print(f"⚠️ URL not reachable, skipping scrape. Will scrape later.")
        
        company_doc = {
            "_id": company_id,
            "salesperson_id": company_data.salesperson_id,
            "company_url": authenticated_url,
            "original_url": company_url_input,
            "search_query": search_query,
            "url_validation": {
                "is_valid": validation_result.get("is_valid", False),
                "is_reachable": validation_result.get("is_reachable", False),
                "ssl_valid": validation_result.get("ssl_valid", False),
                "validated_at": current_timestamp(),
                "domain": validation_result.get("domain"),
                "errors": validation_result.get("errors", []),
                "warnings": validation_result.get("warnings", [])
            },
            "company_data": scraped_data,
            "created_at": current_timestamp(),
            "last_updated": current_timestamp()
        }
        
        collection = get_company_collection()
        await collection.insert_one(company_doc)
        
        # Build status message
        status_messages = []
        if search_query:
            status_messages.append(f"auto-found URL for '{search_query}'")
        if validation_result.get("errors"):
            status_messages.append(f"URL has issues but accepted")
        if validation_result.get("warnings"):
            status_messages.append(f"SSL/reachability warnings")
        
        message = "Company data created successfully"
        if status_messages:
            message += f" ({', '.join(status_messages)})"
        
        return build_api_response(
            success=True,
            data={
                "company_id": company_id,
                "salesperson_id": company_data.salesperson_id,
                "original_input": company_url_input,
                "search_query": search_query,
                "company_url": authenticated_url,
                "company_data": scraped_data,
                "url_validation": {
                    "is_valid": validation_result.get("is_valid", False),
                    "is_reachable": validation_result.get("is_reachable", False),
                    "ssl_valid": validation_result.get("ssl_valid", False),
                    "domain": validation_result.get("domain"),
                    "errors": validation_result.get("errors", []),
                    "warnings": validation_result.get("warnings", [])
                }
            },
            message=message
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error creating company: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{company_id}", response_model=dict)
async def get_company_data(company_id: str):
    """Get company data by ID"""
    
    try:
        collection = get_company_collection()
        company = await collection.find_one({"_id": company_id})
        
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        company["id"] = str(company.pop("_id"))
        
        return build_api_response(
            success=True,
            data=company
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{company_id}", response_model=dict)
async def delete_company(company_id: str):
    """
    Delete a company and all its related data
    
    This endpoint deletes:
    - The company profile
    - All representatives for this company
    - All meetings for this company
    - All conversations for those meetings
    """
    
    try:
        company_collection = get_company_collection()
        
        # Verify company exists before deleting
        company = await company_collection.find_one({"_id": company_id})
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Count representatives to be deleted
        representative_collection = get_representative_collection()
        reps_count = await representative_collection.count_documents({"company_id": company_id})
        
        # Get all meetings for this company to delete conversations
        meeting_collection = get_meeting_collection()
        meetings = []
        async for meeting in meeting_collection.find({"company_id": company_id}):
            meetings.append(str(meeting["_id"]))
        
        # Delete all conversations for these meetings
        conversation_collection = get_conversation_collection()
        if meetings:
            await conversation_collection.delete_many({"meeting_id": {"$in": meetings}})
        
        # Delete all meetings for this company
        await meeting_collection.delete_many({"company_id": company_id})
        
        # Delete all representatives for this company
        await representative_collection.delete_many({"company_id": company_id})
        
        # Delete the company
        result = await company_collection.delete_one({"_id": company_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=500, detail="Failed to delete company")
        
        return build_api_response(
            success=True,
            data={
                "company_id": company_id,
                "deleted_items": {
                    "company": 1,
                    "representatives": reps_count,
                    "meetings": len(meetings),
                }
            },
            message=f"Company '{company_id}' and all related data deleted successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting company: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# @router.post("/{company_id}/representatives", response_model=dict)
# async def add_representative(
#     company_id: str,
#     representative: RepresentativeCreate
# ):
#     """Add a company representative"""
    
#     try:
#         company_collection = get_company_collection()
#         company = await company_collection.find_one({"_id": company_id})
        
#         if not company:
#             raise HTTPException(status_code=404, detail="Company not found")
        
#         rep_id = generate_id()
        
#         rep_doc = {
#             "_id": rep_id,
#             "company_id": company_id,
#             "name": representative.name,
#             "role": representative.role.value,
#             # "tenure_months": representative.tenure_months,
#             # "personality_traits": [trait.value for trait in representative.personality_traits],
#             "is_decision_maker": representative.is_decision_maker,
#             "linkedin_profile": str(representative.linkedin_profile) if representative.linkedin_profile else None,
#             "notes": representative.notes,
#             "voice_id": representative.voice_id,
#             "created_at": current_timestamp()
#         }
        
#         rep_collection = get_representative_collection()
#         await rep_collection.insert_one(rep_doc)
        
#         return build_api_response(
#             success=True,
#             data={"representative_id": rep_id},
#             message="Representative added successfully"
#         )
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))



@router.post("/{company_id}/representatives", response_model=dict)
async def add_representatives(
    company_id: str,
    representatives: List[RepresentativeCreate]
):
    """Add multiple company representatives. Auto-fetches LinkedIn data if URL provided."""

    try:
        company_collection = get_company_collection()
        company = await company_collection.find_one({"_id": company_id})

        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        rep_collection = get_representative_collection()
        inserted_ids = []

        for representative in representatives:
            rep_id = generate_id()

            # Auto-fetch LinkedIn data if URL is provided
            linkedin_url = str(representative.linkedin_profile) if representative.linkedin_profile else None
            linkedin_data = {}
            if linkedin_url:
                try:
                    linkedin_data = await linkedin_scraper.fetch_profile_data(linkedin_url)
                    print(f"  🔗 LinkedIn data for {representative.name}: {list(linkedin_data.keys())}")
                except Exception as e:
                    print(f"  ⚠️ LinkedIn fetch failed for {representative.name}: {e}")

            rep_doc = {
                "_id": rep_id,
                "company_id": company_id,
                "name": representative.name,
                "role": representative.role,
                "gender": representative.gender.value if hasattr(representative.gender, 'value') else (representative.gender or "female"),
                "is_decision_maker": representative.is_decision_maker,
                "linkedin_profile": linkedin_url,
                "linkedin_data": linkedin_data,  # ✅ stored for AI context
                "notes": representative.notes,
                "voice_id": representative.voice_id,
                "created_at": current_timestamp()
            }

            await rep_collection.insert_one(rep_doc)
            inserted_ids.append(rep_id)

        return build_api_response(
            success=True,
            data={"representative_ids": inserted_ids},
            message="Representatives added successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/{company_id}/representatives", response_model=dict)
async def get_company_representatives(company_id: str):
    """Get all representatives for a company"""
    
    try:
        rep_collection = get_representative_collection()
        
        representatives = []
        async for rep in rep_collection.find({"company_id": company_id}):
            rep["id"] = str(rep.pop("_id"))
            rep.pop("company_id", None)
            representatives.append(rep)
        
        return build_api_response(
            success=True,
            data={"representatives": representatives}
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/representatives/{rep_id}", response_model=dict)
async def update_representative(
    rep_id: str,
    representative: RepresentativeCreate
):
    """Update representative information. Auto-fetches LinkedIn data if URL changed."""
    
    try:
        rep_collection = get_representative_collection()
        
        existing = await rep_collection.find_one({"_id": rep_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Representative not found")
        
        # Auto-fetch LinkedIn data if URL is provided and different from existing
        linkedin_url = str(representative.linkedin_profile) if representative.linkedin_profile else None
        linkedin_data = existing.get("linkedin_data", {})
        
        if linkedin_url and linkedin_url != existing.get("linkedin_profile"):
            try:
                linkedin_data = await linkedin_scraper.fetch_profile_data(linkedin_url)
                print(f"  🔗 Updated LinkedIn data for {representative.name}: {list(linkedin_data.keys())}")
            except Exception as e:
                print(f"  ⚠️ LinkedIn fetch failed: {e}")
        
        update_data = {
            "name": representative.name,
            "role": representative.role,
            "is_decision_maker": representative.is_decision_maker,
            "linkedin_profile": linkedin_url,
            "linkedin_data": linkedin_data,
            "notes": representative.notes,
            "voice_id": representative.voice_id,
            "updated_at": current_timestamp()
        }
        
        await rep_collection.update_one(
            {"_id": rep_id},
            {"$set": update_data}
        )
        
        return build_api_response(
            success=True,
            message="Representative updated successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/representatives/{rep_id}", response_model=dict)
async def delete_representative(rep_id: str):
    """Delete a representative"""
    
    try:
        rep_collection = get_representative_collection()
        
        result = await rep_collection.delete_one({"_id": rep_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Representative not found")
        
        return build_api_response(
            success=True,
            message="Representative deleted successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{company_id}/account-details", response_model=dict)
async def get_company_account_details(company_id: str):
    """
    Get full account details for a company:
    - Company info + representatives
    - All meetings with per-meeting analytics
    - AI-generated insights (engagement score, sentiment trend, risk alerts, upsell opportunities)
    """
    try:
        company_col = get_company_collection()
        company = await company_col.find_one({"_id": company_id})
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        rep_col = get_representative_collection()
        representatives = []
        async for rep in rep_col.find({"company_id": company_id}):
            representatives.append({
                "id": str(rep["_id"]),
                "name": rep.get("name"),
                "role": rep.get("role"),
                "is_decision_maker": rep.get("is_decision_maker", False),
            })

        meeting_col = get_meeting_collection()
        conversation_col = get_conversation_collection()

        meetings_data = []
        meetings_summary = []

        async for meeting in meeting_col.find({"company_id": company_id}):
            meeting_id = str(meeting["_id"])
            # Get the latest conversation session for this meeting
            conversation = await conversation_col.find_one(
                {"meeting_id": meeting_id},
                sort=[("attempt_number", -1)]
            )

            analytics = {
                "total_turns": 0,
                "salesperson_talk_time": 0.0,
                "representatives_talk_time": 0.0,
                "total_duration": 0.0,
                "salesperson_talk_ratio": 0.0,
                "questions_asked": 0,
            }
            last_ai_message = ""

            if conversation:
                turns = conversation.get("turns", [])
                sp_time = conversation.get("salesperson_talk_time", 0.0)
                rep_time = conversation.get("representatives_talk_time", 0.0)
                total_time = sp_time + rep_time

                questions_asked = sum(
                    1 for t in turns
                    if t.get("speaker") == "salesperson" and "?" in t.get("text", "")
                )

                ai_turns = [t for t in turns if t.get("speaker") != "salesperson"]
                if ai_turns:
                    last_ai_message = ai_turns[-1].get("text", "")

                analytics = {
                    "total_turns": conversation.get("total_turns", 0),
                    "salesperson_talk_time": sp_time,
                    "representatives_talk_time": rep_time,
                    "total_duration": total_time,
                    "salesperson_talk_ratio": round((sp_time / total_time * 100), 2) if total_time > 0 else 0,
                    "questions_asked": questions_asked,
                }

            session_id = conversation.get("session_id") if conversation else None

            meetings_data.append({
                "meeting_id": meeting_id,
                "session_id": session_id,
                "meeting_goal": meeting.get("meeting_goal"),
                "status": meeting.get("status"),
                "created_at": str(meeting.get("created_at")),
                "total_duration_seconds": meeting.get("total_duration_seconds", 0),
                "analytics": analytics,
            })

            meetings_summary.append({
                "meeting_id": meeting_id,
                "session_id": session_id,
                "meeting_goal": meeting.get("meeting_goal"),
                "created_at": str(meeting.get("created_at")),
                "total_duration_seconds": meeting.get("total_duration_seconds", 0),
                "total_turns": analytics["total_turns"],
                "salesperson_talk_ratio": analytics["salesperson_talk_ratio"],
                "questions_asked": analytics["questions_asked"],
                "last_ai_message": last_ai_message,
            })

        ai_insights = {}
        if meetings_summary:
            ai_insights = await openai_service.generate_account_insights(
                company_data=company,
                meetings_summary=meetings_summary
            )

        # merge meeting scores into meetings_data
        score_map = {s["meeting_id"]: s for s in ai_insights.get("meeting_scores", [])}
        for m in meetings_data:
            score_info = score_map.get(m["meeting_id"], {})
            m["score"] = score_info.get("score", 0)
            m["score_label"] = score_info.get("label", "")

        company["id"] = str(company.pop("_id"))

        return build_api_response(
            success=True,
            data={
                "company_name": ai_insights.get("company_name", ""),
                "company": company,
                "representatives": representatives,
                "total_meetings": len(meetings_data),
                "meetings": meetings_data,
                "ai_insights": ai_insights,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
