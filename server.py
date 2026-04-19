from http.server import SimpleHTTPRequestHandler, HTTPServer
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
            try:
                content_type = self.headers.get("Content-Type", "")
                if "boundary=" not in content_type:
                    raise ValueError("Invalid multipart request")

                content_length = int(self.headers["Content-Length"])
                post_data = self.rfile.read(content_length)
                boundary = content_type.split("boundary=")[1].encode()
                parts = post_data.split(b"--" + boundary)

                file_name = None
                os.makedirs(UPLOAD_DIR, exist_ok=True)

                for part in parts:
                    if b"Content-Disposition" in part and b"filename=" in part:
                        headers, body = part.split(b"\r\n\r\n", 1)
                        file_name = Path(UPLOAD_DIR) / "uploaded_song.mp3"
                        with open(file_name, "wb") as f:
                            f.write(body.strip(b"\r\n--"))
                        break

                if not file_name or not file_name.exists():
                    raise ValueError("No file uploaded")

                title, artist = extract_metadata(file_name)
                if not title or not artist:
                    self.send_response(400)
                    self.send_header("Content-type", "text/plain; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(b"Failed to extract metadata! Please upload an MP3 with title and artist tags.")
                    return

                with sync_playwright() as playwright:
                    lyrics = run(playwright, title, artist)

                self.send_response(200)
                self.send_header("Content-type", "text/plain; charset=utf-8")
                self.end_headers()
                if lyrics:
                    self.wfile.write(lyrics.encode("utf-8"))
                else:
                    self.wfile.write(b"Lyrics not found!")
            except Exception as exc:
                print(f"Upload processing error: {exc}")
                self.send_response(400)
                self.send_header("Content-type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"Upload processing failed. Please try again.")

if __name__ == "__main__":
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    PORT = 8000
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, LyricsRequestHandler)
    print(f"Serving on http://localhost:{PORT}")
    httpd.serve_forever()
