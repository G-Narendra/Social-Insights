"""
URL Canonicalization for deduplication.
Strips marketing and analytics tracking parameters, removes fragments,
normalizes hostname case, and removes trailing slashes.
"""

from __future__ import annotations

import urllib.parse

# Comprehensive set of marketing and session tracking query keys to strip
TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "utm_id",
    "fbclid",
    "gclid",
    "gclsrc",
    "dclid",
    "msclkid",
    "twclid",
    "yclid",
    "igshid",
    "_ga",
    "_gl",
    "mc_cid",
    "mc_eid",
    "ref",
    "ref_src",
    "ref_url",
    "source",
}


def canonicalize_url(url: str | None) -> str | None:
    """
    Produce a canonicalized URL representation:
    - Lowercase scheme and domain
    - Strip known tracking query parameters
    - Sort remaining parameters deterministically
    - Strip fragments (#...)
    - Strip trailing slash
    """
    if not url or not url.strip():
        return None

    try:
        parsed = urllib.parse.urlparse(url.strip())
        if not parsed.scheme or not parsed.netloc:
            return url.strip()

        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()

        # Remove default ports (80 for http, 443 for https)
        if scheme == "http" and netloc.endswith(":80"):
            netloc = netloc[:-3]
        elif scheme == "https" and netloc.endswith(":443"):
            netloc = netloc[:-4]

        # Strip tracking parameters from query string
        query_params = urllib.parse.parse_qsl(parsed.query, keep_blank_values=False)
        clean_params = [(k, v) for k, v in query_params if k.lower() not in TRACKING_PARAMS]
        clean_params.sort(key=lambda pair: pair[0])

        clean_query = urllib.parse.urlencode(clean_params)

        # Normalize path
        path = parsed.path
        if path.endswith("/") and len(path) > 1:
            path = path[:-1]

        canonical = urllib.parse.urlunparse((scheme, netloc, path, parsed.params, clean_query, ""))
        return canonical
    except Exception:
        return url.strip()
