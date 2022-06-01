#%%
# Packages
import numpy as np


#%%
#Ini adalah script yang diisi dengan agent

class agents:
    # Tiap agent memiliki 2 parameter sebagai berikut 
    # R : jarak yang ditempuh dalam satu hari 
    # battery_life : isi atau kapasitas dari baterai
    def __init__(self, driving_r): 
        self.battery_life = battery()
        self.driving_r = driving_r
        self.position_x = np.random.randint(1,100)
        self.position_y = np.random.randint(1,100)
    

    def movement(self):
        if check_station() == False :
            '''random movement von neumann '''
            explore() 
        else : 
            go_station()
    
    def go_station(): 
        '''move to station no matter what'''
        pass 

    def explore(self): 
        decision = np.random.randint(0,1)
        if decision == 0 :
            self.position_x = self.position_x + np.random.randint(-1,1) # can move left, right, or stay
        else : 
            self.position_y = self.position_y + np.random.randint(-1,1) # can move up, down, or stay
    
    def check_station(self): 
        '''manhattan distance'''
        
        pass
        
# %%
class baterai:
    num_of_batteries = 0
    degradation_rate = 0.00025 #Ini didapatkan dari standar baterai HP, secara umum setelah 800 charge cycle, battery health tinggal 80%/0.8

    def __init__(self, max_cap = 1300, health =1):
        # baterai memiliki tiga parameter sebagai berikut:
        # max_cap: kapasitas maksimum baterai, dalam satuan Watt-hour (Baterai gogoro 1.3 kWh)
        # health: kesehatan baterai, real_cap = max_cap * health. Nilai health berkisar antara 0-1. By default 1.
        # charge: isi dari baterai sekarang, charge harus < real_cap. Ketika baterai diciptakan, baterai terisi penuh
        self.max_cap = max_cap
        self.health = health
        self.real_cap = max_cap*health
        self.charge = self.real_cap
        baterai.num_of_batteries += 1
        self.id = baterai.num_of_batteries

    def degrade(self):
        self.health -= baterai.degradation_rate #Diasumsikan degradation rate dari setiap baterai sama


# %%
