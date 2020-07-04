# -*- coding: utf-8 -*-
# (c) 2020 Piotr Wojciechowski <piotr@it-playground.pl>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import yaml
from virl2_client import ClientLibrary


class CMLNetKit(object):
    """
    Initializes a CMLNetKit instance. This class is used to perform all the operations on CML2 lab.

    :param cml_options: Configuration stored in CMLNetKitConfig class.
    :type cml_options: CMLNetKitConfig class
    """

    lab_conf = None
    args = None

    lab_conf_changed = False

    def __init__(self, cml_options):
        super(CMLNetKit, self).__init__()

        self.args = cml_options

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
        """
        Imports an existing topology from a CML2 server. Downloaded configuration is stored in self.lab_conf class
        variable and parsed as YAML object

        :raises TypeError: if no lab_id is provided
        :raises requests.exceptions.HTTPError: if there was a transport error
        """

        cl = ClientLibrary(url="https://" + self.args.host, username=self.args.username,
                           password=self.args.password,
                           ssl_verify=self.args.ssl_verify)
        cl.wait_for_lld_connected()
        try:
            # self.lab_conf = cl.export_lab(lab_id=self.args.lab_id)
            lab = cl.join_existing_lab(self.args.lab_id)
            self.lab_conf = yaml.safe_load(lab.download())
        except TypeError:
            print("TypeError: No lab_id provided. Use the -l option to provide the lab_id")

    def lab_upload(self):
        """
        Upload topology from the self.lab_conf class variable to CML2 server as a new lab.

        :raises requests.exceptions.HTTPError: if there was a transport error
        """

        cl = ClientLibrary(url="https://" + self.args.host, username=self.args.username,
                           password=self.args.password,
                           ssl_verify=self.args.ssl_verify)
        cl.wait_for_lld_connected()
        self.lab_conf = cl.import_lab(topology=yaml.dump(self.lab_conf), title=self.lab_conf["lab"]["title"])

    def update_bridge(self):
        """
        Update the configuration of the "External Connection" objects to "bridge0" value. It is done by processing
        the lab configuration YAML object in self.lab_conf class variable
        """

        for nodenum, nodedef in enumerate(self.lab_conf["nodes"]):
            if nodedef.get("node_definition") == 'external_connector' and nodedef.get("configuration") != 'bridge0':
                self.lab_conf["nodes"][nodenum]["configuration"] = 'bridge0'
                self.lab_conf_changed = True

    def print_labs(self):
        """
        Get list of labs from CML2 server and print it formatted on console.

        :raises requests.exceptions.HTTPError: if there was a transport error
        """

        cl = ClientLibrary(url="https://" + self.args.host, username=self.args.username,
                           password=self.args.password,
                           ssl_verify=self.args.ssl_verify)
        cl.wait_for_lld_connected()
        labs = cl.all_labs()
        print('\nLab ID\tLab Title')
        for lab in labs:
            print(lab.id + '\t' + lab.title)
