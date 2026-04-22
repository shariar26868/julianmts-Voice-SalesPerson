# """
# COMPLETE FIXED conversation.py
# All database saves fixed - both turns saved together
# """

# from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Query, File, UploadFile
# from typing import List, Dict, Any, Optional
# from app.models.schemas import ConversationCreate, AIResponse
# from app.config.database import (
#     get_conversation_collection, get_meeting_collection,
#     get_salesperson_collection, get_company_collection,
#     get_representative_collection
# )
# from app.services.openai_service import openai_service
# from app.services.elevenlabs_service import elevenlabs_service
# from app.services.s3_service import s3_service
# from app.services.whisper_service import whisper_service
# from app.services.audio_stream_service import audio_stream_service
# from app.utils.helpers import (
#     generate_id, current_timestamp, build_api_response,
#     format_duration, extract_speaker_from_message
# )
# import json
# import asyncio

# router = APIRouter(prefix="/api/conversation", tags=["Conversation"])


# @router.post("/send-message", response_model=dict)
# async def send_message(
#     meeting_id: str = Query(..., description="Meeting ID"),
#     speaker: str = Query(default="salesperson", description="Speaker: 'salesperson' or representative ID"),
#     message: str = Query(..., description="Message text"),
#     audio_data: Optional[UploadFile] = File(None, description="Optional audio file")
# ):
#     """
#     Send a message in the conversation and get AI response
    
#     ✅ FIXED: Now saves BOTH salesperson and AI turns together in ONE database update
#     """
    
#     try:
#         print(f"\n{'='*60}")
#         print(f"📩 New message for meeting: {meeting_id}")
#         print(f"💬 Message: {message[:100]}...")
#         print(f"{'='*60}\n")
        
#         # Get meeting data
#         meeting_collection = get_meeting_collection()
#         meeting = await meeting_collection.find_one({"_id": meeting_id})
        
#         if not meeting:
#             raise HTTPException(status_code=404, detail="Meeting not found")
        
#         if meeting["status"] != "active":
#             raise HTTPException(
#                 status_code=400,
#                 detail="Meeting is not active. Please start the meeting first."
#             )
        
#         # Get or create conversation
#         conversation_collection = get_conversation_collection()
#         conversation = await conversation_collection.find_one({"meeting_id": meeting_id})
        
#         if not conversation:
#             print("📝 Creating new conversation document...")
#             conversation = {
#                 "_id": generate_id(),
#                 "meeting_id": meeting_id,
#                 "turns": [],
#                 "total_turns": 0,
#                 "salesperson_talk_time": 0.0,
#                 "representatives_talk_time": 0.0,
#                 "created_at": current_timestamp()
#             }
#             await conversation_collection.insert_one(conversation)
#             print("✅ Conversation document created")
        
#         conversation_history = conversation.get("turns", [])
#         current_turn = len(conversation_history) + 1
        
#         print(f"🔢 Current turn number: {current_turn}")
        
#         # Get speaker name
#         speaker_name = "Salesperson"
#         if speaker != "salesperson":
#             rep_collection = get_representative_collection()
#             rep = await rep_collection.find_one({"_id": speaker})
#             if rep:
#                 speaker_name = rep["name"]
        
#         # Upload audio to S3 if provided
#         audio_url = None
#         message_duration = 0.0
        
#         if audio_data and audio_data.filename:
#             print(f"🎤 Uploading salesperson audio...")
#             audio_bytes = await audio_data.read()
            
#             audio_url = await s3_service.upload_audio(
#                 audio_bytes=audio_bytes,
#                 meeting_id=meeting_id,
#                 turn_number=current_turn,
#                 speaker=speaker
#             )
#             message_duration = 5.0
            
#             if audio_url:
#                 print(f"✅ Audio uploaded: {audio_url[:60]}...")
#             else:
#                 print(f"⚠️ Audio upload failed or S3 disabled")
        
#         # Create turn entry for salesperson message
#         salesperson_turn = {
#             "turn_number": current_turn,
#             "speaker": speaker,
#             "speaker_name": speaker_name,
#             "text": message,
#             "audio_url": audio_url,
#             "timestamp": format_duration(len(conversation_history) * 10),
#             "duration_seconds": message_duration,
#             "created_at": current_timestamp()
#         }
        
#         # Add to conversation history (for AI context)
#         conversation_history.append(salesperson_turn)
        
#         print(f"👤 Salesperson turn created: Turn #{current_turn}")
        
#         # ❌ DO NOT SAVE SALESPERSON TURN YET - We'll save both together later!
        
#         # Get salesperson and company data for AI context
#         salesperson_collection = get_salesperson_collection()
#         salesperson = await salesperson_collection.find_one(
#             {"_id": meeting["salesperson_id"]}
#         )
        
#         company_collection = get_company_collection()
#         company = await company_collection.find_one(
#             {"_id": meeting["company_id"]}
#         )
        
#         # Get representatives data
#         rep_collection = get_representative_collection()
#         representatives = []
        
#         for rep_id in meeting["representative_ids"]:
#             rep = await rep_collection.find_one({"_id": rep_id})
#             if rep:
#                 rep["id"] = str(rep["_id"])
#                 representatives.append(rep)
        
#         if not representatives:
#             raise HTTPException(
#                 status_code=400,
#                 detail="No representatives found for this meeting"
#             )
        
#         print(f"👥 Found {len(representatives)} representatives")
        
#         # Check if message is directed to specific person
#         is_directed, directed_to = extract_speaker_from_message(message)
        
#         # Generate AI response
#         print(f"🤖 Generating AI response...")
#         try:
#             ai_response_data = await openai_service.generate_multi_agent_response(
#                 conversation_history=conversation_history,
#                 representatives=representatives,
#                 salesperson_data=salesperson,
#                 company_data=company,
#                 current_message=message,
#                 speaker=speaker
#             )
#             print(f"✅ AI response generated successfully")
#         except Exception as e:
#             print(f"❌ OpenAI service error: {e}")
#             import traceback
#             traceback.print_exc()
#             raise HTTPException(
#                 status_code=500,
#                 detail=f"AI response generation failed: {str(e)}"
#             )
        
#         # Find the responding representative
#         responding_rep = None
#         responding_rep_id = ai_response_data.get("responding_rep_id")
#         responding_rep_name = ai_response_data.get("responding_rep_name")
        
#         if responding_rep_id:
#             for rep in representatives:
#                 if rep.get("id") == responding_rep_id or rep.get("_id") == responding_rep_id:
#                     responding_rep = rep
#                     break
        
#         if not responding_rep and responding_rep_name:
#             for rep in representatives:
#                 if rep.get("name", "").lower() == responding_rep_name.lower():
#                     responding_rep = rep
#                     break
        
#         if not responding_rep:
#             print(f"⚠️ Could not match representative by ID/name, using first one")
#             responding_rep = representatives[0]
        
#         print(f"🎯 Responding representative: {responding_rep['name']} ({responding_rep['role']})")
        
#         # Get response text
#         response_text = ai_response_data.get("response_text", "")
        
#         if not response_text:
#             print(f"⚠️ Empty AI response, using fallback")
#             response_text = "I understand. Could you tell me more about that?"
        
#         print(f"💬 AI Response: {response_text[:100]}...")
        
#         # Generate voice for AI response
#         personality = responding_rep.get("personality_traits", ["neutral"])[0]
#         voice_id = responding_rep.get("voice_id")
        
