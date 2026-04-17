"""
Domain whitelist for document fetch operations.

Only URLs from approved academic, research, and institutional domains
are permitted for automated PDF fetching.
"""

from urllib.parse import urlparse

ALLOWED_DOMAINS: set[str] = {
    # arXiv
    "arxiv.org",
    "export.arxiv.org",
    # Open-access journals
    "www.frontiersin.org",
    "www.mdpi.com",
    "journals.plos.org",
    # Semantic Scholar API
    "api.semanticscholar.org",
    # ML conferences
    "proceedings.neurips.cc",
    "proceedings.mlr.press",
    "openreview.net",
    # Tech company research blogs
    "ai.googleblog.com",
    "blog.google",
    "deepmind.google",
    "research.ibm.com",
    # Japanese government / research institutes
    "www.nedo.go.jp",
    "www.meti.go.jp",
    "www.aist.go.jp",
}


class DomainNotAllowedError(Exception):
    """Raised when a URL's domain is not in the whitelist."""

    def __init__(self, url: str, domain: str):
        self.url = url
        self.domain = domain
        super().__init__(f"Domain not allowed: {domain} (url: {url})")


def validate_url(url: str) -> str:
    """
    Validate that the URL's domain is in the whitelist.
    Checks both with and without 'www.' prefix.
    Returns the URL if valid, raises DomainNotAllowedError otherwise.
    """
    parsed = urlparse(url)
    domain = parsed.hostname or ""
    domain = domain.lower()

    # Check domain as-is and with/without www. prefix
    domain_no_www = domain.removeprefix("www.")
    domain_with_www = f"www.{domain_no_www}"

    if domain in ALLOWED_DOMAINS or domain_no_www in ALLOWED_DOMAINS or domain_with_www in ALLOWED_DOMAINS:
        return url

    raise DomainNotAllowedError(url, domain)
