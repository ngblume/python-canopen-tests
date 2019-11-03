#!/usr/bin/env python
# coding: utf-8

import canopen
import can
import time
import logging
import os
import struct

class teststand_canopen():
    """ Class containing functions and interface to utilize python-canopen from TestStand """

    # =====================================================================================================================================
    def __init__(self, use_sep_bus_object=False, adapter='socketcan'):
        """ 
        :param boolean use_sep_bus_object:
            Select wether a seperate bus object should be created and used.
        :param str adapter:
            Specify which type of CAN adapter should be used.
            Options: 'socketcan#, 'pcan'
        :raises can.CanError:
            When connection fails.
        """

        # Init variables
        self.USE_EXISTING_BUS = False
        self.network = canopen.Network()

        # Check if seperate bus object should be used and set constant accordingly
        if use_sep_bus_object:
            self.USE_EXISTING_BUS = True
        
        # Create the separate bus if requester
        if (self.USE_EXISTING_BUS == True):
            if adapter == 'socketcan':
                # for SocketCAN, can0 and a bit rate of 250 kB/s)
                self.can_bus = can.interface.Bus(bustype='socketcan', channel='can0', bitrate=250000)
            else if adapter == 'pcan':
                # for PCAN API (USBBUS1 and bit rate 250 kB/s)
                self.can_bus = can.interface.Bus(bustype='pcan', channel='PCAN_USBBUS1', bitrate=250000) 
            else:
                print('ERROR: incorrect adapter specified > ToDo: raise exception')

        # Connect network
        if (self.USE_EXISTING_BUS == True):
            # Assign network to previoulyly created bus
            self.network.bus = can_bus
        else:
            if adapter == 'socketcan':
                # for SocketCAN, can0 and a bit rate of 250 kB/s)
                self.network.connect(bustype='socketcan', channel='can0', bitrate=250000)
            else if adapter == 'pcan':
                # for PCAN API (USBBUS1 and bit rate 250 kB/s)
                self.network.connect(bustype='pcan', channel='PCAN_USBBUS1', bitrate=250000) 
            else:
                print('ERROR: incorrect adapter specified > ToDo: raise exception')

    # =====================================================================================================================================
    def AddNode(self, node_id=0x00, object_dictionary=None):
        """ 
        :param uint8 node_id:
            Node ID to be added to the network
        :param object_dictionary:
            Can be either a string for specifying the path to an
            Object Dictionary file or a
            :class:`canopen.ObjectDictionary` object.
        
        :return:
            The Node object that was added.
        :rtype: canopen.RemoteNode
        """
        # Add node to network
        node = self.network.add_node(node_id, object_dictionary)
        # Return node object for further use
        return node

    def SDO_Upload(self, node_id=0x00, mode='expedited', index=0x1000, subindex=0x00, timeout = 2.0):
        """ 
        :param uint8 node_id:
            Node ID to be used for SDO
        :param str mode:
            Specify which mode should be used
            Options: 'expedited', 'segmented', 'block-filelike'
        :return:
            The Node object that was added.
        :rtype: canopen.RemoteNode
        """
        self.network[node_id].sdo.RESPONSE_TIMEOUT = timeout
        if mode=='expedited':
            # SDO upload via expedited transfer
            result = self.network[node_id].sdo[index][subindex].raw
        else if mode == 'segmented':
            # SDO upload via segmented transfer
            result = self.network[node_id].sdo[index][subindex].data
        else if mode == 'block-filelike':
            # Upload a long string via BLOCK transfer from the node via file-like access
            self.fp = self.network[node_id].sdo[index][subindex].open('r', block_transfer=True)
            result = fp.read()
            fp.close()
        else:
            print('ERROR: SDO mode specified with unknown option')

    def SDO_Download(self, node_id=0x00, mode='expedited', index=0x1000, subindex=0x00, timeout = 2.0, data):

    # def SearchSpecificID():

    # def EmcyListActive():
    
    # def EmcyListLog():

    # Create network_sim = network used to CREATE simulated nodes
    network_sim = canopen.Network()

    # Connect network_sim to same CAN bus
    network_sim.connect(channel='can0', bustype='socketcan')

    # Create simulated nodes (via network_sim) > called "local"
    localSimNode_0x05 = network_sim.create_node(0x05, EDS_PATH)
    localSimNode_0x10 = network_sim.create_node(0x10, EDS_PATH)