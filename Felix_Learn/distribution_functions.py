'''
Ini adalah file yang nanti akan digunakan untuk menggambarkan distribusi penggunaan kendaraan

commuters: people who travels to work
noise: a small subset of drivers that travels for 24/7
taxis: mostly works during the day

'''

#%%
import matplotlib.pyplot as plt
import numpy as np
from math import sqrt,pi,exp
from scipy.special import beta

#Store time string
def get_time_list():
    time_list = []
    hour = 5
    minute = 0

    for i in range(24*60):
        minute += 1
        if minute == 60:
            minute = 0
            hour += 1

    if hour ==24:
        hour = 0

        if hour< 10:
            string_hour = "0" + str(hour)
        else:
            string_hour = str(hour)

        if minute < 10:
            string_minute = "0" + str(minute)
        else:
            string_minute = str(minute)

        time_list.append(string_hour + "." + string_minute)

    time_list.remove('05.00')
    time_list.insert(0,'05.00')
    return time_list

def normal_distribution(x,sigma,mean):
    return (1/(sigma*sqrt(2*pi)))*exp(-(1/2)*((x-mean)/sigma)**2)


def commuter_distribution():
    prob_dis = np.zeros(24*60)
    for i in range(len(prob_dis)):
        prob_dis[i] += normal_distribution(i,60,3*60)

    for i in range(len(prob_dis)):
        prob_dis[i] += normal_distribution(i,60,12*60)

    return prob_dis/max(prob_dis)



def noise_distribution():
    prob_dis = np.zeros(24*60) + 1
    return prob_dis

def taxi_distribution():
    prob_dis = np.zeros(24*60)
    for i in range(1140):
        prob_dis[i] += ((i/(1140))*(1-(i/1140)))
    return prob_dis/max(prob_dis)

if __name__ == '__main__':
    #%%
    hour = ["05:00","06:00","07:00","08:00","09:00","10:00","11:00","12:00","13:00","14:00","15:00","16:00","17:00","18:00","19:00","20:00","21:00","22:00","23:00","00:00","01:00","02:00","03:00","04:00"]
    fig, ax = plt.subplots(figsize=[18,6])
    ax.plot(commuter_distribution())

    ax.set_xticks(np.arange(0,24*60,60))
    ax.set_xticklabels(hour)
    plt.show()


    #%%
    fig, ax = plt.subplots(figsize=[18,6])
    ax.plot(noise_distribution())

    ax.set_xticks(np.arange(0,24*60,60))
    ax.set_xticklabels(hour)

    plt.show()

    #%%
    fig, ax = plt.subplots(figsize=[18,6])
    ax.plot(taxi_distribution())

    ax.set_xticks(np.arange(0,24*60,60))
    ax.set_xticklabels(hour)

    plt.show()



    #%%    
    def normal():
        pass
    # %%
