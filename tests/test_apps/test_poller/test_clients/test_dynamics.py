from unittest import mock

import pytest
import requests_mock
from requests import HTTPError

from server.apps.poller.api_client.dynamics import DynamicsClient


class TestDynamicsClient:
    @property
    def client(self):
        return DynamicsClient()

    @mock.patch.object(DynamicsClient, "_get_access_token", return_value="X")
    def test_get_unsubscribed_contacts(self, mock_value):
        mock_data = {
            "value": [
                {
                    "contact_id": 1,
                    "emailaddress1": "test1@digital.trade.gov.uk",
                },
                {
                    "contact_id": 2,
                    "emailaddress1": "test2@digital.trade.gov.uk",
                },
            ]
        }
        with requests_mock.Mocker() as rmock:
            contacts_mock = rmock.get(
                f"{self.client.contacts_url}?$filter=donotbulkemail%20eq%20true",
                json=mock_data,
            )
            records = list(self.client.get_unsubscribed_contacts())
        assert contacts_mock.called
        assert len(records) == 2
        assert records[0]["emailaddress1"] == mock_data["value"][0]["emailaddress1"]
        assert records[1]["emailaddress1"] == mock_data["value"][1]["emailaddress1"]

    @mock.patch.object(DynamicsClient, "_get_access_token", return_value="X")
    @mock.patch("server.apps.poller.api_client.dynamics.time")
    def test_too_many_requests(self, mock_time, mock_client):
        with requests_mock.Mocker() as rmock:
            contacts_mock = rmock.get(
                f"{self.client.contacts_url}?$filter=donotbulkemail%20eq%20true",
                status_code=429,
            )
            with pytest.raises(HTTPError):
                list(self.client.get_unsubscribed_contacts())
        assert contacts_mock.call_count == self.client.max_retry_attempts

    @mock.patch.object(DynamicsClient, "_get_access_token", return_value="X")
    def test_get_unmanaged_contacts(self, mock_value):
        mock_data = {
            "value": [
                {
                    "contact_id": 3,
                    "emailaddress1": "test3@digital.trade.gov.uk",
                },
                {
                    "contact_id": 4,
                    "emailaddress1": "test4@digital.trade.gov.uk",
                },
            ]
        }
        with requests_mock.Mocker() as rmock:
            contacts_mock = rmock.get(
                (
                    f"{self.client.contacts_url}?$filter="
                    "donotbulkemail eq false "
                    "and externaluseridentifier eq null "
                    "and Microsoft.Dynamics.CRM.LastXDays(PropertyName='createdon',PropertyValue=1)"
                ),
                json=mock_data,
            )
            records = list(self.client.get_unmanaged_contacts(created_since_days=1))
        assert contacts_mock.called
        assert len(records) == 2
        assert records[0]["emailaddress1"] == mock_data["value"][0]["emailaddress1"]
        assert records[1]["emailaddress1"] == mock_data["value"][1]["emailaddress1"]
