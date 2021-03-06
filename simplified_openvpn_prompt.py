#!/usr/bin env python3
# -*- coding: utf-8 -*-

"""File that contains SimplifiedOpenvpnPrompt class."""

class SimplifiedOpenvpnPrompt:
    """Class that hold and handles string values for prompts and flash messages."""
    prompts = dict()

    prompts['server_dir'] = "Enter location of OpenVPN server's directory on your server"
    prompts['easy_rsa_dir'] = "Enter location of Easy RSA's directory on your server"
    prompts['easy_rsa_ver'] = 'Select version of Easy RSA that you are using (2|3)'
    prompts['clients_dir'] = "Enter location for client's directory on your server"
    prompts['hostname'] = 'Enter the hostname of your server'
    prompts['protocol'] = 'Select protocol that you would like to use (TCP|UDP)'
    prompts['port'] = 'Select port that you are using for for your server'
    prompts['mgmt_used'] = "Are you going to use OpenVPN's management interface? (Y|N)"
    prompts['mgmt_address'] = "Enter network address of OpenVPN's management interface"
    prompts['mgmt_port'] = "Enter TCP port of OpenVPN's management interface"
    prompts['sovpn_share_salt'] = 'Enter random salt for sharing script'
    prompts['sovpn_share_address'] = 'Enter network address for sharing script'
    prompts['sovpn_share_port'] = 'Enter TCP port for sharing script'
    prompts['sovpn_share_url'] = 'Enter URL prefix for sharing script'
    prompts['sovpn_config_file'] = "Enter location for Simplified OpenVPN's config file"

    @staticmethod
    def get(target_property, suggestion=None):
        """Method that builds up prompt string and returns it."""
        if target_property in SimplifiedOpenvpnPrompt.prompts:
            prompt = '> ' + SimplifiedOpenvpnPrompt.prompts[target_property]
            if suggestion:
                prompt += ' [' + str(suggestion) + ']'
            prompt += ': '
            return prompt
        return None
