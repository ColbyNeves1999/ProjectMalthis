from celery import Celery

# Celery configuration for the worker.
# Provided by Celery Documentation: https://docs.celeryq.dev/en/stable/getting-started/first-steps-with-celery.html#configuring-celery
celery_app = Celery(
    'worker',
    broker='redis://redis:6379/0',
    backend='redis://redis:6379/0'
)

@celery_app.task
def test_task(x, y):
    return x + y