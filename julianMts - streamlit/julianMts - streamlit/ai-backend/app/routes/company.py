
from fastapi import APIRouter, HTTPException, Body
from typing import List
from app.models.schemas import (
    CompanyCreate, CompanyResponse, RepresentativeCreate,
    RepresentativeResponse, MeetingMode
)
from app.config.database import (
    get_company_collection, get_representative_collection,
    get_meeting_collection, get_conversation_collection
)
from app.services.scraper import scraper
from app.services.openai_service import openai_service
from app.utils.helpers import generate_id, current_timestamp, build_api_response

router = APIRouter(prefix="/api/company", tags=["Company"])


@router.post("/create", response_model=dict)
async def create_company_data(company_data: CompanyCreate):
    """Create company profile with AI-powered data extraction"""
    
    try:
        company_id = generate_id()
        
        scraped_data = {}
        if company_data.auto_fetch:
            scraped_data = await scraper.scrape_company_data(str(company_data.company_url))
        
        company_doc = {
            "_id": company_id,
            "salesperson_id": company_data.salesperson_id,
            "company_url": str(company_data.company_url),
            "company_data": scraped_data,
            "created_at": current_timestamp(),
            "last_updated": current_timestamp()
        }
        
        collection = get_company_collection()
        await collection.insert_one(company_doc)
        
        return build_api_response(
            success=True,
            data={
                "company_id": company_id,
                "salesperson_id": company_data.salesperson_id,
                "company_data": scraped_data
            },
            message="Company data created successfully"
        )
    
    except Exception as e:
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

@router.post("/{company_id}/representatives", response_model=dict)
async def add_representative(
    company_id: str,
    representative: RepresentativeCreate
):
    """Add a company representative"""
    
    try:
        company_collection = get_company_collection()
        company = await company_collection.find_one({"_id": company_id})
        
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        rep_id = generate_id()
        
        rep_doc = {
            "_id": rep_id,
            "company_id": company_id,
            "name": representative.name,
            "role": representative.role.value,
            "tenure_months": representative.tenure_months,
            "personality_traits": [trait.value for trait in representative.personality_traits],
            "is_decision_maker": representative.is_decision_maker,
            "linkedin_profile": str(representative.linkedin_profile) if representative.linkedin_profile else None,
            "notes": representative.notes,
            "voice_id": representative.voice_id,
            "created_at": current_timestamp()
        }
        
        rep_collection = get_representative_collection()
        await rep_collection.insert_one(rep_doc)
        
        return build_api_response(
            success=True,
            data={"representative_id": rep_id},
            message="Representative added successfully"
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
    """Update representative information"""
    
    try:
        rep_collection = get_representative_collection()
        
        existing = await rep_collection.find_one({"_id": rep_id})
        if not existing:
            raise HTTPException(status_code=404, detail="Representative not found")
        
        update_data = {
            "name": representative.name,
            "role": representative.role.value,
            "tenure_months": representative.tenure_months,
            "personality_traits": [trait.value for trait in representative.personality_traits],
            "is_decision_maker": representative.is_decision_maker,
            "linkedin_profile": str(representative.linkedin_profile) if representative.linkedin_profile else None,
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
        # 1. Fetch company
        company_col = get_company_collection()
        company = await company_col.find_one({"_id": company_id})
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        # 2. Fetch representatives
        rep_col = get_representative_collection()
        representatives = []
        async for rep in rep_col.find({"company_id": company_id}):
            representatives.append({
                "id": str(rep["_id"]),
                "name": rep.get("name"),
                "role": rep.get("role"),
                "is_decision_maker": rep.get("is_decision_maker", False),
            })

        # 3. Fetch all meetings for this company
        meeting_col = get_meeting_collection()
        conversation_col = get_conversation_collection()

        meetings_data = []
        meetings_summary = []  # for AI insights

        async for meeting in meeting_col.find({"company_id": company_id}):
            meeting_id = str(meeting["_id"])

            # Per-meeting conversation analytics
            conversation = await conversation_col.find_one({"meeting_id": meeting_id})

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

                # last AI message for context
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

            meetings_data.append({
                "meeting_id": meeting_id,
                "salesperson_id": meeting.get("salesperson_id"),
                "meeting_goal": meeting.get("meeting_goal"),
                "status": meeting.get("status"),
                "created_at": str(meeting.get("created_at")),
                "total_duration_seconds": meeting.get("total_duration_seconds", 0),
                "analytics": analytics,
            })

            meetings_summary.append({
                "meeting_goal": meeting.get("meeting_goal"),
                "created_at": str(meeting.get("created_at")),
                "total_duration_seconds": meeting.get("total_duration_seconds", 0),
                "total_turns": analytics["total_turns"],
                "salesperson_talk_ratio": analytics["salesperson_talk_ratio"],
                "questions_asked": analytics["questions_asked"],
                "last_ai_message": last_ai_message,
            })

        # 4. Generate AI insights
        ai_insights = {}
        if meetings_summary:
            ai_insights = await openai_service.generate_account_insights(
                company_data=company,
                meetings_summary=meetings_summary
            )

        company["id"] = str(company.pop("_id"))

        return build_api_response(
            success=True,
            data={
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
