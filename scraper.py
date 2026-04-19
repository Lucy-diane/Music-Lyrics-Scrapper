import os
from mutagen import File
from mutagen.easyid3 import EasyID3
from playwright.sync_api import Playwright, sync_playwright
from bs4 import BeautifulSoup


def extract_metadata(file_path: str):
    """
    Extract song metadata (title and artist) from the audio file.
    """
    try:
        audio = File(file_path, easy=True)
        if not audio:
            print("Could not read the audio file.")
            return None, None

        title = audio.get("title", [None])[0]
        artist = audio.get("artist", [None])[0]

        if not title or not artist:
            print("Metadata is missing in the file!")
        return title, artist
    except Exception as e:
        print(f"Error reading metadata: {e}")
        return None, None


def run(playwright: Playwright, title: str, artist: str):
    """
    Perform lyrics scraping from Genius.com.
    """
    search_query = f"{title} {artist}".strip()
    search_url = f"https://genius.com/search?q={search_query.replace(' ', '%20')}"

    # Launch the browser in headless mode
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    lyrics = None
    try:
        # Go to the Genius search page
        print(f"Searching for: {search_query}")
        page.goto(search_url, timeout=30000)

        # Wait for the first search result link to appear and click it
        print("Getting the first result")
        css_selector = '.column_layout-column_span.column_layout-column_span--primary a'
        first_res = page.locator(css_selector).first
        first_res.wait_for(timeout=15000)
        first_res.click()
        print("Clicked the first result")

        # Wait for the lyrics page to load
        page.wait_for_load_state("networkidle", timeout=30000)

        # Extract lyrics from the lyrics page
        print("Extracting lyrics")
        lyrics_page_html = page.content()
        soup = BeautifulSoup(lyrics_page_html, "html.parser")

        # Locate the lyrics container (try multiple selectors for robustness)
        lyrics_containers = soup.select('div[data-lyrics-container="true"]')
        if not lyrics_containers:
            lyrics_containers = soup.select('div[class*="Lyrics__Container"]')

        if not lyrics_containers:
            print("Couldn't find the lyrics on the page!")
        else:
            # Extract lyrics text
            lyrics = "\n".join([container.get_text(separator="\n", strip=True) for container in lyrics_containers])

    except Exception as e:
        print(f"Error during scraping: {e}")
    finally:
        browser.close()

    return lyrics


if __name__ == "__main__":
    print("Welcome to the Lyrics Scraper App!")
    print("1. Enter song metadata manually")
    print("2. Use a song file to extract metadata")
    choice = input("Choose an option (1 or 2): ").strip()

    title, artist = None, None

    if choice == "1":
        title = input("Enter the song title: ").strip()
        artist = input("Enter the artist name: ").strip()
        if not title or not artist:
            print("Please provide a valid song title and artist!")
            exit()
    elif choice == "2":
        file_path = input("Enter the path to the song file (e.g., MP3): ").strip()
        if not os.path.exists(file_path):
            print("File does not exist!")
            exit()

        title, artist = extract_metadata(file_path)
        if not title or not artist:
            print("Failed to extract metadata from the file.")
            exit()
    else:
        print("Invalid choice!")
        exit()

    # Proceed to scrape lyrics
    with sync_playwright() as playwright:
        lyrics = run(playwright, title, artist)
        if lyrics:
            print("\nExtracted Lyrics:\n")
            print(lyrics)

            # Save lyrics to a text file
            file_name = f"{title.replace(' ', '_')}_{artist.replace(' ', '_')}.txt"
            with open(file_name, "w", encoding="utf-8") as file:
                file.write(lyrics)
            print(f"Lyrics saved to {file_name}")
        else:
            print("Failed to scrape the lyrics.")
