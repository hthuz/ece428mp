
import sys
import time
import threading

hbinterval = 0.01

class Node:
    def  __init__(self,nodeid,num):
        self.id = nodeid
        self.num = num
        self.timeout = (nodeid + 1) * 0.2
        self.term = 1
        self.state = "FOLLOWER"
        self.leader = None
        self.log = [[None,None]]
        self.logindex = 0
        self.commitIndex = 0
        # Candidate
        self.votenum = 0
        # Follower
        self.votedfor = 0
        self.lasttime = time.time()
        # Leader
        self.replica_num = [None]
        return
    
nodelock = threading.Lock()

def check_timeout(node):
    # Start election
    while True:
        if node.state == "FOLLOWER":
            if time.time() - node.lasttime >= node.timeout:
                debug(f"Check timeout, {time.time()},{node.lasttime}, {time.time() - node.lasttime}",flush=True)
                node.term += 1
                node.votenum = 1
                node.state = "CANDIDATE"

                print(f"STATE state=\"{node.state}\"",flush=True)
                print(f"STATE term={node.term}",flush=True)
                debug(f"STATE state=\"{node.state}\"",flush=True)
                debug(f"STATE term={node.term}",flush=True)
                for nodeid in range(node.num):
                    if nodeid == node.id: continue
                    print(f"SEND {nodeid} RequestVotes {node.term}",flush=True)
                    debug(f"SEND {nodeid} RequestVotes {node.term}",flush=True)
    return

def send_heartbeat(node):
    while True:
        if node.state == "LEADER":
            nodelock.acquire()
            for nodeid in range(node.num):
                if nodeid == node.id: continue
                print(f"SEND {nodeid} AppendEntries {node.term} {node.id}", flush=True)
                debug(f"SEND {nodeid} AppendEntries {node.term} {node.id}", flush=True)
            nodelock.release()
            time.sleep(hbinterval)

def debug(msg,flush):
    # f = open("debug.txt","a")
    # f.write(str(time.time()) + " " +  str(node.id) + " > " + msg + "\n")
    # f.close()
    return