#         print(f"🔊 Generating voice (personality: {personality})...")
        
#         response_audio = None
#         try:
#             response_audio = await elevenlabs_service.text_to_speech(
#                 text=response_text,
#                 voice_id=voice_id,
#                 personality=personality
#             )
            
#             if response_audio and len(response_audio) > 0:
#                 print(f"✅ Generated {len(response_audio)} bytes of audio")
#             else:
#                 print(f"⚠️ ElevenLabs returned empty audio")
#                 response_audio = b""
                
#         except Exception as e:
#             print(f"⚠️ ElevenLabs error (continuing anyway): {e}")
#             response_audio = b""
        
#         # Upload AI response audio to S3
#         ai_turn_number = current_turn + 1
#         ai_audio_url = None
        
#         if response_audio and len(response_audio) > 0:
#             print(f"📤 Uploading AI audio to S3...")
#             try:
#                 ai_audio_url = await s3_service.upload_audio(
#                     audio_bytes=response_audio,
#                     meeting_id=meeting_id,
#                     turn_number=ai_turn_number,
#                     speaker=responding_rep["id"]
#                 )
                
#                 if ai_audio_url:
#                     print(f"✅ AI audio uploaded: {ai_audio_url[:60]}...")
#                 else:
#                     print(f"⚠️ S3 upload returned None (S3 might be disabled)")
                    
#             except Exception as e:
#                 print(f"⚠️ S3 upload error (continuing anyway): {e}")
#                 ai_audio_url = None
#         else:
#             print(f"⚠️ No audio to upload (TTS failed or returned empty)")
        
#         # AI duration estimate
#         ai_duration = 6.0
        
#         # Create turn entry for AI response
#         ai_turn = {
#             "turn_number": ai_turn_number,
#             "speaker": responding_rep["id"],
#             "speaker_name": responding_rep["name"],
#             "text": response_text,
#             "audio_url": ai_audio_url,  # Can be None if S3 disabled
#             "timestamp": format_duration((len(conversation_history) + 1) * 10),
#             "duration_seconds": ai_duration,
#             "created_at": current_timestamp()
#         }
        
#         print(f"🤖 AI turn created: Turn #{ai_turn_number}")
        
#         # ✅ NOW SAVE BOTH TURNS TOGETHER TO DATABASE IN ONE UPDATE
#         print(f"\n{'='*60}")
#         print(f"💾 Saving BOTH turns to database...")
#         print(f"{'='*60}")
        
#         try:
#             update_result = await conversation_collection.update_one(
#                 {"meeting_id": meeting_id},
#                 {
#                     "$inc": {
#                         "salesperson_talk_time": message_duration,
#                         "representatives_talk_time": ai_duration
#                     },
#                     "$push": {
#                         "turns": {
#                             "$each": [salesperson_turn, ai_turn]  # ✅ BOTH TURNS TOGETHER!
#                         }
#                     },
#                     "$set": {
#                         "total_turns": ai_turn_number
#                     }
#                 }
#             )
            
#             if update_result.modified_count > 0:
#                 print(f"✅ Successfully saved turns {current_turn} & {ai_turn_number} to database")
#                 print(f"✅ Total turns now: {ai_turn_number}")
#                 print(f"✅ Salesperson talk time: {message_duration}s added")
#                 print(f"✅ AI talk time: {ai_duration}s added")
#             else:
#                 print(f"⚠️ Database update matched but didn't modify (might be duplicate)")
                
#         except Exception as e:
#             print(f"❌ Database save error: {e}")
#             import traceback
#             traceback.print_exc()
#             # Don't raise exception - conversation worked, just DB save failed
#             print(f"⚠️ Continuing despite DB error...")
        
#         print(f"{'='*60}\n")
        
#         # Return response
#         return build_api_response(
#             success=True,
#             data={
#                 "ai_response": {
#                     "speaker_id": responding_rep["id"],
#                     "speaker_name": responding_rep["name"],
#                     "speaker_role": responding_rep["role"],
#                     "response_text": response_text,
#                     "audio_url": ai_audio_url,
#                     "duration_seconds": ai_duration
#                 },
#                 "turn_number": ai_turn_number,
#                 "reasoning": ai_response_data.get("reasoning", ""),
#                 "salesperson_turn": current_turn,
#                 "ai_turn": ai_turn_number,
#                 "both_turns_saved": True
#             },
#             message="Message sent and AI response generated"
#         )
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"❌ Error in send_message: {e}")
#         import traceback
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/{meeting_id}/history", response_model=dict)
# async def get_conversation_history(meeting_id: str):
#     """Get complete conversation history for a meeting"""
    
#     try:
#         conversation_collection = get_conversation_collection()
#         conversation = await conversation_collection.find_one({"meeting_id": meeting_id})
        
#         if not conversation:
#             return build_api_response(
#                 success=True,
#                 data={
#                     "turns": [],
#                     "total_turns": 0,
#                     "salesperson_talk_time": 0,
#                     "representatives_talk_time": 0
#                 },
#                 message="No conversation found for this meeting"
#             )
        
#         conversation["id"] = str(conversation.pop("_id"))
        
#         return build_api_response(
#             success=True,
#             data=conversation
#         )
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get("/{meeting_id}/analytics", response_model=dict)
# async def get_conversation_analytics(meeting_id: str):
#     """Get analytics for the conversation"""
    
#     try:
#         conversation_collection = get_conversation_collection()
#         conversation = await conversation_collection.find_one({"meeting_id": meeting_id})
        
#         if not conversation:
#             raise HTTPException(status_code=404, detail="Conversation not found")
        
#         total_time = conversation["salesperson_talk_time"] + conversation["representatives_talk_time"]
        
#         # Calculate metrics
#         analytics = {
#             "total_turns": conversation["total_turns"],
#             "salesperson_turns": len([t for t in conversation["turns"] if t["speaker"] == "salesperson"]),
#             "ai_turns": len([t for t in conversation["turns"] if t["speaker"] != "salesperson"]),
#             "salesperson_talk_time": conversation["salesperson_talk_time"],
#             "representatives_talk_time": conversation["representatives_talk_time"],
#             "total_duration": total_time,
#             "salesperson_talk_ratio": round((conversation["salesperson_talk_time"] / total_time * 100), 2) if total_time > 0 else 0,
#             "representatives_talk_ratio": round((conversation["representatives_talk_time"] / total_time * 100), 2) if total_time > 0 else 0,
#         }
        
#         # Count questions asked
#         questions_asked = sum(
#             1 for turn in conversation["turns"]
#             if turn["speaker"] == "salesperson" and "?" in turn["text"]
#         )
        
#         analytics["questions_asked"] = questions_asked
        
#         return build_api_response(
#             success=True,
#             data=analytics
#         )
    
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# @router.websocket("/ws/live-conversation/{meeting_id}")
# async def live_conversation(websocket: WebSocket, meeting_id: str):
#     """
#     🎙️ REAL-TIME LIVE VOICE CONVERSATION
    
#     ✅ FIXED: Saves both turns together in database
#     """
    
#     await websocket.accept()
    
#     try:
#         # Verify meeting exists and is active
#         meeting_collection = get_meeting_collection()
#         meeting = await meeting_collection.find_one({"_id": meeting_id})
        
#         if not meeting:
#             await websocket.send_json({
#                 "type": "error",
#                 "message": "Meeting not found"
#             })
#             await websocket.close()
#             return
        
