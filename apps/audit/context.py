from contextvars import ContextVar

_request_id = ContextVar("request_id", default=None)


def set_request_id(request_id):
    _request_id.set(request_id)


def get_request_id():
    return _request_id.get()
