# -*- coding: utf-8 -*-
"""
    raspberrypi-modio-web
    ~~~~~~~~~~~~~~~~~~~~~

    A simple Python webapp to control something via Olimex's MOD-IO2

    :copyright: (c) 2013 by Christian Jann.
    :license: AGPL, see LICENSE for more details.
"""

import os
import time
import subprocess
from flask import Blueprint, Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash, Markup, escape, send_from_directory, current_app
from settings import settings
from wateringsystem import WateringSystem

from models import SensorReadings, db


hardware = Blueprint('hardware', __name__)

_WS = None
def get_ws():
    global _WS
    if _WS is None:
        _WS = g._watering_system = WateringSystem(settings["wateringsystem"])
    return _WS

@hardware.route('/enable/<ws_obj>')
def enable(ws_obj):
    """Enable the watering object"""
    if not session.get('logged_in'):
        flash('You need to log in!', 'error')
        return redirect(url_for('.control'))
    current_app.logger.warning("state: %s", get_ws()._state)
    current_app.logger.warning("Enable: %s", ws_obj)
    if get_ws()._state.get(ws_obj):
        if get_ws()._state.get(ws_obj)['state'] == "enable":
            flash('Object "{0}" is already enabled!'.format(ws_obj), 'error')
            return redirect(url_for('.control'))
    try:
        get_ws().enable(ws_obj)
        flash("Enabled '{0}'".format(ws_obj))
        sr = SensorReadings(source=ws_obj, value=1)
        db.session.add(sr)
        db.session.commit()
    except RuntimeError as e:
        msg = 'Watering system: object "{0}" is not available or not changeable ({1})'
        flash(msg.format(ws_obj, e))
        current_app.logger.warning(msg, ws_obj, e)
    return redirect(url_for('.control'))

    
@hardware.route('/disable/<ws_obj>')
def disable(ws_obj):
    """Enable the watering object"""
    if not session.get('logged_in'):
        flash('You need to log in!', 'error')
        return redirect(url_for('.control'))
    last_changed = None
    current_app.logger.warning("state: %s", get_ws()._state)
    current_app.logger.warning("Disable: %s" , ws_obj)
    if get_ws()._state.get(ws_obj):
        if get_ws()._state.get(ws_obj)['state'] == "disable":
            flash('Object "{0}" is not enabled!'.format(ws_obj), 'error')
            return redirect(url_for('.control'))
        last_changed = get_ws()._state.get(ws_obj)['last_changed']
        current_app.logger.warning("%s last changed: %s", ws_obj, last_changed)
    try:
        get_ws().disable(ws_obj)
        flash("Disabled '{0}'".format(ws_obj))
        sr = SensorReadings(source=ws_obj, value=0)
        db.session.add(sr)
        if last_changed:
            now_changed = get_ws()._state.get(ws_obj)['last_changed']
            secs = (now_changed - last_changed).seconds
            sr = SensorReadings(source=ws_obj+'_runtime', value=secs)
            flash("Running time for '{0}': {1}secs".format(ws_obj, secs))
            db.session.add(sr)
        db.session.commit()
    except RuntimeError as e:
        msg = 'Watering system: object "{0}" is not available or not changeable ({1})'
        flash(msg.format(ws_obj, e))
        current_app.logger.warning(msg, ws_obj, e)
    return redirect(url_for('.control'))  
    
@hardware.route('/')
def control():
    return render_template('control.j2', ws=get_ws())

@hardware.route('/webcam')
def webcam():
    img = os.path.join(hardware.root_path, '../data', 'webcam.jpg')
    dt = time.ctime(os.path.getmtime(img))
    return render_template('webcam.j2', last_updated=dt)


@hardware.route('/webcam.jpeg')
def camimage():
    print('Acquiring image file....')
    # this may wear out your SD card because
    # each time the page gets reloaded
    # a new image will be stored on your SD card
    if request.args.get("reload",None):
        try:
            subprocess.call(['fswebcam', '-r', '960 x 720', '-d', '/dev/video0', '--no-banner',
                        os.path.join(hardware.root_path, '../data/webcam.jpg')])
        except OSError as e:
            app.logger.error("ERR: fswebcam not found, please install fswebcam (%s)", e)
    return send_from_directory(os.path.join(hardware.root_path, '../data'),
                               'webcam.jpg', mimetype='image/jpeg')