#         if meeting["status"] != "active":
#             await websocket.send_json({
#                 "type": "error",
#                 "message": "Meeting is not active. Please start the meeting first."
#             })
#             await websocket.close()
#             return
        
#         # Get meeting context
#         salesperson_collection = get_salesperson_collection()
#         salesperson = await salesperson_collection.find_one({"_id": meeting["salesperson_id"]})
        
#         company_collection = get_company_collection()
#         company = await company_collection.find_one({"_id": meeting["company_id"]})
        
#         rep_collection = get_representative_collection()
#         representatives = []
#         for rep_id in meeting["representative_ids"]:
#             rep = await rep_collection.find_one({"_id": rep_id})
#             if rep:
#                 rep["id"] = str(rep["_id"])
#                 representatives.append(rep)
        
#         # Get or create conversation
#         conversation_collection = get_conversation_collection()
#         conversation = await conversation_collection.find_one({"meeting_id": meeting_id})
        
#         if not conversation:
#             conversation = {
#                 "_id": generate_id(),
#                 "meeting_id": meeting_id,
#                 "turns": [],
#                 "total_turns": 0,
#                 "salesperson_talk_time": 0.0,
#                 "representatives_talk_time": 0.0,
#                 "created_at": current_timestamp()
#             }
#             await conversation_collection.insert_one(conversation)
        
#         # Send connection confirmation
#         await websocket.send_json({
#             "type": "connected",
#             "message": "Connected to live conversation",
#             "meeting_id": meeting_id,
#             "representatives": [
#                 {
#                     "name": rep["name"],
#                     "role": rep["role"],
#                     "personality": rep.get("personality_traits", [])
#                 }
#                 for rep in representatives
#             ]
#         })
        
#         # Start audio stream
#         audio_stream_service.start_stream(meeting_id)
        
#         print(f"✅ WebSocket connected for meeting {meeting_id}")
        
#         # Main conversation loop
#         while True:
#             # Receive message from client
#             data = await websocket.receive_json()
#             message_type = data.get("type")
            
#             # Handle different message types
#             if message_type == "audio_chunk":
#                 # Client is sending audio chunks while speaking
#                 audio_data = data.get("data")  # Base64 encoded
#                 is_speaking = data.get("is_speaking", True)
                
#                 if is_speaking:
#                     # User is still speaking, collect audio
#                     audio_stream_service.add_audio_chunk(meeting_id, audio_data)
#                 else:
#                     # User stopped speaking, process the complete audio
#                     print("🎙️ User stopped speaking, processing...")
                    
#                     # Get all collected audio chunks
#                     audio_chunks = audio_stream_service.stop_speaking(meeting_id)
                    
#                     if audio_chunks:
#                         # Step 1: Speech-to-Text
#                         print("📝 Transcribing audio...")
                        
#                         try:
#                             transcribed_text = await whisper_service.transcribe_audio_stream(audio_chunks)
                            
#                             if not transcribed_text or transcribed_text.strip() == "":
#                                 print("⚠️ Empty transcription, using fallback")
#                                 transcribed_text = "I said something but it wasn't clear."
                            
#                             print(f"✅ Transcription: {transcribed_text}")
                            
#                         except Exception as e:
#                             print(f"❌ Whisper transcription error: {e}")
#                             import traceback
#                             traceback.print_exc()
                            
#                             await websocket.send_json({
#                                 "type": "error",
#                                 "message": f"Speech recognition failed: {str(e)}"
#                             })
                            
#                             transcribed_text = "Sorry, I couldn't understand that."
                        
#                         await websocket.send_json({
#                             "type": "transcription",
#                             "text": transcribed_text,
#                             "speaker": "salesperson"
#                         })
                        
#                         # Step 2: Get AI Response
#                         print("🤖 Generating AI response...")
                        
#                         await websocket.send_json({
#                             "type": "ai_thinking",
#                             "message": "AI is thinking..."
#                         })
                        
#                         # Get conversation history
#                         conversation_history = conversation.get("turns", [])
#                         current_turn = len(conversation_history) + 1
                        
#                         # Save salesperson turn
#                         salesperson_turn = {
#                             "turn_number": current_turn,
#                             "speaker": "salesperson",
#                             "speaker_name": "Salesperson",
#                             "text": transcribed_text,
#                             "audio_url": None,
#                             "timestamp": format_duration(len(conversation_history) * 10),
#                             "duration_seconds": 5.0,
#                             "created_at": current_timestamp()
#                         }
                        
#                         conversation_history.append(salesperson_turn)
                        
#                         # Generate AI response
#                         try:
#                             ai_response_data = await openai_service.generate_multi_agent_response(
#                                 conversation_history=conversation_history,
#                                 representatives=representatives,
#                                 salesperson_data=salesperson,
#                                 company_data=company,
#                                 current_message=transcribed_text,
#                                 speaker="salesperson"
#                             )
                            
#                             print(f"✅ AI response generated")
                            
#                         except Exception as e:
#                             print(f"❌ OpenAI error: {e}")
#                             import traceback
#                             traceback.print_exc()
                            
#                             await websocket.send_json({
#                                 "type": "error",
#                                 "message": f"AI response generation failed: {str(e)}"
#                             })
                            
#                             ai_response_data = {
#                                 "responding_rep_id": representatives[0]["id"] if representatives else None,
#                                 "responding_rep_name": representatives[0]["name"] if representatives else "AI",
#                                 "response_text": "I understand. Could you tell me more about that?",
#                                 "reasoning": "Fallback response due to error"
#                             }
                        
#                         # Find responding representative
#                         responding_rep_id = ai_response_data.get("responding_rep_id")
#                         responding_rep = None
                        
#                         for rep in representatives:
#                             if rep["id"] == responding_rep_id or rep["name"] == ai_response_data.get("responding_rep_name"):
#                                 responding_rep = rep
#                                 break
                        
#                         if not responding_rep:
#                             responding_rep = representatives[0]
                        
#                         response_text = ai_response_data.get("response_text", "I understand.")
                        
#                         # Send AI thinking info
#                         await websocket.send_json({
#                             "type": "ai_thinking",
#                             "speaker_name": responding_rep["name"],
#                             "speaker_role": responding_rep["role"]
#                         })
                        
#                         # Send AI response text
#                         await websocket.send_json({
#                             "type": "ai_response_text",
#                             "text": response_text,
#                             "speaker_name": responding_rep["name"],
#                             "speaker_role": responding_rep["role"]
#                         })
                        
#                         # Step 3: Text-to-Speech
#                         print("🔊 Generating voice...")
                        
#                         personality = responding_rep.get("personality_traits", ["neutral"])[0]
#                         voice_id = responding_rep.get("voice_id")
                        
#                         response_audio = None
#                         try:
#                             response_audio = await elevenlabs_service.text_to_speech(
#                                 text=response_text,
#                                 voice_id=voice_id,
#                                 personality=personality
#                             )
                            
#                             if not response_audio or len(response_audio) == 0:
#                                 raise Exception("ElevenLabs returned empty audio")
                            
#                             print(f"✅ Generated {len(response_audio)} bytes of audio")
                            
#                         except Exception as e:
#                             print(f"❌ TTS Error: {e}")
#                             import traceback
#                             traceback.print_exc()
                            
#                             await websocket.send_json({
#                                 "type": "error",
#                                 "message": f"Voice generation failed: {str(e)}"
#                             })
                            
