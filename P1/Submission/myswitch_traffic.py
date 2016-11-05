#!usr/bin/env python3

from switchyard.lib.address import *
from switchyard.lib.packet import *
from switchyard.lib.common import *

def switchy_main(net):
    my_interfaces = net.interfaces()
    mymacs = [intf.ethaddr for intf in my_interfaces]
    trafficList = []
    while True:
        try:
            dev,packet = net.recv_packet()
        except NoPackets:
            continue
        except Shutdown:
            return
        #Build the list of sources we already have in our list
        sources = [source[0] for source in trafficList]
        #If the source of the packet is not in our list
        if not packet[0].src in sources:
           #If there is an empty index in the list, add the source and the port to the list.
           if len(trafficList) < 5:
                trafficList.append([packet[0].src, dev, 0])
           else:
                sortedTL = sorted(trafficList, key=lambda x: -x[2])
                trafficList = sortedTL
                trafficList.pop()
                trafficList.append([packet[0].src, dev, 0])
        #If the source of the packet is in our list
        else:
             indexOfSrc = sources.index(packet[0].src)
             #Check to see if the port matches for the corresponding source. Else update the entry
             if not trafficList[indexOfSrc][1] == dev:
                      trafficList[indexOfSrc][1] = dev

        log_debug ("In {} received packet {} on {}".format(net.name, packet, dev))

        #Check to see the destination source entry exists in the table.
        destsources = [source[0] for source in trafficList]
        if packet[0].dst in mymacs:
            log_debug ("Packet intended for me")
        else:
            #If the packet is intended for destination in our list
            if packet[0].dst in destsources:
              indexOfDest = destsources.index(packet[0].dst)
              #Update the traffic info
              trafficList[indexOfDest][2] += 1
              net.send_packet(trafficList[indexOfDest][1], packet)
            else:
              #Flood
              for intf in my_interfaces:
                if dev != intf.name:
                    log_debug ("Flooding packet {} to {}".format(packet, intf.name))
                    net.send_packet(intf.name, packet)
    net.shutdown()
