from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

def extract_metadata(file_path):
    try:
        # Load MP3 file and its metadata
        audio = MP3(file_path, ID3=EasyID3)
        title = audio.get("title", [None])[0]
        artist = audio.get("artist", [None])[0]
        normalized_title = title.strip() if isinstance(title, str) else title
        normalized_artist = artist.strip() if isinstance(artist, str) else artist
        return normalized_title, normalized_artist
    except Exception as e:
        print(f"Error extracting metadata: {e}")
        return None, None
