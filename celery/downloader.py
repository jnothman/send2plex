"""Module for downloading videos and updating requests"""
from __future__ import unicode_literals
import datetime
import os
import json
import psycopg2
import youtube_dl

FILE_SIZES = []
FILE_NAMES = []


def get_db_connection():
    """Get DB connection"""
    return psycopg2.connect(os.environ.get('DB_URL'))


def progress_hook(progress):
    """Called on youtube_dl progress hook"""
    if progress.get('status') == 'finished':
        FILE_SIZES.append(progress.get('total_bytes', 0))
        FILE_NAMES.append(progress.get('filename'))


def update_db_metadata(request_data, metadata):
    """Updates request in database with video metadata"""
    conn = get_db_connection()
    cur = conn.cursor()
    update_statement = """
        UPDATE request 
        SET (
                updated_ts, 
                title, 
                uploader, 
                description, 
                duration, 
                celery_id, 
                other_metadata
            ) = (%s, %s, %s, %s, %s, %s, %s)
        WHERE id = %s
    """
    cur.execute(update_statement, (
        datetime.datetime.now(),
        metadata.get('title'),
        metadata.get('uploader'),
        metadata.get('description'),
        metadata.get('duration'),
        request_data.get('celery_id'),
        json.dumps(metadata),
        request_data.get('id')
    ))
    conn.commit()
    cur.close()
    conn.close()


def mark_db_as_downloaded(request_data):
    """Marks request as completed"""
    conn = get_db_connection()
    cur = conn.cursor()
    name = FILE_NAMES[0]
    update_statement = """
        UPDATE request 
        SET (
                file_size_bytes,
                file_path,
                download_ts,
                downloaded
            ) = (%s, %s, %s, %s)
        WHERE id = %s
    """
    cur.execute(update_statement, (
        sum(FILE_SIZES),
        name[:name[:name.rfind('.')].rfind('.')] + name[name.rfind('.'):],
        datetime.datetime.now(),
        True,
        request_data.get('id')
    ))
    conn.commit()
    del FILE_NAMES[:]
    del FILE_SIZES[:]
    cur.close()
    conn.close()


def download_video(request_data, persist_to_db=True):
    """Core function for downloading requested videos"""
    ydl_opts = {
        'format': 'bestvideo[height>720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height=720][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
        'progress_hooks': [progress_hook],
        'outtmpl': '{}/%(uploader)s/%(title)s.%(ext)s'.format(os.environ.get('DL_DIR'))
    }
    with youtube_dl.YoutubeDL(ydl_opts) as client:
        if persist_to_db: 
            metadata = client.extract_info(
                url=request_data.get('url'), download=False)
            update_db_metadata(request_data, metadata)
        client.download([request_data.get('url')])
        if persist_to_db: 
            mark_db_as_downloaded(request_data)


if __name__ == '__main__':
    download_video({'url': 'https://www.youtube.com/watch?v=u9Mv98Gr5pY'}, False)
