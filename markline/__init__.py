__version__ = "0.2.0"

import copy
import importlib.util
import re
from builtins import slice
from collections import Counter
from datetime import datetime
from select import select
from typing import Callable, List, NamedTuple, Union

import httpx
import pandoc
import pytz
from bs4 import BeautifulSoup, element
from furl import furl

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


class TagLocator(NamedTuple):
    """TagLocator defines a the interface for the BeautifulSoup find_* query methods.
    This class is intended for type hinting and usually invoked by the `loc` function.

    The find* methods are used to locate a single element in a BeautifulSoup
    Look in the children of this PageElement and find PageElements that match
    the given criteria.
    Query methods include `find`, `find_all`, `find_all_next`, `find_all_previous`,
    `find_next`, `find_next_sibling`, `find_next_siblings`, `find_parent`,
    `find_parents`, `find_previous` and `find_previous_sibling`.

    Args:
        name (str, optional) : A filter on tag name.
        attrs (dict, optional) : A dictionary of filters on attribute values.
        recursive (bool, optional) : If this is True, the Find query will perform a
                recursive search of this PageElement's children. Otherwise,
                only the direct children will be considered.
        limit (int, optional) : Stop looking after finding this many results.
    """

    name: str = None
    attrs: dict = {}
    recursive: bool = True
    limit: int = None


class CSSLocator(NamedTuple):
    """CSSLocator defines a single interface for the BeautifulSoup select query methods.
    This class is intended for type hinting and usually invoked by the `loc` function.

    Select
    Perform a CSS selection operation on the current element using the SoupSieve library.
    Query methods include `select` and `select_one`.

    Args:
        selector (str, optional) : A string containing a CSS selector.
        namespaces (dict, optional) : A dictionary mapping namespace prefixes.
        limit (int, optional) : Stop looking after finding this many results.
    """

    selector: str = None
    namespaces: dict = {}
    limit: int = None


def loc(
    name_selector: str,
    attrs: dict = {},
    recursive: bool = True,
    namespaces: dict = {},
    limit: int = None,
) -> dict:
    """Determines the query method and arguments for a BeautifulSoup query.

    If the `attrs` or `recursive` arguments are provided then keyword arguments for
    a Find method is returned. Otherwise, a Select method is returned.

    Args:
        name_selector (str) : A filter on tag name or a string containing a CSS selector.
                This is a required argument and the value may be used in both
                Find and Select methods.
        attrs (dict, optional) : A dictionary of filters on attribute values.
                This argument is only used in Find methods.
        recursive (bool, optional) : If this is True, the Find query will perform a
                recursive search of this PageElement's children. Otherwise,
                only the direct children will be considered.
                This argument is only used in Find methods.
        namespaces (dict, optional) : A dictionary mapping namespace prefixes.
                This argument is only used in Select methods.
        limit (int, optional) : Stop looking after finding this many results.
                This argument is used in both Find and Select methods.

    Returns:
        dict: A dictionay of keyword arguments for the BeautifulSoup query.
    """
    if all((any((attrs, recursive)), namespaces)):
        raise ValueError(
            "Cannot use `attrs` or `recursive` arguments together with `namespaces`."
        )
    if attrs or recursive is False:
        return TagLocator(
            name=name_selector, attrs=attrs, recursive=recursive, limit=limit
        )
    else:
        return CSSLocator(selector=name_selector, namespaces=namespaces, limit=limit)


def package_available(package_name: str) -> bool:
    """Check if a package is installed.
    This is a convenience function for checking if a package is installed.
    It is useful for checking if a package is installed before importing it.

    Args:
        package_name (str): Name of the package to check.

    Returns:
        bool: True if the package is installed.
    """
    spec = importlib.util.find_spec(package_name)
    if spec is None:
        return False
    return True


def unshorten_url(url: str, headers: dict = {}) -> str:
    """Unshorten a URL by following redirects, useful for short
    URLs used in social media.
    A HEAD request is used to avoid downloading the entire page.
    The httpx session recycles connections across redirects.

    Args:
        url (str): A URL to unshorten.
        headers (dict, optional): Headers for the httpx session.
            Defaults to {}.

    Returns:
        str: URL of the final destination.
    """
    client = httpx.Client()
    request = client.build_request("GET", url)
    while request is not None:
        response = client.send(request)
        request = response.next_request
    return str(response.url)


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
        headers (dict, optional): Headers for the httpx session.
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


