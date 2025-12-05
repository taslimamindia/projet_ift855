from bs4 import BeautifulSoup
from outils.webcrawling import Crawling


def test_extract_https_urls_and_clean_documents():
    crawler = Crawling()

    html = (
        '<html><body>'
        '<a href="/path">rel</a>'
        '<a href="https://example.com/page">in</a>'
        '<a href="https://external.com/other">out</a>'
        '</body></html>'
    )

    crawler.soup = BeautifulSoup(html, "html.parser")
    urls = crawler.extract_https_urls("https://example.com", domain="example.com")

    assert "https://example.com/path" in urls
    assert "https://example.com/page" in urls
    assert not any("external.com" in u for u in urls)

    texts = {
        "https://a": "short",
        "https://b": "This is a sufficiently long text that should be kept because it has more than fifty characters." 
    }
    cleaned = crawler.clean_documents(texts)
    assert "https://a" not in cleaned
    assert "https://b" in cleaned
