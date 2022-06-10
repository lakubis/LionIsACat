# %%
import numpy as np
from mesa import Agent,Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector


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

    #TODO: isi ini, tapi sepertinya terlihat tidak usah
    def step(self):
        pass


# %%

class motorist(Agent):

    def __init__(self, unique_id, pos, model, batteries = None): 
        super().__init__(unique_id,model)
        #Assign baterai
        if batteries == None:
            self.batteries = []
        else:
            self.batteries = batteries

        #Assign posisi
        self.pos = pos

    def change_battery(self, new_bat):
        empties = self.batteries
        self.batteries = new_bat
        return empties

    #TODO: Isi fungsi ini
    def move(self):
        pass

    #TODO: Isi fungsi ini
    def step(self):
        pass


# %%
class station(Agent):

    def __init__(self, unique_id, pos, model, inventory_size = 40,charging_port_size=10, assigned_batteries = None):
        super().__init__(unique_id,model)
        
        #Assign posisi
        self.pos = pos
        #Assign spesifikasi
        self.charging_port_size = charging_port_size
        self.inventory_size = inventory_size

        if assigned_batteries ==None:
            self.inventory = []
            self.charging_port = []
            self.queue = []
        else:
            #Ini ntar jangan lupa diisi
            pass
    

    #queue kalau charging port penuh
    # TODO: isi fungsi ini
    def add_queue(self):
        pass
    
    #pindah dari queue ke charging port
    # TODO: isi fungsi ini
    def queue_to_charging(self):
        pass

    #pindah dari charging port ke inventory
    # TODO: isi fungsi ini
    def charging_to_inventory(self):
        pass

    #hilangkan dari inventory
    # TODO: isi fungsi ini
    def remove_inventory(self):
        pass

    def step(self):
    # TODO: isi fungsi ini
        pass

    

    
# %%
class switching_model(Model):
    '''
    inv_size: Ukuran inventory station
    cp_size: Ukuran charging port
    num_of_motorist: Jumlah motor
    num_of_stations: Jumlah station
    '''
    def __init__(self,num_of_motorist, num_of_stations, inv_size, cp_size, width = 20,height = 20):
    
        #Jumlah motor
        self.num_of_motorist = num_of_motorist
        #Jumlah station
        self.num_of_stations = num_of_stations
        #Jumlah inventory
        self.inv_size = inv_size
        #Jumlah charging port
        self.cp_size = cp_size
        #Jumlah baterai = jumlah motor yang ada + jumlah station*Kapasitas station
        self.num_of_batteries = num_of_motorist + num_of_stations*(self.inv_size + self.cp_size)

        #Definisikan ukuran grid
        self.width = width
        self.height = height

        #Definisikan grid dan schedule
        self.grid = MultiGrid(width, height, True)
        
        #Nanti schedule harus coba dimodifikasi sendiri
        self.schedule = RandomActivation(self)

        #Array untuk nyimpen agent
        self.batteries = []
        self.motorists = []
        self.stations = []

        #Create battery
        for i in range(self.num_of_batteries):
            bat = battery(self.next_id(),self)
            self.schedule.add(bat)
            #Tambahkan ke list baterai
            self.batteries.append(bat)


        #Create motorist
        for i in range(self.num_of_motorist):

            x = self.random.randrange(self.width)
            y = self.random.randrange(self.height)
            mot = motorist(self.next_id(),(x,y),self,batteries=self.batteries[i])
            self.grid.place_agent(mot,(x,y))
            self.schedule.add(mot)
            #Tambahkan ke list motor
            self.motorists.append(mot)

        #Create stations
        for i in range(self.num_of_stations):
            x = self.random.randrange(self.width)
            y = self.random.randrange(self.height)
            #Create station + assign batteries
            stat = station(self.next_id(), (x,y), self, assigned_batteries=[bat for bat in self.batteries[self.num_of_motorist+i*(self.inv_size+self.cp_size):self.num_of_motorist+(i+1)*(self.inv_size+self.cp_size)]])
            self.grid.place_agent(stat,(x,y))
            self.schedule.add(stat)
            #Tambahkan ke list station
            self.stations.append(stat)

        #TODO: Definisikan datacollector untuk model ini
        self.datacollector = DataCollector({})