from celery import shared_task
from celery.utils.log import get_task_logger
from django.core.management import call_command # NEW


logger = get_task_logger(__name__)


@shared_task(expires=15)
def sample_task():
    print("sample task")
    logger.info("The sample task just ran.")
    with open('temp.txt', 'w') as f:
        f.write('30 sec schedule')