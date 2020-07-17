# -*- coding: utf-8 -*-
# (c) 2020 Piotr Wojciechowski <piotr@it-playground.pl>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import yaml
from virl2_client import ClientLibrary
from ciscoconfparse import CiscoConfParse
import netaddr


class CMLNetKit(object):
    """
    Initializes a CMLNetKit instance. This class is used to perform all the operations on CML2 lab.

    :param cml_options: Configuration stored in CMLNetKitConfig class.
    :type cml_options: CMLNetKitConfig class
    """

    lab_conf = None
    lab_handler = None
    _cmlnetkitconfig = None

    lab_conf_changed = False

    def __init__(self, cml_options):
        super(CMLNetKit, self).__init__()

        self._cmlnetkitconfig = cml_options

        if self._cmlnetkitconfig.lab_id is None:
            self.print_labs()
            exit(0)

        self.lab_download()
        # print(">>>>>>>>>>")
        # print(self.lab_conf)
        # print(">>>>")
        # print(self.get_node_config(self._get_node_index_by_label("iosv-0")))
        # exit(0)

        if self._cmlnetkitconfig.update_bridge is True:
            self.update_bridge()

        if self._cmlnetkitconfig.update_loopback is True:
            self.update_loopbacks()

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

        cl = ClientLibrary(url="https://" + self._cmlnetkitconfig.host, username=self._cmlnetkitconfig.username,
                           password=self._cmlnetkitconfig.password,
                           ssl_verify=self._cmlnetkitconfig.ssl_verify)
        cl.wait_for_lld_connected()
        try:
            # self.lab_conf = cl.export_lab(lab_id=self._cmlnetkitconfig.lab_id)
            # lab = cl.join_existing_lab(self._cmlnetkitconfig.lab_id)
            # self.lab_conf = yaml.safe_load(lab.download())
            self.lab_handler = cl.join_existing_lab(self._cmlnetkitconfig.lab_id)
            self.lab_conf = yaml.safe_load(self.lab_handler.download())
        except TypeError:
            print("TypeError: No lab_id provided. Use the -l option to provide the lab_id")

    def lab_upload(self):
        """
        Upload topology from the self.lab_conf class variable to CML2 server as a new lab.

        :raises requests.exceptions.HTTPError: if there was a transport error
        """

        cl = ClientLibrary(url="https://" + self._cmlnetkitconfig.host, username=self._cmlnetkitconfig.username,
                           password=self._cmlnetkitconfig.password,
                           ssl_verify=self._cmlnetkitconfig.ssl_verify)
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

    def _get_node_index_by_label(self, node_name):
        for nodenum, nodedef in enumerate(self.lab_conf["nodes"]):
            if nodedef.get("label") == node_name:
                return nodenum

    def _get_node_index_by_id(self, node_id):
        for nodenum, nodedef in enumerate(self.lab_conf["nodes"]):
            if nodedef.get("id") == node_id:
                return nodenum

    def get_node_config(self, node_index):
        return self.lab_conf["nodes"][node_index]["configuration"]

    def set_node_config(self, node_index, node_config):
        self.lab_conf["nodes"][node_index]["configuration"] = node_config

    @staticmethod
    def _iface_ip_addr_defined(iface_conf=[]):
        """
        Returns True if IP address is assigned in interface configuration

        :param iface_conf: Array of interface configuration lines
        :return: Bool
        """
        for config_line in iface_conf:
            if "no ip address" in config_line:
                return False
        return True

    def print_labs(self):
        """
        Get list of labs from CML2 server and print it formatted on console.

        :raises requests.exceptions.HTTPError: if there was a transport error
        """

        cl = ClientLibrary(url="https://" + self._cmlnetkitconfig.host, username=self._cmlnetkitconfig.username,
                           password=self._cmlnetkitconfig.password,
                           ssl_verify=self._cmlnetkitconfig.ssl_verify)
        cl.wait_for_lld_connected()
        labs = cl.all_labs()
        print('\nLab ID\tLab Title')
        for lab in labs:
            print(lab.id + '\t' + lab.title)

    def update_loopbacks(self):
        """
        Updates the Loopback interfaces configuration for nodes in the lab topology.

        For each node it will call the platform specific method to update Loopback interface address
        from provided subnet using the next available address for each device.
        """
        ip = netaddr.IPNetwork('10.0.0.0/24')
        for nodenum, nodedef in enumerate(self.lab_conf["nodes"]):
            self.update_node_loopback_conf_ios(nodedef.get("label"), ip[nodenum + 1].__str__())

    def update_node_loopback_conf_ios(self, node_label=None, ip_addr=None):
        """
        Update the IP address, description and shutdown state configuration of Loopback interface
        if no IP address is assigned

        :param node_label: The node label
        :type node_label: str
        :param ip_addr: The IP address that will be assigned to Loopback interface of the device
        :type ip_addr: str
        """
        if node_label is None or ip_addr is None:
            raise ValueError
        if type(ip_addr) is not str or type(node_label) is not str:
            raise TypeError

        node_config = self.get_node_config(self._get_node_index_by_label(node_label))
        node_parsed_config = CiscoConfParse(node_config.split('\n'))
        # Don't update the interface configuration if IP address is already set
        if self._iface_ip_addr_defined(node_parsed_config.find_children(r'^interface\sLoopback0')):
            return

        ip_addr_str = r'ip address ' + ip_addr + ' 255.255.255.255'
        node_parsed_config.replace_children(r'^interface\sLoopback0', r'no ip address', ip_addr_str)
        node_parsed_config.replace_children(r'^interface\sLoopback0', r'shutdown', r'no shutdown')
        node_parsed_config.replace_children(r'^interface\sLoopback0', r'description to',
                                            r'description Loopback interface')
        node_parsed_config.atomic()
        node_new_config = '\n'.join([i for i in node_parsed_config.ioscfg[0:]])
        self.set_node_config(self._get_node_index_by_label(node_label), node_new_config)
