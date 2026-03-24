import pytest
from django.contrib.auth.models import User
from django.test import RequestFactory

from audittrail.context import (
    clear_audit_context,
    get_current_ip,
    get_current_request_method,
    get_current_request_path,
    get_current_user,
    set_audit_context,
)
from audittrail.middleware import AuditMiddleware


class TestAuditMiddleware:
    def test_sets_and_clears_context(self):
        factory = RequestFactory()
        request = factory.get("/test-path/")
        request.user = type("MockUser", (), {"is_authenticated": True, "pk": 1, "username": "testuser"})()
        request.META["REMOTE_ADDR"] = "192.168.1.100"

        context_during_request = {}

        def mock_get_response(req):
            context_during_request["user"] = get_current_user()
            context_during_request["ip"] = get_current_ip()
            context_during_request["path"] = get_current_request_path()
            context_during_request["method"] = get_current_request_method()
            return type("Response", (), {"status_code": 200})()

        middleware = AuditMiddleware(mock_get_response)
        middleware(request)

        # Context was set during request
        assert context_during_request["user"] is request.user
        assert context_during_request["ip"] == "192.168.1.100"
        assert context_during_request["path"] == "/test-path/"
        assert context_during_request["method"] == "GET"

        # Context is cleared after request
        assert get_current_user() is None
        assert get_current_ip() is None

    def test_x_forwarded_for(self):
        factory = RequestFactory()
        request = factory.get("/", HTTP_X_FORWARDED_FOR="10.0.0.1, 172.16.0.1")
        request.user = type("MockUser", (), {"is_authenticated": False})()

        captured_ip = {}

        def mock_get_response(req):
            captured_ip["ip"] = get_current_ip()
            return type("Response", (), {"status_code": 200})()

        middleware = AuditMiddleware(mock_get_response)
        middleware(request)

        assert captured_ip["ip"] == "10.0.0.1"

    def test_anonymous_user_stored_as_none(self):
        factory = RequestFactory()
        request = factory.get("/")
        request.user = type("MockUser", (), {"is_authenticated": False})()

        captured = {}

        def mock_get_response(req):
            captured["user"] = get_current_user()
            return type("Response", (), {"status_code": 200})()

        middleware = AuditMiddleware(mock_get_response)
        middleware(request)

        assert captured["user"] is None

    def test_clears_context_on_exception(self):
        factory = RequestFactory()
        request = factory.get("/error/")
        request.user = type("MockUser", (), {"is_authenticated": True, "pk": 1})()

        def mock_get_response(req):
            raise ValueError("view error")

        middleware = AuditMiddleware(mock_get_response)

        with pytest.raises(ValueError):
            middleware(request)

        # Context should still be cleared
        assert get_current_user() is None
        assert get_current_ip() is None


class TestAuditContext:
    def test_set_and_get(self):
        set_audit_context(
            user="fake_user",
            remote_addr="1.2.3.4",
            request_path="/foo/",
            request_method="POST",
        )
        assert get_current_user() == "fake_user"
        assert get_current_ip() == "1.2.3.4"
        assert get_current_request_path() == "/foo/"
        assert get_current_request_method() == "POST"
        clear_audit_context()

    def test_clear(self):
        set_audit_context(user="user", remote_addr="1.1.1.1")
        clear_audit_context()
        assert get_current_user() is None
        assert get_current_ip() is None
