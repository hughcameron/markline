from copy import copy
from datetime import datetime, timezone

import markline as ml
from bs4 import BeautifulSoup

# This short URL: https://tinyurl.com/mrx7da4n
# redirects to the test page at: https://raw.githubusercontent.com/hughcameron/markline/main/tests/test.html

SHORT_URL = "https://tinyurl.com/mrx7da4n"
LONG_URL = "https://raw.githubusercontent.com/hughcameron/markline/main/tests/test.html"
IMG_URL = (
    "https://raw.githubusercontent.com/hughcameron/markline/main/tests/coffee.jpeg"
)


test_page = ml.Markup(SHORT_URL)

with open("tests/test.html") as f:
    local_page = BeautifulSoup(f.read(), "html.parser")


def add_byline(markup: ml.Markup):

    authors = ", ".join(test_page.meta.get("article:author"))
    byline = ml.new_tag("strong", literal="By " + authors)

    header = markup.draft.find("h1")
    header.insert_after(byline)


def test_version():
    assert ml.__version__ == "0.1.0"


def test_package_available():
    assert ml.package_available("urllib")


def test_unshorten_url():
    """Test the short_url function."""
    assert test_page.url == LONG_URL


def test_trim_url():
    """Test the trim_url function."""
    utm_tag = "?utm_source=test&utm_medium=test&utm_campaign=test"
    assert ml.trim_url(LONG_URL + utm_tag) == LONG_URL


def test_prepare_url():
    """Test the prepare_url function."""
    assert ml.prepare_url(SHORT_URL) == LONG_URL
    assert ml.prepare_url(LONG_URL) == LONG_URL


def test_coalesce():
    """Test the coalesce function."""
    assert ml.coalesce(None, "default") == "default"


def test_parse_time():
    """Test the parse_time function."""
    expected = datetime(2022, 8, 21, 3, 42, 10, tzinfo=timezone.utc)
    test_timestamp = "2022-08-21T03:42:10Z"
    assert ml.parse_time(test_timestamp) == expected


def test_download_media():
    assert ml.download_media(IMG_URL) == "coffee.jpeg"


def test_new_tag():
    """Test the new_tag function."""
    expected = '<p class="test">\n test\n</p>'
    test_tag = ml.new_tag("p", literal="test", attrs={"class": "test"}).prettify()
    assert test_tag == expected


def test_quote_caption():
    """Test the quote_caption function.
    test_page.draft is reset to ensure the test suite remains idempotent.
    """
    expected = (
        "<blockquote>\n A takeaway coffee with the morning news.\n</blockquote>\n"
    )
    ml.quote_caption(test_page.draft.find("figure"))
    soup_result = test_page.draft.find("blockquote").prettify()
    test_page.draft = copy(test_page.original)
    assert soup_result == expected


def test_fetch_content():
    assert test_page.original.prettify() == local_page.prettify()


def test_gather_meta():
    expected = {
        "UTF-8": None,
        "X-UA-Compatible": "IE=edge",
        "viewport": "width=device-width, initial-scale=1.0",
        "keywords": "HTML5, Article, Publishing",
        "author": "Webber Page",
        "title": "Tips for writing a news article",
        "description": "Learn how to publish articles in HTML5",
        "og:type": "article",
        "og:url": "https://raw.githubusercontent.com/hughcameron/markline/main/tests/test.html",
        "og:title": "Tips for writing a news article",
        "og:site_name": "Webber Publishing",
        "og:description": "Learn how to publish articles in HTML5",
        "og:image": "https://raw.githubusercontent.com/hughcameron/markline/main/tests/coffee.jpeg",
        "article:tag": ["Publishing", "Article"],
        "article:author": ["Webber Page"],
        "twitter:card": "summary_large_image",
        "twitter:domain": "raw.githubusercontent.com",
        "twitter:url": "https://raw.githubusercontent.com/hughcameron/markline/main/tests/test.html/",
        "twitter:title": "Tips for writing a news article",
        "twitter:description": "Learn how to publish articles in HTML5",
        "twitter:image": "https://raw.githubusercontent.com/hughcameron/markline/main/tests/coffee.jpeg",
    }
    assert test_page.meta == expected


def test_set_properties():
    expected = {
        "title": "Tips for writing a news article",
        "url": "https://raw.githubusercontent.com/hughcameron/markline/main/tests/test.html",
        "description": "Learn how to publish articles in HTML5",
        "publisher": "Webber Publishing",
    }
    assert test_page.properties == expected


def test_add_properties():
    """Test the add_properties function
    test_page.properties is reset to ensure the test suite remains idempotent.
    """
    expected = {
        "title": "Tips for writing a news article",
        "url": "https://raw.githubusercontent.com/hughcameron/markline/main/tests/test.html",
        "description": "Learn how to publish articles in HTML5",
        "publisher": "Webber Publishing",
        "authors": ["Webber Page"],
    }
    test_page.add_properties({"authors": test_page.meta.get("article:author")})
    update_result = copy(test_page.properties)
    del test_page.properties["authors"]
    assert update_result == expected


def test_edit():
    """Test the edit method.
    test_page.draft is reset to ensure the test suite remains idempotent.
    """
    expected = "<strong>\n By Webber Page\n</strong>\n"
    test_page.edit(add_byline)
    soup_result = test_page.draft.find("strong").prettify()
    test_page.draft = copy(test_page.original)
    assert soup_result == expected


def test_apply():
    pass


def test_filter():
    expected = (
        "<figcaption>\n A takeaway coffee with the morning news.\n</figcaption>\n"
    )
    test_page.filter(ml.loc("figcaption"))
    soup_result = test_page.draft.prettify()
    test_page.draft = copy(test_page.original)
    assert soup_result == expected


def test_drop():
    expected = '<article>\n <h1 id="tips-for-writing-a-news-article">\n  Tips for writing a news article\n </h1>\n</article>\n'
    test_page.drop(
        [
            ml.loc("figure"),
            ml.loc("section"),
            ml.loc("p"),
            ml.loc("hr"),
        ]
    )
    soup_result = test_page.draft.find("article").prettify()
    test_page.draft = copy(test_page.original)
    assert soup_result == expected


def test_render():
    pass


def test_to_html():
    pass


def test_to_md():
    pass
