
import os
import sys
import time
import socket


if __name__ == "__main__":

    if len(sys.argv) != 4:
        print("Please provide correct arguments")
        exit()

    [node_name, node_ip, node_port] = sys.argv[1:4]

    node = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    node.connect((node_ip, int(node_port)))
    node.send(("%s %s" % (node_name, "start")).encode())
    node.recv(1024)

    counter = 0
    for line in sys.stdin:
        line = line.strip()
        print(counter, node_name, line)
        counter += 1
        node.send(("%s %s" % (node_name, line)).encode())
        node.recv(1024)

    print(node_name,"Send over")
