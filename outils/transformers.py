import spacy


def split_text_into_paragraphs_spacy(texts):
    """Split a text into paragraphs using spaCy for segmentation.

    Args:
        texts (str): Input text to be split.

    Returns:
        list of str: List of sentences/paragraphs extracted from the text.
    """
    try:
        nlp = spacy.load("fr_core_news_sm")
    except OSError:
        from spacy.cli import download
        download("fr_core_news_sm")
        nlp = spacy.load("fr_core_news_sm")

    spacy.util.fix_random_seed()
    nlp = spacy.load("fr_core_news_sm")
    nlp.max_length = len(texts) + 1000

    s = texts.replace('\n', ' ')
    docs = nlp(texts)
    return [sent.text for sent in docs.sents]


def textTosentences(texts):
    """Split multiple texts into sentences using spaCy for segmentation.

    Args:
        texts (dict): Dictionary with URLs as keys and text strings as values.

    Returns:
        dict: Dictionary with URLs as keys and lists of sentences as values.
    """
    texts_transformed = {}
    for url in texts.keys():
        texts_transformed[url] = split_text_into_paragraphs_spacy(texts[url])

    return texts_transformed
