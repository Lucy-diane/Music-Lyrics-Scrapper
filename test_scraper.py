import unittest

from scraper import build_search_url, extract_lyrics_from_html


class ScraperHelpersTests(unittest.TestCase):
    def test_build_search_url_encodes_query(self):
        url = build_search_url("Love Story", "Taylor Swift")
        self.assertEqual(url, "https://genius.com/search?q=Love+Story+Taylor+Swift")

    def test_extract_lyrics_from_data_container(self):
        html = """
        <html><body>
            <div data-lyrics-container="true">Line one<br/>Line two</div>
        </body></html>
        """
        self.assertEqual(extract_lyrics_from_html(html), "Line one\nLine two")

    def test_extract_lyrics_returns_none_when_missing(self):
        self.assertIsNone(extract_lyrics_from_html("<html><body><p>No lyrics</p></body></html>"))


if __name__ == "__main__":
    unittest.main()
