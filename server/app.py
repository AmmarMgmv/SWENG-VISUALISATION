
from flask import Flask, request, redirect, render_template, jsonify
from flask import session as current_session
import requests
import flask
from library import username as usernameAPI
from library import individualMap as mapAPI
from flask_cors import CORS
import json
import os

app = Flask(__name__)
env_config = os.getenv("APP_SETTINGS", "config.DevelopmentConfig")
app.config.from_object(env_config)
CORS(app)

client_id = app.config.get("CLIENT_ID")
client_secret = app.config.get("CLIENT_SECRET")

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/results', methods=["GET"])
def results_page():
    if request.method == 'GET':
        repos_url = 'https://api.github.com/user/repos';
        access_token_url = 'https://api.github.com/user'
        #User is searching for another user
        if 'username' in request.args:
            username = request.args['username']
            access_token_url = f'https://api.github.com/users/{username}'
            repos_url = f'https://api.github.com/users/{username}/repos'
        #User is not logged in
        elif 'access_token' not in current_session:
            return redirect('/login')

        #User is logged in
        # Get logged in user information from github api
        userData = requests.get(access_token_url, auth=('access_token', current_session['access_token']))
        userData = userData.json()

        #Get logged in user repos
        user_repos = requests.get(repos_url, auth=('access_token', current_session['access_token']))
        user_repos = user_repos.json()
        language_dict = {}
        for repo in user_repos:
            if repo['language']:
                if repo['language'] not in language_dict:
                    language_dict[repo['language']] = 1
                else:
                    language_dict[repo['language']] = language_dict[repo['language']] + 1

        #Get user location coords
        map_data = mapAPI.getLatLng(userData['location'])
        print(map_data)

        try:
            return render_template("results2.html", userData=userData, user_repos=user_repos, language_dict=language_dict, map_data=map_data)
        except AttributeError:
            app.logger.debug('error getting username from github, whoops')
            return "I don't know who you are; I should, but regretfully I don't", 500


@app.route('/map')
def map_page():
    return render_template("map.html")

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/handlegithublogin')
def handle_github_login():
    fetch_url = 'https://github.com/login/oauth/authorize' + \
                '?client_id=' + client_id + \
                '&scope=user%20repo%20public_repo' + \
                '&allow_signup=true'
    #print fetch_url
    return redirect(fetch_url)

@app.route('/github-callback', methods=['GET', 'POST'])
def handle_github_callback():
    if 'code' in request.args:
        params = {
            'client_id': client_id,
            'client_secret': client_secret,
            'code': request.args['code']
        }
        headers = {'Accept': 'application/json'}
        req = requests.post('https://github.com/login/oauth/access_token', params=params, headers=headers)
        resp = req.json()

        if 'access_token' in resp:
            current_session['access_token'] = resp['access_token']
            return redirect("/results")
        else:
            return jsonify(error="Error retrieving access_token"), 404
    else:
        return jsonify(error="404_no_code"), 404

@app.route('/username', methods=["GET", "POST"])
def users():
    print("users endpoint reached...")
    if request.method == "GET":
        with open("server/OmaidQ.json", "r") as f:
            data = json.load(f)
            return flask.jsonify(data)
    if request.method == "POST":
        received_data = request.get_json()
        print(f"received data: {received_data}")
        username = received_data['data']
        data = usernameAPI.re_to_json(username)
        print("---------------------")
        coords = mapAPI.getLatLng(data.get("location"))
        data = mapAPI.mergeDictionary(data, coords)
        print(data)
        return flask.Response(response=json.dumps(data), status=201)

@app.route('/react', methods=["GET"])
def react():
    try:
        url = "https://api.github.com/repos/facebook/react/contributors?per_page=100"
        response =  requests.get(url)
        print(json.loads(response.text))
        return json.loads(response.text)

    except:
        print("Error")
        return '{}'

if __name__ == "__main__":
    app.secret_key = "super_duper_secret_key"
    app.run(debug=True)


#maps api key - AIzaSyCaN_NjULWKTMBVQYhQMCHoUIcJvg3fQUk