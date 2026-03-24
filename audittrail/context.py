import threading
from contextlib import contextmanager

_thread_locals = threading.local()


def get_current_user():
    """Return the user from the current request context, or None."""
    return getattr(_thread_locals, "user", None)


def get_current_ip():
    """Return the IP address from the current request context, or None."""
    return getattr(_thread_locals, "remote_addr", None)


def get_current_request_path():
    """Return the request path from the current request context, or empty string."""
    return getattr(_thread_locals, "request_path", "")


def get_current_request_method():
    """Return the HTTP method from the current request context, or empty string."""
    return getattr(_thread_locals, "request_method", "")


def set_audit_context(user=None, remote_addr=None, request_path="", request_method=""):
    """Store request context in thread-local storage."""
    _thread_locals.user = user
    _thread_locals.remote_addr = remote_addr
    _thread_locals.request_path = request_path
    _thread_locals.request_method = request_method


def clear_audit_context():
    """Clear thread-local storage to prevent context leaking between requests."""
    _thread_locals.user = None
    _thread_locals.remote_addr = None
    _thread_locals.request_path = ""
    _thread_locals.request_method = ""


def is_audit_disabled():
    """Check if audit logging is currently disabled."""
    return getattr(_thread_locals, "audit_disabled", False)


@contextmanager
def disabled():
    """Context manager to temporarily disable audit logging.

    Usage:
        with disabled():
            instance.save()  # no audit log created
    """
    previous = getattr(_thread_locals, "audit_disabled", False)
    _thread_locals.audit_disabled = True
    try:
        yield
    finally:
        _thread_locals.audit_disabled = previous
