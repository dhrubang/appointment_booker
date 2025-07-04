from celery import Celery

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend='redis://localhost:6379/0',
        broker='redis://localhost:6379/0'
    )
    celery.conf.update(app.config)
    celery.conf.update(
        broker_connection_retry_on_startup=True  # Suppresses Celery 6.0 warning
    )
    return celery