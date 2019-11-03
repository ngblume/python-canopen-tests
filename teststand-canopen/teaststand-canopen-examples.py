#!/usr/bin/env python
# coding: utf-8

import canopen
import can
import time
import logging
import os
import teststand_canopen

# EDS Path
EDS_PATH = os.path.join(os.path.dirname(__file__), '../00_EDS/SimNode/SimNode.eds')

# Create simulation network
# Create network_sim = network used to CREATE simulated nodes
network_sim = canopen.Network()
# Connect network_sim to same CAN bus
network_sim.connect(channel='can0', bustype='socketcan')
# Create simulated nodes (via network_sim) > called "local"
localSimNode_0x05 = network_sim.create_node(0x05, EDS_PATH)

# Instantiate class teststand_canopen
interface = teststand_canopen.teststand_canopen(use_sep_bus_object=False, adapter='socketcan')

# add remote node = 0x05 to network
remote_node = interface.AddNode(0x05, EDS_PATH)

