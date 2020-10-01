from unittest.mock import patch

from django.conf import settings

from server.apps.poller.api_client.maxemail import MaxEmail


class TestMaxemailClient:
    @property
    def client(self):
        return MaxEmail(settings.MAXEMAIL_USERNAME, settings.MAXEMAIL_PASSWORD)

    def test_all_lists(self, requests_mock):
        mock_data = [
            {
                "list_id": "1",
                "folder_id": "1",
                "name": "Master Unsubscribe List",
                "list_total": "2",
                "status": "available",
                "type": "suppression",
                "created_ts": "2009-02-13 11:18:05",
                "update_ts": "2020-03-06 17:29:57",
            }
        ]

        all_list_mock = requests_mock.post(
            (settings.MAXEMAIL_BASE_URL / "list").tostr(), json=mock_data
        )
        all_lists = self.client.all_lists()

        assert all_lists == mock_data
        assert all_list_mock.called_once
        assert "fetchAll" in all_list_mock.last_request.body

    @patch("server.apps.poller.api_client.maxemail.MaxEmail.all_lists")
    def test_get_unsubscribe_list(self, mocked_all_list):
        mocked_all_list.return_value = [
            {
                "list_id": "1",
                "name": "Master Unsubscribe List",
                "update_ts": "2020-03-06 17:29:57",
            }
        ]
        ret = self.client.get_unsubscribe_list()
        assert ret["list_id"] == "1"
        assert mocked_all_list.called

    @patch("server.apps.poller.api_client.maxemail.HTTPBasicAuth")
    def test_client_initialization(self, http_auth):
        _ = self.client
        http_auth.assert_called_with(
            settings.MAXEMAIL_USERNAME, settings.MAXEMAIL_PASSWORD
        )

    def test_get_members_for_list_generator_one_record(self, requests_mock):
        mock_data = {
            "list_total": "1",
            "count": 1,
            "offset": 0,
            "limit": 5000,
            "sort": "update_ts",
            "dir": "DESC",
            "records": [
                {
                    "record_type": "campaign",
                    "subscribed": "1",
                    "unsubscribe_method": "",
                    "update_ts": "2020-03-06 13:48:01",
                    "recipient_id": "6",
                    "email_address": "test@digital.trade.gov.uk",
                    "sms_number": None,
                    "sms_country_code": None,
                },
            ],
        }

        memebers_mock = requests_mock.post(
            (settings.MAXEMAIL_BASE_URL / "list").tostr(), json=mock_data
        )
        records = list(self.client.get_members_for_list(1))
        assert memebers_mock.called
        assert len(records) == 1
        assert records[0]["email_address"] == mock_data["records"][0]["email_address"]

    def test_get_members_for_list_generator_multiple_records(self, requests_mock):
        mock_data = {
            "list_total": "3",
            "count": 3,
            "records": [
                {
                    "email_address": "test1@digital.trade.gov.uk",
                },
                {
                    "email_address": "test2@digital.trade.gov.uk",
                },
                {
                    "email_address": "test3@digital.trade.gov.uk",
                },
            ],
        }

        memebers_mock = requests_mock.post(
            (settings.MAXEMAIL_BASE_URL / "list").tostr(), json=mock_data
        )
        records = list(self.client.get_members_for_list(1))
        assert memebers_mock.called
        assert len(records) == 3
        assert records[0]["email_address"] == mock_data["records"][0]["email_address"]
        assert records[1]["email_address"] == mock_data["records"][1]["email_address"]
        assert records[2]["email_address"] == mock_data["records"][2]["email_address"]

    def test_get_members_for_list_generator_paging(self, requests_mock):
        mock_data = {
            "list_total": "3",
            "count": 1,
            "records": [
                {
                    "email_address": "test1@digital.trade.gov.uk",
                },
            ],
        }

        memebers_mock = requests_mock.post(
            (settings.MAXEMAIL_BASE_URL / "list").tostr(), json=mock_data
        )
        records = list(self.client.get_members_for_list(1, limit=1))
        assert memebers_mock.called
        assert len(records) == 3
