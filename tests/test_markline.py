from copy import copy
from datetime import datetime, timezone
from unittest import result

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
    soup_result = remote_html.filter("blockquote").to_html()
    remote_html.draft = copy(remote_html.original)
    assert soup_result == expected


def test_loc():
    expected = ml.CSSLocator
    result = type(ml.loc("div"))
    assert result == expected


def test_loc_attrs():
    expected = ml.TagLocator
    result = type(ml.loc("div", attrs={"class": "test"}))
    assert result == expected


def test_new_token():
    """Test the new_token function."""
    expected = "<div>\n <pre><code>[[test]]</code></pre>\n</div>"
    test_token = ml.new_token("[[test]]").prettify()
    assert test_token == expected


def test_fetch_url_content():
    assert remote_html.to_html() == soup_html.prettify()


def test_fetch_local_content():
    assert local_html.to_html() == soup_html.prettify()


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


def test_gather_meta_counts():
    """Test the gather_meta function with counts set to True."""
    expected = {
        "article:tag": 2,
        "UTF-8": 1,
        "X-UA-Compatible": 1,
        "viewport": 1,
        "keywords": 1,
        "author": 1,
        "title": 1,
        "description": 1,
        "og:type": 1,
        "og:url": 1,
        "og:title": 1,
        "og:site_name": 1,
        "og:description": 1,
        "og:image": 1,
        "article:author": 1,
        "twitter:card": 1,
        "twitter:domain": 1,
        "twitter:url": 1,
        "twitter:title": 1,
        "twitter:description": 1,
        "twitter:image": 1,
    }
    assert remote_html.gather_meta(counts=True) == expected


def test_set_properties():
    """Test the set_properties function."""
    expected = {
        "headline": "Tips for writing a news article",
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
        "headline": "Tips for writing a news article",
        "url": "https://raw.githubusercontent.com/hughcameron/markline/main/tests/test.html",
        "description": "Learn how to publish articles in HTML5",
        "publisher": "Webber Publishing",
        "authors": ["Webber Page"],
    }
    remote_html.add_properties({"authors": remote_html.meta.get("article:author")})
    update_result = copy(remote_html.properties)
    del remote_html.properties["authors"]
    assert update_result == expected


def test_properties_block():
    expected = "headline:: Tips for writing a news article\ndescription:: Learn how to publish articles in HTML5\npublisher:: Webber Publishing\nurl:: https://raw.githubusercontent.com/hughcameron/markline/main/tests/test.html\n"
    assert remote_html.properties_block() == expected


def test_select():
    expected = '<aside class="sidenav">\n <a href="#the-headline">\n  The Headline\n </a>\n <a href="#the-lead">\n  The Lead\n </a>\n <a href="#the-body">\n  The Body\n </a>\n</aside>\n'
    soup_result = remote_html.select("aside").prettify()
    assert soup_result == expected


def test_select_attr():
    expected = ["sidenav"]
    soup_result = remote_html.select("aside", attr_value="class")
    assert soup_result == expected


def test_select_all():
    expected = 3
    soup_result = len(remote_html.select_all("section"))
    assert soup_result == expected


def test_select_all_attr():
    expected = ["the-headline", "the-lead", "the-body"]
    soup_result = remote_html.select_all("section", attr_value="id")
    assert soup_result == expected


def test_edit():
    """Test the edit method.
    remote_html.draft is reset to ensure the test suite remains idempotent.
    """
    expected = "<strong>\n By Webber Page\n</strong>\n"
    remote_html.edit(add_byline)
    soup_result = remote_html.filter("strong").to_html()
    remote_html.draft = copy(remote_html.original)
    assert soup_result == expected


def test_apply():
    """Test the apply method."""
    expected = (
        "<blockquote>\n A takeaway coffee with the morning news.\n</blockquote>\n"
    )
    remote_html.apply(ml.quote_caption, ml.loc("figure"))
    soup_result = remote_html.filter("blockquote").to_html()
    remote_html.draft = copy(remote_html.original)
    assert soup_result == expected


