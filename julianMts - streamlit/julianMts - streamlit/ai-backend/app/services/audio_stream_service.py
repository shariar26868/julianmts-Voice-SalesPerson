# import asyncio
# from typing import List, Dict, Any
# import base64


# class AudioStreamService:
#     """Handle audio streaming for WebSocket connections"""
    
#     def __init__(self):
#         self.active_streams = {}
    
#     def start_stream(self, meeting_id: str):
#         """Start a new audio stream for a meeting"""
#         self.active_streams[meeting_id] = {
#             "audio_chunks": [],
#             "is_speaking": False,
#             "last_activity": None
#         }
#         print(f"🎬 Started audio stream for meeting {meeting_id}")
    
#     def add_audio_chunk(self, meeting_id: str, audio_data: str):
#         """
#         Add audio chunk to stream
        
#         Args:
#             meeting_id: Meeting ID
#             audio_data: Base64 encoded audio chunk
#         """
#         if meeting_id not in self.active_streams:
#             self.start_stream(meeting_id)
        
#         try:
#             audio_bytes = base64.b64decode(audio_data)
#             self.active_streams[meeting_id]["audio_chunks"].append(audio_bytes)
#             self.active_streams[meeting_id]["is_speaking"] = True
#             print(f"📦 Added audio chunk: {len(audio_bytes)} bytes (total chunks: {len(self.active_streams[meeting_id]['audio_chunks'])})")
#         except Exception as e:
#             print(f"❌ Error decoding audio chunk: {e}")
    
#     def stop_speaking(self, meeting_id: str) -> List[bytes]:
#         """
#         Mark speaker as stopped and return collected audio
        
#         Returns:
#             List of audio chunks (bytes)
#         """
#         if meeting_id not in self.active_streams:
#             print(f"⚠️ No active stream for meeting {meeting_id}")
#             return []
        
#         self.active_streams[meeting_id]["is_speaking"] = False
#         chunks = self.active_streams[meeting_id]["audio_chunks"].copy()
        
#         print(f"🛑 Stopped speaking - collected {len(chunks)} chunks")
        
#         if chunks:
#             total_size = sum(len(chunk) for chunk in chunks)
#             print(f"📊 Total audio size: {total_size} bytes")
        
#         self.active_streams[meeting_id]["audio_chunks"] = []
        
#         return chunks
    
#     def is_speaking(self, meeting_id: str) -> bool:
#         """Check if user is currently speaking"""
#         if meeting_id not in self.active_streams:
#             return False
#         return self.active_streams[meeting_id]["is_speaking"]
    
#     def clear_stream(self, meeting_id: str):
#         """Clear stream data for a meeting"""
#         if meeting_id in self.active_streams:
#             del self.active_streams[meeting_id]
#             print(f"🧹 Cleared stream for meeting {meeting_id}")
    
#     async def stream_audio_response(self, audio_bytes: bytes, chunk_size: int = 4096):
#         """
#         Stream audio in chunks (for sending back to client)
        
#         Args:
#             audio_bytes: Complete audio data
#             chunk_size: Size of each chunk
            
#         Yields:
#             Base64 encoded audio chunks
#         """
#         total_chunks = (len(audio_bytes) + chunk_size - 1) // chunk_size
#         print(f"📤 Streaming {len(audio_bytes)} bytes in {total_chunks} chunks")
        
#         for i in range(0, len(audio_bytes), chunk_size):
#             chunk = audio_bytes[i:i + chunk_size]
#             yield base64.b64encode(chunk).decode('utf-8')
#             await asyncio.sleep(0.05)


# audio_stream_service = AudioStreamService()




import asyncio
from typing import List, Dict, Any
import base64


