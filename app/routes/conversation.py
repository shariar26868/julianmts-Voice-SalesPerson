from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
from app.models.schemas import ConversationCreate, AIResponse
from app.config.database import (
    get_conversation_collection, get_meeting_collection,
    get_salesperson_collection, get_company_collection,
    get_representative_collection
)
from app.services.openai_service import openai_service
from app.services.elevenlabs_service import elevenlabs_service
from app.services.s3_service import s3_service
from app.utils.helpers import (
    generate_id, current_timestamp, build_api_response,
    format_duration, extract_speaker_from_message
)
import json

router = APIRouter(prefix="/api/conversation", tags=["Conversation"])


@router.post("/send-message", response_model=dict)
async def send_message(
    meeting_id: str,
    speaker: str,  # "salesperson" or rep_id
    message: str,
    audio_data: bytes = None
):
    """
    Send a message in the conversation
    Returns AI response from appropriate representative(s)
    """
    
    try:
        # Get meeting data
        meeting_collection = get_meeting_collection()
        meeting = await meeting_collection.find_one({"_id": meeting_id})
        
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        
        if meeting["status"] != "active":
            raise HTTPException(
                status_code=400,
                detail="Meeting is not active. Please start the meeting first."
            )
        
        # Get conversation history
        conversation_collection = get_conversation_collection()
        conversation = await conversation_collection.find_one({"meeting_id": meeting_id})
        
        if not conversation:
            # Create new conversation
            conversation = {
                "_id": generate_id(),
                "meeting_id": meeting_id,
                "turns": [],
                "total_turns": 0,
                "salesperson_talk_time": 0.0,
                "representatives_talk_time": 0.0,
                "created_at": current_timestamp()
            }
            await conversation_collection.insert_one(conversation)
        
        conversation_history = conversation.get("turns", [])
        
        # Get current turn number
        current_turn = len(conversation_history) + 1
        
        # Get speaker name
        speaker_name = "Salesperson"
        if speaker != "salesperson":
            rep_collection = get_representative_collection()
            rep = await rep_collection.find_one({"_id": speaker})
            if rep:
                speaker_name = rep["name"]
        
        # Upload audio to S3 if provided
        audio_url = None
        message_duration = 0.0
        
        if audio_data:
            audio_url = await s3_service.upload_audio(
                audio_bytes=audio_data,
                meeting_id=meeting_id,
                turn_number=current_turn,
                speaker=speaker
            )
            # TODO: Calculate actual audio duration
            message_duration = 5.0  # Placeholder
        
        # Create turn entry for salesperson message
        salesperson_turn = {
            "turn_number": current_turn,
            "speaker": speaker,
            "speaker_name": speaker_name,
            "text": message,
            "audio_url": audio_url,
            "timestamp": format_duration(len(conversation_history) * 10),  # Approximate
            "duration_seconds": message_duration,
            "created_at": current_timestamp()
        }
        
        # Add to conversation history
        conversation_history.append(salesperson_turn)
        
        # Update salesperson talk time
        if speaker == "salesperson":
            await conversation_collection.update_one(
                {"meeting_id": meeting_id},
                {
                    "$inc": {"salesperson_talk_time": message_duration},
                    "$push": {"turns": salesperson_turn},
                    "$inc": {"total_turns": 1}
                }
            )
        
        # Get salesperson and company data for AI context
        salesperson_collection = get_salesperson_collection()
        salesperson = await salesperson_collection.find_one(
            {"_id": meeting["salesperson_id"]}
        )
        
        company_collection = get_company_collection()
        company = await company_collection.find_one(
            {"_id": meeting["company_id"]}
        )
        
        # Get representatives data
        rep_collection = get_representative_collection()
        representatives = []
        
        for rep_id in meeting["representative_ids"]:
            rep = await rep_collection.find_one({"_id": rep_id})
            if rep:
                rep["id"] = str(rep["_id"])
                representatives.append(rep)
        
        # Check if message is directed to specific person
        is_directed, directed_to = extract_speaker_from_message(message)
        
        # Generate AI response
        ai_response_data = await openai_service.generate_multi_agent_response(
            conversation_history=conversation_history,
            representatives=representatives,
            salesperson_data=salesperson,
            company_data=company,
            current_message=message,
            speaker=speaker
        )
        
        # Find the responding representative
        responding_rep_id = ai_response_data.get("responding_rep_id")
        responding_rep = None
        
        for rep in representatives:
            if rep["id"] == responding_rep_id or rep["name"] == ai_response_data.get("responding_rep_name"):
                responding_rep = rep
                break
        
        if not responding_rep:
            # Fallback to first rep
            responding_rep = representatives[0]
        
        # Generate voice for AI response
        response_text = ai_response_data.get("response_text", "")
        
        # Get personality for voice generation
        personality = responding_rep.get("personality_traits", ["neutral"])[0]
        voice_id = responding_rep.get("voice_id")
        
        # Generate audio
        response_audio = await elevenlabs_service.text_to_speech(
            text=response_text,
            voice_id=voice_id,
            personality=personality
        )
        
        # Upload AI response audio to S3
        ai_turn_number = current_turn + 1
        ai_audio_url = await s3_service.upload_audio(
            audio_bytes=response_audio,
            meeting_id=meeting_id,
            turn_number=ai_turn_number,
            speaker=responding_rep["id"]
        )
        
        # TODO: Calculate actual audio duration
        ai_duration = 6.0  # Placeholder
        
        # Create turn entry for AI response
        ai_turn = {
            "turn_number": ai_turn_number,
            "speaker": responding_rep["id"],
            "speaker_name": responding_rep["name"],
            "text": response_text,
            "audio_url": ai_audio_url,
            "timestamp": format_duration((len(conversation_history) + 1) * 10),
            "duration_seconds": ai_duration,
            "created_at": current_timestamp()
        }
        
        # Update conversation with AI response
        await conversation_collection.update_one(
            {"meeting_id": meeting_id},
            {
                "$inc": {"representatives_talk_time": ai_duration},
                "$push": {"turns": ai_turn},
                "$inc": {"total_turns": 1}
            }
        )
        
        return build_api_response(
            success=True,
            data={
                "ai_response": {
                    "speaker_id": responding_rep["id"],
                    "speaker_name": responding_rep["name"],
                    "speaker_role": responding_rep["role"],
                    "response_text": response_text,
                    "audio_url": ai_audio_url,
                    "duration_seconds": ai_duration
                },
                "turn_number": ai_turn_number,
                "reasoning": ai_response_data.get("reasoning", "")
            },
            message="Message sent and AI response generated"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in send_message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{meeting_id}/history", response_model=dict)
async def get_conversation_history(meeting_id: str):
    """Get complete conversation history for a meeting"""
    
    try:
        conversation_collection = get_conversation_collection()
        conversation = await conversation_collection.find_one({"meeting_id": meeting_id})
        
        if not conversation:
            return build_api_response(
                success=True,
                data={
                    "turns": [],
                    "total_turns": 0,
                    "salesperson_talk_time": 0,
                    "representatives_talk_time": 0
                },
                message="No conversation found for this meeting"
            )
        
        conversation["id"] = str(conversation.pop("_id"))
        
        return build_api_response(
            success=True,
            data=conversation
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{meeting_id}/analytics", response_model=dict)
async def get_conversation_analytics(meeting_id: str):
    """Get analytics for the conversation"""
    
    try:
        conversation_collection = get_conversation_collection()
        conversation = await conversation_collection.find_one({"meeting_id": meeting_id})
        
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        total_time = conversation["salesperson_talk_time"] + conversation["representatives_talk_time"]
        
        # Calculate metrics
        analytics = {
            "total_turns": conversation["total_turns"],
            "salesperson_turns": len([t for t in conversation["turns"] if t["speaker"] == "salesperson"]),
            "ai_turns": len([t for t in conversation["turns"] if t["speaker"] != "salesperson"]),
            "salesperson_talk_time": conversation["salesperson_talk_time"],
            "representatives_talk_time": conversation["representatives_talk_time"],
            "total_duration": total_time,
            "salesperson_talk_ratio": round((conversation["salesperson_talk_time"] / total_time * 100), 2) if total_time > 0 else 0,
            "representatives_talk_ratio": round((conversation["representatives_talk_time"] / total_time * 100), 2) if total_time > 0 else 0,
        }
        
        # Count questions asked
        questions_asked = sum(
            1 for turn in conversation["turns"]
            if turn["speaker"] == "salesperson" and "?" in turn["text"]
        )
        
        analytics["questions_asked"] = questions_asked
        
        return build_api_response(
            success=True,
            data=analytics
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/{meeting_id}")
async def websocket_conversation(websocket: WebSocket, meeting_id: str):
    """
    WebSocket endpoint for real-time conversation
    Allows streaming audio and getting instant AI responses
    """
    
    await websocket.accept()
    
    try:
        # Verify meeting exists
        meeting_collection = get_meeting_collection()
        meeting = await meeting_collection.find_one({"_id": meeting_id})
        
        if not meeting:
            await websocket.send_json({
                "error": "Meeting not found"
            })
            await websocket.close()
            return
        
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            message_type = data.get("type")
            
            if message_type == "message":
                # Process text message
                speaker = data.get("speaker", "salesperson")
                message = data.get("message", "")
                
                # Send acknowledgment
                await websocket.send_json({
                    "type": "received",
                    "message": "Processing your message..."
                })
                
                # Generate AI response (simplified version)
                # In production, call send_message endpoint or duplicate logic here
                
                response = {
                    "type": "ai_response",
                    "speaker_name": "AI Representative",
                    "text": "This is a WebSocket response placeholder",
                    "audio_url": None
                }
                
                await websocket.send_json(response)
            
            elif message_type == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for meeting {meeting_id}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close()