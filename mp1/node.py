import socket
import sys
import time
import threading
import csv
# from openpyxl import load_workbook

SCENARIO_NUM = 1
METRICTABLE_PATH = f"./metrics/scenario{SCENARIO_NUM}/testtable"

########
# class
########
# queue element is [msg_content,msg_id,final_priority,deliverable,ackmessage requestor, [[turn,suggestor],[turn,suggestor]]]
class hold_queue:
    def __init__(self):
        self.queue = []
   
    def displayqueue(self):
        print("#######   queue start  ########")
        for i in range(0,len(self.queue)):
            print (self.queue[i])
        print("#######    queue end   ########")
    
    def displayfirst(self):
        if (len(self.queue) == 0):
            return
        if (len(self.queue) <=10000):
            print("#######   fisrt element and length ########")
            # print (len(self.queue))
            print (self.queue[0],len(self.queue))
            print("#######    end   ########")
    
    def queue_append(self,datalist):
        self.queue.append(datalist)
    
    def queue_find_index(self,msg_id):
        index = -1
        for i in range(len(self.queue)):      
            if (self.queue[i])[1] == msg_id:
                index = i
        return index

    def queue_update_element(self,index,final_priority,deliverable,suggestor):
        self.queue[index][2] = final_priority
        self.queue[index][3] = deliverable
        self.queue[index][4] = suggestor

    def sort_queue(self):
        self.queue.sort(key=lambda x:(x[2], x[3], x[4]))
        # smaller final_priority will be at the head
        # smaller deliverable will be at the head， undiliverable will be at the head
        # smaller suggestor will be at the head
        # notice that!!: (105,0,5) is before (105,1,1)
    def queue_len(self):
        return len(self.queue)
        
    def feedbacklist_append(self, index, proposed_info):
        (self.queue[index][5]).append(proposed_info)
        
    def feedbacklist_check(self, index):
        return len(self.queue[index][5])

    def feedbacklist_sort(self, index):
        (self.queue[index][5]).sort(key=lambda x:(-x[0],x[1]))
        # (504,1) is before (504,7)

    def feedbacklist_agreed_priority(self,index):
        return self.queue[index][5][0][0]
    
    def feedbacklist_suggested_id(self,index):
        return self.queue[index][5][0][1]
    
    def check_and_remove(self):
        global deliver_turn
        while (len(self.queue) > 0 and self.queue[0][3] == DELIVERABLE):

            popdata = self.queue[0]
            msg_id = popdata[1]
            self.queue.remove(self.queue[0])
            # print('{0}. deliver:{1}'.format(deliver_turn,popdata))

            handle_transaction(popdata[0])
            record_endprocess_time(msg_id)
            deliver_turn+=1
        # queue.displayfirst()

    def handle_failure(self,new_node_num):
        # print("start to handle!!!!!")
        for index in range(0,queue.queue_len()):
            msg_id = self.queue[index][1]
            if (self.feedbacklist_check(index) >= new_node_num + 1):

                typemid2 = "decided"+"|" + msg_id
                seen_lock.acquire()
                seen_typemid.append(typemid2)
                seen_lock.release()
                
                # multicast decide message
                self.feedbacklist_sort(index)
                agreed_priority = self.feedbacklist_agreed_priority(index)
                suggested_id = self.feedbacklist_suggested_id(index)
                decidedmessage = decidedMessage(msg_id,str(agreed_priority), str(suggested_id), node_id)
                multicast_message(decidedmessage)

                # update queue value
                self.queue_update_element(index,agreed_priority,DELIVERABLE,suggested_id)
                
        # self.displayqueue()
                



###########
# variable
###########

deliver_turn = 0
node_name = ""
node_num = 0
node_id = ""
node_port = 0

# node_id : value
other_node_ip = dict()    
other_node_port = dict()
send_conn = dict()

# the member of receive_conn : is_prepared
receive_prepared = dict()

receive_conn = []
seen_typemid = []


queue = hold_queue()
turn = 0 # Lamport Timestamp
si = 0  #  isis timestamp
terminate = 0

# lock
seen_lock = threading.Lock()
queue_lock = threading.Lock()
turn_lock = threading.Lock()
si_lock = threading.Lock()
time_table_lock = threading.Lock()
receive_conn_lock = threading.Lock()
send_conn_lock = threading.Lock()
node_num_lock = threading.Lock()

