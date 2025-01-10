from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3

def extract_metadata(file_path):
    try:
        # Load MP3 file and its metadata
        audio = MP3(file_path, ID3=EasyID3)
        title = audio.get("title", ["Unknown"])[0]
        artist = audio.get("artist", ["Unknown"])[0]
        return title, artist
    except Exception as e:
        print(f"Error extracting metadata: {e}")
        return None, None
