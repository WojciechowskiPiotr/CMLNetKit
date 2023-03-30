==============
CMLNetKit
==============

.. image:: http://img.shields.io/badge/license-GPLv3-blue.svg
   :target: https://www.gnu.org/copyleft/gpl.html
   :alt: License
.. image:: https://static.production.devnetcloud.com/codeexchange/assets/images/devnet-published.svg
   :target: https://developer.cisco.com/codeexchange/github/repo/WojciechowskiPiotr/CMLNetKit
   :alt: DevNet Code Exchange

.. contents::

.. _introduction:

What is CMLNetKit?
==================

CMLNetKit is an application for automatic pre-configuration of nodes in
Cisco Modeling Labs 2.x

This version has been tested with Python 3.10 and CML2.5.

In the Cisco VIRL, the most valuable feature is AutoNetKit.
It creates the initial configuration of simulated devices, including
the interface IP address, the loopback interfaces addressing,
routing protocols, and many more. This feature pretty much does not
exist in Cisco Modeling Labs 2.0 (aka. Cisco VIRL2), requiring a
manual configuration of every IP address of every interface in the
lab topology. The CMLNetKit brings some of the AutoNetKit features
back to CML2.0

You need to run the CMLNetKit before starting the lab. CMLNetKit
won't amend running lab nodes configurations.

Features
========

The following features are currently available:
 * Reading and writing the lab configuration from API
 * Changing all ``External Connection`` objects types to ``Bridge``
 * Addressing Loopback interface
 * Addressing management interfaces
 * Addressing directly connected interfaces between two nodes

CMLNetKit does not modify the provided source lab topology; instead,
it creates a new lab using the same lab title.

Management interfaces
---------------------

The dedicated management interfaces are not present on all node types. In this application, the management interfaces
are statically defined as per the below table. If you request CMLNetKit to assign IP addresses to the
management interfaces, it will treat the following interfaces as management. It would be best to connect these
interfaces to a dedicated out-of-band network via ``External Connector`` node.

+------------+----------------------+
| Node type  | Management interface |
+============+======================+
| iosv       | GigabitEthernet0/0   |
+------------+----------------------+
| csr1000v   | GigabitEthernet1     |
+------------+----------------------+
| iosxrv     | MgmtEth0/0/CPU0/0    |
+------------+----------------------+
| iosxrv9000 | MgmtEth0/RP0/CPU0/0  |
+------------+----------------------+
| nxosv      | mgmt0                |
+------------+----------------------+
| nxosv9000  | mgmt0                |
+------------+----------------------+
| iosvl2     | GigabitEthernet0/0   |
+------------+----------------------+
| asav       | Management0/0        |
+------------+----------------------+


Initial configuration changes
-----------------------------

Before you start, you need to add nodes to the topology and connect them.
Then generate the initial configuration of your lab nodes via CML2 GUI. To do that, open
the CML2 GUI, select your lab and click anywhere on the background. Then select ``Design`` tab and press the ``Build
Initial Bootstrap Configurations`` button.

If you update the topology by adding the new nodes, you need to generate initial configurations for them before running
the CMLNetKit again.

The CMLNetKit won't amend the interface configuration if IP addresses are already present.
How to install CMLNetKit?
=========================

Please follow the steps described below to install the CMLNetKit.

Pre-requisites
--------------

CMLNetKit requires Python versions 3.5+. The OS should not
matter. It has been tested on Python version 3.7.7 on Linux and MacOS.

The required Python libraries are defined in ``requirements.txt``. It is also recommended to have ``git`` client
installed on the host. Alternatively, you can download the repository package from GitHub project site.

It is required to run CMLNetKet from the host that is allowed to access the CML2 API. If you can access
the CML2 GUI, you can also use the CMLNetKit from this host.


Installation
------------

Download the CMLNetKit repository

.. code::

    $ git clone https://github.com/WojciechowskiPiotr/CMLNetKit
    $ cd CMLNetKit

Install required python libraries

.. code::

    $ pip install -r requirements.txt


Usage
=====

The minimum required parameter is the hostname or IP address of the CML2 server provided as ``-H`` value.
If no username or password is provided,
the default of ``virl2/virl2`` is used. To disable the SSL verification, always add ``--no-ssl-verification``
to any command you run.

The following options are required or optional. You can always display help using the ``-h`` parameter.

