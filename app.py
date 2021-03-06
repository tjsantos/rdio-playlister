import os

from flask import Flask, url_for, render_template, jsonify, session, request, \
    redirect, flash
from flask_oauthlib.client import OAuth
from flask_sslify import SSLify
from flask_wtf import Form
from wtforms import SubmitField, IntegerField, validators

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


class PlaylistForm(Form):
    submit = SubmitField('Create Playlist')
    track_count = IntegerField('Number of tracks to add',
                               [validators.NumberRange(min=1, max=50)])


@app.route('/', methods=['GET', 'POST'])
def index():
    form = PlaylistForm()
    if form.validate_on_submit():
        # create the playlist

        # get current user station
        response = rdio.post('',
            data={'method': 'currentUser',
                  'extras': '-*,tasteProfileKey'}
        )
        if response.status != 200 or response.data['status'] != 'ok':
            flash('status: {}, data: {}'.format(response.status, response.data))
            return redirect(url_for('index'))

        station_key = response.data['result']['tasteProfileKey']

        # generate tracks from station
        response = rdio.post('',
            data={'method': 'generateStation',
                  'station_key': station_key,
                  'count': form.track_count.data}
        )
        tracks = response.data['result']['tracks']
        track_keys = [track['key'] for track in tracks]
        station_name = response.data['result']['name']

        # create playlist from generated tracks
        response = rdio.post('', data={
            'method': 'createPlaylist',
            'name': station_name,
            'description': 'autogenerated from station: {}'.format(station_name),
            'tracks': track_keys
        })
        print(response.data)

        flash('playlist created')
        return redirect(url_for('index'))

    return render_template('index.html', form=form)


@app.route('/login')
def login():
    return rdio.authorize(callback=url_for('oauth', _external=True))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/oauth')
def oauth():
    response = rdio.authorized_response()
    if response is None:
        return 'Access denied: reason={} error={}'.format(
            request.args['error'],
            request.args['error_description']
        )
    session['rdio_token'] = (response['access_token'], '')
    flash('login successful')
    return redirect(url_for('index'))


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
