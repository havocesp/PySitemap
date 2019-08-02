from urllib.parse import urlsplit, urlunsplit, urljoin, urlparse
import aiohttp
from aiohttp import ClientResponseError, ClientError, ClientConnectionError, ClientOSError, ServerConnectionError
from aiohttp.client import ClientTimeout
import asyncio
import re
# from datetime import datetime
import tldextract


# https://github.com/Cartman720/PySitemap


class Crawler:
    DEFAULT_TIMEOUT = ClientTimeout(total=5*60)
    _request_headers = {
        'Accept-Language': 'en-US,en;q=0.5',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Referer': 'http://thewebsite.com',
        'Connection': 'keep-alive'
    }

    def __init__(self, url, exclude=None, domain=None, no_verbose=False, request_header=None,
                 read_timeout=DEFAULT_TIMEOUT, conn_timeout=None, timeout=DEFAULT_TIMEOUT, retry_times=0):

        self._url = self._normalize(url)
        self._host = urlparse(self._url).netloc
        self._domain = domain if domain is not None else self._get_domain(self._url)
        self._exclude = exclude.split() if exclude else None
        self._no_verbose = no_verbose
        self._found_links = []
        self._error_links = []
        # self._redirect_links = []
        if request_header:
            self._request_headers = request_header
        if request_header is not None and not request_header:
            self._request_headers = None
        self._read_timeout = read_timeout
        self._conn_timeout = conn_timeout
        self._timeout = timeout
        self.retry_times = retry_times

    def start(self):
        self._crawl([self._url])
        if not self._no_verbose:
            print('Failed to parse: ', self._error_links)
        while self.retry_times > 0 and self._error_links:
            urls = self._error_links
            self._error_links = []
            self._crawl(urls)
        return self._found_links

    def _crawl(self, urls):
        if not self._no_verbose:
            print(len(self._found_links), 'Parsing: ', urls)

        responses = self._request(urls)

        if responses:
            links = []
            for index, (url, html) in enumerate(responses):
                if url:
                    # Handle redirects
                    if urls[index] != url:
                        self._add_url(urls[index], self._found_links)
                        if not self._same_domain(url):
                            continue

                    # TODO Handle last modified
                    # last_modified = response.info()['Last-Modified']
                    # Fri, 19 Oct 2018 18:49:51 GMT
                    # if last_modified:
                    #     dateTimeObject = datetime.strptime(last_modified, '%a, %d %b %Y %H:%M:%S %Z')
                    #     print('Last Modified:', dateTimeObject)

                    # TODO Handle priority

                    self._add_url(url, self._found_links)

                    if not html:
                        continue

                    page = str(html)
                    pattern = '<a [^>]*href=[\'|"](.*?)[\'"].*?>'

                    page_links = re.findall(pattern, page)

                    for link in page_links:
                        is_url = self._is_url(link)
                        link = self._normalize(link)
                        if is_url:
                            if self._is_internal(link):
                                self._add_url(link, links)
                            elif self._is_relative(link):
                                link = urljoin(url, link)
                                self._add_url(link, links)

            links = [link for link in links if link not in self._found_links]
            self._crawl(links)

    def _request(self, urls):
        async def __fetch(session, url):
            async with session.post().get(url) as response:
                try:
                    response.raise_for_status()
                    return url, await response.read()
                except (ClientResponseError, ClientError, ClientConnectionError, ClientOSError,
                        ServerConnectionError) as e:
                    if not self._no_verbose:
                        print('HTTP Error code=', e, ' ', url)
                    self._add_url(url, self._error_links)
                    return None, None

        async def __fetch_all():
            if self._timeout:
                async with aiohttp.ClientSession(read_timeout=self._read_timeout, conn_timeout=self._conn_timeout,
                                                 timeout=self._timeout, headers=self._request_headers) as session:
                    return await asyncio.gather(*[asyncio.create_task(__fetch(session, url)) for url in urls])

        task = asyncio.get_event_loop()
        return task.run_until_complete(__fetch_all())

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
