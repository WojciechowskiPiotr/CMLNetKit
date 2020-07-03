==============
CMLNetKit
==============

.. image:: http://img.shields.io/badge/license-GPLv3-blue.svg
   :target: https://www.gnu.org/copyleft/gpl.html
   :alt: License

.. contents::

.. _introduction:

What is CMLNetKit?
==================

CMLNetKit is a small application for device automatic pre-configuration for Cisco Modeling Labs 2.0

In Cisco VIRL the most valuable feature is AutoNetKit. It creates the initial configuration of simulated devices, including
the interface IP address, the loopback interfaces addressing, routing protocols, and many more. This feature pretty much does not
exist in Cisco Modeling Labs 2.0, aka. Cisco VIRL2 requiring a manual configuration of every essential feature. The
CMLNetKit brings some of the AutoNetKit features back to CML2.0

WARNING
=======

The is and early development version. Use at your own risk!


Usage
=====

The following options are required or optional


.. code::

    usage: cmlnetkit.py [-h] [-H HOST] [-l LAB_ID] [-P PORT] [-u USERNAME]
                    [-p PASSWORD] [-b]

optional arguments:
  -h, --help            show this help message and exit

Connection options:
  -H HOST, --host HOST  CML2.0 host address
  -l LAB_ID, --lab LAB_ID
                        Lab ID. If not specified then returns list of labs
  -P PORT, --port PORT  CML 2.0 API port (default 443)
  -u USERNAME, --username USERNAME
                        CML 2.0 API username (default "virl2")
  -p PASSWORD, --password PASSWORD
                        CML 2.0 API password (default "virl2")

Configuration changes:
  -b                    Changing all "External Connection" objects
                        configuration to "Bridge"

.. _Pre-Requisites:

Pre-requisites
==============

CMLNetKit requires Python versions 3.5+. The OS should not
matter. It has been tested on Python version 3.7.7

The required Python libraries are defined in ``requirements.txt``


Features
========

The following features has already been deployed:
 * Reading and writing the lab configuration from API
 * Changing all ``External Connection`` objects types to ``Bridge``
