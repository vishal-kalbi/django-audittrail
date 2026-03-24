import pytest
from django.contrib.auth.models import User

from audittrail import disabled
from audittrail.models import AuditAction, AuditLog

from tests.models import FKModel, JsonFieldModel, SensitiveModel, SimpleModel


@pytest.mark.django_db
class TestCreateAction:
    def test_create_logs_entry(self):
        obj = SimpleModel.objects.create(name="Test", value=42)
        logs = AuditLog.objects.for_instance(obj)
        assert logs.count() == 1
        log = logs.first()
        assert log.action == AuditAction.CREATE
        assert "name" in log.changes
        assert log.changes["name"]["old"] is None
        assert log.changes["name"]["new"] == "Test"
        assert log.changes["value"]["new"] == 42

    def test_create_captures_object_repr(self):
        obj = SimpleModel.objects.create(name="Hello")
        log = AuditLog.objects.for_instance(obj).first()
        assert log.object_repr == "Hello"


@pytest.mark.django_db
class TestUpdateAction:
    def test_update_logs_changed_fields_only(self):
        obj = SimpleModel.objects.create(name="Test", value=10)
        obj.name = "Updated"
        obj.save()

        logs = AuditLog.objects.for_instance(obj)
        assert logs.count() == 2  # create + update
        update_log = logs.filter(action=AuditAction.UPDATE).first()
        assert update_log.changes == {"name": {"old": "Test", "new": "Updated"}}

    def test_no_change_no_log(self):
        obj = SimpleModel.objects.create(name="Test", value=10)
        obj.save()  # save without changes

        logs = AuditLog.objects.for_instance(obj)
        assert logs.count() == 1  # only the create

    def test_multiple_field_changes(self):
        obj = SimpleModel.objects.create(name="Test", value=10)
        obj.name = "New"
        obj.value = 20
        obj.save()

        update_log = AuditLog.objects.for_instance(obj).filter(action=AuditAction.UPDATE).first()
        assert "name" in update_log.changes
        assert "value" in update_log.changes


@pytest.mark.django_db
class TestDeleteAction:
    def test_delete_logs_entry(self):
        obj = SimpleModel.objects.create(name="Test", value=10)
        pk = obj.pk
        obj.delete()

        logs = AuditLog.objects.filter(object_pk=str(pk))
        delete_log = logs.filter(action=AuditAction.DELETE).first()
        assert delete_log is not None
        assert delete_log.changes["name"]["old"] == "Test"
        assert delete_log.changes["name"]["new"] is None


@pytest.mark.django_db
class TestMasking:
    def test_masked_fields_store_stars(self):
        obj = SensitiveModel.objects.create(
            name="Patient", ssn="123-45-6789", password="secret"
        )
        log = AuditLog.objects.for_instance(obj).first()
        assert log.changes["ssn"]["new"] == "***"
        assert log.changes["password"]["new"] == "***"
        assert log.changes["name"]["new"] == "Patient"

    def test_masked_fields_on_update(self):
        obj = SensitiveModel.objects.create(
            name="Patient", ssn="123-45-6789", password="secret"
        )
        obj.ssn = "987-65-4321"
        obj.save()

        update_log = AuditLog.objects.for_instance(obj).filter(action=AuditAction.UPDATE).first()
        assert update_log.changes["ssn"] == {"old": "***", "new": "***"}


@pytest.mark.django_db
class TestExcludeFields:
    def test_excluded_fields_not_in_diff(self):
        obj = SensitiveModel.objects.create(
            name="Patient", ssn="123-45-6789", password="secret"
        )
        log = AuditLog.objects.for_instance(obj).first()
        # updated_at is excluded
        assert "updated_at" not in log.changes


@pytest.mark.django_db
class TestDisabledContextManager:
    def test_disabled_suppresses_logs(self):
        with disabled():
            obj = SimpleModel.objects.create(name="Silent", value=0)
        assert AuditLog.objects.for_instance(obj).count() == 0

    def test_disabled_nested(self):
        with disabled():
            with disabled():
                obj = SimpleModel.objects.create(name="Deep", value=0)
            # still disabled after inner exits
            obj2 = SimpleModel.objects.create(name="Deep2", value=0)

        assert AuditLog.objects.for_instance(obj).count() == 0
        assert AuditLog.objects.for_instance(obj2).count() == 0

    def test_audit_resumes_after_disabled(self):
        with disabled():
            SimpleModel.objects.create(name="Silent", value=0)
        obj = SimpleModel.objects.create(name="Loud", value=1)
        assert AuditLog.objects.for_instance(obj).count() == 1


@pytest.mark.django_db
class TestForeignKey:
    def test_fk_change_tracked(self):
        related1 = SimpleModel.objects.create(name="A", value=1)
        related2 = SimpleModel.objects.create(name="B", value=2)
        obj = FKModel.objects.create(name="FK Test", related=related1)

        obj.related = related2
        obj.save()

        update_log = AuditLog.objects.for_instance(obj).filter(action=AuditAction.UPDATE).first()
        assert "related_id" in update_log.changes
        assert update_log.changes["related_id"]["old"] == related1.pk
        assert update_log.changes["related_id"]["new"] == related2.pk


@pytest.mark.django_db
class TestJsonField:
    def test_json_field_change_tracked(self):
        obj = JsonFieldModel.objects.create(name="JSON", data={"key": "val1"})
        obj.data = {"key": "val2"}
        obj.save()

        update_log = AuditLog.objects.for_instance(obj).filter(action=AuditAction.UPDATE).first()
        assert "data" in update_log.changes


@pytest.mark.django_db
class TestNoRequestContext:
    def test_saves_without_request_context(self):
        """Saving outside a request (e.g. management command) should work with actor=None."""
        obj = SimpleModel.objects.create(name="CLI", value=0)
        log = AuditLog.objects.for_instance(obj).first()
        assert log.actor is None
        assert log.remote_addr is None
        assert log.actor_username == ""