def test_apply_str():
    """Test the apply method with a string locator."""
    expected = (
        "<blockquote>\n A takeaway coffee with the morning news.\n</blockquote>\n"
    )
    remote_html.apply(ml.quote_caption, "figure")
    soup_result = remote_html.filter("blockquote").to_html()
    remote_html.draft = copy(remote_html.original)
    assert soup_result == expected


def test_filter():
    """Test the filter method.
    remote_html.draft is reset to ensure the test suite remains idempotent.
    """
    expected = (
        "<figcaption>\n A takeaway coffee with the morning news.\n</figcaption>\n"
    )
    soup_result = remote_html.filter(ml.loc("figcaption")).to_html()
    remote_html.draft = copy(remote_html.original)
    assert soup_result == expected


def test_filter_str():
    """Test the filter method with a string locator.
    remote_html.draft is reset to ensure the test suite remains idempotent.
    """
    expected = (
        "<figcaption>\n A takeaway coffee with the morning news.\n</figcaption>\n"
    )
    soup_result = remote_html.filter("figcaption").to_html()
    remote_html.draft = copy(remote_html.original)
    assert soup_result == expected


def test_drop():
    """Test the drop method.
    remote_html.draft is reset to ensure the test suite remains idempotent.
    """
    expected = '<article>\n <h1 id="tips-for-writing-a-news-article">\n  Tips for writing a news article\n </h1>\n</article>\n'
    remote_html.drop(ml.loc("figure"), ml.loc("section"), ml.loc("p"), ml.loc("hr"))
    soup_result = remote_html.filter(ml.loc("article")).to_html()
    remote_html.draft = copy(remote_html.original)
    assert soup_result == expected


def test_drop_str():
    """Test the filter method with a string locator.
    remote_html.draft is reset to ensure the test suite remains idempotent.
    """
    expected = '<article>\n <h1 id="tips-for-writing-a-news-article">\n  Tips for writing a news article\n </h1>\n</article>\n'
    remote_html.drop("figure", "section", "p", "hr")
    soup_result = remote_html.filter("article").to_html()
    remote_html.draft = copy(remote_html.original)
    assert soup_result == expected


def test_prepend():
    """Test the prepend method.
    remote_html.draft is reset to ensure the test suite remains idempotent.
    """
    excepted = "<div>\n <p>\n  test\n </p>\n <title>\n  Tips for writing a news article\n </title>\n</div>"
    remote_html.filter("title")
    remote_html.prepend(ml.new_tag("p", literal="test"))
    soup_result = remote_html.to_html()
    # print(soup_result)
    remote_html.draft = copy(remote_html.original)
    assert soup_result == excepted


def test_append():
    """Test the append method.
    remote_html.draft is reset to ensure the test suite remains idempotent.
    """
    excepted = (
        "<title>\n Tips for writing a news article\n <p>\n  test\n </p>\n</title>\n"
    )
    remote_html.filter("title")
    remote_html.append(ml.new_tag("p", literal="test"))
    soup_result = remote_html.to_html()
    remote_html.draft = copy(remote_html.original)
    assert soup_result == excepted


def test_counts():
    """Test the counts method."""
    expected = {"CSSLocator(selector='meta', namespaces={}, limit=None)": 22}
    assert remote_html.counts(ml.loc("meta")) == expected


def test_counts_tag_not_present():
    """Test the counts method."""
    expected = {"CSSLocator(selector='tag_not_present', namespaces={}, limit=None)": 0}
    assert remote_html.counts(ml.loc("tag_not_present")) == expected


def test_counts_all_elements():
    """Test the counts method with no Locations supplied."""
    expected = {
        "meta": 22,
        "li": 9,
        "p": 4,
        "a": 3,
        "section": 3,
        "h2": 3,
        "link": 2,
        "ul": 2,
        "hr": 2,
        "html": 1,
        "head": 1,
        "title": 1,
        "body": 1,
        "aside": 1,
        "article": 1,
        "h1": 1,
        "figure": 1,
        "img": 1,
        "figcaption": 1,
    }
    assert remote_html.counts() == expected


def test_render():
    """Test the render method."""
    remote_html.render() == local_md


def test_to_html():
    """Test the to_html method."""
    remote_html.to_html() == soup_html.prettify()


def test_to_md():
    """Test the to_md method."""
    remote_html.to_md() == local_md
