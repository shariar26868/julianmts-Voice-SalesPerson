import re

path = "app/routes/conversation.py"
content = open(path, "r", encoding="utf-8").read()

old = (
    '                        try:\n'
    '                            transcribed_text = await whisper_service.transcribe_audio_stream(audio_chunks)\n'
    '                            \n'
    '                            if not transcribed_text or transcribed_text.strip() == "":\n'
    '                                print("⚠️ Empty transcription, using fallback")\n'
    "                                transcribed_text = \"I said something but it wasn't clear.\"\n"
    '                            \n'
    '                            print(f"✅ Transcription: {transcribed_text}")\n'
    '                            \n'
    '                        except Exception as e:\n'
    '                            print(f"❌ Whisper transcription error: {e}")\n'
    '                            import traceback\n'
    '                            traceback.print_exc()\n'
    '                            \n'
    '                            await websocket.send_json({\n'
    '                                "type": "error",\n'
    '                                "message": f"Speech recognition failed: {str(e)}"\n'
    '                            })\n'
    '                            \n'
    "                            transcribed_text = \"Sorry, I couldn't understand that.\""
)

new = (
    '                        try:\n'
    '                            transcribed_text = await whisper_service.transcribe_audio_stream(audio_chunks)\n'
    '                            \n'
    '                            if not transcribed_text or transcribed_text.strip() == "":\n'
    '                                print("⚠️ Empty transcription — audio too short or silent, skipping AI response")\n'
    '                                await websocket.send_json({\n'
    '                                    "type": "transcription_empty",\n'
    '                                    "message": "Audio was too short or silent. Please speak clearly and try again."\n'
    '                                })\n'
    '                                continue\n'
    '                            \n'
    '                            print(f"✅ Transcription: {transcribed_text}")\n'
    '                            \n'
    '                        except Exception as e:\n'
    '                            print(f"❌ Whisper transcription error: {e}")\n'
    '                            import traceback\n'
    '                            traceback.print_exc()\n'
    '                            \n'
    '                            await websocket.send_json({\n'
    '                                "type": "error",\n'
    '                                "message": f"Speech recognition failed: {str(e)}"\n'
    '                            })\n'
    '                            continue'
)

if old in content:
    content = content.replace(old, new, 1)
    open(path, "w", encoding="utf-8").write(content)
    print("✅ Root patch applied successfully")
else:
    print("❌ Pattern not found in root conversation.py")
    idx = content.find("Empty transcription")
    if idx >= 0:
        print(repr(content[idx-100:idx+300]))
