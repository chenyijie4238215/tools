from rx.concurrency import ThreadPoolScheduler
import multiprocessing
from rx import Observable

optimal_thread_count = multiprocessing.cpu_count()
pool_scheduler = ThreadPoolScheduler(optimal_thread_count)

disposes = {}


def run_in_thread(func, on_success, on_fail, main_scheduler=None):
    """
    线程中执行耗时操作
    :param func:
    :param on_success:
    :param on_fail:
    :param main_scheduler:
    :return:
    """
    api = Observable.range(0, 1)\
        .map(lambda x: func())\
        .subscribe_on(pool_scheduler)
    if main_scheduler:
        api = api.observe_on(main_scheduler)
    api.subscribe(on_next=on_success, on_error=on_fail)
    return api


def create_http_observable(request_obj, cookie_store=None, cache_store=None, http_client=None):
    """
    创建http观察对象
    :param request_obj:
    :param cookie_store:
    :param cache_store:
    :param http_client:
    :return:
    """
    from tool_package.rx_http_request.http_request import RespondListener
    from tool_package.rx_http_request.http_request import RequestClient

    def create_http(observer):
        respond_listener = RespondListener(observer)
        try:
            http_client.request(request_obj, respond_listener)
        except Exception as e:
            respond_listener.on_fail(e)

    if http_client is None:
        http_client = RequestClient(cookie_store, cache_store)
    return Observable.create(create_http)


def create_http_request(request_obj, cookie_store=None, cache_store=None, use_mock=False):
    """
    创建一个http请求
    :param request_obj:  请求体
    :param use_mock: 是否使用模拟数据
    :return:
    """
    try:
        if use_mock:
            from tool_package.rx_http_request.http_request import MockClient
            return create_http_observable(request_obj, http_client=MockClient())
        else:
            return create_http_observable(request_obj, cookie_store, cache_store)\
                .subscribe_on(pool_scheduler)
    except Exception as e:
        print("create_http_request error:", e)


def auto_release_disposable(disposable, key):
    """
    自动释放重复的网络请求
    :param disposable:
    :param key:
    :return:
    """
    if disposable is not None and hasattr(disposable, 'dispose'):
        last = disposes.pop(key, None)
        if last is not None:
            last.dispose()
        disposes[key] = disposable


if __name__ == "__main__":
    import threading
    import sys

    from tool_package.rx_http_request.rx_application import RxApplication, MainThreadScheduler
    from tool_function.decorator import print_exec_thread

    app = RxApplication(sys.argv)

    print("main:", threading.currentThread().getName())

    @print_exec_thread
    def on_success(data):
        print("on_success", "*"*100)
        print("on_success:", data)

    @print_exec_thread
    def on_fail(error):
        print("on_fail:", error)

    def test_run_in_thread(txt):
        print("test_run_in_thread:", threading.currentThread().getName(), txt)
        return txt

    def test_http_request():
        from tool_package.rx_http_request.http_request import HttpRequest, RequestMethod, RespondFormat
        http_request_obj = HttpRequest()
        http_request_obj.url = "https://www.baidu.com"
        # http_request_obj.url = "http://www.futurecrew.com/skaven/song_files/mp3/razorback.mp3"
        http_request_obj.method = RequestMethod.POST
        http_request_obj.respond_format = RespondFormat.TEXT
        # http_request_obj.respond_format = RespondFormat.STREAM

        _api = create_http_request(http_request_obj, use_mock=True)\
            .map(lambda result: result.data) \
            .observe_on(MainThreadScheduler()) \
            .subscribe(on_next=on_success, on_error=on_fail)
        auto_release_disposable(_api, "test_http_request")


    # run_in_thread(lambda: test_run_in_thread("hello"), on_success, on_fail, MainThreadScheduler())
    test_http_request()

    sys.exit(app.exec_())
