import pytest
from django.contrib.auth.models import User
from django.test import RequestFactory

from audittrail.admin import AuditLogAdmin
from audittrail.models import AuditLog


@pytest.mark.django_db
class TestAuditLogAdmin:
    def test_no_add_permission(self):
        from django.contrib.admin.sites import AdminSite

        admin_instance = AuditLogAdmin(AuditLog, AdminSite())
        factory = RequestFactory()
        request = factory.get("/admin/")
        request.user = User.objects.create_superuser("admin_add", "add@test.com", "pass")
        assert admin_instance.has_add_permission(request) is False

    def test_no_delete_permission(self):
        from django.contrib.admin.sites import AdminSite

        admin_instance = AuditLogAdmin(AuditLog, AdminSite())
        factory = RequestFactory()
        request = factory.get("/admin/")
        request.user = User.objects.create_superuser("admin_del", "del@test.com", "pass")
        assert admin_instance.has_delete_permission(request) is False
