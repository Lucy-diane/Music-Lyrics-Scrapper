import os
from urllib.parse import quote_plus
from playwright.sync_api import Playwright, sync_playwright
from bs4 import BeautifulSoup
from metadata import extract_metadata


def build_search_url(title: str, artist: str) -> str:
    query = f"{title} {artist}".strip()
    return f"https://genius.com/search?q={quote_plus(query)}"


def extract_lyrics_from_html(html: str):
    soup = BeautifulSoup(html, "html.parser")

    containers = soup.select('div[data-lyrics-container="true"]')
    if not containers:
        containers = soup.select('div[class^="Lyrics__Container"]')

    if not containers:
        return None

    lyrics_lines = [container.get_text(separator="\n", strip=True) for container in containers]
    return "\n".join(lyrics_lines).strip() or None


def run(playwright: Playwright, title: str, artist: str):
    """
    Perform lyrics scraping from Genius.com.
    """
    if not title or not artist:
        return None

    search_url = build_search_url(title, artist)

    browser = playwright.chromium.launch(headless=True, timeout=30000)
    context = browser.new_context()
    page = context.new_page()

    try:
        page.goto(search_url, timeout=30000, wait_until="domcontentloaded")
        search_page_html = page.content()
        search_soup = BeautifulSoup(search_page_html, "html.parser")

        top_result = search_soup.select_one('a[href*="-lyrics"]')
        if not top_result:
            return None

        top_result_link = top_result.get("href")
        if not top_result_link:
            return None

        page.goto(top_result_link, timeout=30000, wait_until="domcontentloaded")
        lyrics_page_html = page.content()
        return extract_lyrics_from_html(lyrics_page_html)
    finally:
        browser.close()


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
