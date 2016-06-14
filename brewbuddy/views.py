import flask
import json
import os
import requests

from base64 import b64decode
from base64 import b64encode
from brewbuddy import app

_CLIENT_ID = os.environ['CLIENT_ID']
_CLIENT_SECRET = os.environ['CLIENT_SECRET']

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
        scopes = []
        features = []
        url = _BASE_URL + '/user'
        params = {
            'access_token': access_token,
        }
        response = _SESSION.get(url, params=params)
        if response.status_code not in list(range(200, 300)):
            flask.session['access_token'] = None
            return authenticate()
        if 'X-OAuth-Scopes' in response.headers:
            scopes = response.headers['X-OAuth-Scopes'].split(',')
        auth = response.json()
        if 'repo' in scopes:
            url = _BASE_URL + '/repos/%s/%s/contents/%s' % (
                auth['login'], _REPO, _FILENAME
            )
            response = _SESSION.get(url)
            if response.status_code == 403:
                message = response.json()['messsage']
                return flask.render_template('dashboard', message=message)
            content = b64decode(response.json()['content'])
            features = json.loads(content)['features']
        flask.session['auth'] = auth
        return flask.render_template('dashboard.html', auth=auth,
                                     features=features)


@app.route('/xhr', methods=['POST'])
def xhr():
    # By default, assume that this is NOT the initial commit.
    initial = False
    json_data = flask.request.json
    # Create the `feature` object. If the geojson file already exists,
    # then concatenate the `feature` object to the list of `features`.
    # Otherwise, create a new `FeatureCollection`.
    feature = {
        'type': 'Feature',
        'geometry': {
            'type': 'Point',
            'coordinates': [json_data['lng'], json_data['lat']],
        },
        'properties': {
            'title': json_data['title'],
            'marker-size': 'medium',
            'marker-symbol': 'beer',
        }
    }
    auth = flask.session['auth']
    url = _BASE_URL + '/repos/%s/%s/contents/%s' % (
        auth['login'], _REPO, _FILENAME
    )
    response = _SESSION.get(url)
    if response.status_code == 404:
        initial = True
        content = {
            'type': 'FeatureCollection',
            'features': [],
        }
    else:
        repo = response.json()
        content = json.loads(b64decode(repo['content']))
    titles = [obj['properties']['title']
              for obj in content['features']]
    if json_data['title'] not in titles:
        feature['properties']['description'] = 1
        content['features'].append(feature)
    else:
        # This brewery already exists, so update the counter.
        index = titles.index(json_data['title'])
        description = content['features'][index]['properties']['description']
        description += 1
        # Insert the `description` key with the updated value.
        feature['properties']['description'] = description
    content = json.dumps(content, indent=4)
    data = {
        'path': _FILENAME,
        'content': b64encode(content).strip(),
    }
    data['message'] = (
        'Initial commit' if initial else json_data['title']
    )
    if not initial:
        data['sha'] = repo['sha']
    data = json.dumps(data)
    access_token = flask.session['access_token']
    headers = {
        'Authorization': 'Token %s' % access_token,
    }
    response = _SESSION.put(url, data=data, headers=headers)
    if response.status_code not in list(range(200, 300)):
        return response.reason, response.status_code
    return flask.jsonify(feature)


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
