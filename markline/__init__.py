__version__ = "0.1.0"

import copy
from datetime import datetime
from typing import Callable, List, NamedTuple

import pandoc
import pytz
import requests
from bs4 import BeautifulSoup, element
from furl import furl


class Locator(NamedTuple):
    name: str
    attrs: dict = {}
    recursive: bool = True
    limit: int = None


loc = Locator


DEFAULT_META_ARRAYS = [
    "article:author",
    "article:tag",
    "book:author",
    "book:tag",
    "music:album",
    "music:musician",
    "og:locale:alternate",
    "video:actor",
    "video:director",
    "video:tag",
    "video:writer",
]


def unshorten_url(url: str, headers: dict = {}) -> str:
    """Unshorten a URL by following redirects, useful for short
    URLs used in social media.
    A HEAD request is used to avoid downloading the entire page.
    The requests session recycles connections across redirects.

    Args:
        url (str): A URL to unshorten.
        headers (dict, optional): Headers for the requests session.
            Defaults to {}.

    Returns:
        str: URL of the final destination.
    """
    session = requests.Session()
    response = session.head(url, allow_redirects=True, headers=headers)
    return response.url


def trim_url(url: str) -> str:
    """Remove the query string, including UTM and referral tags, from URLs.

    Args:
        url (str): A long URL with a query string.

    Returns:
        str: A URL with query string removed.
    """
    return furl(url).remove(query=True).tostr()


def prepare_url(
    url: str,
    unshorten: bool = True,
    trim: bool = True,
    headers: dict = {},
) -> str:
    """Prepare a URL for content extraction.

    Args:
        url (str): URL to prepare.
        unshorten (bool, optional): Unshorten the URL. Defaults to True.
        trim (bool, optional): Unshorten the URL. Defaults to True.
        headers (dict, optional): Headers for the requests session.
            Defaults to {}.

    Returns:
        str: Prepared URL.
    """
    if unshorten:
        url = unshorten_url(url, headers)
    if trim:
        url = trim_url(url)
    return url


def coalesce(*args):
    """Return the first non-null value in a list of arguments."""
    for arg in args:
        if arg:
            return arg


def parse_time(
    timestamp: str,
    format: str = "%Y-%m-%dT%H:%M:%SZ",
    zone: str = "utc",
) -> datetime:
    """Convert a timestamp to a datetime object.
    The default timestamp format is ISO 8601, e.g. 2020-01-01T00:00:00Z.
    Timezone of the provided string assumes UTC.

    Args:
        timestamp (str): Timestamp to parse.
        format (str, optional): strptime format of the timestamp.
            Defaults to "%Y-%m-%dT%H:%M:%SZ".
        zone (str, optional): Timezone of the timestamp to be returned.
            Defaults to "utc".

    Returns:
        datetime: A datetime object in UTC unless a timezone is specified.
    """
    ts = datetime.strptime(timestamp, format)
    ts_utc = ts.replace(tzinfo=pytz.utc)
    if zone == "utc":
        return ts_utc
    tz = pytz.timezone(zone)
    return ts_utc.astimezone(tz)


def download_media(url: str, filename: str = None) -> str:
    """Download a file from a URL and save it to a path.
    Useful for downloading images and other media where the
    file format is provided in the Content-Type response header.

    If no filename is provided, the filename is derived from the URL stem
    and the file extension is extracted from the Content-Type header.

    Args:
        url (str): URL of the file to download.
        filename (str, optional): filename to save the file as. Defaults to None.

    Returns:
        str: filename of the downloaded file.
    """
    response = requests.get(url)
    assert response.ok, response.text
    if not filename:
        name = furl(url).path.segments[-1]
        media_type = response.headers.get("Content-Type").split("/")[1]
        filename = f"{name}.{media_type}"
    with open(filename, "wb") as f:
        f.write(response.content)
    return filename


