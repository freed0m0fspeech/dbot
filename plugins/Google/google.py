from typing import Union

import requests
import urllib
from bs4 import BeautifulSoup
from requests_html import HTMLSession


class LyricScraperException(Exception):
    """Handles all lyrics extractor exceptions."""


class ScraperFactory:
    """All scrapers are defined here."""

    PARAGRAPH_BREAK = '\n\n'
    source_code = None
    title = None

    def __call__(self, source_code, title):
        self.source_code = source_code
        self.title = title

    def _update_title(self, title):
        self.title = title

    def _genius_scraper_method_1(self):
        extract = self.source_code.select(".lyrics")
        if not extract:
            return None

        lyrics = (extract[0].get_text()).replace('<br>', '\n').strip()
        return lyrics

    def _genius_scraper_method_2(self):
        all_extracts = self.source_code.select(
            'div[class*="Lyrics__Container-sc-"]')
        if not all_extracts:
            return None

        lyrics = ''
        for extract in all_extracts:
            for br in extract.find_all("br"):
                br.replace_with("\n")
            lyrics += extract.get_text()

        return lyrics.strip()

    def genius_scraper(self):
        lyrics = self._genius_scraper_method_1() or self._genius_scraper_method_2()

        self._update_title(self.title[:-16])

        return lyrics

    def glamsham_scraper(self):
        extract = self.source_code.find_all('font', class_='general')[5]
        if not extract:
            return None

        for br in extract.find_all("br"):
            br.replace_with("\n")
        lyrics = extract.get_text()
        self._update_title(self.title[:-14].strip())

        return lyrics

    def lyricsbell_scraper(self):
        extract = self.source_code.select(".lyrics-col p")
        if not extract:
            return None

        lyrics = ''
        for i in range(len(extract)):
            lyrics += extract[i].get_text() + self.PARAGRAPH_BREAK

        lyrics = lyrics.replace('<br>', '\n').strip()
        self._update_title(self.title[:-13])

        return lyrics

    def lyricsted_scraper(self):
        extract = self.source_code.select(".lyric-content p")
        if not extract:
            return None

        lyrics = ''
        for i in range(len(extract)):
            lyrics += extract[i].get_text().strip() + self.PARAGRAPH_BREAK

        lyrics = lyrics.replace('<br>', '\n').strip()

        return lyrics

    def lyricsoff_scraper(self):
        extract = self.source_code.select("#main_lyrics p")
        if not extract:
            return None

        lyrics = ''
        for i in range(len(extract)):
            lyrics += extract[i].get_text(separator="\n").strip() + self.PARAGRAPH_BREAK

        return lyrics.strip()

    def lyricsmint_scraper(self):
        extract = self.source_code.find('section', {'id': 'lyrics'}).find_all('p')
        if not extract:
            return None

        lyrics = ''
        for i in range(len(extract)):
            lyrics += extract[i].get_text().strip() + self.PARAGRAPH_BREAK

        return lyrics.strip()


class Google:
    """
        Takes in Google Custom Search API & Google Engine ID in contructor args.
        Call get_lyrics function with song_name as args to get started.
        Handle raised LyricScraperException by importing it alongside.
    """

    scraper_factory = ScraperFactory()
    SCRAPERS = {
        "genius": scraper_factory.genius_scraper,
        #'glamsham': scraper_factory.glamsham_scraper,
        #'lyricsbell': scraper_factory.lyricsbell_scraper,
        #'lyricsted': scraper_factory.lyricsted_scraper,
        #'lyricsoff': scraper_factory.lyricsoff_scraper,
        #'lyricsmint': scraper_factory.lyricsmint_scraper,
    }

    def __init__(self, api_key: str, engine_id: str):
        self.__api_key = api_key
        self.__engine_id = engine_id

    def __handle_search_request(self, title):
        title = urllib.parse.quote_plus(title)
        url = f"https://www.google.com/search?q=site:https://genius.com/ {title} lyrics"
        #url = "https://www.google.com/search"
        params = {
            'q': 'site:https://genius.com/ {} lyrics'.format(title),
        }

        try:
            session = HTMLSession()
            response = session.get(url=url)
        except requests.exceptions.RequestException:
            return None

        css_identifier_result = ".tF2Cxc"
        css_identifier_title = "h3"
        css_identifier_link = ".yuRUbf a"
        #css_identifier_text = ".IsZvec"

        results = response.html.find(css_identifier_result)

        data = []

        for result in results:
            item = {
                'title': result.find(css_identifier_title, first=True).text,
                'link': result.find(css_identifier_link, first=True).attrs['href'],
                # 'text': result.find(css_identifier_text, first=True).text
            }

            data.append(item)

        if response.status_code != 200:
            # TODO exeption
            raise LyricScraperException(data)

        return data

    def __extract_lyrics(self, result_url, title):
        # Get the page source code
        page = requests.get(result_url)
        source_code = BeautifulSoup(page.content, 'lxml')

        self.scraper_factory(source_code, title)
        for domain, scraper in self.SCRAPERS.items():
            if domain in result_url:
                lyrics = scraper()

        return lyrics

    def lyrics(self, song_name: str) -> Union[dict, None]:
        """
            Fetches and autocorrects (if incorrect) song name.
            Gets URL and title of the top Results.
            Extracts lyrics by using one of the available scrapers.
            Raises LyricScraperException on handling errors.
            Returns dict with title, lyrics and link.
        """

        data = self.__handle_search_request(song_name)

        #spell = data.get('spelling', {}).get('correctedQuery')
        #data = (spell and self.__handle_search_request(spell)) or data
        #query_results = data.get('items', [])
        query_results = data

        # Try scraping lyrics from top results
        for i in range(len(query_results)):
            result_url = query_results[i]["link"]
            title = query_results[i]["title"]
            try:
                lyrics = self.__extract_lyrics(result_url, title)
            except Exception as err:
                raise LyricScraperException(err)
                # TODO exception

            if lyrics:
                return {
                    "title": self.scraper_factory.title,
                    "lyrics": lyrics,
                    "link": result_url
                }

            return None

        # TODO exception
        # raise LyricScraperException({"error": "No results found"})
