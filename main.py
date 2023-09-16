from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from ytmusicapi import YTMusic
from yt_dlp import YoutubeDL
from fastapi import FastAPI
from contextlib import redirect_stdout
from io import BytesIO

app = FastAPI()
ytm = YTMusic()

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AUDIO_OPTS = {
    'format': 'bestaudio[ext=m4a]',
    "outtmpl": "-",
    'logtostderr': True
}

@app.get("/download-audio/")
def download_tagged_audio_endpoint(video_id):
    buffer = BytesIO()
    with redirect_stdout(buffer), YoutubeDL(AUDIO_OPTS) as ydl:
        try:
            ydl.download(f"https://youtu.be/{video_id}")
        except Exception as e:
            return {"error": e}
        
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="audio/m4a")
