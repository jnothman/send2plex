"""Send2Plex API Server: Provides a RESTful API for persisting requests for the Send2Plex service"""
import datetime
import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy import exc, dialects
from worker import CELERY
from retrying import retry

APP = Flask(__name__)
APP.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_URL')
APP.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
DB = SQLAlchemy(APP)
MA = Marshmallow(APP)


class Request(DB.Model):  # pylint: disable=too-few-public-methods
    """Declaritive base for table Request"""
    id = DB.Column(DB.Integer(), primary_key=True)
    created_ts = DB.Column(DB.DateTime(), nullable=False,
                           default=datetime.datetime.now())
    updated_ts = DB.Column(DB.DateTime(), nullable=False,
                           default=datetime.datetime.now())
    title = DB.Column(DB.String())
    uploader = DB.Column(DB.String())
    description = DB.Column(DB.String())
    file_size_bytes = DB.Column(DB.BigInteger())
    duration = DB.Column(DB.Integer())
    url = DB.Column(DB.String(), nullable=False)
    file_path = DB.Column(DB.String())
    download_ts = DB.Column(DB.DateTime())
    celery_id = DB.Column(DB.String())
    downloaded = DB.Column(DB.Boolean(), default=False)
    other_metadata = DB.Column(dialects.postgresql.JSONB())

    def __repr__(self):
        return '<Request {}>'.format(self.id)


class RequestSchema(MA.ModelSchema):
    """Model schema for SQLAlchemy class Request"""
    class Meta:  # pylint: disable=W0232,C1001
        """Marshmallow meta class for schema generation"""
        model = Request


@retry(wait_exponential_multiplier=1000, wait_exponential_max=10000)
def create_all(database):
    try:
        database.create_all()
    except exc.OperationalError as error:
        print "DB not ready, waiting before retry..."
        raise error


create_all(DB)


@APP.route('/')
def index():
    """Sample index path"""
    return """
    <h1>You are at the index! This was a {} method!</h1>
    """.format(request.method)


REQUESTS_SCHEMA = RequestSchema(many=True)
REQUEST_SCHEMA = RequestSchema()


@APP.route('/requests', methods=['GET', 'POST'])
def requests():
    """Method that handles persisting and serving requests"""
    if request.method == 'GET':
        all_requests = Request.query.order_by(Request.created_ts.desc()).all()
        all_requests_serialized = REQUESTS_SCHEMA.dump(all_requests)
        return jsonify({'requests': all_requests_serialized.data})
    elif request.method == 'POST':
        req = request.get_json()
        new_request = Request(url=req.get('url'))
        try:
            DB.session.add(new_request)
            DB.session.commit()
        except exc.SQLAlchemyError as error:
            response = {
                'success': False,
                'message': 'Unable to commit to database',
                'error': error.message
            }
            return jsonify(response)
        request_dict = REQUEST_SCHEMA.dump(new_request).data
        CELERY.send_task('tasks.download', args=[request_dict])
        return jsonify({'success': True})


if __name__ == '__main__':
    APP.run(host='0.0.0.0')
