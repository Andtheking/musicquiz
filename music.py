from ytmusicapi import YTMusic
import yt_dlp
# from playsound import playsound as play
import os
import jsonpickle
import pylast
import random 
import re
from pydub import AudioSegment

from difflib import SequenceMatcher

from utils.jsonUtils import load_configs

import spotipy
import asyncio
import aiofiles
import pykakasi
import concurrent.futures

sp = spotipy.Spotify(auth_manager=spotipy.SpotifyOAuth(
    client_id=load_configs()['SPOTIFY']['CLIENT_ID'],
    client_secret=load_configs()['SPOTIFY']['CLIENT_SECRET'],
    redirect_uri="http://localhost:5500/callback",
    scope=None
))
PLAYLIST_ID = "37i9dQZEVXbIQnj7RRhdSX"

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

import difflib
import yt_dlp

def search_youtube_music(track_name, track_artist, yt: YTMusic):
    query = f"{track_name} {track_artist}"
    song_results = yt.search(query, limit=4)
    return song_results

def random_from_top50_spotify():
    results = sp.playlist(PLAYLIST_ID)
    if results['items']:
        tracks = results['items']
        random_track = random.choice(tracks)
        track_name = random_track['track']['name']
        artist_name = random_track['track']['artists'][0]['name']
        print(f"Canzone casuale dalla Top 50 Italia: {track_name} - {artist_name}")
    else:
        print("Non ci sono tracce nella playlist.")    

def random_track(network: pylast._Network, username) -> tuple[str, str]:
    top_tracks = network.get_user(username).get_recent_tracks(limit=150)
    unique_tracks = []
    seen_titles = set()

    for track in top_tracks:
        title = track.track.title
        if title not in seen_titles:
            seen_titles.add(title)
            unique_tracks.append(track)
    
    track: pylast.PlayedTrack = random.choice(unique_tracks)
    return (track.track.title, track.track.artist.name)

def format_title(title, artist=None) -> str | tuple[str, str]:
    titoli_regex = [
        (r"(.*) - Single", r"\1"),
        (r"(.*) - EP", r"\1"),
        (r"(.+) \(prod.+\)", r"\1"),
        (r"(.+)\(Lyric.+", r"\1"),
        (r"(.+)\(feat.+", r"\1"),
        (r"(.+)\(/w.+", r"\1"),
        (r"(.+)\(con.+", r"\1"),
        (r"(.+)\(Official.+", r"\1"),
    ]
    
    artisti_regex = [
        (r"(.+), (.+)", r"\1"),
        (r"(.+) e .+", r"\1"),
        (r"Theø.+", r"LA SAD"),
        (r"Fiks.+", r"LA SAD"),
        (r"Plant.+", r"LA SAD"),
        (r"tha supreme", r"thasup"),
        (r"thasup", r"thasup"),
        (r"La Sad", r"LA SAD"),
        (r"(Theø.*Plant.*Fiks|Theø.*Fiks.*Plant|Plant.*Theø.*Fiks|Plant.*Fiks.*Theø|Fiks.*Theø.*Plant|Fiks.*Plant.*Theø)", r"La Sad"),
    ]
    
    if title is not None:
        for i in titoli_regex:
            title = re.sub(i[0], i[1], title)
    
    if artist is not None:
        for i in artisti_regex:
            artist = re.sub(i[0], i[1], artist, flags=re.IGNORECASE)
    
    if artist:
        return (title, artist)    
    else:
        return title

kks = pykakasi.kakasi()
async def download_with_timeout(ydl:  yt_dlp.YoutubeDL, video_link, timeout=300):
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        try:
            await asyncio.wait_for(loop.run_in_executor(pool, ydl.download, video_link), timeout=timeout)
        except asyncio.TimeoutError:
            print("Download interrotto: tempo scaduto.")
            return None

def cut_random_15s(file_path: str, output_path: str):
    audio = AudioSegment.from_file(file_path)
    duration = len(audio)  # Durata in millisecondi

    if duration <= 15000:
        print("Il file è troppo corto per essere tagliato.")
        audio.export(output_path, format="mp3")
        return
    
    start_time = random.randint(0, duration - 15000)
    end_time = start_time + 15000
    
    cut_audio = audio[start_time:end_time]
    cut_audio.export(output_path, format="mp3")
    
async def Main(username):
    yt = YTMusic()
    keys = load_configs()['LAST_FM']
    api_key = keys['API_KEY']
    api_secret = keys['API_SECRET']
    ydl_opts = {
        'outtmpl': 'music/%(title)s.%(ext)s',
        'format': 'bestaudio[abr<=128]/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '5',
        }],
    }
    network = pylast.LastFMNetwork(api_key=api_key, api_secret=api_secret)
    try:
        track = await asyncio.to_thread(random_track, network, username)
    except:
        return None
    search_results = await asyncio.to_thread(search_youtube_music, track[0], track[1], yt)
    ok = False
    i = 0
    while not ok:
        if 'videoId' not in search_results[i]:
            continue    
        video_link = f"https://music.youtube.com/watch?v={search_results[i]['videoId']}"
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await asyncio.to_thread(ydl.extract_info, url=video_link, download=False)
            file_path = ydl.prepare_filename(info)
            file_path = file_path[0:file_path.rindex('.')] + '.mp3'
            if info['duration'] > 600:
                i += 1
            else:
                ok = True

    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        await download_with_timeout(ydl, video_link)
        
        cut_random_15s(file_path, file_path)
        
        result = kks.convert(info['title'])
        result2 = kks.convert(info['channel'])
        # FIXME: Che schifo ti prego sistema
        track = (
            (track[0], info['title'], " ".join([item['hepburn'] for item in result])), # Titolo
            (track[1], info['uploader'], " ".join([item['hepburn'] for item in result2])) # Artista
        )
    
    return (track, file_path)

if __name__ == "__main__":
    track = asyncio.run(Main('Mau428'))[0]
    guessed = False
    while not guessed:
        guess = input("Indovina la canzone:")
        guess = format_title(guess)
        for i in track[0]:
            correct = format_title(i)
            if similar(correct.lower(), guess.lower()) > 0.8:
                guessed = True
                break
        print("Bravo!" if guessed else "No!")
