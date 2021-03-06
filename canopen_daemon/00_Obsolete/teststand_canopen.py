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

        # Create empty lidst of dict for subscriptions
        self.rcvd_msgs = []

        # Create network
        self.network = canopen.Network()

        # Connect network
        self.Connect()

    def __del__(self):
        self.Disconnect

    # =====================================================================================================================================
    # Define simple callbackfunction for receiving message of specific ID > UseCase: RecordSpecificID()
    def _recv_callback(self, can_id, data, timestamp):
        # For debugging - needs to be removed later
        print('CAN-ID: ', hex(can_id), ' - Data: ', data, '- Timestamp: ', timestamp)
        # Add recevied msg to rcvd_msgs (list of dicts)
        self.rcvd_msgs.append({'ID': can_id}, {'data': data}, {'timestamp': timestamp})

    # =====================================================================================================================================
    # Connect 
    def Connect(self):
        if (self.use_sep_bus_object == True):
            # Create bus "manually"
            self.can_bus = can.interface.Bus(bustype=self.adapter, channel=self.channel, bitrate=self.bitrate)
            # Assign network to previoulyly created bus
            self.network.bus = self.can_bus
            # Set notifier
            self.network.notifier = can.Notifier(self.network.bus, self.network.listeners, 1)
        else:
            self.network.connect(bustype=self.adapter, channel=self.channel, bitrate=self.bitrate) 

    # =====================================================================================================================================
    def Disconnect(self):
        time.sleep(3)
        # Disconnect networks from CAN bus
        self.network.disconnect() 

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
    def SDO_Upload(self, node_id, index, subindex, mode='expedited', timeout = 2.0):
        """ 
        :param uint8 node_id:
            Node ID to be used for SDO
        :param str mode:
            Specify which mode should be used
            Options: 'expedited', 'segmented', 'block-filelike'
        :return:
            Data received for the SDO request.
        :rtype: bytes
        """
        # OPEN: Erweiterung um Abfrage von SDOs mittels Parameter-Namen - Auflösung über OD ??

        self.network[node_id].sdo.RESPONSE_TIMEOUT = timeout
        if (mode=='expedited' or mode == 'segmented'):
            # SDO upload via expedited OR segmented transfer
            data = self.network[node_id].sdo.upload(index, subindex)
        elif mode == 'block-filelike':
            # Upload a long string via BLOCK transfer from the node via file-like access
            fp = self.network[node_id].sdo.open(index, subindex, 'rb', block_transfer=True)
            data = fp.read()
            fp.close()
        else:
            print('ERROR: SDO upload mode specified with unknown option')
            data = -50

        return data

    # =====================================================================================================================================
    def SDO_Download(self, node_id, index, subindex, data, mode='expedited', timeout = 2.0):
        """ 
        :param uint8 node_id:
            Node ID to be used for SDO
        :param str mode:
            Specify which mode should be used
            Options: 'expedited', 'segmented', 'block-filelike'
        :param data:
            Data to be written to device as SDO download request
        """
        # OPEN: Erweiterung um Setzen von SDOs mittels Parameter-Namen - Auflösung über OD ??
        
        self.network[node_id].sdo.RESPONSE_TIMEOUT = timeout
        if (mode=='expedited' or mode == 'segmented'):
            # SDO download via expedited OR segmented transfer
            self.network[node_id].sdo.download(index, subindex, data)
        elif mode == 'block-filelike':
            # Upload a long string via BLOCK transfer from the node via file-like access
            fp = self.network[node_id].sdo.open(index, subindex, 'wb', block_transfer=True)
            fp.write(data)
            fp.close()
        else:
            print('ERROR: SDO download mode specified with unknown option')

    # =====================================================================================================================================
    def RecordSpecificID(self, can_id=0x010A, timeout=2.5):
        # Clear recvd sgs
        self.rcvd_msgs = []
        # Subscribe to specified CAN ID with callback-fct
        self.network.subscribe(can_id, self._recv_callback)
        # Stay subscribed to CAN ID for specified amount of time (timeout) - BLOCKING !!!
        time.sleep(timeout)
        self.network.unsubscribe(can_id, self._recv_callback)

        # Print out list of received messages
        print(self.rcvd_msgs)

        # Return rcvd_msgs as result
        return self.rcvd_msgs

    # =====================================================================================================================================
    # def EmcyListActive():
    
    # =====================================================================================================================================
    # def EmcyListLog():
