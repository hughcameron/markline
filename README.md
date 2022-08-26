# <img src="img/markline.svg" width="200">

**Markline** converts HTML to Markdown and supports transformation methods borrowed from data engineering concepts. The goal of this project is to provide a simple API that renders HTML to Markdown for note management applications such as [Logseq](https://logseq.com).


## Getting Started

### Installation

Markline is available on PyPI:

```bash
python -m pip install markline
```

#### Dependencies

Markdown rendering is performed with [Pandoc](https://pandoc.org/) so the `pandoc` command-line tool needs to be available in your environment. You may follow [the official installation instructions](https://pandoc.org/installing.html)
which are OS-dependent, or if you are a [conda](https://www.google.com/search?q=conda+python) user, with the following command:

```bash
conda install -c conda-forge pandoc
```

Beautiful Soup supports the HTML parser included in Python's standard library, but it also supports a number of third-party Python parsers. One is the [lxml parser](http://lxml.de/) which provides a good balance between performance and accuracy. More information about the parsers can be found in the [Beautiful Soup documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/#installing-a-parser).

 For conda users, you can install the lxml package with the following command:

```bash
conda install -c conda-forge lxml
```
