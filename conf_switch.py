#!/usr/bin/env python3
from pysnmp.hlapi import getCmd, SnmpEngine, CommunityData, UdpTransportTarget
from pysnmp.hlapi import ContextData, ObjectType, ObjectIdentity
from time import sleep
#from settings import COMMUNITY, SNMP_PORT, SWITCH_USERNAME, SWITCH_PASSWORD
import argparse
import socket
import sys
import telnetlib

COMMUNITY = 'community'
SNMP_PORT = 161
SWITCH_USERNAME = 'username'
SWITCH_PASSWORD = 'password'
MODEL_NAME = '.1.3.6.1.2.1.1.1.0'
PVID = '1.3.6.1.2.1.17.7.1.4.5.1.1.'

parser = argparse.ArgumentParser(
    description='python conf_switch.py 10.128.141.88 10 -u 123 -t 1800 1850')
parser.add_argument('ip', nargs='?', default='10.128.141.88', type=str)
parser.add_argument('port', type=int)
parser.add_argument('-u', '--untagged', nargs=1, type=int)
parser.add_argument('-t', '--tagged', nargs='+', type=int)
args = parser.parse_args(sys.argv[1:])

ip       = args.ip
port     = str(args.port)
untagged = str(args.untagged[0]) if args.untagged else None
tagged   = [str(item) for item in args.tagged] if args.tagged else None


def prepare_commands(ip='0.0.0.0', port='0', untagged=None, tagged=None) -> list:
    commands = []

    if untagged:
        existed_vlan = port_vid(ip, port)
        if existed_vlan:
            del_vlan = f'config vlan vlanid {existed_vlan} delete {port}\n'
            commands.insert(0, del_vlan)
        add_vlan = f'config vlan vlanid {untagged} add untagged {port}\n'
        commands.append(add_vlan)
    
    if tagged:
        for vid in tagged:
            add_tagged = f'config vlan vlanid {vid} add tagged {port}\n'
            commands.append(add_tagged)

    return commands


def snmp_getcmd(community, ip, port, OID):
    return getCmd(SnmpEngine(),
                  CommunityData(COMMUNITY),
                  UdpTransportTarget((ip, port), timeout=0.5, retries=0),
                  ContextData(),
                  ObjectType(ObjectIdentity(OID)))


def snmp_get(*args):  # args = [community, ip, port, OID]
    errorIndication, errorStatus, errorIndex, varBinds = next(snmp_getcmd(*args))
    if errorIndication:
        return {'error': errorIndication}
    oid, val = varBinds[0]
    return {'reply': val.prettyPrint()}


def snmp_reachable(ip, port):
    switch_model = snmp_get(COMMUNITY, ip, SNMP_PORT, MODEL_NAME)
    if switch_model.get('reply'):
        return True
    else:
        return False


def port_vid(ip, port):
    if snmp_reachable(ip, port):
        pvid = snmp_get(COMMUNITY, ip, SNMP_PORT, (PVID + port))
        if pvid and not pvid == '1':
            reply = pvid.get('reply')
        else:
            reply = False
    else:
        print('No SNMP response received before timeout')
        reply = False
    return reply


def telnet(ip, commands):
    username = f'{SWITCH_USERNAME}\n'.encode('ascii')
    password = f'{SWITCH_PASSWORD}\n'.encode('ascii')

    try:
        telnet = telnetlib.Telnet(ip, timeout=1)
    except socket.timeout:
        return 'host unreachable'
    sleep(0.2)
    telnet.read_very_eager()
    telnet.write(username)
    sleep(0.2)
    telnet.write(password)
    sleep(0.2)
    for command in commands:
        telnet.write(command.encode('utf-8'))
        sleep(0.2)

    skip_current_string = telnet.read_very_eager()
    output = telnet.read_until(b'#', timeout=5)
    output = output.decode('utf-8').split('\n')
    output = output[3:15]
    output = '\n'.join(output)
    return output


if __name__ == '__main__':
    commands = prepare_commands(ip=ip, port=port, untagged=untagged, tagged=tagged)
    telnet(ip, commands)
