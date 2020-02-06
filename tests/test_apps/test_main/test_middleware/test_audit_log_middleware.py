import uuid
from unittest.mock import Mock, call, patch

import pytest
from django.db.models.signals import m2m_changed, post_delete, post_save

from server.apps.main.middleware import AuditLogMiddleware
from server.apps.main.models import LegalBasis


class TestAuditLogMiddleWare:
    pytestmark = pytest.mark.django_db

    @classmethod
    def setup_class(cls):
        cls.get_response = Mock()

    @classmethod
    def is_valid_uuid(cls, v):
        try:
            uuid.UUID(str(v))
            return True
        except ValueError:
            return False

    def test_init(self):
        middleware = AuditLogMiddleware(self.get_response)
        assert middleware.get_response == self.get_response

    @patch.object(AuditLogMiddleware, "make_m2m_signal_receiver")
    @patch.object(AuditLogMiddleware, "make_save_signal_receiver")
    @patch.object(AuditLogMiddleware, "make_delete_signal_receiver")
    def test_get_signal_calls(
        self,
        make_delete_signal_receiver,
        make_save_signal_receiver,
        make_m2m_signal_receiver,
    ):
        middleware = AuditLogMiddleware(self.get_response)

        request = Mock()
        calls = middleware.get_signal_calls(request)

        assert calls[0]["signal"] == post_save
        assert calls[0]["kwargs"]["sender"] == LegalBasis
        assert callable(calls[0]["kwargs"]["receiver"])
        assert self.is_valid_uuid(calls[0]["kwargs"]["dispatch_uid"])

        assert calls[1]["signal"] == post_delete
        assert calls[1]["kwargs"]["sender"] == LegalBasis
        assert callable(calls[1]["kwargs"]["receiver"])
        assert self.is_valid_uuid(calls[1]["kwargs"]["dispatch_uid"])

        assert calls[2]["signal"] == m2m_changed
        assert calls[2]["kwargs"]["sender"] == LegalBasis.consents.through
        assert callable(calls[2]["kwargs"]["receiver"])
        assert self.is_valid_uuid(calls[2]["kwargs"]["dispatch_uid"])

        make_delete_signal_receiver.assert_called_once_with(request)
        make_save_signal_receiver.assert_called_once_with(request)
        make_m2m_signal_receiver.assert_called_once_with(request)

    @patch.object(AuditLogMiddleware, "get_remote_addr")
    @patch("server.apps.main.middleware.action")
    def test_make_save_signal_receiver_when_created(self, action, get_remote_addr):
        middleware = AuditLogMiddleware(self.get_response)

        get_remote_addr.return_value = "127.0.0.1"
        request = Mock()
        instance = Mock()

        middleware.make_save_signal_receiver(request)(
            Mock(), instance=instance, created=True
        )

        action.send.assert_called_once_with(
            sender=request.user,
            action_object=instance,
            verb="created",
            remote_addr="127.0.0.1",
        )

    @patch.object(AuditLogMiddleware, "get_remote_addr")
    @patch("server.apps.main.middleware.action")
    def test_make_save_signal_receiver_when_updated(self, action, get_remote_addr):
        middleware = AuditLogMiddleware(self.get_response)

        get_remote_addr.return_value = "127.0.0.1"
        instance = Mock()
        request = Mock()

        middleware.make_save_signal_receiver(request)(
            Mock(), instance=instance, created=False
        )

        action.send.assert_called_once_with(
            sender=request.user,
            action_object=instance,
            verb="updated",
            remote_addr="127.0.0.1",
        )

    @patch.object(AuditLogMiddleware, "get_remote_addr")
    @patch("server.apps.main.middleware.action")
    def test_make_delete_signal_receiver(self, action, get_remote_addr):
        middleware = AuditLogMiddleware(self.get_response)

        get_remote_addr.return_value = "127.0.0.1"
        instance = Mock()
        request = Mock()
        middleware.make_delete_signal_receiver(request)(Mock(), instance=instance)

        action.send.assert_called_once_with(
            sender=request.user,
            action_object=instance,
            verb="deleted",
            remote_addr="127.0.0.1",
        )

    @patch("server.apps.main.middleware.Consent")
    @patch.object(AuditLogMiddleware, "get_remote_addr")
    @patch("server.apps.main.middleware.action")
    def test_m2m_signal_receiver_when_added(self, action, get_remote_addr, Consent):
        middleware = AuditLogMiddleware(self.get_response)

        get_remote_addr.return_value = "127.0.0.1"
        instance = Mock()
        request = Mock()
        middleware.make_m2m_signal_receiver(request)(
            Mock(), instance=instance, action="post_add", pk_set=[1, 2, 3]
        )

        kwargs = {
            "sender": request.user,
            "target": instance,
            "remote_addr": "127.0.0.1",
        }

        action.send.assert_has_calls(
            [
                call(verb="added", action_object=Consent.objects.get(pk=1), **kwargs),
                call(verb="added", action_object=Consent.objects.get(pk=2), **kwargs),
                call(verb="added", action_object=Consent.objects.get(pk=3), **kwargs),
            ]
        )

    @patch("server.apps.main.middleware.Consent")
    @patch.object(AuditLogMiddleware, "get_remote_addr")
    @patch("server.apps.main.middleware.action")
    def test_m2m_signal_receiver_when_deleted(self, action, get_remote_addr, Consent):
        middleware = AuditLogMiddleware(self.get_response)

        get_remote_addr.return_value = "127.0.0.1"
        instance = Mock()
        request = Mock()
        middleware.make_m2m_signal_receiver(request)(
            Mock(), instance=instance, action="post_remove", pk_set=[1, 2, 3]
        )

        kwargs = {
            "sender": request.user,
            "target": instance,
            "remote_addr": "127.0.0.1",
        }

        action.send.assert_has_calls(
            [
                call(verb="removed", action_object=Consent.objects.get(pk=1), **kwargs),
                call(verb="removed", action_object=Consent.objects.get(pk=2), **kwargs),
                call(verb="removed", action_object=Consent.objects.get(pk=3), **kwargs),
            ]
        )

    @patch.object(AuditLogMiddleware, "get_remote_addr")
    @patch("server.apps.main.middleware.action")
    def test_m2m_signal_receiver_when_cleared(self, action, get_remote_addr):
        middleware = AuditLogMiddleware(self.get_response)

        get_remote_addr.return_value = "127.0.0.1"
        instance = Mock()
        request = Mock()
        middleware.make_m2m_signal_receiver(request)(
            Mock(), instance=instance, action="post_clear"
        )

        kwargs = {
            "sender": request.user,
            "action_object": instance,
            "remote_addr": "127.0.0.1",
        }

        action.send.assert_called_once_with(verb="cleared consents", **kwargs)

    def test_get_remote_addr_x_forwarded_for(self):
        middleware = AuditLogMiddleware(self.get_response)

        assert (
            middleware.get_remote_addr(
                Mock(
                    META={
                        "HTTP_X_FORWARDED_FOR": "172.16.0.1, 192.168.0.1, 127.0.0.1",
                        "REMOTE_ADDR": "192.168.0.1",
                    }
                )
            )
            == "172.16.0.1"
        )

    def test_get_remote_addr(self):
        middleware = AuditLogMiddleware(self.get_response)

        assert (
            middleware.get_remote_addr(Mock(META={"REMOTE_ADDR": "192.168.0.1",}))
            == "192.168.0.1"
        )
