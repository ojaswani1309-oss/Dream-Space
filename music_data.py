from urllib.parse import quote_plus

CATEGORIES = [
    ("happy", "Happy", "☀️", "#FFE9A8"), ("calm", "Calm", "🌿", "#CDEBD8"), ("sad", "Sad", "🌧️", "#C9D8F0"),
    ("romantic", "Romantic", "💗", "#F9D3E0"), ("energetic", "Energetic", "⚡", "#FFD9B8"),
    ("relaxing", "Relaxing", "🫧", "#CFEFF5"), ("focus", "Focus", "🎧", "#DCD6F3"), ("sleep", "Sleep", "🌙", "#D5DDF2"),
]

_SONGS = {
    "happy": [("Walking on Sunshine", "Katrina & The Waves"), ("Happy", "Pharrell Williams"),
              ("Good as Hell", "Lizzo"), ("Lovely Day", "Bill Withers")],
    "calm": [("Weightless", "Marconi Union"), ("Clair de Lune", "Claude Debussy"),
             ("River Flows in You", "Yiruma"), ("Gymnopédie No. 1", "Erik Satie")],
    "sad": [("Fix You", "Coldplay"), ("Someone Like You", "Adele"), ("Skinny Love", "Bon Iver"),
            ("Liability", "Lorde")],
    "romantic": [("Perfect", "Ed Sheeran"), ("Can't Help Falling in Love", "Elvis Presley"),
                 ("La Vie en Rose", "Édith Piaf"), ("At Last", "Etta James")],
    "energetic": [("Can't Stop the Feeling!", "Justin Timberlake"), ("Dog Days Are Over", "Florence + The Machine"),
                  ("Uptown Funk", "Bruno Mars"), ("Dynamite", "BTS")],
    "relaxing": [("Banana Pancakes", "Jack Johnson"), ("Put Your Records On", "Corinne Bailey Rae"),
                 ("Here Comes the Sun", "The Beatles"), ("Better Together", "Jack Johnson")],
    "focus": [("Experience", "Ludovico Einaudi"), ("Time", "Hans Zimmer"), ("Nuvole Bianche", "Ludovico Einaudi"),
              ("Intro", "The xx")],
    "sleep": [("Spiegel im Spiegel", "Arvo Pärt"), ("Moonlight Sonata", "Beethoven"),
              ("Nocturne Op. 9 No. 2", "Chopin"), ("Sleep", "Max Richter")],
}

# which music category suits which mood
MOOD_TO_CATEGORY = {"happy": "happy", "good": "happy", "excited": "energetic", "loved": "romantic",
                    "calm": "calm", "neutral": "focus", "sad": "sad", "anxious": "relaxing",
                    "angry": "relaxing", "tired": "sleep"}


def songs_for(cat):
    meta = {c[0]: c for c in CATEGORIES}[cat]
    return [{"title": t, "artist": a, "emoji": meta[2], "color": meta[3],
             "url": "https://www.youtube.com/results?search_query=" + quote_plus(f"{t} {a}"),
             "spotify": "https://open.spotify.com/search/" + quote_plus(f"{t} {a}")}
            for t, a in _SONGS[cat]]