def new_tag(tag: str, literal: str = None, attrs: dict = {}) -> element.Tag:
    """Generate a new BeautifulSoup tag with attributes and content.

    Args:
        tag (str): HTML tag name.
        literal (str, optional): Readable text content for the element. Defaults to None.
        attrs (dict): HTML tag attributes.

    Returns:
        element.Tag: A new BeautifulSoup tag.
    """
    tag = BeautifulSoup().new_tag(tag, attrs=attrs)
    if literal:
        tag.string = literal
    return tag


def quote_caption(figure: element.Tag):
    """A convenience function to include a copy an image caption
    below the image as a quote within markdown.

    HTML5 allows for the caption of an image to be placed
    in a <figcaption> tag. Following the render to markdown however,
    the caption will no longer be readable in a markdown preview.

    This function copies caption to a blockquote tag below
    the image. It can be applied to the draft using the apply() method.

    For example, the following HTML:

    ```html
    <figure>
        <img src="coffee.jpg" alt="Coffee cup on a newspaper.">
        <figcaption>A takeaway coffee with the morning news.</figcaption>
    </figure>
    ```

    Would be rendered to the following markdown once applied:

    ```markdown
    ![A takeaway coffee with the morning news.](coffee.jpg).

    > A takeaway coffee with the morning news.
    ```

    Args:
        figure (element.Tag): An HTML figure tag.
    """
    quote = new_tag("blockquote", figure.text)
    figure.insert_after(quote)


