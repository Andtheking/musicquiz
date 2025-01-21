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

def search_youtube_music(track_name, track_artist, yt):
    query = f"{track_name} {track_artist}"

    # Esegui la ricerca per "songs"
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




def random_track(network: pylast._Network, username) -> tuple[str,str]:
    # Recupera le top 50 tracce dell'utente
    
    top_tracks = network.get_user(username).get_recent_tracks(limit=150)
    #.get_top_tracks(limit=150)


    # Filtra per tracce uniche
    unique_tracks = []
    seen_titles = set()

    for track in top_tracks:
        title = track.track.title
        if title not in seen_titles:
            seen_titles.add(title)
            unique_tracks.append(track)
            
    # Seleziona una traccia casuale tra le top 50
    track: pylast.PlayedTrack = random.choice(unique_tracks)
    track_name = track.track.title
    artist_name = track.track.artist.name

    return (track_name, artist_name)

def format_title(title, artist = None) -> str|tuple[str,str]:
    # Regex per i titoli delle canzoni
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

    # Regex per gli artisti delle canzoni
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

import aiofiles, asyncio, pykakasi
kks = pykakasi.kakasi()

async def Main(username):
        
    yt = YTMusic()

    
    keys = load_configs()['LAST_FM']

    api_key = keys['API_KEY']
    api_secret = keys['API_SECRET']

    ydl_opts = {
        'outtmpl': 'music/%(title)s.%(ext)s',
        'format': 'bestaudio[abr<=128]/best',  # Limita il bitrate massimo a 128kbps
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '5',  # Valori più alti indicano qualità inferiore
        }],
    }


    # Autenticazione all'API di Last.fm
    network = pylast.LastFMNetwork(api_key=api_key, api_secret=api_secret)
    try:
        track = await asyncio.to_thread(random_track, network, username)
    except:
        return None
    query = f"{track[0]} {track[1]}"
    search_results =  await asyncio.to_thread(search_youtube_music, track[0], track[1], yt)
    # search_results = yt.search(query, filter="videos", limit=4)

    # Ottieni il primo risultato utile
    ok = False
    i = 0
    while not ok:
        if not 'videoId' in search_results[i]:
            continue    
        video_link = f"https://music.youtube.com/watch?v={search_results[i]['videoId']}"
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await asyncio.to_thread(ydl.extract_info, url=video_link, download=False)
            if info['duration'] > 600:
                i += 1
            else:
                ok = True

    track = ([track[0], info['title'], " ".join([k['hepburn'] for k in kks.convert(track[0])])],[track[1], info['channel'], " ".join([k['hepburn'] for k in kks.convert(track[1])])])
    print(f"Link del primo risultato: {video_link}")
    print(f"Soluzione: {track[0]} di {track[1]}")
    

    file = None
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        file = await asyncio.to_thread(ydl.prepare_filename, info)
        dir =  os.listdir('music')
        if not file[:-4] + 'mp3' in dir:
            error_code = await asyncio.to_thread(ydl.download, video_link)
    
    audio = AudioSegment.from_file(file[:-4] + 'mp3')
    audio_length = len(audio)
    segment_duration = 15 * 1000

    if audio_length > segment_duration:
        # Calcola un punto casuale di inizio
        start_time = random.randint(0, audio_length - segment_duration)
        end_time = start_time + segment_duration

        # Estrai il segmento
        segment = audio[start_time:end_time]

        # Salva il segmento estratto in un file temporaneo
        output_file = f"{file[:-4]}_{start_time}_{end_time}.mp3"
        segment.export(output_file, format="mp3")
    else:
        output_file = file[:-4] + 'mp3'
        
    return (track, output_file)


if __name__ == "__main__":
    track, file = asyncio.run(Main('Mau428'))
    from threading import Thread

    guessed = False
    while not guessed:
        guess = input("Indovina la canzone:")
        
        
        guess = format_title(guess)
        
        for i in track[0]:
            correct = format_title(i)
            check = similar(correct.lower(), guess.lower())
            if check > 0.8:
                guessed = True
                break
                
        if guessed:
            print("Bravo!")
        else:
            print("No!")