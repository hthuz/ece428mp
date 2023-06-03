
import sys
import socket
import time
import threading




node_dic = {}
if len(sys.argv) != 3:
    print("Argument as follows: python logger.py logfile metricfile")
    exit()
logfile_name = sys.argv[1]
metricfile_name = sys.argv[2]
# logfile_name = './logger.log' 
# metricfile_name = './metric.csv'

def handle_node(connection,addr):
    while True:
        data = connection.recv(1024).decode()
        connection.send("ack".encode())
        # print(data)
        logfile = open(logfile_name,'a')

        # Start connect node
        if "start" in data:
            node_name = data.split(' ')[0]
            node_dic[threading.get_ident()] = node_name
            # print("%s - %s connected" % (time.time(),node_name))
            logfile.write(("%s - %s connected" % (time.time(),node_name)) + "\n")
            logfile.close()
            continue

        # End connect node
        if not data:
            # print("%s - %s disconected" % (time.time(),node_dic[connection]))
            logfile.write(("%s - %s disconected" % (time.time(),node_dic[threading.get_ident()])) + "\n")
            logfile.close()
            break

        # Message
        [node_name, generate_time, msg] = data.split(' ')[0:3]



        # Get metric and log 
        connect_time = time.time()
        delay = connect_time - float(generate_time)
        bandwidth = len(msg.encode('utf-8')) / delay
            
        metricfile = open(metricfile_name,'a')
        metricfile.write(("%s,%s,%s" % (node_name,delay,bandwidth) + "\n"))
        metricfile.close()

        # print( ("%s %s" % (connect_time, node_name)) )
        # print(msg)
          
        logfile.write( ("%s %s" % (connect_time, node_name)) + "\n" )
        logfile.write(msg + "\n")
        logfile.close()

if __name__ == "__main__":
    
    # IPV4 and TCP protocol
    logger = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    logger_ip = '127.0.0.1'
    logger_port = 1234
    logger.bind((logger_ip,logger_port))
    logger.listen(5)

    while True:
        connection,addr = logger.accept()
        node_thread = threading.Thread(target = handle_node,args=(connection,addr))
        node_thread.start()


