from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse, urljoin
import tldextract
import trafilatura


class Crawling:
    def __init__(self):
        """
        Initializes the class with default attributes for HTML parsing,
        tracking visited URLs, storing extracted text, and handling robots.txt rules.

        Attributes:
            soup (BeautifulSoup | None): Parsed HTML content.
            visited (set | None): Set of visited URLs.
            texts (dict | None): Extracted texts by URL.
            rp (RobotFileParser | None): Robots.txt parser.
        """
        
        self.soup:BeautifulSoup = None
        self.visited:set = None
        self.texts:dict = None
        self.rp: RobotFileParser = None


    def scrape_autorization(self, url: str, user_agent: str = "MyScraperBot"):
        """Download and prepare a RobotFileParser for the target site's robots.txt.

        Args:
            url (str): Target URL to inspect.
            user_agent (str): Name of the bot (default: "MyScraperBot").

        Returns:
            RobotFileParser: parser configured with the site's robots.txt URL (not yet read).
        """
        
        parsed_url = urlparse(url)
        robots_url = urljoin(f"{parsed_url.scheme}://{parsed_url.netloc}", "/robots.txt")
        
        rp = RobotFileParser()
        rp.set_url(robots_url)
        return rp


    def can_scrape(self, rp, url:str, user_agent: str = "MyScraperBot"):
        """
        Check if a given URL is allowed to be scraped according to the site's robots.txt rules.

        Args:
            rp (RobotFileParser): Object of parser file.
            url (str): The target URL you want to scrape.
            user_agent (str): The name of your bot or crawler (default: "MyScraperBot").

        Returns:
            bool: True if scraping the URL is allowed by robots.txt, False otherwise.
        """
        try:
            rp.read()
            return rp.can_fetch(user_agent, url)
        except:
            return False


    def extract_https_urls(self, domain):
        """Extract HTTPS URLs from the same domain as provided.

        Args:
            domain (str): Domain to filter (e.g., 'example.com').

        Returns:
            list of str: List of HTTPS URLs belonging to the specified domain.
        """
        
        https_urls = []
        extension = ('.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.zip', '.rar', '.svg', '.mp4', '.mp3', '.avi', '.mov')
        for a_tag in self.soup.find_all('a', href=True):
            href = a_tag['href']
            if href.startswith('https://') and domain.lower() in href.lower() and not href.endswith(extension):
                https_urls.append(href)
        return https_urls


    def extract_text(self, url, params=None):
        """
        Extract and clean visible text content from a web page.

        This method optionally appends query parameters to the given URL, retrieves the 
        corresponding HTML content using `trafilatura.fetch_url`, and then extracts 
        all visible text by parsing the HTML with BeautifulSoup.

        Args:
            url (str): The base URL of the web page to extract text from.
            params (dict, optional): Optional dictionary of query parameters to append to the URL. Defaults to None.

        Returns:
            str: Cleaned and concatenated visible text from the page, or an empty string if fetching failed.
        """

        from urllib.parse import urlencode

        if params:
            url = url + "?" + urlencode(params)
        
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return ""

        self.soup = BeautifulSoup(downloaded, "html.parser")
        texts = self.soup.stripped_strings
        return " ".join(texts)


    def clean_documents(self, texts):
        """Clean documents by removing empty entries.

        Args:
            texts (dict): Dictionary with URLs as keys and extracted text as values.

        Returns:
            dict: Filtered dictionary containing only entries with at least 100 characters.
        """
        
        cleaned_texts = {}
        for url, text in texts.items():
            if text and len(text) > 100:
                cleaned_texts[url] = text
        return cleaned_texts


    def recursive_crawl(self, url, domain, extract_function, max_depth=2, current_depth=0, params=None):
        """Perform a recursive crawl starting from the given URL up to a maximum depth.

        Args:
            url (str): Starting URL for the crawl.
            domain (str): Domain to filter (e.g., 'example.com').
            max_depth (int): Maximum depth of the crawl.
            current_depth (int): Current depth of the crawl.
        
        Returns:
            tuple:
                - set: Visited URLs.
                - dict: Dictionary of extracted texts from URLs.
        """

        if url in self.visited:
            return None
        
        try:
            self.texts[url] = extract_function(url, params)
            new_urls = self.extract_https_urls(domain)
            self.visited.add(url)

            # stop if max depth reached or no new urls
            if current_depth >= max_depth or not new_urls:
                return None

            new_urls = [u for u in new_urls if u not in self.visited]
            for new_url in new_urls:
                self.recursive_crawl(new_url, domain, extract_function, max_depth, current_depth + 1)

        except Exception:
            # mark as visited and continue on errors
            self.visited.add(url)
            return None


    def crawl(self, data):
        """Perform crawling for a list of URLs.

        Args:
            data (list of tuple): List of tuples containing (URL, domain, max_depth).

        Returns:
            tuple:
                - set: Set of all visited URLs.
                - dict: Dictionary of cleaned extracted texts.
        """

        self.visited = set()
        self.texts = {}

        for entry in data:
            url, domain, max_depth = entry
            self.recursive_crawl(url, domain, self.extract_text, max_depth=max_depth)

        self.texts = self.clean_documents(self.texts)


    def crawl_with_control(self, url, params=None, max_depth=2, mode_search=False):
        """Perform crawling for with control of robots.txt.

        Args:
            url (str): url from user request.
        """

        self.visited = set()
        self.texts = {}

        self.rp = self.scrape_autorization(url)

        if not self.can_scrape(self.rp, url):
            return False, "Désolé, conformément aux règles de navigation de ce site, l’exploration par les robots n’est pas autorisée !!!"
        
        if mode_search:
            self.extract_text(url, params=params)
            form = self.soup.find("form")
            if form:
                url = form.get("action")
            else:
                params = None
        
        ext = tldextract.extract(url)
        self.recursive_crawl(url, f"{ext.domain}.{ext.suffix}", self.extract_text, max_depth, params=params)
        self.texts = self.clean_documents(self.texts)
