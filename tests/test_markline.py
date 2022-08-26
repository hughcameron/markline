from copy import copy
from datetime import datetime, timezone

import markline as ml
from bs4 import BeautifulSoup

SHORT_URL = "https://tinyurl.com/mrx7da4n"
# This short URL: https://tinyurl.com/mrx7da4n
# redirects to the test page at: https://raw.githubusercontent.com/hughcameron/markline/main/tests/test.html
LONG_URL = "https://raw.githubusercontent.com/hughcameron/markline/main/tests/test.html"
IMG_URL = (
    "https://raw.githubusercontent.com/hughcameron/markline/main/tests/coffee.jpeg"
)
LOCAL_HTML = "tests/test.html"


remote_html = ml.Markup(SHORT_URL)
local_html = ml.Markup(filepath=LOCAL_HTML)

with open("tests/test.html") as f:
    soup_html = BeautifulSoup(f.read(), "lxml")

with open("tests/test.md") as f:
    local_md = f.read()


def add_byline(markup: ml.Markup):
    """Add a byline to the article.
    This is a test function for the edit method.

    Args:
        markup (ml.Markup): The markup object to edit.
    """
    authors = ", ".join(remote_html.meta.get("article:author"))
    byline = ml.new_tag("strong", literal="By " + authors)

    header = markup.draft.find("h1")
    header.insert_after(byline)


def test_version():
    """Ensure test suite is up to date with the latest version."""
    assert ml.__version__ == "0.1.0"


def test_package_available():
    assert ml.package_available("urllib")


def test_unshorten_url():
    """Test the short_url function."""
    assert remote_html.url == LONG_URL


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


def test_extract():
    """Test the extract function."""
    expected = "123"
    string = "this-is-a-test-123"
    pattern = r"\-(\d+)$"
    assert ml.extract(pattern, string) == expected


def test_extract_slice():
    """Test the extract function."""
    expected = ["this", "is"]
    string = "this-is-a-test-123"
    pattern = r"(\w+)"
    assert ml.extract(pattern, string, slice(0, 2)) == expected


def test_extract_all():
    """Test the extract_all function."""
    expected = ["this", "is", "a", "test", "123"]
    string = "this-is-a-test-123"
    pattern = r"(\w+)"
    assert ml.extract_all(pattern, string) == expected


def test_parse_time():
    """Test the parse_time function."""
    expected = datetime(2022, 8, 21, 3, 42, 10, tzinfo=timezone.utc)
    test_timestamp = "2022-08-21T03:42:10Z"
    assert ml.parse_time(test_timestamp) == expected


def test_download_media():
    """Test the download_media method."""
    assert ml.download_media(IMG_URL) == "coffee.jpeg"


def test_new_tag():
    """Test the new_tag function."""
    expected = '<p class="test">\n test\n</p>'
    test_tag = ml.new_tag("p", literal="test", attrs={"class": "test"}).prettify()
    assert test_tag == expected


def test_quote_caption():
    """Test the quote_caption function.
    remote_html.draft is reset to ensure the test suite remains idempotent.
    """
    expected = (
        "<blockquote>\n A takeaway coffee with the morning news.\n</blockquote>\n"
    )
    ml.quote_caption(remote_html.draft.find("figure"))
    soup_result = remote_html.draft.find("blockquote").prettify()
    remote_html.draft = copy(remote_html.original)
    assert soup_result == expected


def test_fetch_url_content():
    assert remote_html.original.prettify() == soup_html.prettify()


def test_fetch_local_content():
    assert local_html.original.prettify() == soup_html.prettify()


def test_gather_meta():
    """Test the gather_meta function."""
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
    assert remote_html.meta == expected


def test_set_properties():
    """Test the set_properties function."""
    expected = {
        "title": "Tips for writing a news article",
        "url": "https://raw.githubusercontent.com/hughcameron/markline/main/tests/test.html",
        "description": "Learn how to publish articles in HTML5",
        "publisher": "Webber Publishing",
    }
    assert remote_html.properties == expected


def test_add_properties():
    """Test the add_properties function
    remote_html.properties is reset to ensure the test suite remains idempotent.
    """
    expected = {
        "title": "Tips for writing a news article",
        "url": "https://raw.githubusercontent.com/hughcameron/markline/main/tests/test.html",
        "description": "Learn how to publish articles in HTML5",
        "publisher": "Webber Publishing",
        "authors": ["Webber Page"],
    }
    remote_html.add_properties({"authors": remote_html.meta.get("article:author")})
    update_result = copy(remote_html.properties)
    del remote_html.properties["authors"]
    assert update_result == expected


def test_edit():
    """Test the edit method.
    remote_html.draft is reset to ensure the test suite remains idempotent.
    """
    expected = "<strong>\n By Webber Page\n</strong>\n"
    remote_html.edit(add_byline)
    soup_result = remote_html.draft.find("strong").prettify()
    remote_html.draft = copy(remote_html.original)
    assert soup_result == expected


def test_apply():
    pass


def test_filter():
    """Test the filter method.
    remote_html.draft is reset to ensure the test suite remains idempotent.
    """
    expected = (
        "<figcaption>\n A takeaway coffee with the morning news.\n</figcaption>\n"
    )
    remote_html.filter(ml.loc("figcaption"))
    soup_result = remote_html.draft.prettify()
    remote_html.draft = copy(remote_html.original)
    assert soup_result == expected


def test_drop():
    """Test the filter method.
    remote_html.draft is reset to ensure the test suite remains idempotent.
    """
    expected = '<article>\n <h1 id="tips-for-writing-a-news-article">\n  Tips for writing a news article\n </h1>\n</article>\n'
    remote_html.drop(ml.loc("figure"), ml.loc("section"), ml.loc("p"), ml.loc("hr"))
    soup_result = remote_html.draft.find("article").prettify()
    remote_html.draft = copy(remote_html.original)
    assert soup_result == expected


def test_render():
    """Test the render method."""
    remote_html.render() == local_md


def test_to_html():
    """Test the to_html method."""
    remote_html.to_html() == soup_html.prettify()


def test_to_md():
    """Test the to_md method."""
    remote_html.to_md() == local_md
