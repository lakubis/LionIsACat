# %%
import numpy as np
from mesa import Agent,Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector


#%%
class battery(Agent):
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

    def __init__(self, unique_id, pos, model, batteries = None, moore = False): 
        super().__init__(unique_id,model)
        #Assign baterai
        if batteries == None:
            self.batteries = None
        else:
            self.batteries = batteries

        #Sekarang akan ditentukan status driver
        self.alive = False
        if self.batteries != None:
            if self.batteries.charge > 0:
                self.alive = True
        
        #Tentukan aturan gerakan motor, bila True maka moore, bila False maka von Neumann
        self.moore = moore

        #Assign posisi
        self.pos = pos

    #TODO: Fungsi ini mau di cek lagi
    def change_battery(self, new_bat):
        empties = self.batteries
        self.batteries = new_bat
        return empties

    #TODO: Isi fungsi ini dengan logika gerak
    def random_move(self):
        #argumen terakhir false karena kita ingin driver untuk tetap bergerak, bukan diam di tempat
        next_moves = self.model.grid.get_neighborhood(self.pos, self.moore, False)
        #pick a position to move to
        next_move = self.random.choice(next_moves)
        #move the agent
        self.model.grid.move_agent(self,next_move)
    
    #TODO: Buat fungsi untuk mencari station terdekat 
    def move_to_station(self):
        pass

    #TODO: Isi fungsi ini dengan random move dan move to station
    def step(self):
        self.random_move()
        print(self.pos)
        


# %%
class station(Agent):
    '''
    Di sini, baterai akan disimpan di inventory dan juga charging port.
    inventory_full: List baterai yang terisi penuh
    inventory_empty: List baterai yang kosong tapi belum bisa di cas di charging port (kosong bukan berarti 0, tapi tidak terisi penuh)
    charging_port: List baterai yang sedang di cas
    '''
    def __init__(self, unique_id, pos, model, inventory_size = 40,charging_port_size=10, assigned_batteries = None):
        super().__init__(unique_id,model)
        
        #Assign posisi
        self.pos = pos
        #Assign spesifikasi
        self.charging_port_size = charging_port_size
        self.inventory_size = inventory_size

        #Add array inventory dan charging port
        self.inventory_full = []
        self.inventory_empty = []
        self.charging_port = []

        if assigned_batteries ==None:
            pass
        else:
            self.inventory_full = []
            self.inventory_empty = []
            self.charging_port = []
            #Di cek dulu apakah assigned_batteries melebihi kapasitas station
            if len(assigned_batteries) > (self.charging_port_size+ self.inventory_size):
                raise Exception("Baterai yang di assign di station terlalu banyak")
            else:
                #Kita akan assign battery, pertama2 akan di cek dulu apakah terdapat error, lalu baru di cek apakah baterai penuh atau kosong
                for i in assigned_batteries:
                    if i.charge > i.real_cap:
                        raise Exception("Isi baterai tidak dapat melebihi kapasitas sebenarnya")
                    elif i.charge < 0:
                        raise Exception("Isi baterai tidak boleh negatif")
                    elif i.charge == i.real_cap:
                        #Kalau baterai penuh, maka akan di assign di inventory_full, kalau inventory penuh, assign ke charging port
                        if (len(self.inventory_full) + len(self.inventory_empty)) < self.inventory_size:
                            self.inventory_full.append(i)
                        else:
                            self.charging_port.append(i)
                    elif i.charge < i.real_cap:
                        #Kalau baterai kosong, maka akan di assign ke charging port, kalau charging port penuh, di assign ke inventory_empty
                        if len(self.charging_port) < self.charging_port_size:
                            self.charging_port.append(i)
                        else:
                            self.inventory_empty.append(i)
            
            

    

    #queue kalau charging port penuh
    # TODO: Sepertinya bagian ini mau diganti karena kita sudah ganti sistem
    def add_queue(self):
        pass
    
    #pindah dari queue ke charging port
    # TODO: Sepertinya bagian ini mau diganti juga karena kita sudah ganti sistem
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
        
        #TODO:Nanti schedule harus coba dimodifikasi sendiri
        self.schedule = RandomActivation(self)

        #Id agent
        self.current_id = -1

        #Array untuk nyimpen agent
        self.batteries = []
        self.motorists = []
        self.stations = []

        #Create battery
        for i in range(self.num_of_batteries):
            #Create new battery
            new_id = self.next_id()
            bat = battery(unique_id = new_id,model = self)

            self.schedule.add(bat)
            #Tambahkan ke list baterai
            self.batteries.append(bat)


        #Create motorist
        for i in range(self.num_of_motorist):
            
            x = self.random.randrange(self.width)
            y = self.random.randrange(self.height)

            #Create new motorist
            new_id = self.next_id()
            mot = motorist(new_id,(x,y),self,batteries=self.batteries[i])


            #Place agent
            self.grid.place_agent(mot,(x,y))
            self.schedule.add(mot)
            #Tambahkan ke list motor
            self.motorists.append(mot)

        #Create stations
        for i in range(self.num_of_stations):
            x = self.random.randrange(self.width)
            y = self.random.randrange(self.height)
            #Create station + assign batteries
            new_id = self.next_id()
            stat = station(new_id, (x,y), self, assigned_batteries=[bat for bat in self.batteries[self.num_of_motorist+i*(self.inv_size+self.cp_size):self.num_of_motorist+(i+1)*(self.inv_size+self.cp_size)]])

            self.grid.place_agent(stat,(x,y))
            self.schedule.add(stat)
            #Tambahkan ke list station
            self.stations.append(stat)

        #TODO: Definisikan datacollector untuk model ini
        self.datacollector = DataCollector(agent_reporters={"Position": "pos"})

    def step(self):
        self.datacollector.collect(self)
        self.schedule.step()
# %%