DELIVERABLE = 1
UNDELIVERABLE = 0


################
#### Transaction Related
################

# Account : Balance
bank = dict()


###################
# message function
###################
def askMessage(msg_id,message_content, default_priority, msg_sender):
    string = "ask"+"|" +  msg_id  + "|" + message_content + "|" + default_priority +"|"+ msg_sender+"|" + str(time.time()) + "|"
    return string.ljust(128," ")

def feedbackMessage(msg_id, proposed_priority, suggestor, msg_sender):
    string = "feedback"+"|"+ msg_id + "|" + proposed_priority+ "|" + suggestor +"|"+ msg_sender+"|" + str(time.time()) + "|"
    return string.ljust(128," ")

def decidedMessage(msg_id, agreed_priority, suggested_id, msg_sender):
    string = "decided"+"|"+msg_id+"|"+ agreed_priority+"|"+suggested_id + "|" + msg_sender+"|" + str(time.time()) + "|"
    return string.ljust(128," ")


##########
# readtxt
##########
def readtxt(filename):
    global other_node_ip
    global other_node_port
    global node_num
    f = open(filename, 'r', encoding='utf-8')
    for line in f:
        data_line = line.strip("\n").split()
        if len(data_line) == 1:
            node_num = int(data_line[0])
        else:
            other_node_id = (data_line[0])[4]
            ip = data_line[1]
            port = int(data_line[2])

            other_node_ip[other_node_id] = ip
            other_node_port[other_node_id] = port
    return 


#################
# establish_send
#################
def establish_send(node_id, ip, port):
    global node_name
    global node_num
    global send_conn

    # Keep connecting until all connections are set
    send_conn_lock.acquire()
    while (len(send_conn) != node_num):
        # i is id of other nodes
        try:
            con = socket.socket()
            con.connect((ip, port))
            send_conn[node_id] = con
            break
        except:
            continue
    send_conn_lock.release()
    print(f"#1 {node_name} send connection established")
    return


