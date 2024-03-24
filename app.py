import os
from flask import Flask, session, request, redirect, render_template, jsonify  # Make sure to include render_template here
from flask_session import Session
import spotipy

app = Flask(__name__, static_url_path='', static_folder='static')
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)


@app.route('/')
def index():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(scope = "user-read-private user-read-email user-read-currently-playing playlist-modify-private playlist-read-private user-modify-playback-state",
                                               cache_handler=cache_handler,
                                               show_dialog=True)

    if request.args.get("code"):
        auth_manager.get_access_token(request.args.get("code"))
        return redirect('/')

    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        auth_url = auth_manager.get_authorize_url()
        return '<h2><a href="{auth_url}">Sign in</a></h2>'

    spotify = spotipy.Spotify(auth_manager=auth_manager)
    now_playing = spotify.currently_playing()
    if now_playing:
        track_name = now_playing['item']['name']
        artist_name = now_playing['item']['artists'][0]['name']
    else:
        track_name = "No track playing"
        artist_name = ""

    display_name = spotify.me()["display_name"]
    return render_template('now_playing.html', track_name=track_name, artist_name=artist_name, display_name=display_name)


@app.route('/now_playing_data')
def now_playing_data():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return {'error': 'Not authenticated'}, 401  # Return an error code if not authenticated

    spotify = spotipy.Spotify(auth_manager=auth_manager)
    now_playing = spotify.currently_playing()
    if now_playing:
        track_name = now_playing['item']['name']
        artist_name = now_playing['item']['artists'][0]['name']
        album_art_url = now_playing['item']['album']['images'][0]['url']
    else:
        track_name = "No track playing"
        artist_name = ""
        album_art_url = ""
    
    return {'track_name': track_name, 'artist_name': artist_name, 'album_art_url': album_art_url}


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        search_query = request.form.get('search_query')
        cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
        auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
        if not auth_manager.validate_token(cache_handler.get_cached_token()):
            return redirect('/')
        spotify = spotipy.Spotify(auth_manager=auth_manager)
        results = spotify.search(q=search_query, type='track', limit=10)
        tracks = results['tracks']['items']
        return render_template('search_results.html', tracks=tracks)
    return render_template('search.html')


@app.route('/add_to_queue')
def add_to_queue():
    track_uri = request.args.get('uri')
    if track_uri:
        cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
        auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
        if not auth_manager.validate_token(cache_handler.get_cached_token()):
            return redirect('/')
        spotify = spotipy.Spotify(auth_manager=auth_manager)
        spotify.add_to_queue(uri=track_uri)
        #return "Track added to queue. <a href='/search'>Search again</a> | <a href='/'>home</a>"
        return render_template('added_to_queue.html')
    return "No track specified. <a href='/'>home</a>"



@app.route('/sign_out')
def sign_out():
    session.pop("token_info", None)
    return redirect('/')

@app.route('/play')
def play():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    spotify.start_playback()
    return jsonify({'success': True})

@app.route('/pause')
def pause():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    spotify.pause_playback()
    return jsonify({'success': True})

@app.route('/next')
def next_track():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    spotify.next_track()
    return jsonify({'success': True})

@app.route('/previous')
def previous_track():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    spotify.previous_track()
    return jsonify({'success': True})

@app.route('/playlists')
def playlists():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')

    spotify = spotipy.Spotify(auth_manager=auth_manager)
    playlists = spotify.current_user_playlists(limit=10)

    return render_template('playlists.html', playlists=playlists['items'])

@app.route('/play_playlist', methods=['POST'])
def play_playlist():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
#    playlist_uri = request.form.get('playlist_uri')
    playlist_uri = request.json['playlist_uri']
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    spotify.start_playback(context_uri=playlist_uri)
    return jsonify({'success': True})


'''
Following lines allow application to be run more conveniently with
`python app.py` (Make sure you're using python3)
(Also includes directive to leverage pythons threading capacity.)
'''
if __name__ == '__main__':
    app.run(threaded=True, port=int(os.environ.get("PORT",
                                                   os.environ.get("SPOTIPY_REDIRECT_URI", 8888).split(":")[-1])))