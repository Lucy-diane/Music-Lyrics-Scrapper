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

    def do_POST(self):
        if self.path == "/upload":
            # Parse the multipart form data
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            boundary = self.headers["Content-Type"].split("boundary=")[1].encode()
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

            # Run the scraper
            with sync_playwright() as playwright:
                lyrics = run(playwright, title, artist)

            # Send the response
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            if lyrics:
                self.wfile.write(lyrics.encode("utf-8"))
            else:
                self.wfile.write(b"Lyrics not found!")

if __name__ == "__main__":
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    PORT = 8000
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, LyricsRequestHandler)
    print(f"Serving on http://localhost:{PORT}")
    httpd.serve_forever()
