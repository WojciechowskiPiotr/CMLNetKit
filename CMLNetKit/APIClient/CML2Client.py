# -*- coding: utf-8 -*-
# (c) 2020 Piotr Wojciechowski <piotr@it-playground.pl>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from urllib.parse import urljoin

import argparse
import yaml
from virl2_client import ClientLibrary


class CMLClientLibrary(ClientLibrary):
    def __init__(self, **kwargs):
        super(CMLClientLibrary, self).__init__(**kwargs)

    def export_lab(self, lab_id=None):
        """
        Export an existing topology configuration from CML2 server.

        :param lab_id: Topology ID
        :type lab_id: str
        :returns: Topology configuration YAML
        :rtype: str
        :raises
        :raises ValueError: if there's no lab ID in the API response
        :raises requests.exceptions.HTTPError: if there was a transport error
        """
        if lab_id is None:
            raise TypeError
        response = self.session.get(urljoin(self._base_url, 'labs/' + lab_id + '/download'))
        response.raise_for_status()
        return yaml.safe_load(response.content)


class CML2Client(object):
    lab_conf = None
    args = None

    lab_conf_changed = False

    def __init__(self, **kwargs):
        super(CML2Client, self).__init__(**kwargs)

        parser = argparse.ArgumentParser()

        group_connection = parser.add_argument_group("Connection options")
        group_changes = parser.add_argument_group("Configuration changes")

        group_connection.add_argument('-H', '--host', type=str, dest='host', help='CML2.0 host address')
        group_connection.add_argument('-l', '--lab', type=str, dest='lab_id',
                            help='Lab ID. If not specified then returns list of labs')
        group_connection.add_argument('-P', '--port', type=int, help='CML 2.0 API port (default 443)', dest='port', default=443)
        group_connection.add_argument('-u', '--username', type=str, help='CML 2.0 API username (default "virl2")',
                            dest='username', default="virl2")
        group_connection.add_argument('-p', '--password', type=str, help='CML 2.0 API password (default "virl2")',
                            dest='password',
                            default="virl2")
        group_changes.add_argument('-b',
                            help='Changing all "External Connection" objects configuration to "Bridge"',
                            dest="conf_ext_bridge", default=False, action="store_true")
        self.args = parser.parse_args()

        if self.args.lab_id is None:
            self.print_labs()
            exit(0)

        self.lab_download()
        if self.args.conf_ext_bridge:
            self.update_bridge()

        if self.lab_conf_changed is True:
            self.lab_upload()
        else:
            print("Lab configuration unchanged")

    def lab_download(self):
        cl = CMLClientLibrary(url="https://" + self.args.host, username=self.args.username,
                              password=self.args.password,
                              ssl_verify=False)
        cl.wait_for_lld_connected()
        try:
            self.lab_conf = cl.export_lab(lab_id=self.args.lab_id)
        except TypeError:
            print("TypeError: No lab_id provided. Use the -l option to provide the lab_id")

    def lab_upload(self):
        cl = CMLClientLibrary(url="https://" + self.args.host, username=self.args.username,
                              password=self.args.password,
                              ssl_verify=False)
        cl.wait_for_lld_connected()
        self.lab_conf = cl.import_lab(topology=yaml.dump(self.lab_conf), title=self.lab_conf["lab"]["title"])

    def update_bridge(self):
        for nodenum, nodedef in enumerate(self.lab_conf["nodes"]):
            if nodedef.get("node_definition") == 'external_connector' and nodedef.get("configuration") != 'bridge0':
                self.lab_conf["nodes"][nodenum]["configuration"] = 'bridge0'
                self.lab_conf_changed = True

    def print_labs(self):
        cl = CMLClientLibrary(url="https://" + self.args.host, username=self.args.username,
                              password=self.args.password,
                              ssl_verify=False)
        cl.wait_for_lld_connected()
        labs = cl.all_labs()
        print('\nLab ID\tLab Title')
        for lab in labs:
            print(lab.id + '\t' + lab.title)