.. code::

    usage: cmlnetkit.py [-h] [-H HOST] [-l LAB_ID] [--list-labs] [--list-ips]
                        [-P PORT] [-u USERNAME] [-p PASSWORD]
                        [--no-ssl-verification] [--dry-run] [-b]
                        [--lo-subnet LOOPBACK_SUBNET]
                        [--mgmt-range MGMT_IP_LOW MGMT_IP_HIGH]
                        [--peer-subnet PEER_SUBNET]
                        [--mgmt-netmask MGMT_NETMASK | --mgmt-prefixlen MGMT_PREFIXLEN]

    optional arguments:
      -h, --help            show this help message and exit

    Connection options:
      -H HOST, --host HOST  CML2.0 host address
      -l LAB_ID, --lab LAB_ID
                            Lab ID
      --list-labs           List the ID of existing labs
      --list-ips            List the IP addresses configured on L3 links
      -P PORT, --port PORT  CML 2.0 API port (default 443)
      -u USERNAME, --username USERNAME
                            CML 2.0 API username (default "virl2")
      -p PASSWORD, --password PASSWORD
                            CML 2.0 API password (default "virl2")
      --no-ssl-verification
                            Disable the SSL certification verification on the CML2
                            server
      --dry-run             Don't apply any changes to CML2 server.

    Configuration changes:
      -b                    Changing all "External Connection" objects
                            configuration to "Bridge"
      --lo-subnet LOOPBACK_SUBNET
                            Subnet for the Loopback ip addresses assignment, must
                            be provided in format as subnet/mask. If mask not
                            provided default mask for subnet is used.If none
                            provided the default 10.0.0.0/24 is used. Loopback
                            addresses are always /32
      --mgmt-range MGMT_IP_LOW MGMT_IP_HIGH
                            Contiguous range of IP addresses must be provided. As
                            argument values provide first and last IP address of
                            the range
      --peer-subnet PEER_SUBNET
                            Subnet for the ip addresses assignment for direct
                            connections betweend devices,must be provided in
                            format as subnet/mask. If mask not provided the /24 is
                            used.Direct connections betweend devices are addressed
                            with /30 mask
      --mgmt-netmask MGMT_NETMASK
                            Subnet mask that needs to be assigned to management
                            interfaces IP addresses on devices. Mask must be
                            provided in standard netmask notation 255.255.255.0 If
                            neither -mgmt-netmask nor -mgmt-prefixlen is provided
                            then /24 prefixlen (mask of 255.255.255.0) is
                            assigned.
      --mgmt-prefixlen MGMT_PREFIXLEN
                            Subnet mask that needs to be assigned to management
                            interfaces IP addresses on devices. Prefixlen must be
                            provided as integer between 0 and 32. If neither
                            -mgmt-netmask nor -mgmt-prefixlen is provided then /24
                            prefixlen (mask of 255.255.255.0) is assigned.





Usage examples
==============

First, you need to list available labs on the CML2 server. In GUI, you see the lab's names, but in CMLNetKit, you
need to provide the lab ``ID``. To list all the available labs, use the ``--list-labs`` parameter.

.. code::

    cmlnetkit.py -H cml.server.address --list-labs

In the output, you will see all the available labs. The first column contains six characters long lab ``ID``. Please provide it
every time using ``-l`` as a reference to source lab you want to modify.

To change the "External Connection" objects configuration to "bridge".

.. code::

    cmlnetkit.py -H cml.server.address -l abc123 -b

If you want to amend addressing the Loopback interfaces, use the ``--lo-subnet`` parameter followed by the subnet you
want to use for loopbacks. CMLNetKit will assign /32 addresses from this subnet for the Loopback interfaces
of each node.

.. code::

    cmlnetkit.py -H cml.server.address -l abc123 --lo-subnet 10.0.0.0/24

To assign addresses to management interfaces, you need to provide two parameters: using the ``--mgmt-range``
specify the first and the last IP address of the continuous range that should be used for management interfaces,
and then ``--mgmt-prefixlen`` to specify the subnet mask lengths that should be assigned.
.. code::

    cmlnetkit.py -H cml.server.address -labc123 --mgmt-range 172.16.16.2 172.16.16.25 --mgmt-prefixlen 24

To address interfaces the direct connections between the simulation devices, you need to provide a subnet for peer-to-peer
connections. It will be subnetted into /30's subnet per each link.

.. code::

    cmlnetkit.py -H cml.server.address -l abc123 --peer-subnet 10.100.0.0/22

You can use the parameters altogether with SSL verification disabled to perform all operations at once

.. code::

    cmlnetkit.py -H cml.server.address -l abc123 --no-ssl-verification -lo --lo-subnet 10.0.0.0/24 -mgmt --mgmt-range 172.16.16.2 172.16.16.25 --mgmt-prefixlen 24 --peer-subnet 10.100.0.0/22

List IP addresses assigned to devices in initial configuration

.. code::

    cmlnetkit.py -H cml.server.address -l abc123 --list-ip


Support and requests
====================

If you find a bug or want to request additional features, please open the ``Issue`` on the
CMLNetKit GitHub project at https://github.com/WojciechowskiPiotr/CMLNetKit

