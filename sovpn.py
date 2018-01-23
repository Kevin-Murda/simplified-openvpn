#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Bootstrap file and entry point for Simplified Openvpn."""

import sys
import os
import pystache
from flask import Flask
from flask import send_file
from flask import abort
from simplified_openvpn import SimplifiedOpenvpn
from simplified_openvpn_helper import SimplifiedOpenvpnHelper as _helper
from simplified_openvpn_config import SimplifiedOpenvpnConfig
from simplified_openvpn_data import SimplifiedOpenvpnData

SOVPN = SimplifiedOpenvpn()

if (
        len(sys.argv) == 1 or
        (sys.argv[1].lower() == 'client' and len(sys.argv) == 2) or
        (sys.argv[1].lower() == 'client' and sys.argv[2].lower() == 'create')):
    # Client.
    SOVPN.create_client()
elif len(sys.argv) > 1 and sys.argv[1] == 'share':
    # Share.
    CONFIG = SimplifiedOpenvpnConfig()
    DB = SimplifiedOpenvpnData()
    APP = Flask(__name__)
    PATH = CONFIG.clients_dir

    @APP.route('/<share_hash>')
    def client_page(share_hash):
        """Display all flavours of client's config files to user."""
        slug = DB.find_client_slug_by_share_hash(share_hash)
        if slug is None:
            abort(404)

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

        return send_file(PATH + slug + '/' + config_file)

    APP.run(host='0.0.0.0', port=1195)
