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

    # Launch the browser
    browser = playwright.chromium.launch(headless=False, channel='chrome')
    context = browser.new_context()
    page = context.new_page()

    # Go to the Genius search page
    print(f"Searching for: {search_query}")
    page.goto(search_url, timeout=0)
    page.wait_for_load_state("networkidle")

    # Parse search results
    search_page_html = page.content()
    soup = BeautifulSoup(search_page_html, "html.parser")

    # Select the search results container
    results_div = soup.select_one(".search_results")
    if not results_div:
        print("No search results found!")
        browser.close()
        return None

    # Get the top search result link
    top_result = results_div.select_one("a")
    if not top_result:
        print("No top result link found!")
        browser.close()
        return None

    # Extract and navigate to the top result link
    top_result_link = top_result.get("href")
    print(f"Navigating to the top result: {top_result_link}")
    page.goto(top_result_link, timeout=0)
    page.wait_for_load_state("networkidle")

    # Extract lyrics from the lyrics page
    lyrics_page_html = page.content()
    soup = BeautifulSoup(lyrics_page_html, "html.parser")

    # Locate the lyrics container
    lyrics_containers = soup.select('div[class^="Lyrics__Container"]')

    if not lyrics_containers:
        print("Couldn't find the lyrics on the page!")
        browser.close()
        return None

    # Extract lyrics text
    lyrics = "\n".join([container.get_text(separator="\n", strip=True) for container in lyrics_containers])

    # Close the browser
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
