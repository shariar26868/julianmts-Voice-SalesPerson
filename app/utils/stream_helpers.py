import re

async def sentence_buffer(async_token_stream):
    """
    Takes an async generator of tokens (strings) and yields
    complete sentences as they are formed.
    """
    buffer = ""
    # We look for ., ?, ! followed by a space or end of string, 
    # but we should be careful not to split on e.g., "Mr.", "U.S.A.", etc.
    # For a simple robust TTS split, we can just split on [.?!][\n\s]
    # We'll use a simple regex approach:
    sentence_end_pattern = re.compile(r'([.?!])(\s+|$)')
    
    async for token in async_token_stream:
        buffer += token
        
        while True:
            match = sentence_end_pattern.search(buffer)
            if not match:
                break
            
            # Found a sentence!
            end_idx = match.end()
            sentence = buffer[:end_idx].strip()
            
            if sentence:
                yield sentence
                
            buffer = buffer[end_idx:]
            
    # Yield any remaining text
    buffer = buffer.strip()
    if buffer:
        yield buffer
