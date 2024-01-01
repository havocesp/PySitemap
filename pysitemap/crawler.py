import re
import ssl
from urllib import request
from urllib.error import URLError, HTTPError
from urllib.parse import urljoin
from urllib.request import HTTPRedirectHandler
from pysitemap.abc_crawler import _Crawler


# https://github.com/Guiorgy/PySitemap
# Fork of
# https://github.com/Cartman720/PySitemap


class Crawler(_Crawler):
    def _get_default_context(self):
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context

    class _HTTPRedirectHandler(HTTPRedirectHandler):
        max_redirections = 10

    def __init__(self, url, exclude=None, domain=None, no_verbose=False, request_header=None,
                 timeout=_Crawler.DEFAULT_TIMEOUT, retry_times=1, build_graph=False, verify_ssl=False,
                 max_redirects=10, max_path_depth=None, max_steps_depth=0):
        _Crawler.__init__(self, url, exclude=exclude, domain=domain, no_verbose=no_verbose,
                          request_header=request_header, timeout=timeout, retry_times=retry_times,
                          build_graph=build_graph, verify_ssl=verify_ssl, max_redirects=max_redirects,
                          max_path_depth=max_path_depth, max_steps_depth=max_steps_depth)

        self._context = None if verify_ssl else self._get_default_context()
        if self._max_redirects != 10:
            self._HTTPRedirectHandler.max_redirections = self._max_redirects
            request.build_opener(self._HTTPRedirectHandler)

    def _crawl(self, root_url):
        urls_to_request = {root_url}
        steps = {}
        if self._max_steps_depth:
            steps[root_url] = 0

        while urls_to_request:
            if self._stop:
                return

            try:
                while True:
                    url = urls_to_request.pop()
                    if not self._max_steps_depth or steps[url] <= self._max_steps_depth:
                        break
                    else:
                        try:
                            del steps[url]
                        except KeyError:
                            pass
            except KeyError:
                break

            if not self._no_verbose:
                print('Found:', len(self._graph.keys()), 'Parsing:', url)

            if response := self._request(url):
                step = 0
                if self._max_steps_depth and url in steps:
                    step = steps[url] + 1
                    del steps[url]

                # Handle redirects
                parsed_url = self._normalize(response.geturl())
                if url != parsed_url:
                    if not self._same_domain(parsed_url) or self._url_excluded(parsed_url):
                        continue
                    self._add_graph(url, parsed_url)
                    urls_to_request.discard(parsed_url)
                    if parsed_url in steps:
                        step = min(step, steps[parsed_url] + 1)
                        del steps[parsed_url]
                    if parsed_url in self._graph:
                        continue
                    url = parsed_url

                # TODO Handle last modified
                # last_modified = response.info()['Last-Modified']
                # Fri, 19 Oct 2018 18:49:51 GMT
                # if last_modified:
                #     dateTimeObject = datetime.strptime(last_modified, '%a, %d %b %Y %H:%M:%S %Z')
                #     print('Last Modified:', dateTimeObject)

                # TODO Handle priority

                self._add_graph(url, None)

                links = []

                for match in self._extract_urls(str(response.read())):
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
                         and link not in urls_to_request]

                urls_to_request.update(links)

                if self._max_steps_depth:
                    for link in links:
                        steps[link] = step

    def _request(self, url):
        for i in range(0, self._retry_times):
            try:
                req = request.Request(url, headers=self._request_headers)
                return request.urlopen(req, context=self._context, timeout=self._timeout)
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
        self._add_url(url, self._error_links)
        return None
