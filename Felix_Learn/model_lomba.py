# %%
import numpy as np
from mesa import Agent,Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid


#%%
class battery:
    num_of_batteries = 0
    degradation_rate = 0.00025 #Ini didapatkan dari standar baterai HP, secara umum setelah 800 charge cycle, battery health tinggal 80%/0.8

    def __init__(self, unique_id, model, max_cap = 2600, health = 1):
        super().__init__(unique_id,model)
        # baterai memiliki tiga parameter sebagai berikut:
        # max_cap: kapasitas maksimum baterai, dalam satuan Watt-hour (Baterai gogoro 1.3 kWh, ada 2 biji)
        # health: kesehatan baterai, real_cap = max_cap * health. Nilai health berkisar antara 0-1. By default 1.
        # charge: isi dari baterai sekarang, charge harus < real_cap. Ketika baterai diciptakan, baterai terisi penuh
        self.max_cap = max_cap
        self.health = health
        self.real_cap = max_cap*health
        self.charge = self.real_cap
        battery.num_of_batteries += 1
        self.id = battery.num_of_batteries

    def degrade(self):
        self.health -= battery.degradation_rate #Diasumsikan degradation rate dari setiap baterai sama

    def consume_charge(self,cons_charge):
        self.charge -= cons_charge


# %%

class motorist(Agent):

    def __init__(self, unique_id, model, batteries = None): 
        super().__init__(unique_id,model)
        if batteries == None:
            self.batteries = []
        else:
            self.batteries = batteries

    def change_battery(self, new_bat):
        empties = self.batteries
        self.batteries = new_bat
        return empties

    def move(self):
        pass


# %%
class station(Agent):

    def __init__(self, unique_id, model, inventory_size = 40,charging_port_size=10):
        super().__init__(unique_id,model)
        self.pos_x = np.random.randint(1,100)
        self.pos_y = np.random.randint(1,100)
        self.charging_port_size = charging_port_size
        self.inventory_size = inventory_size
        self.inventory = []
        self.charging_port = []
        self.queue = []

    def add_queue():
        pass

    def queue_to_charging():
        pass

    def charging_to_inventory():
        pass

    def remove_inventory():
        pass

    

    
# %%
class switching_model(Model):
    '''variabel spec berisi tuple (inventory_size, charging_port_size)'''
    def __init__(self,num_of_motorist, num_of_stations, spec, width,height):

        self.num_of_motorist = num_of_motorist
        self.num_of_stations = num_of_stations
        self.spec = spec
        self.grid = MultiGrid(width, height, True)
        self.schedule = RandomActivation(self)

        for i in range(self.num_agents):
            pass