import asyncio
from typing import List, Dict, Any
import base64


class AudioStreamService:
    """Handle audio streaming for WebSocket connections"""
    
    def __init__(self):
        self.active_streams = {}  # meeting_id: {audio_chunks, is_speaking}
    
    def start_stream(self, meeting_id: str):
        """Start a new audio stream for a meeting"""
        self.active_streams[meeting_id] = {
            "audio_chunks": [],
            "is_speaking": False,
            "last_activity": None
        }
    
    def add_audio_chunk(self, meeting_id: str, audio_data: str):
        """
        Add audio chunk to stream
        
        Args:
            meeting_id: Meeting ID
            audio_data: Base64 encoded audio chunk
        """
        if meeting_id not in self.active_streams:
            self.start_stream(meeting_id)
        
        # Decode base64 audio
        audio_bytes = base64.b64decode(audio_data)
        self.active_streams[meeting_id]["audio_chunks"].append(audio_bytes)
        self.active_streams[meeting_id]["is_speaking"] = True
    
    def stop_speaking(self, meeting_id: str) -> List[bytes]:
        """
        Mark speaker as stopped and return collected audio
        
        Returns:
            List of audio chunks
        """
        if meeting_id not in self.active_streams:
            return []
        
        self.active_streams[meeting_id]["is_speaking"] = False
        chunks = self.active_streams[meeting_id]["audio_chunks"].copy()
        
        # Clear chunks for next turn
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
    
    async def stream_audio_response(self, audio_bytes: bytes, chunk_size: int = 4096):
        """
        Stream audio in chunks (for sending back to client)
        
        Args:
            audio_bytes: Complete audio data
            chunk_size: Size of each chunk
            
        Yields:
            Base64 encoded audio chunks
        """
        for i in range(0, len(audio_bytes), chunk_size):
            chunk = audio_bytes[i:i + chunk_size]
            # Encode to base64 for WebSocket transmission
            yield base64.b64encode(chunk).decode('utf-8')
            # Small delay to simulate streaming
            await asyncio.sleep(0.05)


# Singleton instance
audio_stream_service = AudioStreamService()