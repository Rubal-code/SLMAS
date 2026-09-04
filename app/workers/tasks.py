from app.workers.celery_app import celery_app


@celery_app.task(name="slmas.ping")
def ping():
    return {"status": "ok", "service": "slmas"}
