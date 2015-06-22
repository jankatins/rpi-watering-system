# -*- coding: utf-8 -*-
"""
    raspberrypi-modio-web
    ~~~~~~~~~~~~~~~~~~~~~

    A simple Python webapp to control something via Olimex's MOD-IO2

    :copyright: (c) 2013 by Christian Jann.
    :license: AGPL, see LICENSE for more details.
"""

import datetime
import os
import shutil
from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash, Markup, escape, send_from_directory, jsonify
from werkzeug import check_password_hash
from settings import settings
from users import add_user, get_user
from hardware import hardware

from models import SensorReadings, db

# configuration
SECRET_KEY = 'development key'

# Create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_pyfile('application.cfg', silent=True)


# init folder structure
if not os.path.exists(settings['datadir']):
    shutil.copytree("app/default", settings['datadir'])

# add your modules
app.register_blueprint(hardware, url_prefix='/control')


@app.context_processor
def inject_year():
    # {{ year }} is now available in templates
    now = datetime.datetime.utcnow()
    return dict(year=now.strftime("%Y"))


@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = get_user('user_id', session['user_id'])

#@app.teardown_request
# def teardown_request(exception):
#    print("end of request")

# Catch-All URL
#@app.route('/', defaults={'path': ''})


@app.route('/<path:path>')
def catch_all(path):
    # flash('Error: path: %s is not avaible' % path,'error')
    return redirect(url_for('show_start_page'))


@app.route('/')
def show_start_page():
    return render_template('start.j2')


@app.route('/about')
def show_about_page():
    return render_template('about.j2')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static/img'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Logs the user in."""
    if g.user:
        return redirect(url_for('hardware.control'))
    error = None
    if request.method == 'POST':
        user = get_user('username', request.form['username'])
        if user is None:
            error = 'Invalid username'
        elif not check_password_hash(user['password_hash'],
                                     request.form['password']):
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            session['user_id'] = user['user_id']
            return redirect(url_for('hardware.control'))
    return render_template('login.j2', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('user_id', None)
    flash('You were logged out', 'success')
    return redirect(url_for('show_start_page'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registers the user."""
    if not session.get('logged_in'):
        flash('You need to log in to register new Users!', 'error')
        return redirect(url_for('.login'))
    error = None
    if request.method == 'POST':
        if not request.form['username']:
            error = 'You have to enter a username'
        elif not request.form['email'] or \
                '@' not in request.form['email']:
            error = 'You have to enter a valid email address'
        elif not request.form['password']:
            error = 'You have to enter a password'
        elif request.form['password'] != request.form['password2']:
            error = 'The two passwords do not match'
        elif get_user('username', request.form['username']) is not None:
            error = 'The username is already taken'
        else:
            add_user(request.form['username'], request.form[
                     'password'], request.form['email'])
            flash(
                'You were successfully registered and can login now', 'success')
            return redirect(url_for('login'))
    return render_template('register.j2', error=error)



@app.route('/charts')
def show_charts_page():
    return render_template('charts.j2')


#get sensor readings is used via an ajax call with d3.js, to render the graph
@app.route('/sensor_readings.json', methods=['GET'])
def get_sensor_readings():
    import datetime
    import json
    
    try:
       days = request.args.get("days",3)
       days = int(days)
    except Exception as e:
       app.logger.warning('sensor_readings.json called with wrong parameter: days=%s (%s)', days, e)
       days = 3
    current_time = datetime.datetime.utcnow()
    time_ago = current_time - datetime.timedelta(days=days)
    results = {}
    for s in ["tomatos", "front"]:
        sr = SensorReadings.query.filter(
                          SensorReadings.creation_date > time_ago,
                          SensorReadings.source == s).all()
        results[s] = [i.serialize for i in sr]
    water = SensorReadings.query.filter(
                          SensorReadings.creation_date > time_ago,
                          SensorReadings.source == "pump_runtime").all()
    results["water"] = [i.serialize for i in water]
    return jsonify(data=results)

