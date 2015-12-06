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

import re
from bottle import route, run, template, abort


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

@route('/add_key/<hostname>/<key>')
def add_key(hostname, key):
    if not validate_hostname(hostname):
        abort(400, 'Error: Hostname invalid')
    elif not validate_key_format(key):
        abort(400, 'Error: Key format invalid')

    return template('{{hostname}}, {{key}}', hostname=hostname, key=key)

run(host='localhost', port=8080, reloader=True)