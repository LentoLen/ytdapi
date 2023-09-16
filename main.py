from fastapi.middleware.cors import CORSMiddleware
from starlette.background import BackgroundTask
from fastapi.responses import FileResponse
from ytmusicapi import YTMusic
from yt_dlp import YoutubeDL
from fastapi import FastAPI
from io import BytesIO
from PIL import Image
import music_tag
import requests
import os

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
}

def get_audio_opts(out):
    opts = AUDIO_OPTS
    opts["outtmpl"] = out
    return opts

def get_artwork(url):
    artwork = requests.get(url)
    if artwork.status_code == 200:
        artwork = Image.open(BytesIO(artwork.content))
        artwork = artwork.crop(((artwork.width-artwork.height)//2, 0, ((artwork.width-artwork.height)//2)+artwork.height, artwork.height))
        byteart = BytesIO()
        artwork.save(byteart, format="PNG")
        return byteart.getvalue()
    return None

def tag_m4a(title, artist, album, thumbnail, lyrics, filepath):
    if os.path.exists(filepath):
        # add metadata
        m4a_file = music_tag.load_file(filepath)
        m4a_file["title"] = title
        m4a_file["artist"] = artist
        m4a_file["album"] = album
        if lyrics:
            m4a_file["lyrics"] = lyrics
        artwork = get_artwork(thumbnail)
        if artwork:
            m4a_file['artwork'] = artwork
        m4a_file.save()

@app.get("/download-audio/")
def download_tagged_audio_endpoint(video_id):
    filepath = f"/tmp/{video_id}.m4a"
    
    with YoutubeDL(get_audio_opts(filepath)) as ydl:
        try:
            infos = ydl.extract_info(f"https://youtu.be/{video_id}")
        except Exception:
            return None
    
    title = infos.get("title")
    artist = infos.get("artist")
    album = infos.get("album")
    if os.path.exists(filepath):
        thumbnail = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
        lyrics = ""
        browseId = ytm.get_watch_playlist(video_id)["lyrics"]
        if browseId != None:
            lyrics = ytm.get_lyrics(browseId)

        tag_m4a(title, artist, album, thumbnail, lyrics, filepath)
        return FileResponse(filepath, media_type="audio/m4a", background=BackgroundTask(cleanup, filepath))
    
    return None


def cleanup(tmp_file):
    os.remove(tmp_file)

@app.get("/get-tmp/")
def get_tmp_endpoint():
    return os.listdir("/tmp")
