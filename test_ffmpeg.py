import asyncio
import tempfile
import subprocess
import os
import imageio_ffmpeg

def merge_audio_files_ffmpeg(chunks: list[bytes]) -> bytes:
    if not chunks:
        return b""
    if len(chunks) == 1:
        # maybe we should still transcode just in case it's webm
        pass

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    temp_files = []
    
    try:
        # 1. Write chunks to temporary files
        for chunk in chunks:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.tmp')
            tmp.write(chunk)
            tmp.close()
            temp_files.append(tmp.name)

        # 2. Build the ffmpeg command
        # ffmpeg -i file1 -i file2 -filter_complex "[0:a][1:a]concat=n=2:v=0:a=1[out]" -map "[out]" out.mp3
        cmd = [ffmpeg_exe, "-y"]
        for f in temp_files:
            cmd.extend(["-i", f])
            
        filter_str = "".join([f"[{i}:a]" for i in range(len(temp_files))])
        filter_str += f"concat=n={len(temp_files)}:v=0:a=1[out]"
        
        cmd.extend(["-filter_complex", filter_str, "-map", "[out]"])
        cmd.extend(["-c:a", "libmp3lame", "-b:a", "128k"])
        
        out_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
        cmd.append(out_file)

        # 3. Run ffmpeg
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"FFmpeg error: {res.stderr}")
            raise Exception("FFMPEG failed")
            
        with open(out_file, 'rb') as f:
            return f.read()

    finally:
        for f in temp_files:
            if os.path.exists(f): os.remove(f)
        try:
            if os.path.exists(out_file): os.remove(out_file)
        except:
            pass

print("Function defined.")
