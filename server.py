from http.server import SimpleHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
from scraper import run
from metadata import extract_metadata
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

UPLOAD_DIR = "uploads"

class LyricsRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        # Serve the HTML and CSS files
        if self.path == "/":
            self.path = "index.html"
        elif self.path == "/style.css":
            self.path = "style.css"
        return super().do_GET()

    def _send_lyrics(self, title, artist):
        """Run the scraper and send lyrics as the HTTP response."""
        with sync_playwright() as playwright:
            lyrics = run(playwright, title, artist)

        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        if lyrics:
            self.wfile.write(lyrics.encode("utf-8"))
        else:
            self.wfile.write(b"Lyrics not found!")

    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        content_type = self.headers.get("Content-Type", "")

        if self.path == "/search":
            # Handle manual title + artist form submission
            params = parse_qs(post_data.decode("utf-8"))
            title = params.get("title", [None])[0]
            artist = params.get("artist", [None])[0]
            if not title or not artist:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Please provide both a song title and artist name!")
                return
            self._send_lyrics(title.strip(), artist.strip())

        elif self.path == "/upload":
            # Parse the multipart form data
            boundary = content_type.split("boundary=")[1].encode()
            parts = post_data.split(b"--" + boundary)

            # Extract the file content
            for part in parts:
                if b"Content-Disposition" in part:
                    headers, body = part.split(b"\r\n\r\n", 1)
                    file_name = Path(UPLOAD_DIR) / "uploaded_song.mp3"
                    with open(file_name, "wb") as f:
                        f.write(body.strip(b"\r\n--"))

            # Extract metadata
            title, artist = extract_metadata(file_name)
            if not title or not artist:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Failed to extract metadata!")
                return

            self._send_lyrics(title, artist)

if __name__ == "__main__":
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    PORT = 8000
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, LyricsRequestHandler)
    print(f"Serving on http://localhost:{PORT}")
    httpd.serve_forever()
