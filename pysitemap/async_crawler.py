import asyncio
import re
from urllib.parse import urljoin
from aiohttp import ClientResponseError, ClientError, ClientConnectionError, ClientOSError, ServerConnectionError
from aiohttp import TCPConnector, ClientSession
from aiohttp.client import ClientTimeout
from aiohttp.client_exceptions import TooManyRedirects
from pysitemap import crawler


# https://github.com/Guiorgy/PySitemap
# Fork of
# https://github.com/Cartman720/PySitemap


class Crawler(crawler.abc._Crawler):
    DEFAULT_TIMEOUT = ClientTimeout(total=5*60)

    def __init__(self, url, exclude=None, domain=None, no_verbose=False, request_header=None, timeout=DEFAULT_TIMEOUT,
                 retry_times=1, max_requests=100, build_graph=False, verify_ssl=False, max_redirects=10,
                 max_path_depth=None, max_steps_depth=0):
        crawler.abc._Crawler.__init__(url, exclude=exclude, domain=domain, no_verbose=no_verbose,
                                      request_header=request_header, timeout=timeout, retry_times=retry_times,
                                      build_graph=build_graph, verify_ssl=verify_ssl, max_redirects=max_redirects,
                                      max_path_depth=max_path_depth, max_steps_depth=max_steps_depth)

        self._max_requests = max_requests + 1 if max_requests and max_requests > 0 else 100

    def _crawl(self, root_url):
        urls_to_request = {root_url}
        steps = {}
        if self._max_steps_depth:
            steps[root_url] = 0

        while urls_to_request:
            if self._stop:
                return

            urls = []
            try:
                while len(urls) < self._max_requests:
                    url = urls_to_request.pop()
                    if not self._max_steps_depth or steps[url] < self._max_steps_depth:
                        urls.append(url)
            except KeyError:
                # There were less than self._max_requests urls in urls_to_request set
                pass

            if not self._no_verbose:
                print('Found:', len(self._graph.keys()), 'Parsing:', urls)

            responses = self._request(urls)
            if responses:
                for (requested_url, url, html) in responses:
                    if self._stop:
                        return

                    if url:
                        step = steps[requested_url] + 1

                        # Handle redirects
                        if requested_url != url:
                            self._add_graph(requested_url, url)
                            try:
                                del steps[requested_url]
                            except KeyError:
                                pass
                            if not self._same_domain(url) or url in self._graph:
                                continue

                        # TODO Handle last modified
                        # last_modified = response.info()['Last-Modified']
                        # Fri, 19 Oct 2018 18:49:51 GMT
                        # if last_modified:
                        #     dateTimeObject = datetime.strptime(last_modified, '%a, %d %b %Y %H:%M:%S %Z')
                        #     print('Last Modified:', dateTimeObject)

                        # TODO Handle priority

                        self._add_graph(url, None)

                        if not html:
                            continue

                        page = str(html)
                        pattern = '<a [^>]*href=[\'|"](.*?)[\'"].*?>'

                        links = []

                        for match in re.findall(pattern, page):
                            for link in match.split():
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

                        links = [link for link in links
                                 if link not in self._graph
                                 and link not in self._error_links
                                 and link not in urls]

                        urls_to_request.update(links)
                        try:
                            del steps[requested_url]
                        except KeyError:
                            pass
                        for link in links:
                            steps[link] = step

    # def _chunks(self, l, n):
    #     for i in range(0, len(l), n):
    #         yield l[i:i + n]

    def _request(self, urls):
        async def __fetch(session, url):
            for i in range(0, self._retry_times):
                try:
                    async with session.get(url, max_redirects=0) as response:
                        response.raise_for_status()
                        return url, response.url.human_repr(), await response.read()
                except TooManyRedirects:
                    if not self._no_verbose:
                        print("Couldn't get", url, 'there were too many redirection. Error=', e)
                except (ClientResponseError, ClientError, ClientConnectionError, ClientOSError,
                        ServerConnectionError) as e:
                    if not self._no_verbose:
                        print('HTTP Error code=', e, ' ', url)
                except (AssertionError, Exception) as e:
                    if not self._no_verbose:
                        print('Error raised while requesting "', url, '": ', e)
            self._add_url(url, self._error_links)
            return url, None, None

        async def __fetch_all():
            if self._timeout:
                async with ClientSession(timeout=self._timeout,
                                         headers=self._request_headers,
                                         connector=TCPConnector(verify_ssl=self._verify_ssl)) as session:
                    return await asyncio.gather(*[asyncio.create_task(__fetch(session, url)) for url in urls])

        loop = asyncio.get_event_loop()
        return loop.run_until_complete(__fetch_all())

# TODO: Limit the depth of the graph
# TODO: Implement a stop function to stop crawling with current data
