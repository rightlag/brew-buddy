import flask
import json
import os
import requests

from base64 import b64decode, b64encode
from collections import namedtuple
from functools import wraps
from brewbuddy import app

_CLIENT_ID = os.environ['CLIENT_ID']
_CLIENT_SECRET = os.environ['CLIENT_SECRET']

_SESSION = requests.Session()
_SESSION.headers.update({'Accept': 'application/json'})

_BASE_URL = 'https://api.github.com'


def get_default_repo():
    """Return a `namedtuple` with the default repo information."""
    Contents = namedtuple('Contents', ['path'])
    Repo = namedtuple('Repo', ['name', 'url', 'contents'])
    contents = Contents('breweries.geojson')
    repo = Repo('brew-buddy', 'https://github.com/brew-buddy/brew-buddy',
                contents)
    return repo

_REPO = get_default_repo()


def login_required(fn):
    """Decorator to ensure user is authenticated before making requests.
    """
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if ('access_token' not in flask.session or
                flask.session['access_token'] is None):
            return authenticate()
        return fn(*args, **kwargs)
    return wrapped


def authenticate():
    return flask.render_template('index.html')


@app.route('/tests')
def tests():
    """All client-side related tests."""
    return flask.render_template('tests.html')


@app.route('/login')
def login():
    """HTTP redirect for OAuth authorization."""
    scopes = ['repo']
    url = 'https://github.com/login/oauth/authorize?scope=%s&client_id=%s' % (
        ' '.join(scope for scope in scopes),
        _CLIENT_ID
    )
    response = requests.get(url)
    return flask.redirect(response.url)


def get_features():
    """Get a list of features from the repository."""
    features = []
    repo_url = None
    user = flask.session['user']
    url = _BASE_URL + '/repos/%s/%s/contents/%s' % (
        user['login'], _REPO.name, _REPO.contents.path
    )
    response = _SESSION.get(url)
    if response.status_code in [403, 404]:
        message = response.json()['message']
        flask.session['errors'].update({response.status_code: message})
    else:
        repo_url = 'https://github.com/%s/%s' % (user['login'], _REPO.name)
        content = (
            b64decode(response.json()['content']).strip().decode('utf-8')
        )
        features = json.loads(content)['features']
    flask.session['repo_url'] = repo_url
    return features


@app.route('/')
@login_required
def hello():
    scopes = []
    features = []
    flask.session['errors'] = {}
    url = _BASE_URL + '/user'
    response = _SESSION.get(url)
    if response.status_code not in list(range(200, 300)):
        flask.session['access_token'] = None
        return authenticate()
    user = response.json()
    flask.session['user'] = user
    if 'X-OAuth-Scopes' in response.headers:
        scopes = response.headers['X-OAuth-Scopes'].split(',')
    if 'repo' in scopes:
        features = get_features()
    return flask.render_template('dashboard.html', user=user,
                                 features=features)


@app.route('/persist', methods=['POST'])
@login_required
def persist(dry_run=False):
    flask.session['errors'] = (
        {int(k): v for k, v in list(flask.session['errors'].items())}
    )
    if 404 in flask.session['errors']:
        # User still has not forked the repository, throw an error.
        return flask.jsonify(flask.session['errors'][404]), 404
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
    user = flask.session['user']
    url = _BASE_URL + '/repos/%s/%s/contents/%s' % (
        user['login'], _REPO.name, _REPO.contents.path
    )
    response = _SESSION.get(url)
    repo = response.json()
    content = b64decode(repo['content']).strip().decode('utf-8')
    content = json.loads(content)
    titles = [obj['properties']['title']
              for obj in content['features']]
    if json_data['title'] not in titles:
        feature['properties']['description'] = 1
        content['features'].append(feature)
    else:
        # This brewery already exists, so update the counter.
        index = titles.index(json_data['title'])
        content['features'][index]['properties']['description'] += 1
        description = content['features'][index]['properties']['description']
        # Insert the `description` key with the updated value.
        feature['properties']['description'] = description
    content = json.dumps(content, indent=4)
    data = {
        'path': _REPO.contents.path,
        'message': json_data['title'],
        'content': b64encode(content.encode('utf-8')).strip().decode('utf-8'),
        'sha': repo['sha'],
    }
    # Ensure newline at EOF.
    data['content'] += '\n'
    data = json.dumps(data)
    if not dry_run:
        response = _SESSION.put(url, data=data)
        if response.status_code not in list(range(200, 300)):
            return flask.jsonify(response.json())
    return flask.jsonify(feature)


@app.route('/callback')
def callback():
    url = 'https://github.com/login/oauth/access_token'
    code = flask.request.args['code']
    data = {
        'client_id': _CLIENT_ID,
        'client_secret': _CLIENT_SECRET,
        'code': code,
    }
    response = _SESSION.post(url, data=data)
    access_token = response.json()['access_token']
    flask.session['access_token'] = access_token
    _SESSION.headers.update({'Authorization': 'Token %s' % access_token})
    return flask.redirect('/')

app.secret_key = os.urandom(24)
