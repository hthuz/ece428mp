

NODE_NUM = 3
SCENARIO_NUM = 1
METRICTABLE_PATH = f"./metrics/scenario{SCENARIO_NUM}/table"
METRICFIG_PATH = f"./metrics/scenario{SCENARIO_NUM}/figure"

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

msg_start_time_record = dict()
msg_end_time_record = dict()

def bandwidth_draw(node_id):
    bandwidth_file = f"{METRICTABLE_PATH}/bandwidth_node{node_id}.csv"
    df = pd.read_csv(bandwidth_file, header = 1,names = ['data','bandwidth'])

    bandwidth_list = df['bandwidth'].tolist()
    
    # Plot
    msg_index = np.linspace(1, len(bandwidth_list), len(bandwidth_list) )
    plt.figure()
    plt.plot(msg_index, bandwidth_list)
    plt.xlabel("Message Index")
    plt.ylabel("Bandwidth (bits/s)")

    plt.title(f"Scenario {SCENARIO_NUM}, node {node_id}, Message BandWidth")
    plt.savefig(f"{METRICFIG_PATH}/bandwidth_node{node_id}.jpg")

    return


def processing_time_get_table():
    
    # Read data
    f = open(f'{METRICTABLE_PATH}/time.log','r')
    lines = f.readlines()
    for line in lines:
        line = line.strip("\n")
        linelist = line.split(",")
        msg_id, msg_time =  linelist[0], linelist[2]
        if "start_time" in line:
            msg_start_time_record[msg_id] = msg_time

        if "end_time" in line:
            node_id = linelist[1].split("_")[0]
            if msg_id not in msg_end_time_record.keys():
                msg_end_time_record[msg_id] = {}
            msg_end_time_record[msg_id][node_id] = msg_time


    # Write table header
    timefile = open(f"{METRICTABLE_PATH}/process_time.csv", 'w')
    timefile.write("msg_id,first_node_process_time,last_node_process_time\n")
    timefile.close()

    # Write table content
    timefile = open(f'{METRICTABLE_PATH}/process_time.csv', 'a')
    for msg_id in msg_end_time_record.keys():
        start_time = msg_start_time_record[msg_id]
        first_end_time = min(msg_end_time_record[msg_id].values())
        all_end_time = max(msg_end_time_record[msg_id].values())
        first_end_time = float(first_end_time) - float(start_time)
        all_process_time = float(all_end_time) - float(start_time)
        timefile.write(f"{msg_id},{str(first_end_time)}, {str(all_process_time)}\n")
    timefile.close()
    return

def processing_time_draw():
    timefile = open(f'{METRICTABLE_PATH}/process_time.csv', 'r')
    df = pd.read_csv(timefile, header = 1,names = ['msg_id','first_node_process_time','all_node_process_time'])
    first_process_time_list = df['first_node_process_time'].tolist()
    all_process_time_list = df['all_node_process_time'].tolist()
    msg_index = np.linspace(1, len(first_process_time_list), len(first_process_time_list) )

    # Plot
    plt.figure()
    plt.plot(msg_index, first_process_time_list,'r', label = "First node process time")
    plt.plot(msg_index, all_process_time_list, 'b', label = "Last node process time")
    plt.xlabel("Message Index")
    plt.ylabel("Time (s)")
    plt.legend()
    plt.title(f"Scenario {SCENARIO_NUM}, Process time")
    plt.savefig(f"{METRICFIG_PATH}/process_time.jpg")

    return



if __name__ == "__main__":

    for node_id in range(1,NODE_NUM + 1):
        bandwidth_draw(str(node_id))

    processing_time_get_table()
    processing_time_draw()