###########################
# receive_message_thread
###########################
def receive_message(receive_conn_member):
    global queue
    global node_id
    global turn
    global node_num
    global receive_conn
    global receive_prepared
    global seen_typemid
    global si

    con = receive_conn_member
    othernode_fail = 0
    while (terminate == 0):
        # Receive message
        receive_prepared [receive_conn_member] = 1
        data = con.recv(128).decode('utf-8')
        if not data:
            othernode_fail = 1
            break
        if (len(data) != 128):
            data += con.recv(128).decode('utf-8')

        datalist = data.split("|")

        # Shared data for all messages
        msg_type = datalist[0]
        msg_id = datalist[1]
        typemid = msg_type + "|" + msg_id

        get_metrics(data)


        if (msg_type == "feedback"):
            typemid = typemid + "|feebacker:" + datalist[3]

        # judge if it is in the seen list
        seen_lock.acquire()
        if (typemid in seen_typemid):
            seen_lock.release()   # fuck it!
            continue
        
        # update seen msg list when receive
        seen_typemid.append(typemid)
        need_multicast = 1
        seen_lock.release()

        if (msg_type == "ask"):
            msg_content = datalist[2]
            original_priority = int(datalist[3])

            
            # update queue
            # [content,msg_id,final_priority,deliverable,suggestor,[]]
            queue_lock.acquire()
            queue.queue_append([msg_content,msg_id,original_priority,UNDELIVERABLE,int(msg_id[0]),[]])
            queue.sort_queue()
            queue_lock.release()

            # add the my_turn
            si_lock.acquire()
            si += 1
            cur_si = si
            si_lock.release()

            # update seen msg list when send
            typemid1 = "feedback" + "|" + msg_id + "|feebacker:" + node_id
            seen_lock.acquire()
            seen_typemid.append(typemid1)
            seen_lock.release()

            # send feedback message
            # the first node_id means propose node, the second node_id means the msg_sender
            feedbackmessage = feedbackMessage(msg_id,str(cur_si), node_id, node_id)
            multicast_message(feedbackmessage)

            if (need_multicast == 1):
                askmessage = askMessage(msg_id,msg_content, str(original_priority), node_id)
                multicast_message(askmessage)


        if (msg_type == "feedback"):

            proposed_priority = int(datalist[2])
            suggestor = int(datalist[3])

            if (msg_id[0] == node_id):

                # update queue
                # [content,mid,final_priority,deliverable,sender,[]]
                queue_lock.acquire()
                index = queue.queue_find_index(msg_id)
                if index == -1: 
                    queue_lock.release()
                    continue
                queue.feedbacklist_append(index, [proposed_priority,suggestor])
                
                # When all receive feedback from all other nodes
                if (queue.feedbacklist_check(index) >= node_num + 1):
                   
                    # update seen_typemid when send
                    typemid2 = "decided"+"|" + msg_id
                    seen_lock.acquire()
                    seen_typemid.append(typemid2)
                    seen_lock.release()

                    # multicast decide message
                    queue.feedbacklist_sort(index)
                    agreed_priority = queue.feedbacklist_agreed_priority(index)
                    suggested_id = queue.feedbacklist_suggested_id(index)
                    decidedmessage = decidedMessage(msg_id,str(agreed_priority), str(suggested_id), node_id)
                    multicast_message(decidedmessage)

                    # update queue value
                    queue.queue_update_element(index,agreed_priority,DELIVERABLE ,suggested_id)
                    queue.sort_queue()
                    queue.check_and_remove()

                queue_lock.release()

            if (need_multicast == 1):
                feedbackmessage = feedbackMessage(msg_id, str(proposed_priority), str(suggestor), node_id)
                multicast_message(feedbackmessage)



        if (msg_type == "decided"):
                
            sk = int(datalist[2])
            suggestor_id = int(datalist[3])

            si_lock.acquire()
            temp = si
            si = max([temp,sk])
            si_lock.release()

            # update priority and suggested_id
            queue_lock.acquire()
            index = queue.queue_find_index(msg_id)
            if (index == -1):
                queue_lock.release()
                continue
            queue.queue_update_element(index,sk,DELIVERABLE,suggestor_id)
            queue.sort_queue()
            queue.check_and_remove()
            queue_lock.release()

            if (need_multicast == 1):
                decidedmessage = decidedMessage(msg_id, str(sk), str(suggestor_id), node_id)
                multicast_message(decidedmessage)

    
    if (othernode_fail == 1):
        receive_conn_lock.acquire()
        receive_conn.remove(con)
        receive_conn_lock.release()
        print ("one node fail")
        node_num_lock.acquire()
        node_num = node_num - 1
        queue_lock.acquire()
        queue.handle_failure(node_num)
        queue_lock.release()
        node_num_lock.release()
    else:
        receive_conn_lock.acquire()
        receive_conn.remove(con)
        receive_conn_lock.release()

    # close
    con.close()


    return

            
        
    
    
###########################
# send_message thread
############################

def multicast_message(msg_content):
    global send_conn
    global queue
    global node_num
    
    delete_send_conn = []
    send_conn_lock.acquire()
    for key in send_conn:
        try:
            (send_conn[key]).send("{0}".format(msg_content).encode("utf-8"))
        except:
            delete_send_conn.append(key)
            continue
    for i in delete_send_conn:
        send_conn.pop(i)

    send_conn_lock.release()



def handle_transaction(msg_content):
    global bank

    if "DEPOSIT" in msg_content:
        account, amount = msg_content.split(' ')[1], int(msg_content.split(' ')[2])
        if account not in bank:
            bank[account] = 0
        bank[account] += amount

    if "TRANSFER" in msg_content:
        account, dest, amount = msg_content.split(' ')[1], msg_content.split(' ')[3], int(msg_content.split(' ')[4])
        if account not in bank:
            print("Error!, Account not in Bank!")
            exit(1)
        if dest not in bank:
            bank[dest] = 0

        # Do Transaction
        if bank[account] - amount >= 0:
            bank[account] -= amount
            bank[dest] += amount

    # Print balance information
    balance_info = ""
    sorted_accounts = list(bank.keys())
    sorted_accounts.sort()
    for account in sorted_accounts:
        balance_info += " " + account + ":" + str(bank[account])
    print("BALANCES" + balance_info ) 


    return

