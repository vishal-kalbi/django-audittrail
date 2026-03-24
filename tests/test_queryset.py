import datetime

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from audittrail.context import clear_audit_context, set_audit_context
from audittrail.models import AuditAction, AuditLog

from tests.models import SimpleModel


@pytest.mark.django_db
class TestAuditQuerySet:
    def test_for_instance(self):
        obj1 = SimpleModel.objects.create(name="A", value=1)
        obj2 = SimpleModel.objects.create(name="B", value=2)

        logs1 = AuditLog.objects.for_instance(obj1)
        logs2 = AuditLog.objects.for_instance(obj2)

        assert logs1.count() == 1
        assert logs2.count() == 1
        assert logs1.first().object_pk == str(obj1.pk)

    def test_for_model(self):
        SimpleModel.objects.create(name="A", value=1)
        SimpleModel.objects.create(name="B", value=2)

        logs = AuditLog.objects.for_model(SimpleModel)
        assert logs.count() == 2

    def test_by_user(self):
        user = User.objects.create_user(username="auditor", password="test")
        set_audit_context(user=user, remote_addr="127.0.0.1")
        try:
            SimpleModel.objects.create(name="Tracked", value=1)
        finally:
            clear_audit_context()

        logs = AuditLog.objects.by_user(user)
        assert logs.count() == 1
        assert logs.first().actor == user
        assert logs.first().actor_username == "auditor"

    def test_creates_filter(self):
        obj = SimpleModel.objects.create(name="Test", value=1)
        obj.name = "Updated"
        obj.save()

        assert AuditLog.objects.for_instance(obj).creates().count() == 1
        assert AuditLog.objects.for_instance(obj).updates().count() == 1

    def test_deletes_filter(self):
        obj = SimpleModel.objects.create(name="Test", value=1)
        pk = obj.pk
        obj.delete()

        all_logs = AuditLog.objects.filter(object_pk=str(pk))
        assert all_logs.deletes().count() == 1

    def test_between(self):
        now = timezone.now()
        SimpleModel.objects.create(name="Test", value=1)

        later = now + datetime.timedelta(seconds=5)
        logs = AuditLog.objects.between(now - datetime.timedelta(seconds=1), later)
        assert logs.count() >= 1
