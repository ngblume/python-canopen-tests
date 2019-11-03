#!/usr/bin/env python
# coding: utf-8

import canopen
import can
import time
import logging
import os

class teststand-canopen():
    """ Class containing functions and interface to utilize python-canopen from TestStand """

    def __init__(self, use_sep_bus_object=False, ):
    

    def Addnode(self, node_id=0x00):

    def PerformSDO():

    def SearchSpecificID():

    def EmcyListActive():
    
    def EmcyListLog():

    def _recv_callback(can_id, data, timestamp):
        print('CAN-ID: ', hex(can_id), ' - Data: ', data, '- Timestamp: ', timestamp)