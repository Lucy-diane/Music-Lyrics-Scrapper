from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

def normalize_metadata_field(value):
    return value.strip() if isinstance(value, str) else value


def extract_metadata(file_path):
    try:
        # Load MP3 file and its metadata
        audio = MP3(file_path, ID3=EasyID3)
        title = audio.get("title", [None])[0]
        artist = audio.get("artist", [None])[0]
        return normalize_metadata_field(title), normalize_metadata_field(artist)
    except Exception as e:
        print(f"Error extracting metadata: {e}")
        return None, None
