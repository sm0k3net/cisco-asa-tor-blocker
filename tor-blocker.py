#!/usr/bin/python
## Python version: Python v2.7
## Description: This script may help automate process of removing & adding Tor Exit Nodes IPs to Cisco ASA, 
## also before flushing previous rules it will make backup in text file as well, 
## as create additional text file for new list of IP addresses parsed from official #Tor website.
import sys, os, paramiko, time, re, requests
from html.parser import HTMLParser
from bs4 import BeautifulSoup

## Creating files (old_list = from ASA, new_list = from Tor Project website)
old_list = open('tor_nodes_old.txt', 'w');
new_list = open('tor_nodes_new.txt', 'w');

## Setting user-agent
headers = {
        'User-Agent': 'Mozilla/5.1 (Macintosh; Intel Mac OS X 10.9; rv:43.0) Gecko/20100101 Firefox/43.0'
      }

## Parsing list of TOR exit nodes
page = 'https://check.torproject.org/cgi-bin/TorBulkExitList.py?ip=1.1.1.1&port=80'
r = requests.get(page, headers = headers)
data = BeautifulSoup(r.text, "lxml")
raw = ''.join(data.find(text=True))
exitNode_pattern = re.compile(r'(\d+\.\d+\.\d+\.\d+)')
parsed = []
for exitNode in re.findall(exitNode_pattern, str(raw)):
	if exitNode != '1.1.1.1':
		parsed += exitNode.split(',')
new_list.write(str(parsed))

## SSH Connection Debug (uncomment if required)
#paramiko.util.log_to_file("ssh_conn.log")

## Communicating with Cisco ASA
login_password = "YOUR_PASSWORD"
ssh_client = paramiko.SSHClient()
print ('client created')
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
print ('key policy set')
ssh_client.connect(hostname='192.168.1.1', username='YOUR_USERNAME', password=login_password, port=22)
print ('client connected')
remote_conn = ssh_client.invoke_shell()
output = remote_conn.recv(65535)
print output

remote_conn.send('enable\n')
time.sleep(2)
remote_conn.send(login_password + '\n')
time.sleep(2)
output = remote_conn.recv(65535)

remote_conn.send('sh run object-group id TorNodes-Block\n')
for expand in range(100):
	remote_conn.send(' ')
time.sleep(2)
ip_output = remote_conn.recv(65535)
cisco_pattern = re.compile(r'(\d+\.\d+\.\d+\.\d+)')
ciscoIP = []
for item in re.findall(cisco_pattern, str(ip_output)):
	if item != '99.99.99.99':
		ciscoIP += item.split(',')
old_list.write(str(ciscoIP))

## Removing old IPs
remote_conn.send('conf t\n')
time.sleep(2)
remote_conn.send('object-group network TorNodes-Block\n')
time.sleep(2)
for ipAddr in ciscoIP:
	remote_conn.send('no network-object host '+ipAddr+'\n')
	time.sleep(1)
remote_conn.send('exit\n')
time.sleep(2)
remote_conn.send('exit\n')
time.sleep(2)
remote_conn.send('wr mem\n')
time.sleep(2)
ip_removing = remote_conn.recv(65535)
print ip_removing

## Adding new IP addresses
remote_conn.send('conf t\n')
time.sleep(2)
remote_conn.send('object-group network TorNodes-Block\n')
time.sleep(2)
for torIP in parsed:
	remote_conn.send('network-object host '+torIP+'\n')
	time.sleep(1)
remote_conn.send('exit\n')
time.sleep(2)
remote_conn.send('exit\n')
time.sleep(2)
remote_conn.send('wr mem\n')
time.sleep(2)
ip_adding = remote_conn.recv(65535)
print ip_adding
