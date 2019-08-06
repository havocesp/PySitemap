import urllib.request
from urllib.parse import urlsplit, urlunsplit, urljoin, urlparse
from urllib.error import URLError, HTTPError
import re
# from datetime import datetime
import tldextract
import ssl


# https://github.com/Guiorgy/PySitemap
# Fork of
# https://github.com/Cartman720/PySitemap


class Crawler:
    _request_headers = {
        'Accept-Language': 'en-US,en;q=0.5',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Referer': 'http://thewebsite.com',
        'Connection': 'keep-alive'
    }

    def _get_context(self):
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context

    def __init__(self, url, exclude=None, domain=None, no_verbose=False, request_header=None, build_graph=False,
                 verify_ssl=False):

        self._url = self._normalize(url)
        self._host = urlparse(self._url).netloc
        self._domain = domain if domain is not None else self._get_domain(self._url)
        self._exclude = exclude.split() if exclude else None
        self._no_verbose = no_verbose
        self._error_links = []
        if request_header:
            self._request_headers = request_header
        if request_header == {}:
            self._request_header = None
        self._build_graph = build_graph
        self._graph = {}
        self._context = None if verify_ssl else self._get_context()

    def start(self):
        if not self._url:
            return None
        self._crawl(self._url)
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

    def _crawl(self, url):
        if not self._no_verbose:
            print(len(self._graph.keys()), 'Parsing: ' + url)

        response = self._request(url)
        if response:
            # Handle redirects
            parsed_url = response.geturl()
            if url != parsed_url:
                self._add_graph(url, parsed_url)
                url = parsed_url
                if not self._same_domain(url) or url in self._graph:
                    return

            # TODO Handle last modified
            # last_modified = response.info()['Last-Modified']
            # Fri, 19 Oct 2018 18:49:51 GMT
            # if last_modified:
            #     dateTimeObject = datetime.strptime(last_modified, '%a, %d %b %Y %H:%M:%S %Z')
            #     print('Last Modified:', dateTimeObject)

            # TODO Handle priority

            self._add_graph(url, None)

            page = str(response.read())
            pattern = '<a [^>]*href=[\'|"](.*?)[\'"].*?>'

            page_links = re.findall(pattern, page)
            links = []

            for link in page_links:
                is_url = self._is_url(link)
                link = self._normalize(link)
                if is_url:
                    if self._is_internal(link):
                        self._add_url(link, links)
                    elif self._is_relative(link):
                        link = urljoin(url, link)
                        self._add_url(link, links)

            if self._build_graph:
                self._add_all_graph(url, links)

            for link in links:
                if link not in self._graph and link not in self._error_links:
                    self._crawl(link)

    def _request(self, url):
        try:
            request = urllib.request.Request(url, headers=self._request_headers)
            return urllib.request.urlopen(request, context=self._context)
        except HTTPError as e:
            if not self._no_verbose:
                print('HTTP Error code: ', e.code, ' ', url)
            self._add_url(url, self._error_links)
        except URLError as e:
            if not self._no_verbose:
                print('Error: Failed to reach server. ', e.reason)
        except ValueError as e:
            if not self._no_verbose:
                print('Error: Failed read url. ', e)
        return None

    def _add_url(self, url, url_list):
        url = self._normalize(url)
        if url:
            not_in_list = url not in url_list

            excluded = False
            if self._exclude:
                for pattern in self._exclude:
                    excluded |= (re.search(pattern, url) is not None)

            if not_in_list and not excluded:
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
        scheme, netloc, path, qs, anchor = urlsplit(url)
        # print(url, ' ', scheme, ' ', netloc, ' ', path, ' ', qs, ' ', anchor)
        anchor = ''
        return urlunsplit((scheme, netloc, path, qs, anchor))

    def _is_internal(self, url):
        host = urlparse(url).netloc
        if self._domain:
            return self._domain in host
        return host == self._host

    def _is_relative(self, url):
        host = urlparse(url).netloc
        return host == ''

    def _same_domain(self, url):
        domain = self._get_domain(url)
        if domain and domain == self._domain:
            return True
        elif urlparse(url).netloc == self._host:
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
