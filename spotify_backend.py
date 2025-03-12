import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import dotenv

dotenv.load_dotenv()

def get_spotify_client():
    scope = "user-library-read playlist-modify-private playlist-modify-public playlist-read-private"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
        client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET"),
        redirect_uri=os.environ.get("SPOTIFY_REDIRECT_URI", "http://localhost:8501/callback"),
        scope=scope,
        cache_path=".cache"
    ))
    return sp

def get_all_liked_songs(sp):
    """Recupera todas las 'Liked Songs' mediante paginado."""
    offset = 0
    limit = 50
    songs = []
    while True:
        results = sp.current_user_saved_tracks(limit=limit, offset=offset)
        for item in results['items']:
            track = item['track']
            songs.append({
                "id": track["id"],
                "name": track["name"],
                "artist": ", ".join([artist["name"] for artist in track["artists"]]),
                "uri": track["uri"],
                "album": track["album"]["name"],
                "album_image": track["album"]["images"][0]["url"] if track["album"]["images"] else None
            })
        if len(results['items']) < limit:
            break
        offset += limit
    return songs

def get_user_playlists(sp):
    """Recupera las playlists del usuario."""
    playlists = []
    results = sp.current_user_playlists(limit=50)
    for playlist in results['items']:
        playlists.append({
            "id": playlist["id"],
            "name": playlist["name"],
            "description": playlist["description"],
            "images": playlist["images"]
        })
    return playlists

def get_playlist_songs(sp, playlist_id):
    """Recupera los URIs de las canciones ya presentes en una playlist (paginado)."""
    songs = []
    offset = 0
    limit = 100
    while True:
        results = sp.playlist_tracks(playlist_id, limit=limit, offset=offset)
        for item in results['items']:
            track = item['track']
            if track:
                songs.append(track["uri"])
        if len(results['items']) < limit:
            break
        offset += limit
    return songs

def get_difference_songs(sp, playlist_id, liked_songs):
    """
    Calcula la diferencia entre las 'Liked Songs' y las canciones ya presentes en la playlist.
    Devuelve aquellas canciones que están en 'Liked Songs' pero no en la playlist.
    """
    playlist_song_uris = set(get_playlist_songs(sp, playlist_id))
    difference = [song for song in liked_songs if song["uri"] not in playlist_song_uris]
    return difference

def add_songs_to_playlist(sp, playlist_id, song_uris):
    """Añade las canciones indicadas a la playlist en lotes de 100."""
    for i in range(0, len(song_uris), 100):
        batch = song_uris[i:i+100]
        sp.playlist_add_items(playlist_id, batch)