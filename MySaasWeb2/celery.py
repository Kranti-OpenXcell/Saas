# from __future__ import absolute_import, unicode_literals
# import os
# from celery import Celery

# # Set the default Django settings module for the 'celery' program.
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MySaasWeb2.settings')

# app = Celery('MySaasWeb2')    

# # Using a string here means the worker doesn't have to serialize
# # the configuration object to child processes.
# # Namespace 'CELERY' means all celery-related config keys should be prefixed with 'CELERY_'.
# app.config_from_object('django.conf:settings', namespace='CELERY')

# # Autodiscover tasks from all registered Django app configs.
# app.autodiscover_tasks()

# @app.task(bind=True)
# def debug_task(self):
#     print(f'Request: {self.request!r}')
