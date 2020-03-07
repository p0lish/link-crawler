from datetime import datetime
from random import choice
from urllib.request import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

import colorama

# Colorama init https://pypi.org/project/colorama/
colorama.init()
GREEN = colorama.Fore.GREEN
GRAY = colorama.Fore.LIGHTBLACK_EX
RESET = colorama.Fore.RESET


# Initialize link sets, and exceptions
WRONG_SCHEMES = ('mailto', 'market')
internal_urls = set()
external_urls = set()

total_urls_visited = 0

USER_AGENTS = [
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/37.0.2062.94 Chrome/37.0.2062.94 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
]


def get_user_agent():
    return choice(USER_AGENTS)


def check_url_validity(url):
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)


def handle_external_link(href):
    if href not in external_urls:
        print(f"{GRAY}[!] External link: {href}{RESET}")
        external_urls.add(href)


def handle_internal_link(href, urls):
    print(f"{GREEN}[*] Internal link: {href}{RESET}")
    urls.add(href)
    internal_urls.add(href)


def get_all_website_links(url):
    """
    Returns URLs that is found on `url` in which belongs to the website
    """
    # all URLs of `url`
    urls = set()

    # Add random user agent to the request from the list
    headers = requests.utils.default_headers()
    headers.update({
        'User-Agent': get_user_agent()
    })

    # domain name of the URL without the protocol
    domain_name = urlparse(url).netloc
    soup = BeautifulSoup(requests.get(
        url, headers=headers).content, "html.parser")
    for a_tag in soup.findAll():
        href = a_tag.attrs.get("href")
        if href == "" or href is None:
            continue

        href = urljoin(url, href)
        parsed_href = urlparse(href)

        # remove URL GET parameters, URL fragments, etc.
        href = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
        if (parsed_href.scheme in WRONG_SCHEMES):
            continue
        if not check_url_validity(href):
            continue
        if href in internal_urls:
            continue
        if domain_name not in href:
            # external link
            handle_external_link(href)
            continue
        handle_internal_link(href, urls)
    return urls


def crawl(url, max_urls=50):
    """
    Crawls a web page and extracts all links.
    params:
        max_urls (int): number of max urls to crawl, default is 50.
        if max_urls is 0 then it has no limit.
    """
    global total_urls_visited
    total_urls_visited += 1
    links = get_all_website_links(url)
    for link in links:
        if max_urls > 0 and total_urls_visited > max_urls:
            break
        crawl(link, max_urls=max_urls)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Link Extractor Tool in Python")
    parser.add_argument("url", help="Target URL.")
    parser.add_argument(
        "-m", "--max-urls", help="Number of max URLs to crawl, default is 50. If its 0 then no limit", default=50, type=int)

    args = parser.parse_args()
    url = args.url
    max_urls = args.max_urls
    crawl(url, max_urls=max_urls)

    print("[+] Total Internal links:", len(internal_urls))
    print("[+] Total External links:", len(external_urls))
    print("[+] Total URLs:", len(external_urls) + len(internal_urls))

    domain_name = urlparse(url).netloc

    with open(f"{domain_name}_{datetime.now()}_internal_links.txt", "w") as f:
        for internal_link in internal_urls:
            print(internal_link.strip(), file=f)

    with open(f"{domain_name}_{datetime.now()}_external_links.txt", "w") as f:
        for external_link in external_urls:
            print(external_link.strip(), file=f)
