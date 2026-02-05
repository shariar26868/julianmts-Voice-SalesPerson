from datetime import datetime
from typing import Any, Dict
import uuid


def generate_id() -> str:
    """Generate unique ID"""
    return str(uuid.uuid4())


def current_timestamp() -> datetime:
    """Get current UTC timestamp"""
    return datetime.utcnow()


def format_duration(seconds: float) -> str:
    """Format duration in seconds to HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def calculate_talk_time_ratio(
    salesperson_time: float,
    total_time: float
) -> float:
    """Calculate salesperson talk time ratio"""
    if total_time == 0:
        return 0.0
    return round((salesperson_time / total_time) * 100, 2)


def validate_file_type(filename: str, allowed_types: list) -> bool:
    """Validate if file extension is allowed"""
    extension = filename.split('.')[-1].lower()
    return extension in allowed_types


def get_content_type(filename: str) -> str:
    """Get content type based on file extension"""
    
    content_types = {
        'pdf': 'application/pdf',
        'pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'ppt': 'application/vnd.ms-powerpoint',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'doc': 'application/msword',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'mp3': 'audio/mpeg',
        'wav': 'audio/wav'
    }
    
    extension = filename.split('.')[-1].lower()
    return content_types.get(extension, 'application/octet-stream')


def build_api_response(
    success: bool,
    data: Any = None,
    message: str = None,
    error: str = None
) -> Dict[str, Any]:
    """Build standardized API response"""
    
    response = {
        "success": success,
        "timestamp": current_timestamp().isoformat()
    }
    
    if data is not None:
        response["data"] = data
    
    if message:
        response["message"] = message
    
    if error:
        response["error"] = error
    
    return response


def parse_personality_traits(traits: str) -> list:
    """Parse comma-separated personality traits into list"""
    if isinstance(traits, list):
        return traits
    return [t.strip() for t in traits.split(',') if t.strip()]


def merge_audio_files(audio_files: list) -> bytes:
    """
    Merge multiple audio files into one
    This is a placeholder - implement with pydub
    """
    # TODO: Implement audio merging with pydub
    pass


def extract_speaker_from_message(message: str) -> tuple:
    """
    Extract if message is directed to specific person
    Returns: (is_directed, person_name)
    """
    
    # Check for patterns like "Person1, what do you think?"
    import re
    
    patterns = [
        r"^([A-Z][a-z]+),",  # "John, what do you think?"
        r"I (?:asked|ask) (?:to )?([A-Z][a-z]+)",  # "I asked to John"
        r"(?:Hey |Hi )?([A-Z][a-z]+),",  # "Hey John,"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message)
        if match:
            return (True, match.group(1))
    
    return (False, None)