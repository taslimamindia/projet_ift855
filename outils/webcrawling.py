import requests
from bs4 import BeautifulSoup

def request_url(url):
    """ Fait une requête HTTP GET à l'URL donnée et retourne le contenu HTML."""

    response = requests.get(url)
    response.raise_for_status()
    return response.text

def parse_html(html):
    """ Parse le contenu HTML avec BeautifulSoup et retourne l'objet soup.
    
    Args:
        html (str): Le contenu HTML à parser.
    """

    soup = BeautifulSoup(html, 'html.parser')
    return soup

def extract_https_urls(soup, domain):
    """ Extrait les URLs HTTPS du même domaine que l'url fourni.
    
    Args:
        soup (BeautifulSoup): L'objet BeautifulSoup du contenu HTML.
        domain (str): Le domaine à filtrer (ex: 'example.com').
    """

    https_urls = []
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if href.startswith('https://') and domain.lower() in href.lower() and not href.endswith('.pdf') :
            https_urls.append(href)
    return https_urls

def extract_text(soup):
    """ Extrait le texte du contenu HTML.

    Args:
        soup (BeautifulSoup): L'objet BeautifulSoup du contenu HTML.
    """

    texts = soup.stripped_strings
    return " ".join(texts)

def clean_documents(texts):
    """ Nettoie les documents en supprimant les entrées vides.
    
    Args:
        texts (dict): Dictionnaire avec les URLs comme clés et le texte extrait comme valeurs.
    """

    cleaned_texts = {}
    for url, text in texts.items():
        if text:
            cleaned_texts[url] = text
    return cleaned_texts

def recursive_crawl(url, domain, max_depth=2, current_depth=0, visited=None, texts=None):
    """ Effectue un crawl récursif à partir de l'URL donnée jusqu'à une profondeur maximale.

    Args:
        url (str): L'URL de départ pour le crawl.
        domain (str): Le domaine à filtrer (ex: 'example.com').
        max_depth (int): La profondeur maximale du crawl.
        current_depth (int): La profondeur actuelle du crawl.
        visited (set): Ensemble des URLs déjà visitées.
        texts (dict): Dictionnaire pour stocker les textes extraits.
    """

    if visited is None:
        visited = set()
        
    if texts is None:
        texts = {}
    
    if current_depth > max_depth or url in visited:
        return None
    
    try:
        html_content = request_url(url)
        parsed_soup = parse_html(html_content)
        new_urls = extract_https_urls(parsed_soup, domain)
        text_content = extract_text(parsed_soup)
        visited.add(url)
        texts[url] = text_content

        if new_urls == []:
            return None
        else:
            for new_url in new_urls:
                recursive_crawl(new_url, domain, max_depth, current_depth + 1, visited, texts)
    except requests.RequestException as e:
        print(f"Failed to retrieve {url}")
        visited.add(url)
        return None

    return visited, texts

def crawl(data):
    """ Effectue un crawl pour une liste d'URLs.

    Args:
        data (list): Liste de tuple qui comprend l'url, le domaine, et la profondeur de recherche.
    """

    visited = set()
    texts = {}

    for entry in data:
        url, domain, max_depth = entry
        recursive_crawl(url, domain, max_depth=max_depth, visited=visited, texts=texts)

    cleaned_texts = clean_documents(texts)
    return visited, cleaned_texts