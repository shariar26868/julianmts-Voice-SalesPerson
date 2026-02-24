from fastapi import APIRouter, HTTPException
from typing import List
from app.models.schemas import MeetingCreate, MeetingResponse
from app.config.database import (
    get_meeting_collection, get_salesperson_collection,
    get_company_collection, get_representative_collection
)
from app.services.openai_service import openai_service
from app.utils.helpers import generate_id, current_timestamp, build_api_response

router = APIRouter(prefix="/api/meeting", tags=["Meeting"])


@router.post("/create", response_model=dict)
async def create_meeting(meeting_data: MeetingCreate):
    """
    Create a new meeting setup
    Generates top 5 questions based on salesperson and company data
    """
    
    try:
        # Verify salesperson exists
        salesperson_collection = get_salesperson_collection()
        salesperson = await salesperson_collection.find_one({"_id": meeting_data.salesperson_id})
        
        if not salesperson:
            raise HTTPException(status_code=404, detail="Salesperson not found")
        
        # Verify company exists
        company_collection = get_company_collection()
        company = await company_collection.find_one({"_id": meeting_data.company_id})
        
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Verify representatives exist
        rep_collection = get_representative_collection()
        representatives = []
        
        for rep_id in meeting_data.representatives:
            rep = await rep_collection.find_one({"_id": rep_id})
            if not rep:
                raise HTTPException(
                    status_code=404,
                    detail=f"Representative {rep_id} not found"
                )
            representatives.append(rep)
        
        # Validate meeting mode vs number of representatives
        mode_rep_count = {
            "1-on-1": 1,
            "1-on-2": 2,
            "1-on-3": 3
        }
        
        expected_count = mode_rep_count.get(meeting_data.meeting_mode.value)
        if len(representatives) != expected_count:
            raise HTTPException(
                status_code=400,
                detail=f"Meeting mode {meeting_data.meeting_mode.value} requires {expected_count} representative(s)"
            )
        
        # Generate top 5 questions using OpenAI
        top_questions = await openai_service.generate_top_questions(
            salesperson_data=salesperson,
            company_data=company,
            meeting_goal=meeting_data.meeting_goal
        )
        
        # Create meeting document
        meeting_id = generate_id()
        
        meeting_doc = {
            "_id": meeting_id,
            "salesperson_id": meeting_data.salesperson_id,
            "company_id": meeting_data.company_id,
            "meeting_mode": meeting_data.meeting_mode.value,
            "representative_ids": meeting_data.representatives,
            "meeting_goal": meeting_data.meeting_goal,
            "top_5_questions": top_questions,
            "personality": meeting_data.personality.value,
            "duration_minutes": meeting_data.duration_minutes,
            "difficulty": meeting_data.difficulty.value,
            "status": "pending",  # pending, active, completed
            "created_at": current_timestamp(),
            "started_at": None,
            "ended_at": None,
            "total_duration_seconds": 0
        }
        
        # Insert into MongoDB
        meeting_collection = get_meeting_collection()
        await meeting_collection.insert_one(meeting_doc)
        
        # Prepare response with representative details
        reps_response = []
        for rep in representatives:
            reps_response.append({
                "id": str(rep["_id"]),
                "name": rep["name"],
                "role": rep["role"],
                "personality_traits": rep["personality_traits"],
                "is_decision_maker": rep["is_decision_maker"]
            })
        
        return build_api_response(
            success=True,
            data={
                "meeting_id": meeting_id,
                "top_5_questions": top_questions,
                "representatives": reps_response,
                "status": "pending"
            },
            message="Meeting created successfully. Ready to start!"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{meeting_id}", response_model=dict)
async def get_meeting(meeting_id: str):
    """Get meeting details"""
    
    try:
        meeting_collection = get_meeting_collection()
        meeting = await meeting_collection.find_one({"_id": meeting_id})
        
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        # Get representative details
        rep_collection = get_representative_collection()
        representatives = []
        
        for rep_id in meeting.get("representative_ids", []):
            rep = await rep_collection.find_one({"_id": rep_id})
            if rep:
                representatives.append({
                    "id": str(rep["_id"]),
                    "name": rep["name"],
                    "role": rep["role"],
                    "personality_traits": rep["personality_traits"],
                    "is_decision_maker": rep["is_decision_maker"]
                })
        
        meeting["id"] = str(meeting.pop("_id"))
        meeting["representatives"] = representatives
        
        return build_api_response(
            success=True,
            data=meeting
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{meeting_id}/start", response_model=dict)
async def start_meeting(meeting_id: str):
    """Start the meeting (change status to active)"""
    
    try:
        meeting_collection = get_meeting_collection()
        meeting = await meeting_collection.find_one({"_id": meeting_id})
        
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        if meeting["status"] != "pending":
            raise HTTPException(
                status_code=400,
                detail=f"Meeting is already {meeting['status']}"
            )
        
        # Update status to active
        await meeting_collection.update_one(
            {"_id": meeting_id},
            {
                "$set": {
                    "status": "active",
                    "started_at": current_timestamp()
                }
            }
        )
        
        return build_api_response(
            success=True,
            message="Meeting started successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{meeting_id}/end", response_model=dict)
async def end_meeting(meeting_id: str):
    """End the meeting (change status to completed)"""
    
    try:
        meeting_collection = get_meeting_collection()
        meeting = await meeting_collection.find_one({"_id": meeting_id})
        
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        if meeting["status"] != "active":
            raise HTTPException(
                status_code=400,
                detail="Meeting is not active"
            )
        
        # Calculate total duration
        started_at = meeting.get("started_at")
        ended_at = current_timestamp()
        
        duration_seconds = 0
        if started_at:
            duration_seconds = (ended_at - started_at).total_seconds()
        
        # Update status to completed
        await meeting_collection.update_one(
            {"_id": meeting_id},
            {
                "$set": {
                    "status": "completed",
                    "ended_at": ended_at,
                    "total_duration_seconds": duration_seconds
                }
            }
        )
        
        return build_api_response(
            success=True,
            data={"duration_seconds": duration_seconds},
            message="Meeting ended successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{meeting_id}", response_model=dict)
async def delete_meeting(meeting_id: str):
    """Delete a meeting"""
    
    try:
        meeting_collection = get_meeting_collection()
        
        result = await meeting_collection.delete_one({"_id": meeting_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        # TODO: Also delete related conversation data
        
        return build_api_response(
            success=True,
            message="Meeting deleted successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/salesperson/{salesperson_id}/meetings", response_model=dict)
async def get_salesperson_meetings(salesperson_id: str):
    """Get all meetings for a salesperson"""
    
    try:
        meeting_collection = get_meeting_collection()
        
        meetings = []
        async for meeting in meeting_collection.find({"salesperson_id": salesperson_id}):
            meeting["id"] = str(meeting.pop("_id"))
            meetings.append(meeting)
        
        return build_api_response(
            success=True,
            data={"meetings": meetings, "total": len(meetings)}
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))