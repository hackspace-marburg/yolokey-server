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
from bottle import route, run, abort, request
from hashlib import sha256

hostname_regex = re.compile(r'35\d{3}-[\w-]{1,}', re.IGNORECASE)  # 35xxx-xxxxx_Xxxxx

def validate_hostname(hostname):
    return bool(hostname_regex.match(hostname))

def validate_key_format(key):
    try:
        b = bytes.fromhex(key)
    except ValueError:
        return False
    if len(b) != 32:
        return False
    return True

def find_key(key, fastd_peers_dir='/etc/fastd/site/peers'):
    for peer in os.listdir(fastd_peers_dir):
        if os.path.isdir(peer):
            continue
        for line in open(os.path.join(fastd_peers_dir, peer), 'r'):
            if key in line:
                yield peer

@route('/add/<hostname>/<key>')
def add(hostname, key):
    if not validate_hostname(hostname):
        abort(400, 'Error: Hostname invalid')
    elif not validate_key_format(key):
        abort(400, 'Error: Key format invalid')

    existing_keys = list(
        find_key(key, fastd_peers_dir=os.environ['FASTD_PEERS_DIR'])
    )
    if len(existing_keys) == 1:
        if existing_keys[0] == hostname:
            abort(409, 'Warning: The same key does already exist for {hostname}'.format(
                    hostname=hostname
                )
            )
        else:
            abort(409, 'Error: Key is linked to another hostname.')
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
        content = 'key "{key}";'.format(key=key)
        config.write(content)
        config.close()
        if subprocess.check_call(
            ['git', '-C', os.environ['FASTD_PEERS_DIR'], 'pull']
        ):
            abort(500, 'Error: git pull failed')
        if subprocess.check_call(
            ['git', '-C', os.environ['FASTD_PEERS_DIR'], 'add', hostname]
        ):
            abort(500, 'Error: git add failed')
        if subprocess.check_call(
            ['git', '-C', os.environ['FASTD_PEERS_DIR'], 'commit', '-m', 'Added {hostname}'.format(hostname=hostname)]
        ):
            abort(500, 'Error: git commit failed')
        if subprocess.check_call(
            ['git', '-C', os.environ['FASTD_PEERS_DIR'], 'push']
        ):
            abort(500, 'Error: git push failed')

    return 'Info: Added {key} for {hostname}'.format(hostname=hostname, key=key)

run(host='::', port=8080, reloader=False)