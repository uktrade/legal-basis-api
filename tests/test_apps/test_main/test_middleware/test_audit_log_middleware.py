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

    @patch.object(AuditLogMiddleware, "handle_m2m_post_add_remove_actions")
    @patch.object(AuditLogMiddleware, "get_remote_addr")
    def test_m2m_signal_receiver_with_post_add(
        self, get_remote_addr, handle_m2m_post_add_remove_actions
    ):
        middleware = AuditLogMiddleware(self.get_response)

        get_remote_addr.return_value = "127.0.0.1"
        instance = Mock()
        request = Mock()

        action_kwargs = {"sender": request.user, "remote_addr": "127.0.0.1"}

        middleware.make_m2m_signal_receiver(request)(
            Mock(), instance=instance, action="post_add", pk_set=[1, 2, 3]
        )
        handle_m2m_post_add_remove_actions.assert_called_once_with(
            instance=instance,
            action_kwargs=action_kwargs,
            action_name="post_add",
            pk_set=[1, 2, 3],
        )

    @patch.object(AuditLogMiddleware, "handle_m2m_post_add_remove_actions")
    @patch.object(AuditLogMiddleware, "get_remote_addr")
    def test_m2m_signal_receiver_with_post_remove(
        self, get_remote_addr, handle_m2m_post_add_remove_actions
    ):
        middleware = AuditLogMiddleware(self.get_response)

        get_remote_addr.return_value = "127.0.0.1"
        instance = Mock()
        request = Mock()

        action_kwargs = {"sender": request.user, "remote_addr": "127.0.0.1"}

        middleware.make_m2m_signal_receiver(request)(
            Mock(), instance=instance, action="post_remove", pk_set=[3, 4, 5]
        )
        handle_m2m_post_add_remove_actions.assert_called_once_with(
            instance=instance,
            action_kwargs=action_kwargs,
            action_name="post_remove",
            pk_set=[3, 4, 5],
        )

    @patch.object(AuditLogMiddleware, "handle_m2m_post_clear_action")
    @patch.object(AuditLogMiddleware, "get_remote_addr")
    def test_m2m_signal_receiver_with_post_clear(
        self, get_remote_addr, handle_m2m_post_clear_action,
    ):
        middleware = AuditLogMiddleware(self.get_response)

        get_remote_addr.return_value = "127.0.0.1"
        instance = Mock()
        request = Mock()

        action_kwargs = {"sender": request.user, "remote_addr": "127.0.0.1"}

        middleware.make_m2m_signal_receiver(request)(
            Mock(), instance=instance, action="post_clear"
        )
        handle_m2m_post_clear_action.assert_called_once_with(
            instance=instance, action_kwargs=action_kwargs,
        )

    @patch("server.apps.main.middleware.Consent")
    @patch("server.apps.main.middleware.action")
    def test_handle_m2m_post_add_remove_actions_with_post_add(self, action, Consent):
        middleware = AuditLogMiddleware(self.get_response)
        instance = Mock()

        middleware.handle_m2m_post_add_remove_actions(
            instance=instance,
            action_kwargs={},
            action_name="post_add",
            pk_set=[1, 2, 3],
        )

        kwargs = {
            "target": instance,
            "verb": "added",
        }

        action.send.assert_has_calls(
            [
                call(action_object=Consent.objects.get(pk=1), **kwargs),
                call(action_object=Consent.objects.get(pk=2), **kwargs),
                call(action_object=Consent.objects.get(pk=3), **kwargs),
            ]
        )

    @patch("server.apps.main.middleware.Consent")
    @patch("server.apps.main.middleware.action")
    def test_handle_m2m_post_add_remove_actions_with_post_remove(self, action, Consent):
        middleware = AuditLogMiddleware(self.get_response)
        instance = Mock()

        middleware.handle_m2m_post_add_remove_actions(
            instance=instance,
            action_kwargs={},
            action_name="post_remove",
            pk_set=[3, 4, 5],
        )

        kwargs = {
            "target": instance,
            "verb": "removed",
        }

        action.send.assert_has_calls(
            [
                call(action_object=Consent.objects.get(pk=3), **kwargs),
                call(action_object=Consent.objects.get(pk=4), **kwargs),
                call(action_object=Consent.objects.get(pk=5), **kwargs),
            ]
        )

    @patch("server.apps.main.middleware.action")
    def test_handle_m2m_post_clear_action(self, action):
        middleware = AuditLogMiddleware(self.get_response)
        instance = Mock()

        middleware.handle_m2m_post_clear_action(
            instance=instance, action_kwargs={},
        )

        action.send.assert_called_once_with(
            verb="cleared consents", action_object=instance
        )

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
