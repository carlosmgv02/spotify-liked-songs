import streamlit as st
from spotify_backend import (
    get_spotify_client,
    get_user_playlists,
    get_all_liked_songs,
    get_difference_songs,
    add_songs_to_playlist
)
import datetime

st.set_page_config(page_title="Spotify Playlist Refresher", layout="wide")
st.title("Spotify Playlist Refresher")

# --- Barra lateral: Programación y vista de playlists ---
with st.sidebar:
    st.header("Opciones de Programación")
    scheduled_time = st.time_input("Programar recarga a la hora",
                                   value=datetime.datetime.now().time())
    if st.button("Programar recarga"):
        st.success(
            f"La playlist se recargará a las {scheduled_time.strftime('%H:%M:%S')}. (Nota: la ejecución programada es solo de interfaz)")
    st.header("Información de Playlists")

# --- Sección 0: Cliente autenticado ---
sp = get_spotify_client()

# --- Sección 1: Selección de Playlist destino ---
st.header("Selecciona la Playlist Destino")
playlists = get_user_playlists(sp)
if playlists:
    playlist_options = {}
    for playlist in playlists:
        image_url = playlist["images"][0]["url"] if playlist["images"] else None
        playlist_options[playlist["name"]] = {"id": playlist["id"], "image": image_url}
    playlist_names = list(playlist_options.keys())
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_playlist_name = st.selectbox("Elige la playlist a actualizar", playlist_names)
    with col2:
        selected_playlist = playlist_options[selected_playlist_name]
        if selected_playlist["image"]:
            st.image(selected_playlist["image"], width=100)
    selected_playlist_id = playlist_options[selected_playlist_name]["id"]
else:
    st.error("No se pudieron obtener tus playlists. Asegúrate de estar autenticado correctamente.")
    st.stop()

# --- Sección 2: Recuperar canciones faltantes ---
if st.button("Obtener canciones faltantes"):
    with st.spinner("Recuperando canciones guardadas..."):
        liked_songs = get_all_liked_songs(sp)
        diff_songs = get_difference_songs(sp, selected_playlist_id, liked_songs)
        st.session_state["all_diff_songs"] = diff_songs
        # Guardamos un índice para la visualización en caso de querer ver la selección manual
        st.session_state["display_index"] = 20
    st.success(f"Se encontraron {len(diff_songs)} canciones faltantes.")

# --- Sección 3: Opciones de actualización ---
if "all_diff_songs" in st.session_state:
    diff_songs = st.session_state["all_diff_songs"]
    total_missing = len(diff_songs)
    st.write(f"**Total de canciones faltantes: {total_missing}**")

    # Permite elegir el modo de actualización
    modo = st.radio("Elige el modo de actualización", ["Añadir todas", "Seleccionar manualmente"])

    if modo == "Añadir todas":
        if st.button("Añadir todas las canciones faltantes"):
            all_uris = [song["uri"] for song in diff_songs]
            add_songs_to_playlist(sp, selected_playlist_id, all_uris)
            st.success(
                f"Se han añadido {len(all_uris)} canciones a la playlist '{selected_playlist_name}'.")
    else:
        st.write("Modo de selección manual (se muestran en páginas de 20 canciones):")
        display_index = st.session_state.get("display_index", 20)
        songs_to_show = diff_songs[:display_index]

        # Se muestran las canciones con su imagen y nombre; se usan checkboxes individuales
        selected_uris = []
        for song in songs_to_show:
            with st.container():
                cols = st.columns([1, 4])
                with cols[0]:
                    if song["album_image"]:
                        st.image(song["album_image"], width=80)
                with cols[1]:
                    if st.checkbox(f"{song['name']} - {song['artist']}", key=song["id"]):
                        selected_uris.append(song["uri"])

        if display_index < total_missing:
            if st.button("Cargar más canciones"):
                st.session_state["display_index"] = display_index + 20
                # La reejecución natural de Streamlit actualizará la visualización con más canciones
        if st.button("Añadir canciones seleccionadas"):
            if selected_uris:
                add_songs_to_playlist(sp, selected_playlist_id, selected_uris)
                st.success(
                    f"Se han añadido {len(selected_uris)} canciones a la playlist '{selected_playlist_name}'.")
            else:
                st.warning("No has seleccionado ninguna canción.")