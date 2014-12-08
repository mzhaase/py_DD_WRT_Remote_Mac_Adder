This program remotely sets the wifi mac filterlists of multiple DD-WRT routers.

Prerequisites:

paramiko
paramikoSCP from https://github.com/jbardin/scp.py/blob/master/README.md

Usage:

Put list of IP-addresses into accessPoints.txt. Formatting doesnt matter.
Put list of Mac-addresses into mac.txt. Formatting doesnt matter.

Execute script. Mac filterlist of the router is replaced with macs in macs.txt.

Copyright 2014 Mattis Haase
