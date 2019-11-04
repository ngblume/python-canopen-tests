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
    def __init__(self, use_sep_bus_object=False, adapter='socketcan', channel='can0', bitrate=250000):
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
        self.use_sep_bus_object = use_sep_bus_object
        self.adapter = adapter
        self.channel = channel
        self.bitrate = bitrate

        # Create network
        self.network = canopen.Network()
        
        # Create the separate bus if requested
        if (self.use_sep_bus_object == True):
            self.CreateBus()

        # Connect network
        self.Connect()

    def __del__(self):
        # body of destructor
        self.Disconnect

    # =====================================================================================================================================
    # Define simple callbackfunction for receiving message of specific ID > UseCase: RecordSpecificID()
    def _recv_callback(can_id, data, timestamp):
        print('CAN-ID: ', hex(can_id), ' - Data: ', data, '- Timestamp: ', timestamp)

    # =====================================================================================================================================
    # Connect 
    def Connect(self):
        if (self.use_sep_bus_object == True):
            # Assign network to previoulyly created bus
            self.network.bus = self.can_bus
        else:
            self.network.connect(bustype=self.adapter, channel=self.channel, bitrate=self.bitrate) 

    # =====================================================================================================================================
    def Disconnect(self):
        time.sleep(3)
        # Disconnect networks from CAN bus
        self.network.disconnect()
    
    # =====================================================================================================================================
    def CreateBus(self):
        self.can_bus = can.interface.Bus(bustype=self.adapter, channel=self.channel, bitrate=self.bitrate)

    # =====================================================================================================================================
    def Scanner(self):
        # Scan network with scanner via Index 0x1000 Subindex 0x00
        self.network.scanner.search()
        # Wait for nodes to respond
        time.sleep(1)
        # for node_id in self.network.scanner.nodes:
        #     print('Found node: ', hex(node_id))
        
        return self.network.scanner.nodes

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

    # =====================================================================================================================================
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
            result = self.network[node_id].sdo[index].raw
        elif mode == 'segmented':
            # SDO upload via segmented transfer
            result = self.network[node_id].sdo[index][subindex].data
        elif mode == 'block-filelike':
            # Upload a long string via BLOCK transfer from the node via file-like access
            self.fp = self.network[node_id].sdo[index][subindex].open('r', block_transfer=True)
            result = fp.read()
            fp.close()
        else:
            print('ERROR: SDO mode specified with unknown option')

    # =====================================================================================================================================
    # def SDO_Download():

    # def RecordSpecificID():

    # def EmcyListActive():
    
    # def EmcyListLog():