class Markup:
    """
    Markup content extracted from a URL. The original extracted content is maintained
    as a BeautifulSoup object in the `original` attribute.
    The `draft` attribute is a copy of `original` that can be modified by a pipeline
    of steps and exported to markdown or HTML.

    Args:
    url (str): URL to prepare and fetch content from.
    unshorten (bool, optional): Unshorten the URL. Defaults to True.
    trim (bool, optional): Unshorten the URL. Defaults to True.
    headers (dict, optional): Headers for the requests session. Defaults to {}.
    meta_arrays (list, optional): List of meta tags to be converted to arrays. Defaults to None.
        See the gather_meta() docstring for more details on meta_arrays.

    Properties:
    original (BeautifulSoup): The original HTML content of the URL.
    draft (BeautifulSoup): HTML content of the URL to be processed for export.
    meta (dict): Metadata extracted from the original HTML content.
    properties (dict): Properties selected from the original HTML content and metadata.
    """

    def __init__(
        self,
        url: str,
        unshorten: bool = True,
        trim: bool = True,
        headers: dict = {},
        meta_arrays: list = None,
    ):
        self.headers = headers
        self.url = prepare_url(url, unshorten, trim, self.headers)
        self.original = self.fetch_content(url)
        self.draft = copy.copy(self.original)
        self.meta_arrays = meta_arrays
        self.meta = self.gather_meta()
        self.properties = self.set_properties()

    def fetch_content(self, url: str) -> BeautifulSoup:
        """Fetch the HTML content of a URL.

        Args:
            url (str): URL to fetch.

        Returns:
            BeautifulSoup: BeautifulSoup object of the HTML content.
        """
        response = requests.get(url, self.headers)
        return BeautifulSoup(response.content, "html.parser")

    def gather_meta(self) -> dict:
        """Extract metadata from the <meta> tags within HTML content.
        Some metadata is extracted as arrays, e.g. article:tag, where
        multiple <meta> tags with the same property are present on the page.

        For more information on metadata and arrays, refer to https://ogp.me/#array.

        Some publishers will have a distinct <meta> schema that includes meta arrays.
        To account for this, the meta_arrays argument can be passed to the Markup class.

        Returns:
            dict: Metadata store.
        """
        meta = {}
        for tag in self.original.find_all("meta"):
            key = coalesce(tag.attrs.get("property"), tag.attrs.get("name"))
            value = tag.attrs.get("content")
            if key in DEFAULT_META_ARRAYS + self.meta_arrays:
                meta[key] = meta.get(key, []) + [value]
            else:
                meta[key] = value
        return meta

    def set_properties(self):
        """Properties store annotate of blocks in Logseq. Extracting properties
        from page metadata and content adds consistency to the Logseq block annotation.
        For more information on Logseq block properties refer to the Logseq documentation.
        https://docs.logseq.com/#/page/term%2Fproperties

        Returns:
            properties (dict): Default properties to store.
        """
        return {
            "title": coalesce(self.meta.get("og:title"), self.original.title.string),
            "url": self.url,
            "description": self.meta.get("og:description"),
            "publisher": self.meta.get("og:site_name"),
        }

    def add_properties(self, properties: dict) -> None:
        """Add properties to the properties store.

        Args:
            properties (dict): Properties to add.
        """
        self.properties.update(properties)

    def edit(self, editor: Callable) -> None:
        """Edit the HTML content with an editor function.

        The editor function should accept a BeautifulSoup
        object and return a BeautifulSoup object.

        Args:
            editor (Callable): Editor function.
        """
        self.draft = editor(self)

    def apply(self, loc: Locator | List[Locator], editor: Callable) -> None:
        """Apply an `editor` function to HTML elements.
        Use apply() or the 'apply' step in a pipeline to
        remove elements from the draft.

        While the edit() method is used to edit the HTML content as a whole,
        the apply() method is used to edit specific elements within the HTML content.

        Args:
            loc (Locator | List[Locator]): Locator or list of locators of
                matching elements to apply changes.
            editor (Callable): Function to apply to matching elements from the draft.
        """
        loclist = [loc] if isinstance(loc, Locator) else loc
        for loc in loclist:
            for result in self.draft.find_all(*loc):
                editor(result)

    def filter(self, loc: Locator) -> None:
        """Filter HTML elements.
        Use filter() or the 'filter' step in a pipeline to
        remove elements from the draft.

        The filter() method accepts a single locator and
        removes all non-matching elements from the draft.

        Args:
            loc (Locator): Locator of matching elements to inlcude.
        """
        self.draft = self.draft.find_all(*loc)

    def drop(self, loc: Locator | List[Locator]) -> None:
        """Drop HTML elements.
        Use drop() or the 'drop' step in a pipeline to
        remove elements from the draft.

        While the filter() method is used to remove non-matching elements,
        the drop() method is used to remove matching elements from the draft.

        Args:
            loc (Locator | List[Locator]): Locator or list of locators of
                matching elements to drop.
        """
        loclist = [loc] if isinstance(loc, Locator) else loc
        for loc in loclist:
            for result in self.draft.find_all(*loc):
                result.decompose()

    def process(self, pipeline: dict) -> None:
        for step in pipeline:
            method = step.get("method")
            args = step.get("args", [])
            kwargs = step.get("kwargs", {})
            getattr(self, method)(*args, **kwargs)

    def render(
        self,
        input_format: str = "html-native_divs-native_spans",
        output_format: str = "gfm",
        output_options: List[str] = ["--wrap=none"],
    ) -> str:
        """Render the draft HTML content to a Pandoc formatted output.

        The BeautifulSoup object is converted to an HTML string
        and passed to Pandoc.

        For a complete list of supported input and output formats, refer to the
        the Pandoc README: https://github.com/jgm/pandoc#pandoc

        Args:
            input_format (str, optional): A Pandoc supported format.
                Defaults to "html-native_divs-native_spans". This is recommended to
                preserve only the necessary HTML tags and attributes.
            output_format (str, optional): A Pandoc supported format.
                Defaults to "gfm" or Github Flavored Markdown (GFM).
            output_options (List[str], optional): A list of Pandoc write options.
                Defaults to ["--wrap=none"]. See available options:
                https://pandoc.org/MANUAL.html#options

        Returns:
            str: Pandoc formatted output.
        """
        doc = pandoc.read(self.draft.prettify(), format=input_format)
        return pandoc.write(doc, format=output_format, options=output_options)

    def to_html(self) -> str:
        """Render the draft as HTML.

        Returns:
            str: HTML content.
        """
        return self.draft.prettify()

    def to_md(self) -> str:
        """Render the draft as Markdown.

        Accepts the default input and output formats for the render() method.

        Returns:
            str: Markdown content.
        """
        return self.render()
