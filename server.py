#!/usr/bin/env python3

# Copyright (C) 2015 Oleander Reis <oleander@oleander.cc>
# 
# This software is provided 'as-is', without any express or implied
# warranty.  In no event will the authors be held liable for any damages
# arising from the use of this software.
# 
# Permission is granted to anyone to use this software for any purpose,
# including commercial applications, and to alter it and redistribute it
# freely, subject to the following restrictions:
# 
# 1. The origin of this software must not be misrepresented; you must not
#    claim that you wrote the original software. If you use this software
#    in a product, an acknowledgment in the product documentation would be
#    appreciated but is not required.
# 2. Altered source versions must be plainly marked as such, and must not be
#    misrepresented as being the original software.
# 3. This notice may not be removed or altered from any source distribution.

import os
import re
import subprocess
import json
import uuid
import requests
import base64
from bottle import route, post, run, abort, request
from requests.compat import urljoin
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA
from Crypto.Signature import PKCS1_v1_5

HOSTNAME_REGEX = re.compile(r'35\d{3}-[\w-]{1,}', re.IGNORECASE)  # 35xxx-xxxxx_Xxxxx
TRAVIS_API_HOST = 'https://api.travis-ci.org'

def validate_hostname(hostname):
    return bool(HOSTNAME_REGEX.match(hostname))

def validate_key_format(key):
    try:
        b = bytes.fromhex(key)
    except ValueError:
        return False
    if len(b) != 32:
        return False
    return True

def git(command):
    if subprocess.check_call(['git', '-C', os.environ['FASTD_PEERS_DIR']] + command):
        abort(500, 'Error: {command} failed'.format(
                command=' '.join(command)
            )
        )

def find_key(key):
    git(['checkout', 'master'])
    git(['pull'])

    for peer in os.listdir(os.environ['FASTD_PEERS_DIR']):
        if os.path.isdir(peer):
            continue
        for line in open(os.path.join(os.environ['FASTD_PEERS_DIR'], peer), 'r'):
            if key in line:
                yield peer

    git(['checkout', 'deploy'])

def get_travis_public_key():
    r = requests.get(urljoin(TRAVIS_API_HOST, '/config'))
    return r.json()['config']['notifications']['webhook']['public_key']

@route('/add/<hostname>/<key>')
def add(hostname, key):
    if not validate_hostname(hostname):
        abort(400, 'Error: Hostname invalid')
    elif not validate_key_format(key):
        abort(400, 'Error: Key format invalid')

    existing_keys = list(
        find_key(key)
    )
    if len(existing_keys) == 1:
        if existing_keys[0] == hostname:
            abort(409, 'Warning: The same key does already exist for {hostname}'.format(
                    hostname=hostname
                )
            )
        else:
            abort(409, 'Error: Key is linked to another hostname.')  # add method to change hostname
    elif len(existing_keys) >= 2:
        abort(409, 'Error: WAT? Key is linked to more than one hostname: {peers}'.format(
                peers=', '.join(existing_keys)
            )
        )

    if os.path.isfile(os.path.join(os.environ['FASTD_PEERS_DIR'], hostname)):
        hostname = '{hostname}__{rand}'.format(
            hostname=hostname,
            rand=uuid.uuid4().hex[:8]
        )

    with open(os.path.join(os.environ['FASTD_PEERS_DIR'], hostname), 'w') as config:
        content = 'key "{key}";\n'.format(key=key)
        config.write(content)
        config.close()

        git(['checkout', 'master'])
        git(['pull'])
        git(['add', hostname])
        git(
            [
                'commit', '-m',
                'Added {hostname}'.format(hostname=hostname)
            ]
        )
        git(['push'])
        git(['checkout', 'deploy'])

    return 'Info: Added {key} for {hostname}'.format(hostname=hostname, key=key)

@post('/deploy')
def deploy():
    payload = request.forms.get('payload')

    key = RSA.importKey(get_travis_public_key())
    if not PKCS1_v1_5.new(key).verify(
        SHA.new(payload.encode('utf-8')),
        base64.b64decode(request.get_header('Signature'))
    ):
        abort(401, 'Error: Signature verification invalid')

    if json.loads(payload)['state'] != 'passed':
        return 'Okay. ;_;'

    git(['checkout', 'master'])
    git(['pull'])
    git(['checkout', 'deploy'])
    git(['pull'])
    git(['merge', 'master'])
    git(['push'])

    fastd_reload_command = [
        'sudo', 'systemctl', 'reload', 
        'fastd@{site}.service'.format(site=os.environ['FASTD_SITE'])
    ]
    if subprocess.check_call(fastd_reload_command):
            abort(500, 'Error: {command} failed'.format(
                    command=' '.join(command)
                )
            )

    return 'Yay. Thx Travis!'

run(server='meinheld', host='::1', port=8081, reloader=True)
