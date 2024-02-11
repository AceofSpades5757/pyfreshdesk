import re
from typing import Final


# Search Results
RESULTS_PER_PAGE: Final[int] = 30
MAX_PAGES: Final[int] = 10
MAX_SEARCH_RESULTS: Final[int] = RESULTS_PER_PAGE * MAX_PAGES

RE_FRESHDESK_ARTICLE_URL: Final[re.Pattern] = re.compile(
    r"/support/solutions/articles/\d{6,}",
)
RE_FRESHDESK_ADMIN_ARTICLE_URL: Final[re.Pattern] = re.compile(
    r".*/a/solutions/articles/(?P<article_id>\d+).*",
)
