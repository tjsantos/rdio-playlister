from flask import Flask, url_for, render_template, jsonify, session, request
from flask_oauthlib.client import OAuth
from flask_sslify import SSLify
import os

app = Flask(__name__)
sslify = SSLify(app)
oauth = OAuth(app)
app.debug = bool(os.environ.get('WEB_DEBUG'))
app.secret_key = os.environ['FLASK_SECRET_KEY']

rdio = oauth.remote_app(
    'rdio',
    consumer_key=os.environ.get('RDIO_ID'),
    consumer_secret=os.environ.get('RDIO_SECRET'),
    base_url='https://services.rdio.com/api/1/',
    authorize_url='https://www.rdio.com/oauth2/authorize',
    access_token_url='https://services.rdio.com/oauth2/token'
)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login')
def login():
    return rdio.authorize(callback=url_for('oauth', _external=True))


@app.route('/oauth')
def oauth():
    response = rdio.authorized_response()
    if response is None:
        return 'Access denied: reason={} error={}'.format(
            request.args['error'],
            request.args['error_description']
        )
    session['rdio_token'] = (response['access_token'], '')
    return jsonify(response)


@app.route('/info')
def info():
    post_data = {'method': 'currentUser'}
    response = rdio.request('', method='POST', data=post_data)
    if response.status != 200:
        return 'response status {}'.format(response.status)

    return jsonify(response.data)

@rdio.tokengetter
def get_rdio_oauth_token():
    return session.get('rdio_token')


if __name__ == '__main__':
    app.run()