def extract(
    pattern: str,
    string: str,
    group: Union[int, slice] = 0,
) -> Union[str, List[str]]:
    """_summary_

    Args:
        pattern (str): Pattern to extract.
        string (str): String to extract from.
        group (Union[int, slice], optional): Group to extract. Defaults to 0.

    Returns:
        Union[str, List[str]]: Extracted value.
    """
    result = re.findall(pattern, string)
    if result:
        return result[group]


def extract_all(pattern: str, string: str) -> List[str]:
    """_summary_

    Args:
        pattern (str): Pattern to extract.
        string (str): String to extract from.

    Returns:
        List[str]: Extracted values.
    """
    result = re.findall(pattern, string)
    if result:
        return result


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
    response = httpx.get(url)
    assert response.status_code == 200, response.text
    if not filename:
        name = furl(url).path.segments[-1]
        media_type = response.headers.get("Content-Type").split("/")[1]
        # TODO support extension aliases like "jpg" for "jpeg"
        if name.endswith("." + media_type):
            filename = name
        else:
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


def new_token(token: str) -> element.Tag:
    """Create a new token tag.
    Token tags are used to mark content that should not be modified
    with the markdown render.

    Args:
        token (str): _description_

    Returns:
         -> element.Tag: HTML element with token content in a <pre><code> tag.
    """
    token_tag = new_tag("div")
    code = new_tag("pre")
    code.append(new_tag("code", token))
    token_tag.append(code)
    return token_tag


def outline_newlines(markdown: str) -> str:
    """Add block points before all newlines in markdown.

    Args:
        markdown (str): Markdown to outline.

    Returns:
        str: Outlined markdown.
    """
    return markdown.replace("\n", "\n- ")


