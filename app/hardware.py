# -*- coding: utf-8 -*-
"""
    raspberrypi-modio-web
    ~~~~~~~~~~~~~~~~~~~~~

    A simple Python webapp to control something via Olimex's MOD-IO2

    :copyright: (c) 2013 by Christian Jann.
    :license: AGPL, see LICENSE for more details.
"""

import os
import subprocess
from flask import Blueprint, Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash, Markup, escape, send_from_directory
from settings import settings
from wateringsystem import WateringSystem


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
    try:
        get_ws().enable(ws_obj)
        flash("Enabled '{0}'".format(ws_obj))
    except RuntimeError as e:
        msg = 'Watering system: object "{0}" is not available or not changeable ({1})'
        flash(msg.format(ws_obj, e))
        hardware.logger.warning(msg, ws_obj, e)
    return redirect(url_for('.control'))

    
@hardware.route('/disable/<ws_obj>')
def disable(ws_obj):
    """Enable the watering object"""
    if not session.get('logged_in'):
        flash('You need to log in!', 'error')
        return redirect(url_for('.control'))
    try:
        get_ws().disable(ws_obj)
        flash("Disabled '{0}'".format(ws_obj))
    except RuntimeError as e:
        msg = 'Watering system: object "{0}" is not available or not changeable ({1})'
        flash(msg.format(ws_obj, e))
        hardware.logger.warning(msg, ws_obj, e)
    return redirect(url_for('.control'))  
    
@hardware.route('/')
def control():
    return render_template('control.j2', ws=get_ws())

@hardware.route('/webcam')
def webcam():
    return render_template('webcam.j2')


@hardware.route('/webcam.jpeg')
def camimage():
    print('Acquiring image file....')
    # this may wear out your SD card because
    # each time the page gets reloaded
    # a new image will be stored on your SD card
    try:
        subprocess.call(['fswebcam', '-r', '640x480', '-d', '/dev/video0',
                        '--title=Raspberry Pi Webcam', '--subtitle=www.jann.cc',
                        os.path.join(hardware.root_path, '../data/webcam.jpg')])
    except OSError:
        print("ERR: fswebcam not found, please install fswebcam")
    return send_from_directory(os.path.join(hardware.root_path, '../data'),
                               'webcam.jpg', mimetype='image/jpeg')
