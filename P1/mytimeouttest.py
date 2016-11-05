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
    testpkt = mk_pkt("30:00:00:00:00:00", "10:00:00:00:00:01", "192.168.1.0", "192.168.1.1")
    s.expect(PacketInputEvent("eth0", testpkt, display=Ethernet), "An Ethernet frame fomr 30:00:00:00:00:00 to 10:00:00:00:00:01 should arrive on eth0")

    # test case 1: Packet arrives from eth0 to an address not learned.
    # Should be flooded out all ports except ingress
    testpkt = mk_pkt("30:00:00:00:00:00", "30:00:00:00:00:01", "192.168.1.0", "192.168.1.1")
    s.expect(PacketInputEvent("eth0", testpkt, display=Ethernet), "An Ethernet frame fomr 30:00:00:00:00:00 to 30:00:00:00:00:01 should arrive on eth0")
    s.expect(PacketOutputEvent("eth1", testpkt, "eth2", testpkt, display=Ethernet), "The Ethernet frame for 30:00:00:00:00:01 should be flouded out eth1 and eth2")

    # test case 2: Packet from address 30:00:00:00:00:00 arrived at eth1
    # There is a change in the port for the addresses
    testpkt = mk_pkt("30:00:00:00:00:00", "30:00:00:00:00:01", "192.168.1.0", "192.168.1.1")
    s.expect(PacketInputEvent("eth1", testpkt, display=Ethernet), "An Ethernet frame fomr 30:00:00:00:00:00 to 30:00:00:00:00:01 should arrive on eth1")
    s.expect(PacketOutputEvent("eth0", testpkt, "eth2", testpkt, display=Ethernet), "The Ethernet frame for 30:00:00:00:00:01 should be flouded out eth0 and eth2")
 
    
    # timeout for 6 seconds. Nothing should change in the table.
    s.expect(PacketInputTimeoutEvent(6.0), "Time out for 6 seconds")
    
    # test case 3: Packet from address 30:00:00:00:00:01 arrived at eth2
    # The address and port for destination is known and will be sent out port eth1
    testpkt = mk_pkt("30:00:00:00:00:01", "30:00:00:00:00:00", "192.168.1.1", "192.168.1.0")
    s.expect(PacketInputEvent("eth2", testpkt, display=Ethernet), "An Ethernet frame from 30:00:00:00:00:01 should arrive on eth2")
    s.expect(PacketOutputEvent("eth1", testpkt, display=Ethernet), "The Ethernet frame for 30:00:00:00:00:00 should be flouded on eth1")

    # test case 4: a frame from 30:00:00:00:00:02 arriving on eth1 to flood out eth0 and eth2 
    testpkt = mk_pkt("30:00:00:00:00:02", "30:00:00:00:00:15", "192.168.1.2", "192.168.1.15")
    s.expect(PacketInputEvent("eth1", testpkt, display=Ethernet), "An Ethernet frame from 30:00:00:00:00:02 with a broadcast destination address should arrive on eth1")
    s.expect(PacketOutputEvent("eth0", testpkt, "eth2", testpkt, display=Ethernet), "The Ethernet frame with a broadcast destination address should be forward out ports eth0 and eth2")

    # timeout for 6 seconds. eth1 at 30:00:00:00:00:00 should now not be in the list as its timeout period has passed
    s.expect(PacketInputTimeoutEvent(6.0), "Time out for 6 seconds")
    
    # test case 5: a frame from 30:00:00:00:00:02 on eth1 arrived intended for 30:00:00:00:00:00. We had removed the entry for 30:00:00:00:00:00 earlier so flooding through eth0 and eth2 should happen
    testpkt = mk_pkt("30:00:00:00:00:02", "30:00:00:00:00:00", "192.168.1.2", "192.168.1.0")
    s.expect(PacketInputEvent("eth1", testpkt, display=Ethernet), "An Ethernet frame from 30:00:00:00:00:02 should arrive on eth1")
    s.expect(PacketOutputEvent("eth0", testpkt, "eth2", testpkt, display=Ethernet), "The Ethernet frame for 30:00:00:00:00:00 should be flouded on eth0 and eth2")

    # test case 6: a frame from 30:00:00:00:00:00 on eth0 to 30:00:00:00:00:02. This had been learned earlier so sends it through eth1
    testpkt = mk_pkt("30:00:00:00:00:00", "30:00:00:00:00:02", "192.168.1.0", "192.168.1.2")
    s.expect(PacketInputEvent("eth0", testpkt, display=Ethernet), "An Ethernet frame from 30:00:00:00:00:00 should arrive on eth0")
    s.expect(PacketOutputEvent("eth1", testpkt, display=Ethernet), "The Ethernet frame for 30:00:00:00:00:02 should be flouded on eth1")

    return s

scenario = switch_tests()