def outline_paragraphs(markdown: str) -> str:
    """Separate paragraphs into block points within markdown.

    Args:
        markdown (str): Markdown to outline.

    Returns:
        str: Outlined markdown.
    """
    return markdown.replace("\n\n", "\n- \n- ")


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
        <img src="coffee.jpeg" alt="Coffee cup on a newspaper.">
        <figcaption>A takeaway coffee with the morning news.</figcaption>
    </figure>
    ```

    Would be rendered to the following markdown once applied:

    ```markdown
    ![A takeaway coffee with the morning news.](coffee.jpeg).

    > A takeaway coffee with the morning news.
    ```

    Args:
        figure (element.Tag): An HTML figure or figcaption tag.
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
    headers (dict, optional): Headers for the httpx session. Defaults to {}.
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
        url: str = None,
        filepath: str = None,
        parser: str = "lxml",
        unshorten: bool = True,
        trim: bool = True,
        headers: dict = {},
        meta_arrays: list = [],
    ):
        if not any((url, filepath)):
            raise ValueError("One of URL or filepath must be provided.")
        if all((url, filepath)):
            raise ValueError("Only one of URL or filepath can be provided.")
        if filepath:
            self.url = filepath
        if url:
            self.headers = headers
            url = prepare_url(url, unshorten, trim, self.headers)
            self.url = url
        self.original = self.fetch_content(url=url, parser=parser, filepath=filepath)
        self.draft = copy.copy(self.original)
        self.meta_arrays = meta_arrays
        self.meta = self.gather_meta()
        self.properties = self.set_properties()

    def fetch_content(
        self,
        url: str,
        parser: str = "lxml",
        filepath: str = None,
    ) -> BeautifulSoup:
        """Fetch the HTML content of a URL.
        Content is fetched from the URL or local file and parsed as
        a BeautifulSoup object. If lxml is not available Python’s
        standard HTML library is used. Parsing with the lxml parser is
        faster than the standard library parser.

        Read more about package dependencies here:
        https://github.com/hughcameron/markline#dependencies

        Args:
            url (str): URL to fetch.
            parser (str, optional): Parser to use. Defaults to "lxml".
            filepath (str, optional): Path to a local file. Defaults to None.

        Returns:
            BeautifulSoup: BeautifulSoup object of the HTML content.
        """
        if parser == "lxml" and not package_available("lxml"):
            parser = "html.parser"
        if filepath:
            with open(filepath, "r") as f:
                return BeautifulSoup(f.read(), parser)
        response = httpx.get(url, headers=self.headers)
        return BeautifulSoup(response.content, parser)

    def gather_meta(self, counts: bool = False) -> dict:
        """Extract metadata from the <meta> tags within HTML content.
        Some metadata is extracted as arrays, e.g. article:tag, where
        multiple <meta> tags with the same property are present on the page.

        For more information on metadata and arrays, refer to https://ogp.me/#array.

        Some publishers will have a distinct <meta> schema that includes meta arrays.
        To account for this, the meta_arrays argument can be passed to the Markup class.

        Args:
            counts (bool, optional): Whether to return counts of the meta keys found.
                Defaults to False.

        Returns:
            dict: Metadata store.
                When counts is True, a dict of counts of meta elements keys is returned.
        """
        meta = {}
        meta_keys = []
        for tag in self.original.find_all("meta"):
            key_terms = ["property", "name"]
            key_terms += [k for k in tag.attrs.keys() if k != "content"]
            key = coalesce(*(tag.attrs.get(k) for k in key_terms))
            value = tag.attrs.get("content")
            if key in DEFAULT_META_ARRAYS + self.meta_arrays:
                meta[key] = meta.get(key, []) + [value]
            else:
                meta[key] = value
            meta_keys.append(key)
        if counts:
            return dict(Counter(meta_keys).most_common())
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
            "headline": coalesce(self.meta.get("og:title"), self.original.title.string),
            "description": self.meta.get("og:description"),
            "publisher": self.meta.get("og:site_name"),
            "url": self.url,
        }

    def add_properties(self, properties: dict) -> None:
        """Add properties to the properties store.
        Lists are appended with a `,` to ensure that lists with
        single values still appear as links in Logseq.

        Args:
            properties (dict): Properties to add.
        """
        self.properties.update(properties)

    def properties_block(self) -> str:
        properties_block = ""
        for key, value in self.properties.items():
            if isinstance(value, str) and ", " in value:
                value = f'"{value}"'
            if isinstance(value, list):
                value = ", ".join(value) + ","
            if isinstance(value, object):
                value = str(value)
            properties_block += f"{key}:: {str(value)}\n"
        return properties_block

    def select(
        self,
        loc: CSSLocator | TagLocator | str,
        get_attr: str = None,
        get_text: bool = False,
        version: str = "draft",
    ) -> element.Tag:
        """Select the first element from the HTML content using a locator.
        Args:
            loc (CSSLocator | TagLocator | str): locator to select.
            get_attr (str, optional): Name of the element attribute from which to retrieve a value.
                If provided, only the value of the attribute is returned. Defaults to None.
            get_text (bool, optional): Whether to return the text of the selected element. Defaults to False.
            version (str, optional): Version of the HTML content to select from. Defaults to "draft".
        Returns:
            element.Tag: Element from query.
        """
        markup = getattr(self, version)
        if isinstance(loc, TagLocator):
            result = markup.find(*loc)
        if isinstance(loc, CSSLocator):
            result = markup.select_one(selector=loc.selector, namespaces=loc.namespaces)
        if isinstance(loc, str):
            loc = CSSLocator(loc)
            result = markup.select_one(selector=loc.selector, namespaces=loc.namespaces)
        if get_attr:
            return result.attrs.get(get_attr)
        if get_text:
            return result.text.strip()
        return result

    def select_all(
        self,
        loc: CSSLocator | TagLocator | str,
        get_attr: str = None,
        get_text: bool = False,
        version: str = "draft",
    ) -> element.ResultSet | list:
        """Select elements from the HTML content using a locator.
        Args:
            loc (CSSLocator | TagLocator | str): locator to select.
            get_attr (str, optional): Name of the element attribute from which to retrieve a value.
                If provided, a value is returned from each element. Defaults to None.
            get_text (bool, optional): Whether to return the text of each element. Defaults to False.
            version (str, optional): Version of the HTML content to select from. Defaults to "draft".
        Returns:
            element.ResultSet: ResultSet of elements from query.
        """
        markup = getattr(self, version)
        if isinstance(loc, TagLocator):
            results = markup.find_all(*loc)
        if isinstance(loc, CSSLocator):
            results = markup.select(*loc)
        if isinstance(loc, str):
            loc = CSSLocator(loc)
            results = markup.select(*loc)
        if get_attr:
            return [r.attrs.get(get_attr) for r in results]
        if get_text:
            return [r.text.strip() for r in results if r.text.strip()]
        return results

    def edit(self, editor: Callable) -> None:
        """Edit the HTML content with an editor function.

        The editor function should accept a Markup object.

        Args:
            editor (function): Editor function.
        """
        assert callable(editor), "Editor must be a callable."
        editor(self)
        return self

    def apply(
        self,
        editor: Callable,
        *locations: CSSLocator | TagLocator | str,
    ) -> None:
        """Apply an `editor` function to HTML elements.
        Use apply() edit elements matching a specified location within the draft.
        The editor function should accept a bs4.element.Tag object.

        While the edit() method is used to edit the HTML content as a whole,
        the apply() method is used to edit specific elements within the HTML content.

        Args:
            editor (Callable): Function to apply to matching elements from the draft.
            loc (CSSLocator | TagLocator | str): locator or list of locators of
                matching elements to apply changes.
        """
        assert callable(editor), "Editor must be a callable."
        for loc in locations:
            for result in self.select_all(loc):
                editor(result)
        return self

    def filter(self, loc: CSSLocator | TagLocator | str) -> None:
        """Filter HTML elements.
        Use filter() to reduce the draft to matching elements.

        The filter() method accepts a single locator and
        removes all non-matching elements from the draft.

        Args:
            loc (CSSLocator | TagLocator | str): locator of matching elements to inlcude.
        """
        self.draft = self.select(loc)
        return self

    def drop(self, *locations: CSSLocator | TagLocator | str) -> None:
        """Drop HTML elements.
        Use drop() to remove elements from the draft.

        While the filter() method is used to remove non-matching elements,
        the drop() method is used to remove matching elements from the draft.

        Args:
            loc (CSSLocator | TagLocator | str): One or more locators of matching elements to drop.
        """
        for loc in locations:
            for result in self.select_all(loc):
                result.decompose()
        return self

    def prepend(self, *elements: element.Tag) -> None:
        """Prepend HTML elements to the draft.

        Args:
            elements (element.Tag): One or more elements to prepend to the draft.
        """
        collect = new_tag("div")
        fill = (*elements, self.draft)
        for elem in fill:
            collect.append(elem)
        self.draft = collect
        return self

    def append(self, *elements: element.Tag) -> None:
        """Append HTML elements to the draft.

        Args:
            elements (element.Tag): One or more elements to append to the draft.
        """
        for elem in elements:
            self.draft.append(elem)
        return self

    def counts(self, *locations: CSSLocator | TagLocator | str) -> dict:
        """Count of HTML elements.
        Calculates a dict of counts of matching elements, grouped by the locator used.

        Note that where multiple locators of elements are provided this is not a
        deduplicated count of elements, as locators can match overlapping elements.

        Args:
            loc (CSSLocator | TagLocator | str): One or more locators to count matching elements.

        Returns:
            dict: Count of matching elements dropped.
        """
        loc_count = Counter()
        if locations:
            for loc in locations:
                loc_count[str(loc)] = 0
                for _ in self.select_all(loc):
                    loc_count[str(loc)] += 1
            return dict(loc_count.most_common())
        else:
            elems = [e.name for e in self.draft.find_all()]
            return dict(Counter(elems).most_common())

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

    def to_html(self, filepath: str = None) -> str:
        """Render the draft as HTML.
        If a filepath is provided, the HTML content is written to the file.

        Returns:
            str: HTML content.
            filepath (str, optional): Filepath to write HTML content to.
                 Defaults to None.
        """
        if filepath:
            with open(filepath, "w") as f:
                return f.write(self.draft.prettify())
        return self.draft.prettify()

    def to_md(self, filepath: str = None, outliner: str = None) -> str:
        """Render the draft as Markdown.
        Accepts the default input and output formats for the render() method.

        If a filepath is provided, the markdown content is written to the file.

        If an outliner is provided, the markdown content is passed to the outliner
        to generate an block outline suitable for use in Logseq. Currently only the
        `newlines` and `paragraphs` outliners are supported.

        Returns:
            str: Markdown content.
            filepath (str, optional): Filepath to write HTML content to.
                Defaults to None.
            outliner (str, optional): A block outlining style.
        """
        markdown = self.render()
        outline_approach = {
            "newlines": outline_newlines,
            "paragraphs": outline_paragraphs,
        }
        if outliner:
            assert (
                outliner in outline_approach
            ), f"Outliner must be one of {outline_approach.keys()}."
            markdown = outline_approach[outliner](markdown)
        if filepath:
            with open(filepath, "w") as f:
                return f.write(markdown)
        return markdown
