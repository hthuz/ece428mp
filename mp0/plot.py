# Get data
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

file_index = list(range(1,11))
min_delays,max_delays,avg_delays = [],[],[]
min_bws,max_bws,avg_bws = [],[],[]

for index in file_index:
    metricfile = './metrics/metric' + str(index) + '.csv'
    df = pd.read_csv(metricfile)
    df = df[df['node'] == 'A']

    min_delay,max_delay,avg_delay = df['delay'].min(),df['delay'].max(),df['delay'].mean()
    min_bw,max_bw,avg_bw = df['bandwidth'].min(),df['bandwidth'].max(),df['bandwidth'].mean()
    min_delays.append(min_delay)
    max_delays.append(max_delay)
    avg_delays.append(avg_delay)
    min_bws.append(min_bw)
    max_bws.append(max_bw)
    avg_bws.append(avg_bw)


ys = [min_delays,max_delays,avg_delays,min_bws,max_bws,avg_bws]
ylabels = ["Min Delay(s)","Max Delay(s)",'Average Delay(s)','Min Bandwidth(bytes/s)','Max Bandwith(bytes/s)','Average Bandwidth(bytes/s)']
filenames = ['min_delay','max_delay','avg_delay','min_bandwidth','max_bandwidth','avg_bandwidth']

# Plot
for i in range(6):

    RAs = np.linspace(0.1,1,10)
    coeff = np.polyfit(RAs,ys[i],1)
    plt.figure()
    plt.plot(RAs, ys[i], '-o',label='Raw data')
    plt.plot(RAs,coeff[0] * RAs + coeff[1], 'r-',label='Curvefitting')
    plt.xlabel('RA')
    plt.ylabel(ylabels[i])
    plt.legend()
    plt.title(filenames[i])
    plt.savefig('./plots/' + filenames[i] + '.jpg')


print("Please go to plots directory to see figures")