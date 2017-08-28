from urllib.parse import urlparse

import requests
from PyQt5.QtCore import QUrl, QByteArray
from PyQt5.QtNetwork import QNetworkCookie, QNetworkCookieJar

from tool_function.decorator import singleton


@singleton
class CacheStore(object):
    def __init__(self):
        """
        可以分为内存缓存和磁盘缓存
        """
        pass

    def add(self, request, data):
        pass

    def get(self, request):
        pass

    def clear(self, request):
        pass


@singleton
class CookieStore(object):
    def __init__(self):
        self._cookie_jar = QNetworkCookieJar()

    def add(self, cookie_dict, scheme, hostname, path="/"):
        cookie_list = []
        for key, value in cookie_dict.items():
            cookie = QNetworkCookie()
            cookie.setDomain(hostname)
            cookie.setPath(path)
            key_b = QByteArray()
            key_b.append(key)
            cookie.setName(key_b)
            value_b = QByteArray()
            value_b.append(value)
            cookie.setValue(value_b)
            cookie_list.append(cookie)
        self._cookie_jar.setCookiesFromUrl(cookie_list, QUrl(str(scheme)))

    def get(self, url):
        cookie_list = self._cookie_jar.cookiesForUrl(QUrl(url))
        cookie_dict = {}
        for cookie in cookie_list:
            cookie_dict[cookie.name()] = cookie.value()
        return cookie_dict

    def clear(self, url):
        cookie_list = self._cookie_jar.cookiesForUrl(QUrl(url))
        for cookie in cookie_list:
            cookie.setValue("")
        self._cookie_jar.setCookiesFromUrl(cookie_list, QUrl(url))


class ApiException(Exception):
    def __init__(self, code, data=None, msg=''):
        self.code = code
        self.data = data
        self.msg = msg


class RequestMethod:
    POST = "POST"
    GET = "GET"


class RespondFormat:
    TEXT = "text"
    JSON = "json"
    BINARY = "binary"
    STREAM = "stream"


class HttpException(Exception):
    def __init__(self, code, msg, request, response):
        self.code = code
        self.msg = msg
        self.request = request
        self.response = response


class HttpResult(object):
    def __init__(self, request, response, data):
        self.request = request
        self.response = response
        self.data = data


class HttpRequest(object):
    def __init__(self):
        self.method = RequestMethod.POST
        self.url = None
        self.headers = None
        self.files = None
        self.data = None
        self.params = None
        self.auth = None
        self.cookies = None
        self.hooks = None
        self.json = None
        self.verify = True
        self.respond_format = RespondFormat.JSON
        self.time_out = 10
        self.can_read_cache = False
        self.can_write_cache = False
        self.user_agent = ""


class RespondListener(object):
    def __init__(self, observer):
        self.observer = observer

    def on_progress(self, chunk, chunk_size, transported_size, total_size):
        progress_dict = dict()
        progress_dict["chunk"] = chunk
        progress_dict["chunk_size"] = chunk_size
        progress_dict["transported_size"] = transported_size
        progress_dict["total_size"] = total_size
        self.observer.on_next(progress_dict)

    def on_success(self, http_result):
        if http_result is not None:
            self.observer.on_next(http_result)
        self.observer.on_completed()

    def on_fail(self, error):
        print(error)
        self.observer.on_error(error)


class RequestClient(object):
    def __init__(self, cookie_store=None, cache_store=None):
        self._cookie_store = cookie_store
        self._cache_store = cache_store
        self._session = requests.Session()
        self.proxies = None

    def request(self, http_request, respond_listener):
        hostname = urlparse(http_request.url).hostname
        scheme = urlparse(http_request.url).scheme

        if self._cache_store is not None:
            cookie_dict = self._cache_store.get(http_request.url)
            if len(cookie_dict) > 0:
                self._session.cookies = requests.utils.cookiejar_from_dict(cookie_dict)

        if self._cache_store is not None and http_request.read_cache_enable:
            pass

        prepped = self._session.prepare_request(
            requests.Request(
                method=http_request.method,
                url=http_request.url,
                headers=http_request.headers,
                files=http_request.files,
                data=http_request.data,
                params=http_request.params,
                auth=http_request.auth,
                cookies=http_request.cookies,
                hooks=http_request.hooks,
                json=http_request.json
            )
        )
        prepped.headers["User-Agent"] = http_request.user_agent
        resp = None
        content = None
        try:
            self._session.verify = http_request.verify
            stream = True if http_request.respond_format == RespondFormat.STREAM else False
            if self.proxies is None:
                resp = self._session.send(prepped, stream=stream, timeout=http_request.time_out)
            else:
                resp = self._session.send(prepped, stream=stream, timeout=http_request.time_out, proxies=self.proxies)
            resp.raise_for_status()
            if http_request.respond_format == RespondFormat.TEXT:
                content = resp.text
            elif http_request.respond_format == RespondFormat.JSON:
                content = resp.json()
            elif http_request.respond_format == RespondFormat.BINARY:
                content = resp.content
        except BaseException as e:
            respond_listener.on_fail(error=e)
        finally:
            if http_request.files is not None:
                try:
                    f = http_request.files.get("file", None)
                    if f:
                        f.close()
                except Exception as e:
                    print(e)

        if resp and resp.status_code != 200:
            respond_listener.on_fail(HttpException(resp.status_code, "", http_request, resp))
            return

        if self._cookie_store is not None:
            if len(resp.cookies) > 0:
                self._cookie_store.add(cookie_dict=requests.utils.dict_from_cookiejar(resp.cookies),
                                       scheme=scheme, hostname=hostname)

        if http_request.respond_format in RespondFormat.STREAM:
            tran_size = 0
            total_length = resp.headers.get('content-length')
            total_length = 0 if total_length is None else int(total_length)
            for chunk in resp.iter_content(1024):
                chunk_size = len(chunk)
                tran_size += chunk_size
                respond_listener.on_progress(chunk, chunk_size, tran_size, total_length)
        respond_listener.on_success(HttpResult(http_request, resp, content))


@singleton
class MockClient(object):
    def __init__(self, mock_data_path=None):
        if not mock_data_path:
            import os
            self.mock_data_path = os.path.dirname(os.path.realpath(__file__))+"/mock.json".replace("\\", "/")

    def request(self, http_request, respond_listener):
        from rx import Observable

        def on_next(i):
            print(i)
            if data:
                respond_listener.on_success(HttpResult(http_request, None, data))
            else:
                respond_listener.on_fail("mock data have no:{}".format(http_request.url))
        with open(self.mock_data_path, "r") as f:
            import json
            mock_data = json.load(f)
        data = mock_data.get(http_request.url, None)
        Observable.timer(1000).subscribe(on_next)