class AudioStreamService:
    """Handle audio streaming for WebSocket connections"""
    
    def __init__(self):
        self.active_streams = {}
    
    def start_stream(self, meeting_id: str):
        """Start a new audio stream for a meeting"""
        self.active_streams[meeting_id] = {
            "audio_chunks": [],
            "is_speaking": False,
            "last_activity": None
        }
        print(f"🎬 Started audio stream for meeting {meeting_id}")
    
    def add_audio_chunk(self, meeting_id: str, audio_data: str):
        """
        Add audio chunk to stream
        
        Args:
            meeting_id: Meeting ID
            audio_data: Base64 encoded audio chunk
        """
        if meeting_id not in self.active_streams:
            self.start_stream(meeting_id)
        
        try:
            audio_bytes = base64.b64decode(audio_data)
            self.active_streams[meeting_id]["audio_chunks"].append(audio_bytes)
            self.active_streams[meeting_id]["is_speaking"] = True
            print(f"📦 Added audio chunk: {len(audio_bytes)} bytes (total chunks: {len(self.active_streams[meeting_id]['audio_chunks'])})")
        except Exception as e:
            print(f"❌ Error decoding audio chunk: {e}")
    
    def stop_speaking(self, meeting_id: str) -> List[bytes]:
        """
        Mark speaker as stopped and return collected audio
        
        Returns:
            List of audio chunks (bytes)
        """
        if meeting_id not in self.active_streams:
            print(f"⚠️ No active stream for meeting {meeting_id}")
            return []
        
        self.active_streams[meeting_id]["is_speaking"] = False
        chunks = self.active_streams[meeting_id]["audio_chunks"].copy()
        
        print(f"🛑 Stopped speaking - collected {len(chunks)} chunks")
        
        if chunks:
            total_size = sum(len(chunk) for chunk in chunks)
            print(f"📊 Total audio size: {total_size} bytes")
        
        self.active_streams[meeting_id]["audio_chunks"] = []
        
        return chunks
    
    def is_speaking(self, meeting_id: str) -> bool:
        """Check if user is currently speaking"""
        if meeting_id not in self.active_streams:
            return False
        return self.active_streams[meeting_id]["is_speaking"]
    
    def clear_stream(self, meeting_id: str):
        """Clear stream data for a meeting"""
        if meeting_id in self.active_streams:
            del self.active_streams[meeting_id]
            print(f"🧹 Cleared stream for meeting {meeting_id}")
    
    async def stream_audio_response(self, audio_bytes: bytes, chunk_size: int = 16384):
        """
        ✅ FIXED: Stream audio in larger chunks with proper timing for smooth playback
        
        Args:
            audio_bytes: Complete audio data
            chunk_size: Size of each chunk (16KB = ~1 second of audio at 128kbps)
            
        Yields:
            Base64 encoded audio chunks
        """
        total_size = len(audio_bytes)
        total_chunks = (total_size + chunk_size - 1) // chunk_size
        
        print(f"📤 Streaming {total_size} bytes in {total_chunks} chunks (chunk_size: {chunk_size} bytes)")
        
        for i in range(0, total_size, chunk_size):
            chunk = audio_bytes[i:i + chunk_size]
            chunk_number = (i // chunk_size) + 1
            
            # Encode to base64
            base64_chunk = base64.b64encode(chunk).decode('utf-8')
            
            print(f"  📦 Chunk {chunk_number}/{total_chunks}: {len(chunk)} bytes")
            
            yield base64_chunk
            
            # ✅ FIXED: Proper delay calculation for smooth streaming
            # MP3 bitrate ~128kbps = 16,000 bytes/second
            # So each chunk represents: chunk_size / 16000 seconds of audio
            # We use 70% of that time to allow for buffering overlap
            
            chunk_duration_seconds = len(chunk) / 16000  # Duration this chunk represents
            delay = chunk_duration_seconds * 0.7  # 70% overlap for smooth transition
            
            # Minimum delay to avoid overwhelming the client
            delay = max(delay, 0.05)
            
            await asyncio.sleep(delay)
        
        print(f"✅ Finished streaming {total_chunks} chunks")


audio_stream_service = AudioStreamService()