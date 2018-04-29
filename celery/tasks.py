"""Celery module for async tasks"""
import os
from celery import Celery
import downloader

APP = Celery('tasks', broker=os.environ.get('BROKER_URL', 'pyamqp://guest@rabbit//'))


@APP.task(bind=True, name='tasks.download')
def download_video(self, video_info):
    """Task for downloading the requested video and updating the request in the DB"""
    video_info['celery_id'] = self.request.id
    downloader.download_video(video_info)