#                             response_audio = None
                        
#                         # Step 4: Stream audio back to client
#                         if response_audio:
#                             print("📤 Streaming audio response...")
                            
#                             chunk_count = 0
#                             try:
#                                 async for audio_chunk in audio_stream_service.stream_audio_response(response_audio):
#                                     chunk_count += 1
                                    
#                                     if not audio_chunk:
#                                         continue
                                    
#                                     await websocket.send_json({
#                                         "type": "ai_audio_chunk",
#                                         "audio_data": audio_chunk,
#                                         "chunk_number": chunk_count,
#                                         "is_final": False
#                                     })
                                    
#                                     await asyncio.sleep(0.01)
                                
#                                 # Send final chunk marker
#                                 await websocket.send_json({
#                                     "type": "ai_audio_chunk",
#                                     "audio_data": "",
#                                     "chunk_number": chunk_count + 1,
#                                     "is_final": True
#                                 })
                                
#                                 print(f"✅ Sent {chunk_count} audio chunks")
                                
#                             except Exception as e:
#                                 print(f"❌ Audio streaming error: {e}")
#                                 await websocket.send_json({
#                                     "type": "error",
#                                     "message": "Audio streaming interrupted"
#                                 })
#                         else:
#                             print("⚠️ No audio to stream, text-only response")
#                             await websocket.send_json({
#                                 "type": "no_audio",
#                                 "message": "Text response only (audio generation failed)"
#                             })
                        
#                         # Step 5: Save conversation to database
#                         ai_turn_number = current_turn + 1
#                         ai_turn = {
#                             "turn_number": ai_turn_number,
#                             "speaker": responding_rep["id"],
#                             "speaker_name": responding_rep["name"],
#                             "text": response_text,
#                             "audio_url": None,
#                             "timestamp": format_duration((len(conversation_history) + 1) * 10),
#                             "duration_seconds": 6.0,
#                             "created_at": current_timestamp()
#                         }
                        
#                         # ✅ SAVE BOTH TURNS TOGETHER
#                         try:
#                             await conversation_collection.update_one(
#                                 {"meeting_id": meeting_id},
#                                 {
#                                     "$inc": {
#                                         "salesperson_talk_time": 5.0,
#                                         "representatives_talk_time": 6.0
#                                     },
#                                     "$push": {
#                                         "turns": {
#                                             "$each": [salesperson_turn, ai_turn]  # ✅ BOTH!
#                                         }
#                                     },
#                                     "$set": {"total_turns": ai_turn_number}
#                                 }
#                             )
                            
#                             print(f"💾 Saved turns {current_turn} & {ai_turn_number} to database")
                            
#                             await websocket.send_json({
#                                 "type": "conversation_saved",
#                                 "turn_number": ai_turn_number,
#                                 "message": "Conversation saved"
#                             })
                            
#                         except Exception as e:
#                             print(f"❌ Database save error: {e}")
#                             import traceback
#                             traceback.print_exc()
            
#             elif message_type == "ping":
#                 # Heartbeat
#                 await websocket.send_json({"type": "pong"})
            
#             elif message_type == "disconnect":
#                 # Client wants to disconnect
#                 break
    
#     except WebSocketDisconnect:
#         print(f"🔌 WebSocket disconnected for meeting {meeting_id}")
#     except Exception as e:
#         print(f"❌ WebSocket error: {e}")
#         import traceback
#         traceback.print_exc()
#         try:
#             await websocket.send_json({
#                 "type": "error",
#                 "message": str(e)
#             })
#         except:
#             pass
#     finally:
#         # Cleanup
#         audio_stream_service.clear_stream(meeting_id)
#         print(f"🧹 Cleaned up stream for meeting {meeting_id}")


# @router.websocket("/ws/test-connection/{meeting_id}")
# async def test_websocket_connection(websocket: WebSocket, meeting_id: str):
#     """Simple WebSocket test endpoint"""
#     await websocket.accept()
    
#     try:
#         await websocket.send_json({
#             "type": "connected",
#             "message": f"✅ Connected to meeting {meeting_id}!",
#             "test": True
#         })
        
#         while True:
#             data = await websocket.receive_json()
#             await websocket.send_json({
#                 "type": "echo",
#                 "received": data
#             })
            
#             if data.get("type") == "ping":
#                 await websocket.send_json({
#                     "type": "pong"
#                 })
    
#     except WebSocketDisconnect:
#         print(f"WebSocket test disconnected")







