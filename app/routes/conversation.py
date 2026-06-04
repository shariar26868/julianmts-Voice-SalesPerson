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
    get_representative_collection, get_methodology_prompt_collection,
    get_system_config_collection, get_sales_methodology_collection
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

# Phrases that, when detected in user speech/text, should immediately end the meeting
END_PHRASES = [
    "goodbye", "good bye", "bye", "see you", "see you soon",
    "thank you", "thanks", "meet you tomorrow", "talk to you later",
    "that's all", "that is all", "i'm done", "i am done"
]


# ─────────────────────────────────────────────────────────────────────────────
# Methodology Coverage Analysis
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/{meeting_id}/methodology-analysis", response_model=dict)
async def get_methodology_analysis(meeting_id: str, session_id: Optional[str] = None):
    """
    Analyze the conversation transcript for a meeting and return which
    methodology core fields were covered by the salesperson.

    - If `session_id` is provided, analyzes that specific session.
    - If omitted, analyzes the most recent (latest) session.
    - The result is cached inside the conversation document so repeated calls
      are fast (no redundant OpenAI calls).

    Returns:
    {
      "meeting_id": "...",
      "session_id": "...",
      "methodology": "MEDDIC",
      "overall_coverage_score": 66.7,
      "fields_analyzed": [
        {
          "field": "Metrics",
          "definition": "Quantified business impact / ROI",
          "covered": true,
          "questions_asked": ["What ROI are you targeting?"],
          "answers_received": ["We need a 20% cost reduction."],
          "coverage_notes": "Salesperson asked about ROI and received a clear answer."
        },
        ...
      ]
    }
    """
    try:
        # ── 1. Get the meeting ─────────────────────────────────────────────
        meeting_col = get_meeting_collection()
        meeting = await meeting_col.find_one({"_id": meeting_id})
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")

        methodology_name: str = meeting.get("sales_methodology", "")
        if not methodology_name:
            raise HTTPException(
                status_code=400,
                detail="No sales methodology is linked to this meeting"
            )

        # ── 2. Get core fields for this methodology ────────────────────────
        methodology_col = get_sales_methodology_collection()

        # Try exact key match first (stored as UPPER_SNAKE)
        m_key = methodology_name.strip().upper().replace(" ", "_")
        method_doc = await methodology_col.find_one({"_id": m_key})

        # Fallback: case-insensitive name scan
        if not method_doc:
            async for d in methodology_col.find():
                if d.get("name", "").lower() == methodology_name.strip().lower():
                    method_doc = d
                    break

        # If still not found, try to seed defaults and retry once
        if not method_doc:
            from app.routes.methodology import _seed_defaults
            await _seed_defaults()
            method_doc = await methodology_col.find_one({"_id": m_key})

        if not method_doc:
            raise HTTPException(
                status_code=404,
                detail=f"Methodology '{methodology_name}' not found in the database. "
                       f"Please POST it to /api/methodology/ first with its core fields."
            )

        core_fields: List[Dict[str, str]] = method_doc.get("core_fields", [])
        if not core_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Methodology '{methodology_name}' has no core fields defined"
            )

        # ── 3. Get the conversation session ───────────────────────────────
        conv_col = get_conversation_collection()
        query = {"meeting_id": meeting_id}
        if session_id:
            query["session_id"] = session_id
            conv = await conv_col.find_one(query)
        else:
            conv = await conv_col.find_one(query, sort=[("attempt_number", -1)])

        if not conv:
            raise HTTPException(
                status_code=404,
                detail="No conversation found for this meeting. "
                       "Please complete a conversation session first."
            )

        turns: List[Dict] = conv.get("turns", [])
        if not turns:
            raise HTTPException(
                status_code=400,
                detail="Conversation has no turns yet. "
                       "Please complete a conversation session first."
            )

        actual_session_id: str = conv.get("session_id", "")

        # ── 4. Return cached analysis if already generated ─────────────────
        if "methodology_analysis" in conv:
            cached = conv["methodology_analysis"]
            print(f"✅ Returning cached methodology analysis for session {actual_session_id}")
            return build_api_response(
                success=True,
                data={
                    "meeting_id":             meeting_id,
                    "session_id":             actual_session_id,
                    "methodology":            cached.get("methodology", methodology_name),
                    "overall_coverage_score": cached.get("overall_coverage_score", 0),
                    "fields_analyzed":        cached.get("fields_analyzed", []),
                    "generated_at":           cached.get("generated_at"),
                    "cached":                 True,
                },
                message="Methodology coverage analysis (cached)"
            )

        # ── 5. Run OpenAI analysis ─────────────────────────────────────────
        print(f"🔍 Running methodology coverage analysis | meeting={meeting_id} | method={methodology_name}")
        analysis = await openai_service.analyze_methodology_coverage(
            conversation_turns=turns,
            methodology_name=methodology_name,
            core_fields=core_fields,
        )

        now = current_timestamp()

        # ── 6. Cache result in conversation document ───────────────────────
        save_payload = {
            "methodology":            methodology_name,
            "overall_coverage_score": analysis.get("overall_coverage_score", 0),
            "fields_analyzed":        analysis.get("fields_analyzed", []),
            "generated_at":           now,
        }

        try:
            query_filter = {"session_id": actual_session_id} if actual_session_id else {"_id": conv["_id"]}
            await conv_col.update_one(
                query_filter,
                {"$set": {"methodology_analysis": save_payload}}
            )
            print(f"💾 Methodology analysis cached for session {actual_session_id}")
        except Exception as db_err:
            print(f"⚠️ Could not cache analysis: {db_err}")

        # ── 7. Return result ───────────────────────────────────────────────
        return build_api_response(
            success=True,
            data={
                "meeting_id":             meeting_id,
                "session_id":             actual_session_id,
                "methodology":            methodology_name,
                "overall_coverage_score": analysis.get("overall_coverage_score", 0),
                "fields_analyzed":        analysis.get("fields_analyzed", []),
                "generated_at":           now.isoformat() if hasattr(now, "isoformat") else str(now),
                "cached":                 False,
            },
            message=f"Methodology coverage analysis complete — {analysis.get('overall_coverage_score', 0)}% coverage"
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ methodology-analysis error: {e}")
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))