if __name__ == "__main__":

    node = Node(int(sys.argv[1]),int(sys.argv[2]) )
    check_timeout_thread = threading.Thread(target=check_timeout,args=(node,))
    send_heartbeat_thread = threading.Thread(target=send_heartbeat, args=(node,))
    check_timeout_thread.start()
    send_heartbeat_thread.start()
    # f = open("debug.txt","a")

    msg_id = 0


    while True:

        line = sys.stdin.readline()
        if line is None: break
        line = line.strip()
        # f = open("debug.txt","a")
        # f.write(str(time.time()) + " " + str(node.id) + " < " + line + "\n")
        # f.close()

        if node.state == "LEADER":
            # for nodeid in range(node.num):
            #     if nodeid == node.id: continue
            #     print(f"SEND {nodeid} AppendEntries {node.term} {node.id}", flush=True)
            #     debug(f"SEND {nodeid} AppendEntries {node.term} {node.id}", flush=True)
            # time.sleep(hbinterval)

            # line = sys.stdin.readline()
            # if line is None: break
            # line = line.strip()
            # f = open("debug.txt","a")
            # f.write(str(node.id) + " < " + line + "\n")
            # f.close()

            # As a leader, receive request votes from candidate
            if "RequestVotes" in line:
                sender_id = int(line.split(" ")[1])
                print(f"SEND {sender_id} AppendEntries {node.term} {node.id}",flush = True)
                debug(f"SEND {sender_id} AppendEntries {node.term} {node.id}",flush = True)
                continue
                

            # Receive Log from client
            if "LOG" in line:
                content = "".join(line.split(" ")[1:])
                node.log.append([node.term, content])

                node.logindex += 1
                node.replica_num.append(1)
                print(f"STATE log[{node.logindex}]=[{node.term},\"{content}\"]",flush=True)
                debug(f"STATE log[{node.logindex}]=[{node.term},\"{content}\"]",flush=True)
                ########################################
                for nodeid in range(node.num):
                    if nodeid == node.id: continue
                    print(f"SEND {nodeid} AppendEntries {node.term} {node.id} [\"{node.log[node.logindex][1]}\"]",flush=True)
                    debug(f"SEND {nodeid} AppendEntries {node.term} {node.id} [\"{node.log[node.logindex][1]}\"]",flush=True)
                ########################################
                continue

            # if a term changes before the leader has a chance to fully commit the message, it is no longer 
            # required to send a response, even if the message has not been yet committed
            if node.logindex > 0:
                lastest_logterm = node.log[node.logindex][0]
                if node.term > lastest_logterm:
                    continue

            if "AppendEntriesResponse" in line:
                continue
            if "AppendLogResponse" in line:
                if node.commitIndex < node.logindex:
                    logindex = int(line.split(" ")[4])
                    node.replica_num[logindex] += 1

                if node.replica_num[logindex] > node.num / 2:
                    node.commitIndex = logindex

                    print(f"STATE commitIndex={node.commitIndex}",flush=True)
                    print(f"COMMITTED {node.log[logindex][1]} {node.commitIndex}", flush=True)
                    debug(f"STATE commitIndex={node.commitIndex}",flush=True)
                    debug(f"COMMITTED {node.log[logindex][1]} {node.commitIndex}", flush=True)
                    for nodeid in range(node.num):
                        if nodeid == node.id: continue
                        print(f"SEND {nodeid} Committed {node.term} {node.commitIndex}", flush=True)
                        debug(f"SEND {nodeid} Committed {node.term} {node.commitIndex}", flush=True)
                    continue

            # A leader with higher term because of network partition or a new leader comes into play
            if "AppendEntries" in line:
                if node.id == 0:
                    debug(f"Partition Recovers",flush=True)
                sender_id = int(line.split(" ")[1])
                sender_term = int(line.split(" ")[3])
                if sender_term >= node.term:
                    node.lasttime = time.time()
                    node.term = sender_term
                    node.leader = sender_id
                    node.state = "FOLLOWER"
                    debug(f"STATE term={node.term}",flush=True)
                    debug(f"STATE state=\"{node.state}\"",flush=True)
                    debug(f"STATE leader={node.leader}",flush=True)
                    print(f"STATE term={node.term}",flush=True)
                    print(f"STATE state=\"{node.state}\"",flush=True)
                    print(f"STATE leader={node.leader}",flush=True)
                    if len(line.split(" ")) == 6:
                        content = line.split(" ")[5]
                        content = content[2:-2]
                        node.log.append([node.term,content])
                        node.logindex += 1
                        node.replica_num.append(None)

                        print(f"STATE log[{node.logindex}]=[{node.term},\"{content}\"]",flush=True)
                        debug(f"STATE log[{node.logindex}]=[{node.term},\"{content}\"]",flush=True)
                        print(f"SEND {sender_id} AppendLogResponse {sender_term} {node.logindex} true",flush=True)
                        debug(f"SEND {sender_id} AppendLogResponse {sender_term} {node.logindex} true",flush=True)

                        
                continue


        if node.state == "CANDIDATE":
            # line = sys.stdin.readline()
            # if line is None: break
            # line = line.strip()
            # f = open("debug.txt","a")
            # f.write(str(node.id) + " < " + line + "\n")
            # f.close()

            # Receive RPC from valid leader
            if "AppendEntries" in line:
                node.lasttime = time.time()
                sender_id = int(line.split(" ")[1])
                sender_term = int(line.split(" ")[3])
                node.leader = sender_id
                node.state = "FOLLOWER"
                node.term = sender_term

                if len(line.split(" ")) == 6:
                    content = line.split(" ")[5]
                    content = content[2:-2]
                    node.log.append([node.term,content])
                    node.logindex += 1
                    node.replica_num.append(None)
                    print(f"STATE log[{node.logindex}]=[{node.term},\"{content}\"]",flush=True)
                    debug(f"STATE log[{node.logindex}]=[{node.term},\"{content}\"]",flush=True)

                    continue
            # Receive RequestVote Response
            if "RequestVotesResponse" in line:
                reply = line.split(" ")[4]
                if reply == "true":
                    node.votenum += 1

            # Set as leader
            if node.votenum > node.num / 2:
                node.leader = node.id
                node.state = "LEADER"
                print(f"STATE state=\"{node.state}\"",flush=True)
                print(f"STATE leader={node.leader}",flush=True)
                print(f"=================LEADER SELECTED==========",flush=True)
                debug(f"STATE state=\"{node.state}\"",flush=True)
                debug(f"STATE leader={node.leader}",flush=True)
                debug(f"=================LEADER SELECTED==========",flush=True)
                continue

        if node.state == "FOLLOWER":
            # Receive Message
            # line = sys.stdin.readline()
            # if line is None: break
            # line = line.strip()

            node.lasttime = time.time()
            # f = open("debug.txt","a")
            # f.write(str(node.id) + " < " + line + "\n")
            # f.close()
            # Follower may wait for some time here
            # If the node has become candidate after timeout
            # But the node still has to wait for this message to arrive
            # and then it releazes it is candidate now
            # This may need to be improved
            debug(f"Receive Message at time {node.lasttime}",flush=True)
            ###############################################
            if node.state == "CANDIDATE":
                # Receive RPC from valid leader
                if "AppendEntries" in line:
                    node.lasttime = time.time()
                    sender_id = int(line.split(" ")[1])
                    sender_term = int(line.split(" ")[3])
                    node.leader = sender_id
                    node.state = "FOLLOWER"
                    node.term = sender_term

                    if len(line.split(" ")) == 6:
                        content = line.split(" ")[5]
                        content = content[2:-2]
                        node.log.append([node.term,content])
                        node.logindex += 1
                        node.replica_num.append(None)
                        print(f"STATE log[{node.logindex}]=[{node.term},\"{content}\"]",flush=True)
                        debug(f"STATE log[{node.logindex}]=[{node.term},\"{content}\"]",flush=True)

                    continue

                # Receive RequestVote Response
                if "RequestVotesResponse" in line:
                    reply = line.split(" ")[4]
                    if reply == "true":
                        node.votenum += 1

                # Set as leader
                if node.votenum > node.num / 2:
                    node.leader = node.id
                    node.state = "LEADER"
                    print(f"STATE state=\"{node.state}\"",flush=True)
                    print(f"STATE leader={node.leader}",flush=True)
                    print(f"=================LEADER SELECTED==========",flush=True)
                    debug(f"STATE state=\"{node.state}\"",flush=True)
                    debug(f"STATE leader={node.leader}",flush=True)
                    debug(f"=================LEADER SELECTED==========",flush=True)
                    continue
                continue
            ###############################################


            # Receive RequestVote
            if "RequestVotes" in line:
                sender_id = line.split(" ")[1]
                sender_term = line.split(" ")[3]
                # debug(f"term is {node.term} and votedfor is {node.votedfor}",flush=True)
                if int(sender_term) < node.term:
                    print(f"SEND {sender_id} RequestVotesResponse {node.term} false",flush=True)
                    debug(f"SEND {sender_id} RequestVotesResponse {node.term} false",flush=True)
                    continue
                if int(sender_term) > node.term:
                    node.term = int(sender_term)
                    node.votedfor = None
                if node.votedfor == None:
                    node.votedfor = int(sender_id)
                    node.leader = int(sender_id)
                    print(f"SEND {sender_id} RequestVotesResponse {node.term} true", flush=True)
                    debug(f"SEND {sender_id} RequestVotesResponse {node.term} true", flush=True)
                    continue

            # Receive AppendEntries
            if "AppendEntries" in line and "AppendEntriesResponse" not in line:
                sender_id = line.split(" ")[1]
                sender_term = line.split(" ")[3]
                node.leader = int(sender_id)
                node.term = int(sender_term)

                print(f"STATE state=\"{node.state}\"",flush=True)
                print(f"STATE term={node.term}",flush=True)
                print(f"STATE leader={node.leader}",flush=True)
                debug(f"STATE state=\"{node.state}\"",flush=True)
                debug(f"STATE term={node.term}",flush=True)
                debug(f"STATE leader={node.leader}",flush=True)
                if len(line.split(" ")) == 6:
                    content = line.split(" ")[5]
                    content = content[2:-2]
                    node.log.append([node.term,content])
                    node.logindex += 1
                    node.replica_num.append(None)

                    print(f"STATE log[{node.logindex}]=[{node.term},\"{content}\"]",flush=True)
                    debug(f"STATE log[{node.logindex}]=[{node.term},\"{content}\"]",flush=True)
                    print(f"SEND {sender_id} AppendLogResponse {sender_term} {node.logindex} true",flush=True)
                    debug(f"SEND {sender_id} AppendLogResponse {sender_term} {node.logindex} true",flush=True)
                else:
                    print(f"SEND {sender_id} AppendEntriesResponse {sender_term} true",flush=True)
                    debug(f"SEND {sender_id} AppendEntriesResponse {sender_term} true",flush=True)
                # print(f"SEND {sender_id} AppendEntriesResponse {sender_term} true",flush=True)
                # debug(f"SEND {sender_id} AppendEntriesResponse {sender_term} true",flush=True)
                
                continue

            # Receive committed
            if "Committed" in line:
                sender_id = int(line.split(" ")[1])
                commitIndex = int(line.split(" ")[4])
                node.commitIndex = commitIndex # Or node.logindex

                print(f"STATE commitIndex={node.commitIndex}",flush=True)
                print(f"COMMITTED {node.log[node.logindex][1]} {node.commitIndex}",flush=True)

                debug(f"STATE commitIndex={node.commitIndex}",flush=True)
                debug(f"COMMITTED {node.log[node.logindex][1]} {node.commitIndex}",flush=True)
                continue

    print("Somehow it comes to an end",flush=True)
    debug("Somehow it comes to an end",flush=True)
        



        