"""
conversation.py
✅ Primary + Secondary responder support
✅ Turn numbers from DB always
✅ Audio as single base64 blob
✅ Both reps can speak in one turn
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Query, File, UploadFile
from typing import List, Dict, Any, Optional
from app.models.schemas import ConversationCreate, AIResponse
from app.config.database import (
    get_conversation_collection, get_meeting_collection,
    get_salesperson_collection, get_company_collection,
    get_representative_collection, get_methodology_prompt_collection
)
from app.services.openai_service import openai_service
from app.services.elevenlabs_service import elevenlabs_service
from app.services.s3_service import s3_service
from app.services.whisper_service import whisper_service
from app.services.audio_stream_service import audio_stream_service
from app.utils.helpers import (
    generate_id, current_timestamp, build_api_response,
    format_duration, extract_speaker_from_message
)
import json
import asyncio
import base64
import io
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/api/conversation", tags=["Conversation"])


async def _get_rep_voice_and_personality(rep: Dict) -> tuple:
    """Extract voice_id and personality from rep dict"""
    voice_id = rep.get("voice_id")
    traits = rep.get("personality_traits", [])
    personality = traits[0] if traits and isinstance(traits[0], str) else "neutral"
    return voice_id, personality


async def _generate_audio(text: str, voice_id: str, personality: str) -> bytes:
    """Generate TTS audio, return bytes or empty"""
    try:
        audio = await elevenlabs_service.text_to_speech(
            text=text, voice_id=voice_id, personality=personality
        )
        return audio if audio else b""
    except Exception as e:
        print(f"⚠️ TTS error: {e}")
        return b""


async def _upload_audio(audio_bytes: bytes, meeting_id: str, turn_number: int, speaker_id: str) -> Optional[str]:
    """Upload audio to S3, return URL or None"""
    if not audio_bytes:
        return None
    try:
        url = await s3_service.upload_audio(
            audio_bytes=audio_bytes,
            meeting_id=meeting_id,
            turn_number=turn_number,
            speaker=speaker_id
        )
        return url
    except Exception as e:
        print(f"⚠️ S3 upload error: {e}")
        return None


@router.post("/send-message", response_model=dict)
async def send_message(
    meeting_id: str = Query(...),
    speaker: str = Query(default="salesperson"),
    message: str = Query(...),
    audio_data: Optional[UploadFile] = File(None)
):
    try:
        print(f"\n{'='*60}\n📩 Meeting: {meeting_id}\n💬 {message[:80]}...\n{'='*60}")
        
        meeting_collection = get_meeting_collection()
        meeting = await meeting_collection.find_one({"_id": meeting_id})
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        if meeting["status"] != "active":
            raise HTTPException(status_code=400, detail="Meeting is not active")
        
        conversation_collection = get_conversation_collection()
        conversation = await conversation_collection.find_one({"meeting_id": meeting_id})
        
        if not conversation:
            conversation = {
                "_id": generate_id(), "meeting_id": meeting_id,
                "turns": [], "total_turns": 0,
                "salesperson_talk_time": 0.0, "representatives_talk_time": 0.0,
                "created_at": current_timestamp()
            }
            await conversation_collection.insert_one(conversation)
        
        existing_turns = conversation.get("turns", [])
        current_turn   = conversation.get("total_turns", len(existing_turns)) + 1
        conversation_history = list(existing_turns)
        
        # Speaker name
        speaker_name = "Salesperson"
        if speaker != "salesperson":
            rep_col = get_representative_collection()
            rep = await rep_col.find_one({"_id": speaker})
            if rep:
                speaker_name = rep["name"]
        
        # Upload salesperson audio
        audio_url = None
        msg_duration = 0.0
        if audio_data and audio_data.filename:
            ab = await audio_data.read()
            audio_url = await _upload_audio(ab, meeting_id, current_turn, speaker)
            msg_duration = 5.0
        
        salesperson_turn = {
            "turn_number": current_turn, "speaker": speaker, "speaker_name": speaker_name,
            "text": message, "audio_url": audio_url,
            "timestamp": format_duration(len(conversation_history) * 10),
            "duration_seconds": msg_duration, "created_at": current_timestamp()
        }
        conversation_history.append(salesperson_turn)
        
        # Get context
        salesperson = await get_salesperson_collection().find_one({"_id": meeting["salesperson_id"]})
        company     = await get_company_collection().find_one({"_id": meeting["company_id"]})
        
        rep_col = get_representative_collection()
        representatives = []
        for rid in meeting["representative_ids"]:
            r = await rep_col.find_one({"_id": rid})
            if r:
                r["id"] = str(r["_id"])
                representatives.append(r)
        
        if not representatives:
            raise HTTPException(status_code=400, detail="No representatives found")
        
        # AI response
        ai_data = await openai_service.generate_multi_agent_response(
            conversation_history=conversation_history,
            representatives=representatives,
            salesperson_data=salesperson,
            company_data=company,
            current_message=message,
            speaker=speaker
        )
        
        # Find primary rep
        primary_rep = None
        for rep in representatives:
            if rep.get("id") == ai_data.get("primary_rep_id"):
                primary_rep = rep
                break
        if not primary_rep:
            primary_rep = representatives[0]
        
        primary_text = ai_data.get("primary_response", "Could you tell me more?")
        primary_turn_number = current_turn + 1
        
        # Primary TTS
        v_id, personality = await _get_rep_voice_and_personality(primary_rep)
        primary_audio = await _generate_audio(primary_text, v_id, personality)
        primary_audio_url = await _upload_audio(primary_audio, meeting_id, primary_turn_number, primary_rep["id"])
        
        primary_turn = {
            "turn_number": primary_turn_number, "speaker": primary_rep["id"],
            "speaker_name": primary_rep["name"], "text": primary_text,
            "audio_url": primary_audio_url,
            "timestamp": format_duration((len(conversation_history)) * 10),
            "duration_seconds": 6.0, "created_at": current_timestamp()
        }
        
        # Secondary rep (optional)
        secondary_rep   = None
        secondary_text  = ai_data.get("secondary_response")
        secondary_turn  = None
        secondary_audio = b""
        secondary_turn_number = primary_turn_number + 1
        
        if secondary_text and ai_data.get("secondary_rep_id"):
            for rep in representatives:
                if rep.get("id") == ai_data.get("secondary_rep_id"):
                    secondary_rep = rep
                    break
        
        if secondary_rep and secondary_text:
            v_id2, personality2 = await _get_rep_voice_and_personality(secondary_rep)
            secondary_audio = await _generate_audio(secondary_text, v_id2, personality2)
            secondary_audio_url = await _upload_audio(secondary_audio, meeting_id, secondary_turn_number, secondary_rep["id"])
            secondary_turn = {
                "turn_number": secondary_turn_number, "speaker": secondary_rep["id"],
                "speaker_name": secondary_rep["name"], "text": secondary_text,
                "audio_url": secondary_audio_url,
                "timestamp": format_duration((len(conversation_history) + 1) * 10),
                "duration_seconds": 4.0, "created_at": current_timestamp()
            }
        
        # Save all turns
        turns_to_save = [salesperson_turn, primary_turn]
        total_ai_time = 6.0
        last_turn_number = primary_turn_number
        
        if secondary_turn:
            turns_to_save.append(secondary_turn)
            total_ai_time += 4.0
            last_turn_number = secondary_turn_number
        
        await conversation_collection.update_one(
            {"meeting_id": meeting_id},
            {
                "$inc": {"salesperson_talk_time": msg_duration, "representatives_talk_time": total_ai_time},
                "$push": {"turns": {"$each": turns_to_save}},
                "$set": {"total_turns": last_turn_number}
            }
        )
        print(f"💾 Saved {len(turns_to_save)} turns")
        
        # Build response
        primary_b64   = base64.b64encode(primary_audio).decode() if primary_audio else None
        secondary_b64 = base64.b64encode(secondary_audio).decode() if secondary_audio else None
        
        return build_api_response(
            success=True,
            data={
                "primary_response": {
                    "speaker_id": primary_rep["id"], "speaker_name": primary_rep["name"],
                    "speaker_role": primary_rep["role"], "response_text": primary_text,
                    "audio_url": primary_audio_url, "audio_base64": primary_b64,
                    "audio_mime_type": "audio/mpeg", "turn_number": primary_turn_number
                },
                "secondary_response": {
                    "speaker_id": secondary_rep["id"] if secondary_rep else None,
                    "speaker_name": secondary_rep["name"] if secondary_rep else None,
                    "response_text": secondary_text,
                    "audio_base64": secondary_b64,
                    "audio_mime_type": "audio/mpeg",
                    "turn_number": secondary_turn_number
                } if secondary_rep and secondary_text else None,
                "salesperson_turn": current_turn,
                "reasoning": ai_data.get("reasoning", "")
            },
            message="Message processed"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{meeting_id}/sessions", response_model=dict)
async def get_meeting_sessions(meeting_id: str):
    """List all practice sessions for a meeting, newest first."""
    try:
        col = get_conversation_collection()
        cursor = col.find({"meeting_id": meeting_id}, sort=[("attempt_number", -1)])
        sessions = []
        async for doc in cursor:
            raw_s3_url = doc.get("recording_s3_url")
            # Generate a pre-signed URL (7 days) so the client can access
            # private S3 objects without getting AccessDenied errors.
            presigned_url = None
            if raw_s3_url:
                presigned_url = s3_service.generate_presigned_url(
                    raw_s3_url, expiration=604800  # 7 days
                )
            sessions.append({
                "session_id":       doc.get("session_id"),
                "attempt_number":   doc.get("attempt_number", 1),
                "total_turns":      doc.get("total_turns", 0),
                "created_at":       doc.get("created_at"),
                # Pre-signed URL (valid 7 days). null until background task finishes.
                "recording_s3_url": presigned_url,
                # Fallback streaming endpoint (merges on-the-fly)
                "recording_url":    f"/api/conversation/{meeting_id}/recording?session_id={doc.get('session_id')}",
                "history_url":      f"/api/conversation/{meeting_id}/history?session_id={doc.get('session_id')}",
            })
        return build_api_response(success=True, data={"sessions": sessions, "total": len(sessions)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{meeting_id}/history", response_model=dict)
async def get_conversation_history(meeting_id: str, session_id: Optional[str] = None):
    """Get transcript for a specific session (or latest if no session_id)."""
    try:
        col = get_conversation_collection()
        query = {"meeting_id": meeting_id}
        if session_id:
            query["session_id"] = session_id
            conv = await col.find_one(query)
        else:
            # Return the most recent session
            conv = await col.find_one(query, sort=[("attempt_number", -1)])
        if not conv:
            return build_api_response(success=True, data={"turns": [], "total_turns": 0,
                "salesperson_talk_time": 0, "representatives_talk_time": 0})
        conv["id"] = str(conv.pop("_id"))

        # Convenience fields at top level
        analytics_data = conv.get("analytics", {})
        conv["summary"] = analytics_data.get("summary", "")
        conv["engagement_score"] = analytics_data.get("engagement_score", 0)
        conv["questions_asked"] = analytics_data.get("questions_asked", 0)
        conv["open_questions"] = analytics_data.get("open_questions", 0)
        conv["active_listening_grade"] = analytics_data.get("active_listening_grade", "N/A")

        # Convert stored raw S3 URL to a pre-signed URL (7 days)
        raw_s3_url = conv.get("recording_s3_url")
        if raw_s3_url:
            conv["recording_s3_url"] = s3_service.generate_presigned_url(
                raw_s3_url, expiration=604800  # 7 days
            )
        else:
            conv["recording_s3_url"] = None

        return build_api_response(success=True, data=conv)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{meeting_id}/recording")
async def get_conversation_recording(meeting_id: str, session_id: Optional[str] = None):
    """
    Download the full conversation as a single merged MP3 file.
    Fetches each turn's audio from S3 (in turn_number order) and streams
    the concatenated bytes back as audio/mpeg.
    """
    try:
        col = get_conversation_collection()
        query = {"meeting_id": meeting_id}
        if session_id:
            query["session_id"] = session_id
            conv = await col.find_one(query)
        else:
            conv = await col.find_one(query, sort=[("attempt_number", -1)])
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")

        turns = conv.get("turns", [])
        if not turns:
            raise HTTPException(status_code=404, detail="No turns found in conversation")

        # Sort turns by turn_number so audio is in the correct order
        sorted_turns = sorted(turns, key=lambda t: t.get("turn_number", 0))

        # Collect audio URLs that actually have audio saved
        audio_urls = [
            t["audio_url"]
            for t in sorted_turns
            if t.get("audio_url")
        ]

        if not audio_urls:
            raise HTTPException(
                status_code=404,
                detail="No audio recordings found for this conversation. "
                       "Audio may not have been saved during the session."
            )

        print(f"🎞️ Merging {len(audio_urls)} audio segments for meeting {meeting_id}")

        # Download all segments from S3 and concatenate
        merged = io.BytesIO()
        downloaded = 0
        for url in audio_urls:
            audio_bytes = await s3_service.download_file(url)
            if audio_bytes:
                merged.write(audio_bytes)
                downloaded += 1

        if downloaded == 0:
            raise HTTPException(
                status_code=502,
                detail="Could not download any audio segments from storage."
            )

        merged.seek(0)
        print(f"✅ Merged {downloaded}/{len(audio_urls)} segments — "
              f"{merged.getbuffer().nbytes} bytes total")

        filename = f"meeting_{meeting_id}_recording.mp3"

        return StreamingResponse(
            merged,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(merged.getbuffer().nbytes),
                "X-Segments-Merged": str(downloaded),
                "X-Total-Segments": str(len(audio_urls)),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Recording merge error: {e}")
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{meeting_id}/analytics", response_model=dict)
async def get_conversation_analytics(meeting_id: str, session_id: Optional[str] = None):
    try:
        col = get_conversation_collection()
        query = {"meeting_id": meeting_id}
        if session_id:
            query["session_id"] = session_id
        
        # Get the requested session (or latest)
        conv = await col.find_one(query, sort=[("attempt_number", -1)])
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Return saved AI analytics if they exist
        if "analytics" in conv:
            return build_api_response(success=True, data=conv["analytics"])
        
        # Fallback to basic stats if AI analytics pending
        total_time = conv.get("salesperson_talk_time", 0) + conv.get("representatives_talk_time", 0)
        basic_stats = {
            "status": "processing",
            "message": "AI analytics are currently being generated. Please wait and refresh.",
            "total_turns": conv.get("total_turns", 0),
            "salesperson_talk_time": conv.get("salesperson_talk_time", 0),
            "representatives_talk_time": conv.get("representatives_talk_time", 0),
            "total_duration": total_time,
        }
        return build_api_response(success=True, data=basic_stats)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def _generate_and_save_analytics(session_id: str):
    """Background task to generate and save AI analytics after a session ends."""
    try:
        conv_col = get_conversation_collection()
        conv = await conv_col.find_one({"session_id": session_id})
        if not conv or not conv.get("turns"):
            print(f"⏭️ Skipping analytics for {session_id} - no conversation data")
            return
            
        print(f"📊 Starting background AI analytics for session {session_id}...")
        
        try:
            # Fetch related data for context
            meeting_id = conv["meeting_id"]
            meeting = await get_meeting_collection().find_one({"_id": meeting_id})
            if meeting:
                salesperson = await get_salesperson_collection().find_one({"_id": meeting["salesperson_id"]})
                company = await get_company_collection().find_one({"_id": meeting["company_id"]})
                
                # Generate complex AI analytics
                analytics_result = await openai_service.generate_conversation_analytics(
                    conversation_history=conv["turns"],
                    salesperson_data=salesperson or {},
                    company_data=company or {}
                )
                
                # Calculate talk time ratios
                total_time = conv.get("salesperson_talk_time", 0) + conv.get("representatives_talk_time", 0)
                sp_ratio = round(conv.get("salesperson_talk_time", 0) / total_time * 100, 2) if total_time else 0
                ai_ratio = round(conv.get("representatives_talk_time", 0) / total_time * 100, 2) if total_time else 0
                
                # Combine basic stats with AI insights
                analytics_result.update({
                    "total_turns": conv.get("total_turns", 0),
                    "salesperson_turns": len([t for t in conv["turns"] if t["speaker"] == "salesperson"]),
                    "ai_turns": len([t for t in conv["turns"] if t["speaker"] != "salesperson"]),
                    "salesperson_talk_time": conv.get("salesperson_talk_time", 0),
                    "representatives_talk_time": conv.get("representatives_talk_time", 0),
                    "total_duration": total_time,
                    "salesperson_talk_ratio": sp_ratio,
                    "representatives_talk_ratio": ai_ratio
                })
                
                # Save analytics back to database
                await conv_col.update_one(
                    {"session_id": session_id},
                    {"$set": {"analytics": analytics_result}}
                )
                print(f"✅ AI Analytics completed and saved for session {session_id}")
        except Exception as e:
            print(f"❌ Background analytics generation error for {session_id}: {e}")
            import traceback; traceback.print_exc()

    except Exception as e:
        print(f"❌ Background analytics error for {session_id}: {e}")
        import traceback; traceback.print_exc()

    # ── Full recording upload (runs regardless of analytics success) ──────────
    try:
        conv = await conv_col.find_one({"session_id": session_id})
        if not conv:
            return

        turns = conv.get("turns", [])
        meeting_id = conv.get("meeting_id")
        sorted_turns = sorted(turns, key=lambda t: t.get("turn_number", 0))
        audio_urls = [t["audio_url"] for t in sorted_turns if t.get("audio_url")]

        if not audio_urls:
            print(f"⚠️ No audio URLs — skipping full recording upload for {session_id}")
            return

        print(f"🎞️ Extracting {len(audio_urls)} segments for full recording ({session_id})...")
        import tempfile
        import os
        import subprocess
        import imageio_ffmpeg
        
        temp_files = []
        
        try:
            # Download chunks to temp files
            for url in audio_urls:
                chunk = await s3_service.download_file(url)
                if chunk:
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.tmp')
                    tmp.write(chunk)
                    tmp.close()
                    temp_files.append(tmp.name)

            if not temp_files:
                print(f"⚠️ Could not download any audio segments — skipping full recording upload")
                return

            print(f"✅ Downloaded {len(temp_files)}/{len(audio_urls)} segments. Merging via FFMPEG...")
            
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

            # Step 1: Convert ALL files to mp3 first (handles mixed webm/mp3 formats)
            converted_files = []
            try:
                for src in temp_files:
                    dst = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
                    conv_cmd = [ffmpeg_exe, "-y", "-i", src, "-c:a", "libmp3lame", "-b:a", "128k", "-ar", "22050", "-ac", "1", dst]
                    conv_res = subprocess.run(conv_cmd, capture_output=True, text=True)
                    if conv_res.returncode == 0:
                        converted_files.append(dst)
                    else:
                        print(f"⚠️ Could not convert segment, skipping: {conv_res.stderr[:200]}")

                if not converted_files:
                    raise Exception("No segments could be converted to mp3")

                # Step 2: Merge all converted mp3 files
                if len(converted_files) == 1:
                    with open(converted_files[0], 'rb') as f:
                        merged_bytes = f.read()
                else:
                    out_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
                    cmd = [ffmpeg_exe, "-y"]
                    for f in converted_files:
                        cmd.extend(["-i", f])
                    filter_str = "".join([f"[{i}:a]" for i in range(len(converted_files))])
                    filter_str += f"concat=n={len(converted_files)}:v=0:a=1[out]"
                    cmd.extend(["-filter_complex", filter_str, "-map", "[out]", "-c:a", "libmp3lame", "-b:a", "128k", out_file])
                    res = subprocess.run(cmd, capture_output=True, text=True)
                    if res.returncode != 0:
                        raise Exception(f"FFMPEG failed: {res.stderr}")
                    with open(out_file, 'rb') as f:
                        merged_bytes = f.read()
                    os.remove(out_file)

            finally:
                for f in converted_files:
                    if os.path.exists(f): os.remove(f)

            print(f"✅ Merge successful — {len(merged_bytes)} bytes")

        finally:
            for f in temp_files:
                if os.path.exists(f): os.remove(f)

        recording_url = await s3_service.upload_full_meeting_audio(
            audio_bytes=merged_bytes,
            meeting_id=meeting_id
        )

        if recording_url:
            await conv_col.update_one(
                {"session_id": session_id},
                {"$set": {"recording_s3_url": recording_url}}
            )
            print(f"✅ Full recording uploaded: {recording_url}")
        else:
            print(f"⚠️ S3 upload returned None for full recording ({session_id})")

    except Exception as e:
        print(f"❌ Full recording upload error for {session_id}: {e}")
        import traceback; traceback.print_exc()


@router.websocket("/ws/live-conversation/{meeting_id}")
async def live_conversation(websocket: WebSocket, meeting_id: str):
    """
    🎙️ Live voice conversation WebSocket
    ✅ Primary + Secondary responder
    ✅ Audio as single base64 blob per speaker
    ✅ DB-based turn numbers
    """
    await websocket.accept()
    
    try:
        meeting_col = get_meeting_collection()
        meeting = await meeting_col.find_one({"_id": meeting_id})
        
        if not meeting:
            await websocket.send_json({"type": "error", "message": "Meeting not found"})
            await websocket.close(); return
        
        if meeting["status"] != "active":
            await websocket.send_json({"type": "error", "message": "Meeting is not active"})
            await websocket.close(); return
        
        salesperson = await get_salesperson_collection().find_one({"_id": meeting["salesperson_id"]})
        company     = await get_company_collection().find_one({"_id": meeting["company_id"]})

        # Fetch methodology prompt
        methodology = meeting.get("sales_methodology", "MEDDIC").upper()
        methodology_col = get_methodology_prompt_collection()
        methodology_doc = await methodology_col.find_one({"_id": methodology})
        methodology_prompt = methodology_doc.get("prompt", "") if methodology_doc else ""
        if not methodology_prompt:
            from app.routes.admin import _seed_defaults
            await _seed_defaults()
            methodology_doc = await methodology_col.find_one({"_id": methodology})
            methodology_prompt = methodology_doc.get("prompt", "") if methodology_doc else ""
            if not methodology_prompt:
                methodology_prompt = f"The salesperson is using the {meeting.get('sales_methodology', 'custom')} sales methodology. Respond realistically and make them work to qualify the opportunity."

        # Append user-provided description if any
        methodology_description = meeting.get("methodology_description", "")
        if methodology_description:
            methodology_prompt += f"\n\nAdditional context from the trainer:\n{methodology_description}"

        print(f"📋 Using methodology: {methodology}")
        
        rep_col = get_representative_collection()
        representatives = []
        for rid in meeting["representative_ids"]:
            r = await rep_col.find_one({"_id": rid})
            if r:
                r["id"] = str(r["_id"])
                representatives.append(r)
        
        conv_col = get_conversation_collection()

        # Count existing sessions to determine attempt number
        existing_count = await conv_col.count_documents({"meeting_id": meeting_id})
        attempt_number = existing_count + 1
        session_id = generate_id()  # unique per session

        # Always create a FRESH conversation document for this session
        conversation = {
            "_id": generate_id(),
            "session_id": session_id,
            "meeting_id": meeting_id,
            "attempt_number": attempt_number,
            "turns": [], "total_turns": 0,
            "salesperson_talk_time": 0.0, "representatives_talk_time": 0.0,
            "created_at": current_timestamp()
        }
        await conv_col.insert_one(conversation)
        print(f"📋 New session #{attempt_number} created: {session_id}")

        await websocket.send_json({
            "type": "connected",
            "message": "Connected to live conversation",
            "meeting_id": meeting_id,
            "session_id": session_id,
            "attempt_number": attempt_number,
            "representatives": [
                {"id": r["id"], "name": r["name"], "role": r["role"],
                 "personality": r.get("personality_traits", [])}
                for r in representatives
            ]
        })
        
        audio_stream_service.start_stream(session_id)  # use session_id so streams don't collide
        print(f"✅ WS connected: {meeting_id} | session #{attempt_number} ({session_id})")
        
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=30.0)
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "ping"})
                continue
            msg_type = data.get("type")
            
            if msg_type == "audio_chunk":
                is_speaking = data.get("is_speaking", True)
                
                if is_speaking:
                    audio_stream_service.add_audio_chunk(session_id, data.get("data"))
                else:
                    print("🎙️ User stopped, processing...")
                    chunks = audio_stream_service.stop_speaking(session_id)
                    
                    if not chunks:
                        continue
                    
                    # Combine raw audio bytes (used for both Whisper AND S3 upload)
                    combined_salesperson_audio = b"".join(chunks)
                    
                    # Transcribe
                    try:
                        transcribed = await whisper_service.transcribe_audio_stream(chunks)
                        if not transcribed or transcribed.strip() == "":
                            transcribed = "I said something but it wasn't clear."
                        print(f"✅ Transcription: {transcribed}")
                    except Exception as e:
                        print(f"❌ Whisper error: {e}")
                        await websocket.send_json({"type": "error", "message": f"Speech recognition failed: {str(e)}"})
                        transcribed = "Sorry, I couldn't understand that."
                    
                    await websocket.send_json({"type": "transcription", "text": transcribed, "speaker": "salesperson"})
                    await websocket.send_json({"type": "ai_thinking", "message": "AI is thinking..."})
                    
                    # Fresh DB state for THIS session
                    conversation = await conv_col.find_one({"session_id": session_id})
                    conv_history = list(conversation.get("turns", []))
                    current_turn = conversation.get("total_turns", len(conv_history)) + 1
                    
                    # Upload salesperson audio to S3 for full recording
                    salesperson_audio_url = None
                    if combined_salesperson_audio:
                        salesperson_audio_url = await _upload_audio(
                            combined_salesperson_audio, meeting_id, current_turn, "salesperson"
                        )
                    
                    salesperson_turn = {
                        "turn_number": current_turn, "speaker": "salesperson",
                        "speaker_name": "Salesperson", "text": transcribed,
                        "audio_url": salesperson_audio_url,
                        "timestamp": format_duration(len(conv_history) * 10),
                        "duration_seconds": 5.0, "created_at": current_timestamp()
                    }
                    conv_history.append(salesperson_turn)
                    
                    # --- STREAMING PIPELINE START ---
                    
                    # Pick responder locally (no extra API call)
                    last_speaker_id = None
                    for t in reversed(conv_history):
                        if t.get("speaker") != "salesperson":
                            last_speaker_id = t.get("speaker")
                            break

                    primary_rep = representatives[0]
                    if last_speaker_id and len(representatives) > 1:
                        for rep in representatives:
                            if rep.get("id") != last_speaker_id:
                                primary_rep = rep
                                break

                    # If salesperson addressed someone by name/role, use that rep
                    msg_lower = transcribed.lower()
                    for rep in representatives:
                        if rep.get("name", "").lower() in msg_lower or rep.get("role", "").lower() in msg_lower:
                            primary_rep = rep
                            break
                        
                    await websocket.send_json({
                        "type": "ai_thinking",
                        "message": f"{primary_rep['name']} is preparing to speak..."
                    })
                    
                    # Stream OpenAI response token by token
                    token_stream = openai_service.stream_response(
                        conversation_history=conv_history,
                        representatives=representatives,
                        salesperson_data=salesperson,
                        company_data=company,
                        current_message=transcribed,
                        primary_rep=primary_rep,
                        methodology_prompt=methodology_prompt
                    )

                    # Buffer into sentences then TTS each sentence
                    from app.utils.stream_helpers import sentence_buffer
                    sentence_stream = sentence_buffer(token_stream)

                    v_id, personality = await _get_rep_voice_and_personality(primary_rep)
                    audio_stream = elevenlabs_service.stream_tts_from_sentences(
                        sentences_stream=sentence_stream,
                        voice_id=v_id,
                        personality=personality
                    )

                    full_text = ""
                    full_audio_bytes = b""
                    chunk_no = 0

                    print(f"🚀 Starting stream to frontend for {primary_rep['name']}...")

                    async for sentence, audio_bytes in audio_stream:
                        chunk_no += 1
                        full_text += sentence + " "
                        if audio_bytes:
                            full_audio_bytes += audio_bytes

                        await websocket.send_json({
                            "type": "ai_response_text",
                            "text": sentence,
                            "speaker_id": primary_rep["id"],
                            "speaker_name": primary_rep["name"],
                            "speaker_role": primary_rep["role"],
                            "is_primary": True,
                            "is_chunk": True
                        })

                        # Send audio chunk
                        if audio_bytes:
                            import base64
                            await websocket.send_json({
                                "type": "ai_audio_complete",
                                "audio_data": base64.b64encode(audio_bytes).decode(),
                                "audio_mime_type": "audio/mpeg",
                                "speaker_id": primary_rep["id"],
                                "speaker_name": primary_rep["name"],
                                "speaker_role": primary_rep["role"],
                                "is_primary": True,
                                "is_final": False,
                                "chunk_no": chunk_no
                            })
                    
                    full_text = full_text.strip()
                    if not full_text:
                        full_text = "I understand. Could you tell me more about that?"
                        
                    # Final complete notification
                    await websocket.send_json({
                        "type": "no_audio"
                    })
                    print("✅ Stream finished!")
                    
                    # --- STREAMING PIPELINE END ---
                    
                    # Upload full audio to S3
                    primary_turn_number = current_turn + 1
                    primary_audio_url = None
                    if full_audio_bytes:
                        primary_audio_url = await _upload_audio(
                            full_audio_bytes, meeting_id, primary_turn_number, primary_rep["id"]
                        )
                    
                    primary_turn = {
                        "turn_number": primary_turn_number, 
                        "speaker": primary_rep["id"],
                        "speaker_name": primary_rep["name"], 
                        "text": full_text,
                        "audio_url": primary_audio_url,
                        "timestamp": format_duration(len(conv_history) * 10),
                        "duration_seconds": max(1.0, len(full_audio_bytes) / 32000), # approx duration 
                        "created_at": current_timestamp()
                    }
                    
                    # Secondary Rep Removed for Low Latency Flow
                    
                    turns_to_save = [salesperson_turn, primary_turn]
                    total_ai_time = primary_turn["duration_seconds"]
                    last_turn_no = primary_turn_number
                    
                    try:
                        await conv_col.update_one(
                            {"session_id": session_id},
                            {
                                "$inc": {"salesperson_talk_time": 5.0, "representatives_talk_time": total_ai_time},
                                "$push": {"turns": {"$each": turns_to_save}},
                                "$set": {"total_turns": last_turn_no}
                            }
                        )
                        print(f"💾 Saved {len(turns_to_save)} turns (up to #{last_turn_no})")
                        await websocket.send_json({
                            "type": "conversation_saved",
                            "session_id": session_id,
                            "turns": [
                                {
                                    "turn_number": t["turn_number"],
                                    "speaker":     t["speaker"],
                                    "speaker_name": t["speaker_name"],
                                    "text":        t["text"],
                                    "audio_url":   t.get("audio_url"),
                                }
                                for t in turns_to_save
                            ]
                        })
                    except Exception as e:
                        print(f"❌ DB save error: {e}")
            
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})
            
            elif msg_type == "disconnect":
                break
    
    except WebSocketDisconnect:
        print(f"🔌 WS disconnected: {meeting_id}")
    except Exception as e:
        print(f"❌ WS error: {e}")
        import traceback; traceback.print_exc()
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass
    finally:
        audio_stream_service.clear_stream(session_id)
        # Trigger AI Analytics in background after disconnect
        asyncio.create_task(_generate_and_save_analytics(session_id))
        print(f"🧹 Cleaned up session: {session_id} (meeting: {meeting_id})")


@router.websocket("/ws/test-connection/{meeting_id}")
async def test_websocket_connection(websocket: WebSocket, meeting_id: str):
    await websocket.accept()
    try:
        await websocket.send_json({"type": "connected", "message": f"✅ Connected to {meeting_id}!", "test": True})
        while True:
            data = await websocket.receive_json()
            await websocket.send_json({"type": "echo", "received": data})
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        print("WS test disconnected")