async def _get_rep_voice_and_personality(rep: Dict) -> tuple:
    """Extract voice_id and personality from rep dict"""
    voice_id = rep.get("voice_id")
    traits = rep.get("personality_traits", [])
    personality = traits[0] if traits and isinstance(traits[0], str) else "neutral"
    return voice_id, personality


def _get_rep_personality_list(rep: Dict, meeting_personality: Optional[str]) -> List[str]:
    """Return a normalized personality list for reps, with meeting fallback."""
    rep_traits = rep.get("personality_traits")
    rep_personality = rep.get("personality")

    if isinstance(rep_traits, list) and rep_traits:
        return rep_traits
    if isinstance(rep_personality, list) and rep_personality:
        return rep_personality
    if isinstance(rep_personality, str) and rep_personality.strip():
        return [rep_personality.strip()]
    if isinstance(meeting_personality, str) and meeting_personality.strip():
        return [meeting_personality.strip()]
    return ["neutral"]


async def _generate_audio(text: str, voice_id: str, personality: str, gender: Optional[str] = None) -> bytes:
    """Generate TTS audio, return bytes or empty"""
    try:
        audio = await elevenlabs_service.text_to_speech(
            text=text, voice_id=voice_id, personality=personality, gender=gender
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
        # Check if meeting already passed expected end time
        expected_end = meeting.get("expected_end_time")
        if expected_end and current_timestamp() >= expected_end:
            # mark meeting completed
            started_at = meeting.get("started_at")
            ended_at = current_timestamp()
            duration_seconds = 0
            if started_at:
                duration_seconds = (ended_at - started_at).total_seconds()
            await meeting_collection.update_one({"_id": meeting_id}, {"$set": {"status": "completed", "ended_at": ended_at, "total_duration_seconds": duration_seconds}})
            return build_api_response(success=True, message="Meeting already ended due to scheduled end time")
        
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

        # Check for user-triggered end phrases
        msg_lower = message.lower()
        end_requested = False
        for phrase in END_PHRASES:
            if phrase in msg_lower:
                # mark meeting to end after agent responds
                await meeting_collection.update_one({"_id": meeting_id}, {"$set": {"end_after_response": True}})
                end_requested = True
                break

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
        primary_rep = None
        for rep in representatives:
            if rep.get("id") == ai_data.get("primary_rep_id"):
                primary_rep = rep
                break
        if not primary_rep:
            primary_rep = representatives[0]
        
        primary_text = ai_data.get("primary_response", "Could you tell me more?")
        primary_turn_number = current_turn + 1
        
        # Primary TTS — use primary rep's own gender
        v_id, personality = await _get_rep_voice_and_personality(primary_rep)
        rep_gender = (primary_rep.get("gender") or "female").lower()
        if rep_gender not in ("male", "female"):
            rep_gender = "female"
        primary_audio = await _generate_audio(primary_text, v_id, personality, rep_gender)
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
            rep_gender2 = (secondary_rep.get("gender") or "female").lower()
            if rep_gender2 not in ("male", "female"):
                rep_gender2 = "female"
            secondary_audio = await _generate_audio(secondary_text, v_id2, personality2, rep_gender2)
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
        
        # After saving turns, if an end was requested earlier, end the meeting now
        meeting_latest = await meeting_collection.find_one({"_id": meeting_id})
        ended_payload = None
        if meeting_latest.get("end_after_response"):
            started_at = meeting_latest.get("started_at")
            ended_at = current_timestamp()
            duration_seconds = 0
            if started_at:
                duration_seconds = (ended_at - started_at).total_seconds()
            await meeting_collection.update_one({"_id": meeting_id}, {"$set": {"status": "completed", "ended_at": ended_at, "total_duration_seconds": duration_seconds, "end_after_response": False}})
            ended_payload = {"ended_at": ended_at, "duration_seconds": duration_seconds}

        response_data = {
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
        }

        if ended_payload:
            response_data["meeting_ended"] = ended_payload

        return build_api_response(success=True, data=response_data, message="Message processed")
    
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

        # Fetch global admin system prompt (if set, overrides everything)
        config_col = get_system_config_collection()
        system_config = await config_col.find_one({"_id": "global_system_prompt"})
        admin_system_prompt = system_config.get("prompt", "").strip() if system_config else ""
        if admin_system_prompt:
            print("🔐 Admin system prompt active — overriding default + methodology")
        else:
            print("ℹ️ No admin prompt set — using built-in default + methodology")

        # Fetch role descriptions for all reps in this meeting
        from app.config.database import get_role_description_collection
        role_desc_col = get_role_description_collection()
        role_descriptions: Dict[str, str] = {}
        async for doc in role_desc_col.find():
            role_descriptions[doc["_id"]] = doc.get("description", "")
        print(f"📋 Loaded {len(role_descriptions)} role descriptions")
        
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
            "meeting_mode": meeting.get("meeting_mode"),
            "duration_minutes": meeting.get("duration_minutes"),
            "difficulty": meeting.get("difficulty"),
            "meeting_personality": meeting.get("personality"),
            "representatives": [
                {
                    "id": r["id"],
                    "name": r["name"],
                    "role": r["role"],
                    "personality": _get_rep_personality_list(r, meeting.get("personality")),
                    "is_decision_maker": r.get("is_decision_maker", False)
                }
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
                    
                    # Combine raw audio bytes — reorder WebM init chunk to front
                    # so the S3-stored file is a valid WebM container for ffmpeg.
                    _WEBM_MAGIC = b'\x1a\x45\xdf\xa3'
                    _init_idx = next(
                        (i for i, c in enumerate(chunks) if _WEBM_MAGIC in c[:64]),
                        None
                    )
                    if _init_idx is not None and _init_idx != 0:
                        chunks = [chunks[_init_idx]] + chunks[:_init_idx] + chunks[_init_idx + 1:]
                    combined_salesperson_audio = b"".join(chunks)

                    # ── PARALLEL: Whisper STT + DB fetch run at the same time ──
                    # Motor coroutines need an async wrapper to be used with create_task
                    async def _prefetch_conv():
                        return await conv_col.find_one({"session_id": session_id})

                    whisper_task      = asyncio.create_task(
                        whisper_service.transcribe_audio_stream(chunks)
                    )
                    db_prefetch_task  = asyncio.create_task(_prefetch_conv())

                    # Transcribe
                    try:
                        transcribed = await whisper_task
                        if not transcribed or transcribed.strip() == "":
                            print("⚠️ Empty transcription — audio too short or silent, skipping AI response")
                            db_prefetch_task.cancel()
                            await websocket.send_json({
                                "type": "transcription_empty",
                                "message": "Audio was too short or silent. Please speak clearly and try again."
                            })
                            continue
                        print(f"✅ Transcription: {transcribed}")
                        # Check for user-triggered end phrases in live transcription
                        msg_lower = transcribed.lower()
                        end_requested = False
                        for phrase in END_PHRASES:
                            if phrase in msg_lower:
                                # mark meeting to end after AI responds
                                await meeting_col.update_one({"_id": meeting_id}, {"$set": {"end_after_response": True}})
                                end_requested = True
                                break
                        if end_requested:
                            await websocket.send_json({"type": "meeting_will_end", "message": "Meeting will end after agent response"})
                    except Exception as e:
                        print(f"❌ Whisper error: {e}")
                        db_prefetch_task.cancel()
                        await websocket.send_json({"type": "error", "message": f"Speech recognition failed: {str(e)}"})
                        continue

                    await websocket.send_json({"type": "transcription", "text": transcribed, "speaker": "salesperson"})

                    # ── IMMEDIATE END: skip AI stream entirely if end was requested ──
                    if end_requested:
                        # Send a short goodbye directly — no OpenAI call needed
                        goodbye_text = "Thank you for the meeting. It was great speaking with you. Goodbye!"
                        await websocket.send_json({
                            "type": "ai_response_text",
                            "text": goodbye_text,
                            "speaker_name": representatives[0]["name"] if representatives else "Representative",
                            "speaker_role": representatives[0].get("role", "") if representatives else "",
                            "is_primary": True,
                            "is_chunk": False,
                        })
                        await websocket.send_json({"type": "no_audio"})

                        # Save salesperson turn in background (fire and forget)
                        _sp_turn_snap = {
                            "turn_number": 0, "speaker": "salesperson",
                            "speaker_name": "Salesperson", "text": transcribed,
                            "audio_url": None, "duration_seconds": 5.0,
                            "timestamp": "0:00", "created_at": current_timestamp()
                        }
                        async def _quick_save_end():
                            try:
                                await conv_col.update_one(
                                    {"session_id": session_id},
                                    {
                                        "$inc": {"salesperson_talk_time": 5.0},
                                        "$push": {"turns": _sp_turn_snap},
                                    }
                                )
                            except Exception:
                                pass
                        asyncio.create_task(_quick_save_end())

                        # End meeting immediately
                        meeting_latest = await meeting_col.find_one({"_id": meeting_id})
                        started_at = meeting_latest.get("started_at")
                        ended_at = current_timestamp()
                        duration_seconds = (ended_at - started_at).total_seconds() if started_at else 0
                        await meeting_col.update_one({"_id": meeting_id}, {"$set": {
                            "status": "completed", "ended_at": ended_at,
                            "total_duration_seconds": duration_seconds,
                            "end_after_response": False
                        }})
                        await websocket.send_json({
                            "type": "meeting_ended",
                            "message": "Meeting ended by user",
                            "ended_at": ended_at.isoformat(),
                            "duration_seconds": duration_seconds
                        })
                        print(f"✅ Meeting ended immediately on user phrase ({duration_seconds:.0f}s)")
                        break  # exit the while loop

                    # ── Normal flow: AI stream (only if NOT ending) ────────────
                    await websocket.send_json({"type": "ai_thinking", "message": "AI is thinking..."})

                    # ── PARALLEL: DB fetch already done alongside Whisper ──
                    # Direct address check first (zero latency, no API call needed)
                    msg_lower = transcribed.lower()
                    direct_rep = None
                    for rep in representatives:
                        rep_name = rep.get("name", "").lower().strip()
                        rep_role = rep.get("role", "").lower().strip()
                        if rep_name and rep_name in msg_lower:
                            direct_rep = rep
                            break
                        if rep_role and rep_role in msg_lower:
                            direct_rep = rep
                            break

                    async def _select_responder(conv_history_snapshot):
                        if direct_rep:
                            return direct_rep
                        responder_data = await openai_service.fast_identify_responder(
                            conversation_history=conv_history_snapshot,
                            representatives=representatives,
                            salesperson_data=salesperson,
                            company_data=company,
                            current_message=transcribed,
                            meeting_goal=meeting.get("meeting_goal", ""),
                            role_descriptions=role_descriptions,
                        )
                        for rep in representatives:
                            if rep.get("id") == responder_data.get("primary_rep_id"):
                                return rep
                        return representatives[0]

                    # Step 1: use the DB result already fetched in parallel with Whisper
                    conversation = await db_prefetch_task
                    conv_history = list(conversation.get("turns", []))
                    current_turn = conversation.get("total_turns", len(conv_history)) + 1

                    # Step 2: S3 upload + responder selection in parallel
                    salesperson_audio_bytes = combined_salesperson_audio if combined_salesperson_audio else b""

                    upload_task     = asyncio.create_task(
                        _upload_audio(salesperson_audio_bytes, meeting_id, current_turn, "salesperson")
                        if salesperson_audio_bytes else asyncio.sleep(0)
                    )
                    responder_task  = asyncio.create_task(_select_responder(conv_history))

                    # Wait for responder (usually faster than S3)
                    primary_rep = await responder_task
                    print(f"🎯 {'Direct' if direct_rep else 'AI'} → {primary_rep.get('name')} ({primary_rep.get('role')})")

                    # Build salesperson turn (S3 URL filled in after upload finishes)
                    salesperson_turn = {
                        "turn_number": current_turn, "speaker": "salesperson",
                        "speaker_name": "Salesperson", "text": transcribed,
                        "audio_url": None,  # filled after upload_task
                        "timestamp": format_duration(len(conv_history) * 10),
                        "duration_seconds": 5.0, "created_at": current_timestamp()
                    }
                    conv_history.append(salesperson_turn)

                    # Check scheduled end time
                    meeting_latest = await meeting_col.find_one({"_id": meeting_id})
                    exp_end = meeting_latest.get("expected_end_time")
                    if exp_end and current_timestamp() >= exp_end:
                        started_at = meeting_latest.get("started_at")
                        ended_at = current_timestamp()
                        duration_seconds = (ended_at - started_at).total_seconds() if started_at else 0
                        await meeting_col.update_one({"_id": meeting_id}, {"$set": {
                            "status": "completed", "ended_at": ended_at,
                            "total_duration_seconds": duration_seconds
                        }})
                        await websocket.send_json({"type": "meeting_ended",
                            "message": "Meeting ended due to scheduled end time",
                            "ended_at": ended_at.isoformat()})
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
                        methodology_prompt=methodology_prompt,
                        admin_system_prompt=admin_system_prompt,
                        role_descriptions=role_descriptions,
                    )

                    v_id, personality = await _get_rep_voice_and_personality(primary_rep)
                    rep_gender = (primary_rep.get("gender") or "female").lower()
                    if rep_gender not in ("male", "female"):
                        rep_gender = "female"
                    audio_stream = elevenlabs_service.stream_tts_websocket(
                        token_stream=token_stream,
                        voice_id=v_id,
                        personality=personality,
                        gender=rep_gender,
                    )

                    full_text = ""
                    full_audio_bytes = b""
                    chunk_no = 0

                    print(f"🚀 Starting WS stream to frontend for {primary_rep['name']}...")

                    async for msg_type, data in audio_stream:
                        if msg_type == "text":
                            full_text += data
                            await websocket.send_json({
                                "type": "ai_response_text",
                                "text": data,
                                "speaker_id": primary_rep["id"],
                                "speaker_name": primary_rep["name"],
                                "speaker_role": primary_rep["role"],
                                "is_primary": True,
                                "is_chunk": True
                            })
                        elif msg_type == "audio":
                            chunk_no += 1
                            full_audio_bytes += data
                            import base64
                            await websocket.send_json({
                                "type": "ai_audio_complete",
                                "audio_data": base64.b64encode(data).decode(),
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
                    await websocket.send_json({"type": "no_audio"})
                    print("✅ Stream finished!")

                    # ── POST-STREAM: collect S3 results + upload AI audio in parallel ──
                    primary_turn_number = current_turn + 1

                    # Collect salesperson S3 URL (upload_task started before stream)
                    try:
                        salesperson_audio_url = await upload_task
                    except Exception:
                        salesperson_audio_url = None
                    # ✅ Set BEFORE creating _finish_and_save task — closure captures the dict
                    salesperson_turn["audio_url"] = salesperson_audio_url

                    # Capture locals for the closure — avoids loop-variable overwrite bug
                    _full_audio_bytes   = full_audio_bytes
                    _full_text          = full_text
                    _primary_rep        = primary_rep
                    _primary_turn_num   = primary_turn_number
                    _salesperson_turn   = dict(salesperson_turn)  # snapshot, not reference

                    # Upload AI audio + DB save in background
                    async def _finish_and_save():
                        ai_audio_url = None
                        if _full_audio_bytes:
                            ai_audio_url = await _upload_audio(
                                _full_audio_bytes, meeting_id, _primary_turn_num, _primary_rep["id"]
                            )
                        p_turn = {
                            "turn_number": _primary_turn_num,
                            "speaker": _primary_rep["id"],
                            "speaker_name": _primary_rep["name"],
                            "text": _full_text,
                            "audio_url": ai_audio_url,
                            "timestamp": format_duration(len(conv_history) * 10),
                            "duration_seconds": max(1.0, len(_full_audio_bytes) / 32000),
                            "created_at": current_timestamp()
                        }
                        turns_to_save = [_salesperson_turn, p_turn]
                        total_ai_time = p_turn["duration_seconds"]
                        try:
                            await conv_col.update_one(
                                {"session_id": session_id},
                                {
                                    "$inc": {"salesperson_talk_time": 5.0, "representatives_talk_time": total_ai_time},
                                    "$push": {"turns": {"$each": turns_to_save}},
                                    "$set": {"total_turns": _primary_turn_num}
                                }
                            )
                            print(f"💾 Saved {len(turns_to_save)} turns (up to #{_primary_turn_num}) | salesperson audio: {_salesperson_turn.get('audio_url') is not None}")
                        except Exception as e:
                            print(f"❌ DB save error: {e}")
                        return p_turn

                    # Fire and forget — don't await, let stream continue
                    save_task = asyncio.create_task(_finish_and_save())

                    await websocket.send_json({
                        "type": "conversation_saved",
                        "session_id": session_id,
                        "turns": [
                            {"turn_number": current_turn, "speaker": "salesperson",
                             "speaker_name": "Salesperson", "text": transcribed},
                            {"turn_number": primary_turn_number, "speaker": primary_rep["id"],
                             "speaker_name": primary_rep["name"], "text": full_text},
                        ]
                    })

                    # Check if meeting should end after this response
                    meeting_now = await meeting_col.find_one({"_id": meeting_id})
                    if meeting_now.get("end_after_response"):
                        # Wait for save to complete before ending
                        await save_task
                        started_at = meeting_now.get("started_at")
                        ended_at = current_timestamp()
                        duration_seconds = 0
                        if started_at:
                            duration_seconds = (ended_at - started_at).total_seconds()
                        await meeting_col.update_one({"_id": meeting_id}, {"$set": {
                            "status": "completed", "ended_at": ended_at,
                            "total_duration_seconds": duration_seconds,
                            "end_after_response": False
                        }})
                        await websocket.send_json({
                            "type": "meeting_ended",
                            "message": "Meeting ended by user phrase after agent response",
                            "ended_at": ended_at.isoformat(),
                            "duration_seconds": duration_seconds
                        })
            
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