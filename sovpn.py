#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pylint: disable=W0621

"""Bootstrap file and entry point for Simplified Openvpn."""

import sys
import os
import logging
import pystache
from flask import Flask
from flask import send_file
from flask import abort
from simplified_openvpn import SimplifiedOpenvpn
from simplified_openvpn_helper import SimplifiedOpenvpnHelper as _helper
from simplified_openvpn_config import SimplifiedOpenvpnConfig
from simplified_openvpn_data import SimplifiedOpenvpnData

LOG = logging.getLogger('werkzeug')
LOG.setLevel(logging.ERROR)

if (
        len(sys.argv) == 1 or
        (sys.argv[1].lower() == 'client' and len(sys.argv) == 2) or
        (sys.argv[1].lower() == 'client' and sys.argv[2].lower() == 'create')):
    # Crate client.
    if len(sys.argv) > 3:
        PRETTY_NAME = ' '.join(sys.argv[3:]).strip()
    else:
        PRETTY_NAME = None

    SOVPN = SimplifiedOpenvpn()
    SOVPN.create_client(PRETTY_NAME)
elif len(sys.argv) > 2 and (
        sys.argv[1].lower() == 'client' and sys.argv[2].lower() == 'revoke'
        or sys.argv[1].lower() == 'revoke'):
    # Revoke client.
    try:
        COMMON_NAME_INDEX = 2 if sys.argv[1].lower() == 'revoke' else 3
        COMMON_NAME = sys.argv[COMMON_NAME_INDEX].strip()
        SOVPN = SimplifiedOpenvpn()
        SOVPN.revoke_client(COMMON_NAME)
    except IndexError:
        print('> Usage: ' + sys.argv[0] + ' revoke [Common Name]')
elif len(sys.argv) > 1 and sys.argv[1] == 'share':
    # Share.
    CONFIG = SimplifiedOpenvpnConfig()
    DB = SimplifiedOpenvpnData()
    APP = Flask(__name__)
    PATH = CONFIG.clients_dir
    ALLOWED_SLUGS = None

    # If slugs are specified, then only allow sharing for specific clients.
    if len(sys.argv) > 2:
        # As we are only serving files to specific clients we can aswell output their hashes.
        print('> Sharing mappings:')

        ALLOWED_SLUGS = list()
        for slug in sys.argv[2:]:
            ALLOWED_SLUGS.append(slug)
            share_hash = DB.find_client_share_hash_by_slug(slug)
            if share_hash:
                print('> ' + slug + ' : ' + share_hash)
            else:
                print('> ' + slug + ' : ---')
    else:
        print('> Sharing confirguration files for everybody.')
    print()

    @APP.route('/<share_hash>')
    def client_page(share_hash):
        """Display all flavours of client's config files to user."""
        slug = DB.find_client_slug_by_share_hash(share_hash)
        if slug is None:
            abort(404)
        if ALLOWED_SLUGS is not None:
            if slug not in ALLOWED_SLUGS:
                abort(403)

        data = dict()
        data['client_name'] = slug
        data['list_items'] = ''

        files = os.listdir(PATH + slug)
        for config_file in files:
            if config_file == 'pretty-name.txt':
                data['client_name'] = _helper.read_file_as_value(PATH + slug + '/' + config_file)
                continue

            anchor = '<a href="' + share_hash + '/' + config_file +  '">' + config_file + '</a>'
            data['list_items'] += '<li>' + anchor + '</li>'

        renderer = pystache.Renderer()
        return renderer.render_path('./templates/share.mustache', data)

    @APP.route('/<share_hash>/<config_file>')
    def download_config(share_hash, config_file):
        """Serve client's config file and make it downloadable."""
        slug = DB.find_client_slug_by_share_hash(share_hash)
        if slug is None:
            abort(404)
        if ALLOWED_SLUGS is not None:
            if slug not in ALLOWED_SLUGS:
                abort(403)

        return send_file(PATH + slug + '/' + config_file)

    APP.run(host='0.0.0.0', port=CONFIG.sovpn_share_port)
elif len(sys.argv) > 1 and (sys.argv[1] == 'init' or sys.argv[1] == 'edit'):
    ACTION = sys.argv[1]

    if ACTION == 'init':
        if not SimplifiedOpenvpnConfig.needs_setup():
            CONFIG = SimplifiedOpenvpnConfig()
            CONFIG.destroy()
            del CONFIG

    CONFIG = SimplifiedOpenvpnConfig()
    CONFIG.wipe()
    CONFIG.setup()

    if ACTION == 'edit':
        SOVPN = SimplifiedOpenvpn()
        SOVPN.rotate_share_hashes()
elif len(sys.argv) > 1 and sys.argv[1] == 'destroy':
    if SimplifiedOpenvpnConfig.needs_setup():
        exit(0)

    CONFIG = SimplifiedOpenvpnConfig()
    CONFIG.destroy()