def get_metrics(data):

    datalist = data.split("|")
    msg_sender = int(datalist[4])
    msg_send_time = float(datalist[5])

    # Bandwidth
    delay = time.time() - msg_send_time
    if (delay == 0):
        time.sleep(0.0000001)
        delay = time.time() - msg_send_time
    bandwidth = len(data.encode('utf-8')) / delay

    metricfile_name = f"{METRICTABLE_PATH}/bandwidth_node{msg_sender}.csv"
    metricfile = open(metricfile_name, 'a')
    metricfile.write(f"{data},{str(bandwidth)}\n")
    metricfile.close()
    
    return

def record_startprocess_time(msg_id):
    
    f = open(f'{METRICTABLE_PATH}/time.log','a')
    f.write(f"{msg_id},start_time,{time.time()}\n")
    f.close()

    return

def record_endprocess_time(msg_id):

    f = open(f'{METRICTABLE_PATH}/time.log', 'a')
    f.write(f"{msg_id},node{node_id}_end_time,{time.time()}\n")
    f.close()

    return
#######
# main
#######
def main():
    # Node Information
    global node_name
    global node_id
    global node_port
    global node_num 
    global other_node_ip

    # Connection Information
    global send_conn
    global receive_conn
    global receive_prepared

    global turn
    global queue
    global terminate
    global seen_typemid


    if len(sys.argv) != 4:
        print("invalid input")
        return -1
    

    # Node Basic Info
    node_name = sys.argv[1]
    node_port = int(sys.argv[2])
    readtxt(sys.argv[3])
    node_id = node_name[4:]

    # Write bandwidth metric header
    metricfile_name = f"{METRICTABLE_PATH}/bandwidth_{node_name}.csv"
    metricfile = open(metricfile_name, 'w')
    metricfile.write("data, bandwidth\n")
    metricfile.close()

    print(f"#1 {node_name} is waiting for connection")

    # establish send connection (set send_conn)
    for i in other_node_ip.keys():
        send_conn_thread = threading.Thread(target=establish_send, args=(i, other_node_ip[i], other_node_port[i]))
        send_conn_thread.start()
    
    # establish the receive socket
    node = socket.socket()
    node.bind(('127.0.0.1', node_port))
    node.listen(20)
    while (len(receive_conn) != node_num):
        conn,addr = node.accept()
        receive_conn.append(conn)
        receive_prepared[conn] = 1

    print(f"#1 {node_name} receive connection established")
    # wait until send connection established already
    while (len(send_conn) != node_num or len(receive_conn) != node_num):
        continue
    #####
    # Connection is done
    #####

    # tackles message receive from each other node
    for receive_conn_member in receive_conn:
        receive_thread = threading.Thread(target=receive_message, args=(receive_conn_member,))
        receive_thread.start()

    # wait until receive thread prepared already
    while True:
        sum = 0
        for receive_conn_member in receive_conn:
            sum = sum + receive_prepared[receive_conn_member]
        if (sum == node_num):
            break
    

    # send message
    try:
        while(True):
            for row in sys.stdin:
                msg_content = row.strip('\n')

                # update turn, store cur_turn
                turn_lock.acquire()
                turn += 1
                cur_turn = turn
                turn_lock.release()

                # message id example: "1 520", which means node1, turn 520
                msg_id = node_id + " " + str(cur_turn)

                # update seen_typemid when send
                # Msg Type | node_id lamport timestamp
                typemid = "ask" + "|" + msg_id
                seen_lock.acquire()
                seen_typemid.append(typemid)
                seen_lock.release()


                # update queue
                queue_lock.acquire()
                queue.queue_append([msg_content,msg_id,cur_turn,UNDELIVERABLE,int(node_id),[]])
                queue.feedbacklist_append(queue.queue_find_index(msg_id), [cur_turn,int(node_id)])
                queue.sort_queue()
                queue_lock.release()

                # Record start time
                time_table_lock.acquire()
                record_startprocess_time(msg_id)
                time_table_lock.release()

                # prepare the message and start the send thread
                askmessage = askMessage( msg_id, msg_content, str(cur_turn),node_id)
                multicast_message(askmessage)
    except:
        terminate = 1
        while (len(receive_conn) != 0):
            # print (len(receive_conn))
            continue
        print(f"I {node_id} fail")
        # print("aquire 1")
        queue_lock.acquire()
        print("get 1")
        for i in range(0, node_num):
            queue.handle_failure(i)
        queue_lock.release()
        # print("release 1")
    



if __name__ == '__main__':
        main()

        

