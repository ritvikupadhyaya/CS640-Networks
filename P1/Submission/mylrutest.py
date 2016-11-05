#!/usr/bin/env python

import sys
from switchyard.lib.address import *
from switchyard.lib.packet import *
from switchyard.lib.common import *
from switchyard.lib.testing import *

def mk_pkt(hwsrc, hwdst, ipsrc, ipdst, reply=False):
    ether = Ethernet()
    ether.src = EthAddr(hwsrc)
    ether.dst = EthAddr(hwdst)
    ether.ethertype = EtherType.IP

    ippkt = IPv4()
    ippkt.srcip = IPAddr(ipsrc)
    ippkt.dstip = IPAddr(ipdst)
    ippkt.protocol = IPProtocol.ICMP
    ippkt.ttl = 32

    icmppkt = ICMP()
    if reply:
        icmppkt.icmptype = ICMPType.EchoReply
    else:
        icmppkt.icmptype = ICMPType.EchoRequest

    return ether + ippkt + icmppkt

def switch_tests():
    s = Scenario("switch tests")
    s.add_interface('eth0', '10:00:00:00:00:01')
    s.add_interface('eth1', '10:00:00:00:00:02')
    s.add_interface('eth2', '10:00:00:00:00:03')

    # test case 0: Packet arrives from eth0
    # But is intended for the switch. So should not do anything.
    testpkt = mk_pkt("30:00:00:00:00:01", "10:00:00:00:00:01", "192.168.1.1", "192.168.1.0")
    s.expect(PacketInputEvent("eth0", testpkt, display=Ethernet), "An Ethernet frame from 30:00:00:00:00:01 to 10:00:00:00:00:01 should arrive on eth0")

    # test case 1: Packet arrives from eth0 to an address not learned.
    # Should be flooded out all ports except ingress
    testpkt = mk_pkt("30:00:00:00:00:01", "30:00:00:00:00:02", "192.168.1.1", "192.168.1.2")
    s.expect(PacketInputEvent("eth0", testpkt, display=Ethernet), "An Ethernet frame from 30:00:00:00:00:01 to 30:00:00:00:00:02 should arrive on eth0")
    s.expect(PacketOutputEvent("eth1", testpkt, "eth2", testpkt, display=Ethernet), "The Ethernet frame for 30:00:00:00:00:02 should be flooded out eth1 and eth2")
    
    # test case 2: Packet from address 30:00:00:00:00:01 arrived at eth1
    # There is a change in the port for the addresses
    testpkt = mk_pkt("30:00:00:00:00:01", "30:00:00:00:00:02", "192.168.1.1", "192.168.1.2")
    s.expect(PacketInputEvent("eth1", testpkt, display=Ethernet), "An Ethernet frame from 30:00:00:00:00:01 to 30:00:00:00:00:02 should arrive on eth1")
    s.expect(PacketOutputEvent("eth0", testpkt, "eth2", testpkt, display=Ethernet), "The Ethernet frame for 30:00:00:00:00:02 should be flooded out eth0 and eth2")

    # test case 2: Packet from address 30:00:00:00:00:02 arrived at eth2
    # The address and port for destination is known and will be sent out port eth1
    testpkt = mk_pkt("30:00:00:00:00:02", "30:00:00:00:00:01", "192.168.1.2", "192.168.1.1")
    s.expect(PacketInputEvent("eth2", testpkt, display=Ethernet), "An Ethernet frame from 30:00:00:00:00:02 to 30:00:00:00:00:01 should arrive on eth2") 
    s.expect(PacketOutputEvent("eth1", testpkt, display=Ethernet), "An Ethernet frame from 30:00:00:00:00:02 to 30:00:00:00:00:01 should be sent out eth1") 

    # test case 3: Learn 0
    # The address and port of destination is known and will be sent out port eth2
    testpkt = mk_pkt("30:00:00:00:00:00", "30:00:00:00:00:02", "192.168.1.0", "192.168.1.2")
    s.expect(PacketInputEvent("eth0", testpkt, display=Ethernet), "An Ethernet frame from 30:00:00:00:00:00 to 30:00:00:00:00:02 should arrive on eth0") 
    s.expect(PacketOutputEvent("eth2", testpkt, display=Ethernet), "An Ethernet frame from 30:00:00:00:00:00 to 30:00:00:00:00:02 should be sent out eth2") 

    # test case 4: Learn a new source address for eth1
    # The address and port of destination is known and will be sent out port eth0
    testpkt = mk_pkt("30:00:00:00:00:03", "30:00:00:00:00:00", "192.168.1.3", "192.168.1.0")
    s.expect(PacketInputEvent("eth1", testpkt, display=Ethernet), "An Ethernet frame from 30:00:00:00:00:03 to 30:00:00:00:00:00 should arrive on eth1") 
    s.expect(PacketOutputEvent("eth0", testpkt, display=Ethernet), "An Ethernet frame from 30:00:00:00:00:03 to 30:00:00:00:00:00 should be sent out eth0")

    # test case 5: Learn a new source address for eth2
    # The address and port of destination is known and will be sent out port eth1
    testpkt = mk_pkt("30:00:00:00:00:04", "30:00:00:00:00:03", "192.168.1.4", "192.168.1.3")
    s.expect(PacketInputEvent("eth2", testpkt, display=Ethernet), "An Ethernet frame from 30:00:00:00:00:04 to 30:00:00:00:00:03 should arrive on eth2") 
    s.expect(PacketOutputEvent("eth1", testpkt, display=Ethernet), "An Ethernet frame from 30:00:00:00:00:04 to 30:00:00:00:00:03 should be sent out eth1")

    # test case 6: Learn a new source address for eth0
    # The address and port of destination is known and will be sent out port eth1
    testpkt = mk_pkt("30:00:00:00:00:05", "30:00:00:00:00:04", "192.168.1.5", "192.168.1.4")
    s.expect(PacketInputEvent("eth0", testpkt, display=Ethernet), "An Ethernet frame from 30:00:00:00:00:05 to 30:00:00:00:00:04 should arrive on eth0") 
    s.expect(PacketOutputEvent("eth2", testpkt, display=Ethernet), "An Ethernet frame from 30:00:00:00:00:05 to 30:00:00:00:00:04 should be sent out eth2")

    # test case 7: Forgot the eth1 entry for 30:00:00:00:00:01
    # Should floor all except ingress
    testpkt = mk_pkt("30:00:00:00:00:04", "30:00:00:00:00:01", "192.168.1.4", "192.168.1.1")
    s.expect(PacketInputEvent("eth2", testpkt, display=Ethernet), "An Ethernet frame from 30:00:00:00:00:04 to 30:00:00:00:00:01 should arrive on eth2") 
    s.expect(PacketOutputEvent("eth0", testpkt, "eth1", testpkt, display=Ethernet), "The Ethernet frame for 00:00:00:00:00:01 should be flooded out eth0 and eth1")
    return s

scenario = switch_tests()
