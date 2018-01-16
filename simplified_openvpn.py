#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Management interface for OpenVPN Community Edition."""

import os
import zipfile
from shutil import copyfile
from subprocess import run
import pystache
from simplified_openvpn_helper import SimplifiedOpenvpnHelper as _helper
from simplified_openvpn_config import SimplifiedOpenvpnConfig


class SimplifiedOpenvpn:
    """Main class that takes care of managing OpenVPN on your server."""

    def __init__(self):
        """Loads config if possible, else asks you to generate config."""
        self._config = SimplifiedOpenvpnConfig()

    def client_exists(self, verbose=True):
        """Checks if client with generated slug already exists."""
        if os.path.isdir(self._config.clients_dir + self._config.slug):
            if verbose:
                print('> Client with this name already exists.')
            return True
        return False

    def create_pretty_name_file(self):
        """Creates file that contains origianl input for client name."""
        if self._config.client_dir and self._config.pretty_name:
            with open(self._config.client_dir + 'pretty-name.txt', 'w') as pretty_name_file:
                pretty_name_file.write(self._config.pretty_name + "\n")
                return True
        return False

    def move_client_files(self):
        """Moves client's keys to client's directory."""
        client_files = [self._config.slug + '.crt', self._config.slug + '.key']
        for client_file in client_files:
            source = self._config.easy_rsa_dir + 'keys/' + client_file
            destination = self._config.client_dir + client_file
            os.rename(source, destination)

    def copy_ca_file(self):
        """Copies certificate authority key to client's directory."""
        source = self._config.easy_rsa_dir + 'keys/ca.crt'
        destination = self._config.client_dir + 'ca.crt'
        copyfile(source, destination)

    def copy_ta_file(self):
        """Copies TLS auth key to client's directory."""
        source = self._config.server_dir + 'ta.key'
        destination = self._config.client_dir + 'ta.key'
        copyfile(source, destination)

    def create_config(self):
        """Creates up basic config that can be changed based on flavour."""
        config = dict()
        config['protocol'] = self._config.protocol
        config['hostname'] = self._config.hostname
        config['ipv4'] = self._config.ipv4
        config['port'] = self._config.port
        config['slug'] = self._config.slug
        config['inline'] = False
        return config

    def write_config(self, options, flavour=''):
        """Writes a single config file/archive for client to the disk."""
        template = self._config.server_dir + 'client.mustache'
        if not os.path.isfile(template):
            print("> Template for client's config is missing, exiting.")
            exit(1)

        renderer = pystache.Renderer()
        client_dir = self._config.client_dir
        slug = self._config.slug

        # Creates up name for config file.
        config_path = client_dir + self._config.hostname
        if flavour != '':
            config_path += '-' + flavour
        config_path += '.ovpn'

        with open(config_path, 'w') as config_file:
            config_file.write(renderer.render_path(template, options))

        if not options['inline']:
            with zipfile.ZipFile(config_path + '.zip', 'w') as config_zip:
                config_zip.write(config_path)
                config_zip.write(client_dir + 'ca.crt', 'ca.crt')
                config_zip.write(client_dir + slug + '.crt', slug + '.crt')
                config_zip.write(client_dir + slug + '.key', slug + '.key')
                config_zip.write(client_dir + 'ta.key', 'ta.key')

            # Remove config file that you just zipped but keep certificates for others.
            os.remove(config_path)

    def generate_config_files(self):
        """Generates different flavours of config files."""
        ca_path = self._config.client_dir + 'ca.crt'
        cert_path = self._config.client_dir + self._config.slug + '.crt'
        key_path = self._config.client_dir + self._config.slug + '.key'
        ta_path = self._config.client_dir + 'ta.key'
        options = self.create_config()

        # Plain Windows flavour.
        self.write_config(options)

        # Plain Debian flavour.
        options['deb'] = True
        self.write_config(options, 'deb')
        options['deb'] = False

        # Plain RedHat flavour.
        options['rhel'] = True
        self.write_config(options, 'rhel')
        options['rhel'] = False

        # Inline Windows flavour.
        options['inline'] = True
        options['ca'] = _helper.read_file_as_value(ca_path)
        options['cert'] = _helper.read_file_as_value(cert_path)
        options['key'] = _helper.read_file_as_value(key_path)
        options['ta'] = _helper.read_file_as_value(ta_path)
        self.write_config(options, 'inline')

        # Inline Debian flavour.
        options['deb'] = True
        self.write_config(options, 'inline-deb')
        options['deb'] = False

        # Inline RedHat flavour.
        options['rhel'] = True
        self.write_config(options, 'inline-rhel')
        options['rhel'] = False

        # Clean up.
        self.cleanup_client_certificates()

    def cleanup_client_certificates(self):
        """Cleans up client's certificates as they are no longer needed."""
        cert_files = [self._config.slug + '.crt', self._config.slug + '.key', 'ca.crt', 'ta.key']
        for cert_file in cert_files:
            os.remove(self._config.client_dir + cert_file)

    def create_client(self, pretty_name=None):
        """Entry point for client creation process."""
        if self._config.pretty_name is None:
            while pretty_name is None:
                pretty_name = input('> Enter Full Name for client: ').strip()
                self._config.slug = pretty_name
                if self.client_exists(self._config.slug) or pretty_name == '':
                    pretty_name = None

            self._config.pretty_name = pretty_name
        else:
            self._config.slug = self._config.pretty_name
            self.client_exists(True)

        # Key generation.
        cmd = './build-key ' + self._config.slug + ' 1> /dev/null'
        run(cmd, shell=True, cwd=self._config.easy_rsa_dir)

        # Config generation.
        self._config.client_dir = self._config.slug
        self.create_pretty_name_file()
        self.move_client_files()
        self.copy_ca_file()
        self.copy_ta_file()
        self.generate_config_files()
