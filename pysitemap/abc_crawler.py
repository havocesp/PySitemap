import re
import socket
from abc import ABC, abstractmethod
from urllib.parse import urlsplit, urlunsplit
from tldextract import tldextract


# https://github.com/Guiorgy/PySitemap
# Fork of
# https://github.com/Cartman720/PySitemap


class _Crawler(ABC):
    DEFAULT_TIMEOUT = socket._GLOBAL_DEFAULT_TIMEOUT

    _request_headers = {
        'Accept-Language': 'en-US,en;q=0.5',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Referer': 'http://thewebsite.com',
        'Connection': 'keep-alive'
    }

    def __init__(self, url, exclude=None, domain=None, no_verbose=False, request_header=None, timeout=DEFAULT_TIMEOUT,
                 retry_times=1, build_graph=False, verify_ssl=False, max_redirects=10, max_path_depth=None,
                 max_steps_depth=0):

        self._url = self._normalize(url)
        self._host = urlsplit(self._url).netloc
        self._domain = domain if domain is not None else self._get_domain(self._url)
        self._exclude = exclude.split() if exclude else None
        self._no_verbose = no_verbose
        self._error_links = []
        if request_header:
            self._request_headers = request_header
        if request_header == {}:
            self._request_header = None
        self._timeout = timeout if timeout else self.DEFAULT_TIMEOUT
        self._retry_times = retry_times
        self._build_graph = build_graph
        self._graph = {}
        self._verify_ssl = verify_ssl if verify_ssl is not None else False
        self._max_path_depth = max_path_depth + 2 if max_path_depth and max_path_depth > 0 else None
        self._stop = False
        self._max_redirects = max_redirects if max_redirects and max_redirects >= 0 else 10
        self._max_steps_depth = max_steps_depth if max_steps_depth and max_steps_depth >= 0 else 0

    def start(self):
        if not self._url:
            return None
        self._crawl(self._normalize(self._url))
        if not self._no_verbose and self._error_links:
            print('Failed to parse: ', self._error_links)
        return self._graph.keys()

    def close(self):
        del self._error_links, self._graph

    def generate_sitemap(self):
        sitemap = '''<?xml version="1.0" encoding="UTF-8"?>
            <urlset xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9
                http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd"
                xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'''
        for url in self._graph.keys():
            sitemap += "\n\t<url>\n\t\t<loc>{0}</loc>\n\t</url>".format(url)
        sitemap += '\n</urlset>'
        return sitemap

    def generate_graph(self):
        if not self._build_graph:
            return None
        return self._graph

    @abstractmethod
    def _crawl(self, root_url):
        pass

    @abstractmethod
    def _request(self, url):
        pass

    _pattern = '<a [^>]*href=[\'|"](.*?)[\'"].*?>'

    def _extract_urls(self, html):
        re.findall(self._pattern, html)

    def _url_excluded(self, url):
        excluded = False

        if self._exclude:
            for pattern in self._exclude:
                excluded |= (re.search(pattern, url) is not None)

        if self._max_path_depth:
            excluded |= url.count('/') > self._max_path_depth

        return excluded

    def _add_url(self, url, url_list):
        url = self._normalize(url)
        if url and url not in url_list and not self._url_excluded(url):
            url_list.append(url)

    def _add_graph(self, source, url):
        if source not in self._graph:
            self._graph[source] = set() if self._build_graph else None
        if not self._build_graph or url is None:
            return
        self._graph[source].add(url)

    def _add_all_graph(self, source, urls):
        if source not in self._graph:
            self._graph[source] = set() if self._build_graph else None
        self._graph[source].update(urls)

    def _normalize(self, url):
        if url.endswith('/'):
            url = url[:-1]
        scheme, netloc, path, qs, anchor = urlsplit(url)
        # print(url, ' ', scheme, ' ', netloc, ' ', path, ' ', qs, ' ', anchor)
        anchor = ''
        if scheme == 'https':
            scheme = 'http'
        if not netloc.startswith('www.'):
            netloc = 'www.' + netloc
        return urlunsplit((scheme, netloc, path, qs, anchor))

    def _is_internal(self, url):
        host = urlsplit(url).netloc
        if self._domain:
            return self._domain in host
        return host == self._host

    def _is_relative(self, url):
        host = urlsplit(url).netloc
        return host == ''

    def _same_domain(self, url):
        domain = self._get_domain(url)
        if domain and domain == self._domain:
            return True
        elif urlsplit(url).netloc == self._host:
            return True
        return False

    def _is_url(self, url):
        scheme, netloc, path, qs, anchor = urlsplit(url)
        if url != '' and scheme in ['http', 'https', '']:
            return True
        else:
            return False

    def _get_domain(self, url):
        sub, domain, suffix = tldextract.extract(url)
        if domain and suffix:
            return domain + '.' + suffix
        return None

    def stop(self, stop_crawling=True):
        self._stop = stop_crawling
