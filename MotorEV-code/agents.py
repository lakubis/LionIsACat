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
        self.battery_life = baterai()
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
        change = np.random.randint(-1,1)
        pct_change = 1 + np.random.randn()
        self.battery_life = self.battery_life - (change*pct_change)
        if decision == 0 :
            self.position_x = self.position_x + change  # can move left, right, or stay
        else : 
            self.position_y = self.position_y + change # can move up, down, or stay
    
    def check_station(self): 
        '''manhattan distance'''
        return self.position_x 
        
# %%
class baterai:
    num_of_batteries = 0
    degradation_rate = 0.00025 #Ini didapatkan dari standar baterai HP, secara umum setelah 800 charge cycle, battery health tinggal 80%/0.8

    


# %%
