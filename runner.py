"""Railway entrypoint with a dedicated Moonmedia discovery adapter."""
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

import bot

_original_discover = bot.discover


def host(url):
    return (urlsplit(url).hostname or "").lower().removeprefix("www.")


def moonmedia_items(document, base):
    soup = BeautifulSoup(document, "html.parser")
    rows = {}
    for a in soup.select('a[href*="/post/"]'):
        url = bot.canonical(urljoin(base, a.get("href", "")))
        if urlsplit(url).scheme not in ("http", "https") or host(url) != host(base):
            continue
        if not urlsplit(url).path.startswith("/post/"):
            continue
        title = a.get_text(" ", strip=True)
        if len(title) <= 15:
            title = a.get("title", "").strip()
        if len(title) <= 15:
            image = a.find("img", alt=True)
            title = image.get("alt", "").strip() if image else ""
        if len(title) <= 15:
            continue
        previous = rows.get(url)
        if previous is None or len(title) > len(previous["title"]):
            rows[url] = {"url": url, "title": title, "published": None}
    return list(rows.values())[:100]


def discover(name, base):
    if name != "moonmedia":
        return _original_discover(name, base)
    rows = {}
    for page_url in (urljoin(base, "latest"), base):
        try:
            response = bot.get(page_url)
            response_base = response.url or page_url
            if host(response_base) != host(base):
                raise RuntimeError("unexpected cross-site redirect")
            found = moonmedia_items(response.text, response_base)
            for item in found:
                rows.setdefault(item["url"], item)
        except Exception as exc:
            bot.LOG.warning("moonmedia HTML discovery failed page=%s error=%s",
                            page_url, type(exc).__name__)
    if rows:
        return list(rows.values())[:100]
    # Keep the original feed path available if the site later exposes a feed.
    return _original_discover(name, base)


bot.discover = discover

if __name__ == "__main__":
    bot.main()
