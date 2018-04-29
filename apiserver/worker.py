"""Celery module for async tasks"""
import os
from celery import Celery

CELERY = Celery('tasks', broker=os.environ.get('BROKER_URL', 'pyamqp://guest@rabbit//'))
