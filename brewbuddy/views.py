import flask
import json
import os
import requests

from base64 import b64decode
from base64 import b64encode
from brewbuddy import app

_CLIENT_ID = os.environ.get('CLIENT_ID')
_CLIENT_SECRET = os.environ.get('CLIENT_SECRET')

_SESSION = requests.Session()
_SESSION.headers.update({'Accept': 'application/json'})

_BASE_URL = 'https://api.github.com'
_REPO = 'brew-buddy'
_FILENAME = 'breweries.geojson'


def authenticate():
    return flask.render_template('index.html', client_id=_CLIENT_ID)


@app.route('/')
def hello():
    if 'access_token' not in flask.session:
        return authenticate()
    else:
        access_token = flask.session['access_token']
        url = _BASE_URL + '/user'
        params = {
            'access_token': access_token,
        }
        auth_result = _SESSION.get(url, params=params)
        if auth_result.status_code not in list(range(200, 300)):
            flask.session['access_token'] = None
            return authenticate()
        auth_result = auth_result.json()
        flask.session['auth'] = auth_result
        return flask.render_template('index.html', auth_result=auth_result)


@app.route('/xhr', methods=['POST'])
def xhr():
    initial = False
    auth = flask.session['auth']
    url = (
        _BASE_URL + '/repos/{}/{}/contents/{}'
    ).format(auth['login'], _REPO, _FILENAME)
    data = flask.request.json
    feature = {
        'type': 'Feature',
        'geometry': {
            'type': 'Point',
            'coordinates': [data['lng'], data['lat']],
        },
        'properties': {
            'title': data['name'],
            'marker-size': 'medium',
            'marker-symbol': 'beer',
        }
    }
    res = _SESSION.get(url)
    if res.status_code == 404:
        initial = True
        content = {
            'type': 'FeatureCollection',
            'features': []
        }
    else:
        repo = res.json()
        content = json.loads(b64decode(repo['content']))
    content['features'].append(feature)
    content = json.dumps(content, indent=4)
    data = {
        'path': _FILENAME,
        'content': b64encode(content).strip(),
    }
    data['message'] = (
        'Initial commit' if initial else 'Added some more breweries!'
    )
    if not initial:
        data['sha'] = repo['sha']
    data = json.dumps(data)
    access_token = flask.session['access_token']
    headers = {
        'Authorization': 'Token {}'.format(access_token),
    }
    res = _SESSION.put(url, data=data, headers=headers)
    if res.status_code not in list(range(200, 300)):
        return res.reason, res.status_code
    return '', res.status_code


@app.route('/callback')
def callback():
    url = 'https://github.com/login/oauth/access_token'
    session_code = flask.request.args['code']
    data = {
        'client_id': _CLIENT_ID,
        'client_secret': _CLIENT_SECRET,
        'code': str(session_code),
    }
    response = _SESSION.post(url, data=data)
    flask.session['access_token'] = response.json()['access_token']
    return flask.redirect('/')

app.secret_key = os.urandom(24)
