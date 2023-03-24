import logging

from django.core.management import call_command
from django.db import transaction
from django_tqdm import BaseCommand

from server.apps.main.models import Commit
from server.apps.poller.models import ActivityStreamType


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = """
    Rerun the poll_formsapi poller from the beginning of time, deleting
    any previously ingested Commit and LegalBasis instances first

    e.g. ./manage.py poll_formsapi_rerun
    """

    def handle(self, *args, **options) -> None:

        with transaction.atomic():
            logger.info('Deleting all Commits created by the Forms API poller')
            for commit in Commit.objects.filter(
                extra__id__startswith="dit:directoryFormsApi:Submission:"
            ):
                logger.info('Deleting commit %s', commit)
                commit.legalbasis_set.all().delete()
                commit.delete()

            logger.info('Resetting the Forms API poller to the beginning')
            activity_stream_obj, _ = ActivityStreamType.objects.get_or_create(name='dit:directoryFormsApi:Submission')
            activity_stream_obj.last_document_timestamp = None
            activity_stream_obj.last_document_id = ''
            activity_stream_obj.save(update_fields=['last_document_timestamp', 'last_document_id'])

            logger.info('Running the Forms API poller')
            call_command('poll_formsapi')
