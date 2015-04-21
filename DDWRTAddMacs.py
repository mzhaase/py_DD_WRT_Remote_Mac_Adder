'''Copyright 2014 Mattis Haase

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.'''

import getpass
import os
import re
import sys
import time
from socket import error as socket_error

import paramiko
from paramiko.ssh_exception import SSHException, BadHostKeyException,\
    AuthenticationException

#https://github.com/jbardin/scp.py/blob/master/README.md
from scp import SCPClient
from piston_mini_client.failhandlers import SocketError

installpath = os.path.abspath(os.path.dirname(sys.argv[0]))
status = []

class AllowAllKeys(paramiko.MissingHostKeyPolicy):
    def missing_host_key(self, client, hostname, key):
        return
    
class bcolors:
    ''' Does not work under Windows
    HEADER  = '\033[95m' #pink?
    OKBLUE  = '\033[94m'
    OKGREEN = '\033[92m' #green
    WARNING = '\033[93m' # yellow
    FAIL    = '\033[91m'#red
    ENDC    = '\033[0m' '''

    HEADER  = ''
    OKBLUE  = ''
    OKGREEN = ''
    WARNING = '' 
    FAIL    = ''
    ENDC    = ''
    
def parseConfig():
    '''Parses the two config files ./accessPoints.txt and ./macs.txt with regex
    both files can be freely formatted
    
    Output: list of mac addresses and ip adddresses'''
    
    reMac       = re.compile(r'[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:'\
                        '[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}', re.IGNORECASE)
    reIP        = re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')
    
    macString   = ''
    apString    = ''
    
    macs        = ''
    aps         = ''
    
    with open('accessPoints.txt', 'r') as f:
        for line in f:
            apString += line
    
    with open('macs.txt', 'r') as f:
        for line in f:
            macString += line
            
    macs    = re.findall(reMac, macString)
    aps     = re.findall(reIP, apString)
    
    return macs, aps

def statusChange(status):
    '''Prints everything on screen, is called for every update.
    
    Input: list of dictionaries: 
    status = [{'ip':127.0.0.1, 'status':'pending'}, ...]
    
    Output: void'''
    
    string = ''
    
    for element in status:
        string += element['ip'] + ' ' + element['status'] + '\n'
        
    os.system("cls")

    ''' print chr(27) + "[2J"  Does not work under windows '''

    sys.stdout.write(string)
    sys.stdout.flush()
    
def statusChangeOneIP(ip, newStatus):
    '''Changes global variable status, searches for IP and replaces current
    status of match with new one.
    
    Input:  ip: ip address to be searched, string
            newStatus: the new status, string
    
    Output: void'''
    
    global status
    for index, element in enumerate(status):
        if element['ip'] == ip:
            status[index]['status'] = newStatus
    statusChange(status)
    
def addMacs(user, passwd, ip):
    '''Connects to DD-WRT router with ip address ip over ssh. Then SCPs the
    maclist into the DD-WRT /root/ directory. Feeds this file into a Shell-
    Variable, then updates the mac filterlist and commits the config.
    
    Input:      user: username, string
                passwd: password, string
                ip:    ip address to connect to, string
    
    Output: void'''
    
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(AllowAllKeys())
    
    try:
        statusChangeOneIP(ip, bcolors.OKBLUE + 'connecting' + bcolors.ENDC)
        client.connect(ip, username=user, password=passwd)
    except BadHostKeyException:
        statusChangeOneIP(ip, bcolors.FAIL + 'Host Key Exception' +\
                            bcolors.ENDC)
        client.close()
        return
    except AuthenticationException:
        user = raw_input('Authentication Exception, username: ')
        passwd = getpass.getpass('Password: ')
        addMacs(user, passwd, ip, macs)
    except SSHException:
        statusChangeOneIP(ip, bcolors.FAIL + 'SSH Exception' + bcolors.ENDC)
        client.close()
        return
    except socket_error:
        statusChangeOneIP(ip, bcolors.FAIL + 'cannot reach device' +\
                            bcolors.ENDC)
        client.close()
        return
        
    statusChangeOneIP(ip, bcolors.OKBLUE + 'connected' + bcolors.ENDC)
    try:
        scp = SCPClient(client.get_transport())
        
        '''Copy the parse mac addresses over to /root/, wait a second to make
        sure transfer is complete, then set the _maclist variables on the router
        and commit changes'''
        
        scp.put(installpath + '/macsParsed.txt', 'macs.txt')
        time.sleep(1)
        client.exec_command('nvram set ath0_maclist="$(cat macs.txt)" && '\
                    'nvram set wl0_maclist="$(cat macs.txt)" && nvram commit')
        
        statusChangeOneIP(ip, bcolors.OKGREEN + 'changes committed' +\
                            bcolors.ENDC)
        #print('Changes commited')
    except SSHException:
        statusChangeOneIP(ip, bcolors.FAIL + 'SSH Exception' + bcolors.ENDC)
        client.close()
        return
    client.close()

def restart(user, passwd, ip):
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(AllowAllKeys())

    try:
        statusChangeOneIP(ip, bcolors.OKBLUE + 'connecting' + bcolors.ENDC)
        client.connect(ip, username=user, password=passwd)
    except BadHostKeyException:
        statusChangeOneIP(ip, bcolors.FAIL + 'Host Key Exception' +\
                            bcolors.ENDC)
        client.close()
        return
    except AuthenticationException:
        user = raw_input('Authentication Exception, username: ')
        passwd = getpass.getpass('Password: ')
        addMacs(user, passwd, ip, macs)
    except SSHException:
        statusChangeOneIP(ip, bcolors.FAIL + 'SSH Exception' + bcolors.ENDC)
        client.close()
        return
    except socket_error:
        statusChangeOneIP(ip, bcolors.FAIL + 'cannot reach device' +\
                            bcolors.ENDC)
        client.close()
        return
    
    try:
        '''restart the boxes'''
        
        client.exec_command('nrc restart')
        time.sleep(0.5)
        statusChangeOneIP(ip, bcolors.OKGREEN + 'radio restarted' +\
                            bcolors.ENDC)
        #print('Changes commited')
    except SSHException:
        statusChangeOneIP(ip, bcolors.FAIL + 'SSH Exception' + bcolors.ENDC)
        client.close()
        return
    client.close()
    
def start(user, passwd, aps):
    for ip in aps:
        addMacs(user, passwd, ip)
    for ip in aps:
        restart(user, passwd, ip)        
    input('Press Enter to exit')
    
macs, aps = parseConfig()

with open('macsParsed.txt', 'w') as f:
    for mac in macs:
        f.write(mac + ' ')
        
user = raw_input("Username: ")
password = getpass.getpass("Password: ")

if user and password:
    for ip in aps:
        status.append({'ip': ip, 'status': 'waiting'})
    statusChange(status)
    start(user, password, aps)
