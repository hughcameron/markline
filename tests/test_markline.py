import markline as ml

# This is a short URL: https://tinyurl.com/mrx7da4n
# for the test page at: https://raw.githubusercontent.com/hughcameron/markline/main/tests/test.html

SHORT_URL = "https://tinyurl.com/mrx7da4n"
LONG_URL = "https://raw.githubusercontent.com/hughcameron/markline/main/tests/test.html"

test_asset = ml.Markup("https://tinyurl.com/mrx7da4n")


def test_version():
    assert ml.__version__ == "0.1.0"


def test_quote_caption():
    """Test the quote_caption function."""
    return True
