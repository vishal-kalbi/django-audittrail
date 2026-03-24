from audittrail.context import clear_audit_context, set_audit_context


class AuditMiddleware:
    """Middleware that stores request context (user, IP, path) for audit logging.

    Add to MIDDLEWARE after SessionMiddleware and AuthenticationMiddleware:

        MIDDLEWARE = [
            ...
            'audittrail.middleware.AuditMiddleware',
            ...
        ]
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user and not user.is_authenticated:
            user = None

        set_audit_context(
            user=user,
            remote_addr=self._get_client_ip(request),
            request_path=request.path[:500],
            request_method=request.method,
        )

        try:
            response = self.get_response(request)
        finally:
            clear_audit_context()

        return response

    @staticmethod
    def _get_client_ip(request):
        """Extract client IP, respecting X-Forwarded-For for reverse proxies."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")
