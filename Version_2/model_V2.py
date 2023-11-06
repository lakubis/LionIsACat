'''
This is the second version
Last revised: 03.10.2022

This file is modified from the competition file, here we removed several variables to keep track of, because it's just not very useful, it's just for testing and we already knew it works
The removed variables are:
*Position
*cp full
*cp empty
*inventory full
*inventory empty

Felix note 06.11.2023: I think we can add the test back, but make it optional. I haven't thought of how to do it, but it should be possible. We also have to code everything in English, to make it readable for someone else.
'''

# %%
from logging import exception
from random import random
import numpy as np
from mesa import Agent,Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from distribution_functions import commuter_distribution, taxi_distribution, noise_distribution
import matplotlib.pyplot as plt
import math

#%%

def alive_num(model):
    """This is a function that retrieves the number of alive motorist in a model.

    Args:
        model (switching_model): Model containing switching stations and motorists

    Returns:
        Number of alive motorists: Number of motorist that is still alive.
    """
    num_of_alive = 0 # Initiate the counting
    for motor in model.motorists:
        if motor.alive: # Check the status of the motorists
            num_of_alive += 1
    return num_of_alive

def num_of_charging(model):
    """ This is a function that retrieves the number of currently charging model in each stations

    Args:
        model (switching model): Model containing switching stations and motorists

    Returns:
        total_charging : Number of batteries that is currently charging
    """
    total_charging = 0 # Initiate the counting
    for stat in model.stations:
        total_charging += len(stat.cp_empty) #FIXME: This might pose a problem, because it checks for empty batteries, and not every empty batteries are charging
    return total_charging

class battery(Agent):
    """_summary_

    Args:
        Agent (_type_): _description_

    Raises:
        Exception: _description_
    """
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

        #Biar ga error
        self.alive = None
        self.inventory_full = []
        self.inventory_empty = []
        self.cp_full = []
        self.cp_empty = []

        #nama object
        self.agent_name = "battery"

    def degrade(self):
        self.health -= battery.degradation_rate #Diasumsikan degradation rate dari setiap baterai sama
        #Ini kita sesuaikan kembali real capacity dari baterai
        self.real_cap = self.max_cap*self.health

    def consume_charge(self):
        '''
        Saat ini, cons_charge akan ditentukan melalui aproksimasi kasar: karena time step 1 menit, maka dengan menggunakan asumsi kecepatan motor sebesar 40 km/jam, pada setiap step agent akan bergerak sejauh 2/3 km. Selain itu, diketahui pula untuk 170 km, diperlukan energi sebesar 2600 Wh. Akan didapatkan penggunaan sebesar 15 Wh/km. Berarti akan dihabiskan energi sebesar 10Wh per menit/step
        '''
        cons_charge = 10 #Wh
        self.charge = max(0.0, self.charge - cons_charge)
        #TODO: check for error, remove this line to improve performance
        if self.charge < 0:
            raise Exception("Charge tidak mungkin bernilai negatif")

    def step(self):
        pass


# %%

class motorist(Agent):

    def __init__(self, unique_id, pos, model, status, batteries = None, moore = False): 
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

        #Biar ga error
        self.charge = None
        self.inventory_full = []
        self.inventory_empty = []
        self.cp_full = []
        self.cp_empty = []

        #Assign posisi
        self.pos = pos

        #Target station
        self.target_station = None

        #Nama dan status motorist
        self.agent_name = "motorist"
        #status dapat berupa commuter, taxi, atau noise
        self.status = status


    def change_battery(self):
        #Baterai kosong
        empty_bat = self.batteries
        #Cek tipe station, dengan inventory atau tidak
        if self.target_station.inventory_size > 0:
            #Ngecek station punya baterai penuh atau tidak:
            if len(self.target_station.inventory_full) > 0:
                #print(len(self.target_station.inventory_full))
                #print(len(self.target_station.inventory_empty))
                self.target_station.inventory_empty.append(empty_bat)
                self.batteries = self.target_station.inventory_full[0]
                self.target_station.inventory_full.remove(self.batteries) #successfully charge
                self.target_station.register[0] += 1
                #print("Motor dengan id: " + str(self.unique_id) + " menukar baterai " + str(empty_bat.unique_id) + " dengan " + str(self.batteries.unique_id))
                
                #Setelah itu hilangkan target station
                self.target_station = None

            elif (len(self.target_station.inventory_full) == 0): # fail to charge
                self.target_station.register[1] += 1
                #print("Station habis")
                if self.batteries.charge ==0:
                    self.alive = False
                else:
                    self.set_target_station()
        else:
            if len(self.target_station.cp_full) > 0:
                #Tukar baterai
                #empty_bat.degrade()
                self.target_station.cp_empty.append(empty_bat)
                self.batteries = self.target_station.cp_full[0]
                self.target_station.cp_full.remove(self.batteries) #successfully charge

                self.target_station.register[0] += 1
                
                #Hilangkan target station
                self.target_station = None
            elif (len(self.target_station.cp_full) == 0): # fail to charge
                self.target_station.register[1] += 1
                if self.batteries.charge == 0:
                    self.alive = False
                else:
                    self.set_target_station()


    def random_move(self):
        #argumen terakhir false karena kita ingin driver untuk tetap bergerak, bukan diam di tempat
        next_moves = self.model.grid.get_neighborhood(self.pos, self.moore, False)
        #pick a position to move to
        next_move = self.random.choice(next_moves)
        #move the agent
        self.model.grid.move_agent(self,next_move)
    
    def move_to_station(self):
        if self.target_station == None:
            raise Exception("Tidak ada target")

        move_H = False
        move_V = False
        if abs(self.pos[0]-self.target_station.pos[0]) > 0:
            move_H = True
        elif abs(self.pos[1] - self.target_station.pos[1]) > 0:
            move_V = True
        else:
            raise Exception("Sudah berada di lokasi tapi masih disuruh gerak")

        
        if move_H:
            self.move_horizontal()
        elif move_V:
            self.move_vertical()





    def set_target_station(self):
        #Kalau misalnya ada target lama, dia akan diexclude dari pencarian target
        stats = self.model.stations.copy()
        if self.target_station == None:
            pass
        else:
            stats.remove(self.target_station)

        # TODO: Look at what's wrong with the distance algorithm

        '''
        for stat in stats:

            # This is the new station choosing logic
            min_dis = math.inf #set it to infinity
            for stat in stats:
                new_man_distance = abs(self.pos[0]-stat.pos[0]) + abs(self.pos[1] - stat.pos[1])
                if new_man_distance < min_dis:
                    min_dis = new_man_distance
                
            # After we got the minimum distance, we'll remove any station that is farther than the min_dis
            for stat in stats:
                new_man_distance = abs(self.pos[0]-stat.pos[0]) + abs(self.pos[1] - stat.pos[1])
                if new_man_distance > min_dis:
                    stats.remove(stat)
        

            # After we got the final collection of stations, we'll choose random station as our target station
        self.target_station = np.random.choice(stats)
        '''

        curr_target = None
        for stat in stats:
            #Kalau ga ada target, maka langsung assign
            if curr_target == None:
                curr_target = stat
            else:
                #Hitung Manhattan distancenya, lalu bandingkan
                old_man_distance = abs(self.pos[0]-curr_target.pos[0]) + abs(self.pos[1]-curr_target.pos[1])
                new_man_distance = abs(self.pos[0]-stat.pos[0]) + abs(self.pos[1] - stat.pos[1])
                if new_man_distance < old_man_distance:
                    curr_target = stat
        self.target_station = curr_target
        

    # This is a method to move the agent horizontally
    def move_horizontal(self):
        if (self.target_station.pos[0] - self.pos[0]) > 0:
            #Gerak ke kanan
            self.model.grid.move_agent(self,(self.pos[0] + 1,self.pos[1]))
        else:
            #Gerak ke kiri
            self.model.grid.move_agent(self,(self.pos[0] - 1,self.pos[1]))

    # This is a method to move the agent vertically
    def move_vertical(self):
        if (self.target_station.pos[1]-self.pos[1]) > 0:
            #Gerak ke atas
            self.model.grid.move_agent(self,(self.pos[0],self.pos[1] + 1))
        else:
            #Gerak ke bawah
            self.model.grid.move_agent(self,(self.pos[0],self.pos[1] - 1))

    def step(self):
        #Di sini, kita akan melihat probabilitas gerak
        if self.status == 'commuter':
            move_prob = self.model.commute_dis[self.model.minute]
        elif self.status == 'taxi':
            move_prob = self.model.taxi_dis[self.model.minute]
        elif self.status == 'noise':
            move_prob = self.model.noise_dis[self.model.minute]
        else:
            raise exception('Ini tidak seharusnya terjadi, cek distribusi')

        move = False
        if np.random.uniform(low = 0.0, high= 1.0) < move_prob:
            move = True

        #Cek persentase baterai, kalau baterai <= 10 persen, maka cari station
        if self.alive:
            if (self.batteries.charge/self.batteries.real_cap) > 0.1:
                if move:
                    self.random_move()
                    self.batteries.consume_charge()
            elif (self.batteries.charge/self.batteries.real_cap) <= 0.1:
                #Cek sudah ada target atau belum
                if self.target_station == None:
                    if self.batteries.charge == 0:
                        self.alive = False
                    else:
                        self.set_target_station()
                else:
                    #Cek posisinya udah sama dengan target atau belum
                    if self.pos == self.target_station.pos:
                        self.change_battery()
                        if self.batteries.charge == 0:
                            self.alive = False
                    else:
                        if move:
                            self.move_to_station()
                            self.batteries.consume_charge()
                        if self.batteries.charge == 0:
                            self.alive = False
        else:
            pass

    



# %%
class station(Agent):
    '''
    Di sini, baterai akan disimpan di inventory dan juga charging port.
    inventory_full: List baterai yang terisi penuh
    inventory_empty: List baterai yang kosong tapi belum bisa di cas di charging port (kosong bukan berarti 0, tapi tidak terisi penuh)
    cp_full: List baterai yang penuh di charging port
    cp_empty: List baterai yang sedang di cas di charging port
    '''
    def __init__(self, unique_id, pos, model, inventory_size = 40,charging_port_size=10, assigned_batteries = None):
        super().__init__(unique_id,model)
        
        #Assign posisi
        self.pos = pos
        #Assign spesifikasi
        self.charging_port_size = charging_port_size
        self.inventory_size = inventory_size

        #register, if charging is successful, then self.register[0] += 1, and if it fails self.register[1] += 1
        self.register = np.zeros(2)

        #Assign daya, dihitung dari 2600 Wh butuh 3 jam untuk ngecas
        self.charge_rate = 14.5 #Wh/menit

        #Add array inventory dan charging port
        self.inventory_full = []
        self.inventory_empty = []

        #cp dipisahkan untuk memudahkan pemodelan nantinya
        self.cp_full = []
        self.cp_empty = []

        #Biar ga error
        self.charge = None
        self.alive = None

        #Nama agent
        self.agent_name = "station"

        if assigned_batteries ==None:
            pass
        else:
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
                            self.cp_full.append(i)
                    elif i.charge < i.real_cap:
                        #Kalau baterai kosong, maka akan di assign ke charging port, kalau charging port penuh, di assign ke inventory_empty
                        if (len(self.cp_full) + len(self.cp_empty)) < self.charging_port_size:
                            self.cp_empty.append(i)
                        else:
                            self.inventory_empty.append(i)
            
    
    def charge_batteries(self):
        for bat in self.cp_empty:
            #Biar charge tidak melewati real capacity
            bat.charge = min(bat.real_cap, bat.charge + self.charge_rate)

            #TODO: temporary check for error, remove this to improve computational performance
            if bat.charge > bat.real_cap:
                raise Exception("Ada error dengan fungsi minimum")

            #Kalau baterainya penuh, pindahkan dari cp_empty ke cp_full
            elif bat.charge == bat.real_cap:
                self.cp_full.append(bat)
                self.cp_empty.remove(bat)

        
    def switch_cp_inventory(self):
        #Tentukan dulu mana yang lebih sedikit, baterai kosong di inventory atau baterai penuh di charging port
        min_index = min(len(self.inventory_empty), len(self.cp_full))

        if min_index > 0:
            empty_bats = self.inventory_empty[0:min_index] #Baterai kosong
            full_bats = self.cp_full[0:min_index] # Baterai penuh

            #degradasi baterai dan tukar baterai
            for bat in empty_bats:
                #bat.degrade()
                self.cp_empty.append(bat)
                self.inventory_empty.remove(bat)

            #tukar full battery
            for bat in full_bats:
                self.inventory_full.append(bat)
                self.cp_full.remove(bat)
            


    def step(self):
        #Bagian ini untuk model yang punya inventory
        if self.inventory_size > 0:
            self.charge_batteries()
            self.switch_cp_inventory()
        
        #Bagian ini untuk yang tidak punya inventory
        else:
            self.charge_batteries()

    

    
# %%
class switching_model(Model):
    '''
    inv_size: Ukuran inventory station
    cp_size: Ukuran charging port
    num_of_motorist: array berisi (jumlah commuter, jumlah taxi, jumlah noise)
    num_of_stations: Jumlah station
    '''
    def __init__(self,num_of_motorist, num_of_stations, inv_size, cp_size, width = 20,height = 20, moore = False, configuration = "random"):
    
        #TODO: Make three types of motorist, constant function for leisure, constant function for taxis, and two normal functions for commuters(?)
        #Jumlah motor
        self.num_of_motorist = num_of_motorist
        #Jumlah station
        self.num_of_stations = None
        if configuration == "random":
            self.num_of_stations = num_of_stations
        elif configuration == "less":
            self.num_of_stations = 4
        elif configuration == "normal":
            self.num_of_stations = 9
        elif configuration == "more":
            self.num_of_stations = 16
        print(self.num_of_stations)

        #Buat distribusi permintaan
        self.commute_dis = commuter_distribution()
        self.taxi_dis = taxi_distribution()
        self.noise_dis = noise_distribution()

        #Jumlah inventory
        self.inv_size = inv_size
        #Jumlah charging port
        self.cp_size = cp_size
        #Jumlah baterai = jumlah motor yang ada + jumlah station*Kapasitas station
        self.num_of_batteries = sum(self.num_of_motorist) + self.num_of_stations*(self.inv_size + self.cp_size)

        #Gerak Moore atau von Neumann
        self.moore = moore

        #Definisikan ukuran grid
        self.width = width
        self.height = height

        #Definisikan grid dan schedule
        self.grid = MultiGrid(width, height, True)
        
        self.schedule = RandomActivation(self)

        #jam, agar perhitungan tidak terlalu banyak
        self.minute = 0

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


        
        #bat_id untuk assign ke motor
        bat_id = 0

        #Create motor
        for i in range(len(num_of_motorist)):
            
            if i == 0:
                status = "commuter"
            elif i == 1:
                status = "taxi"
            elif i == 2:
                status = "noise"


            for j in range(num_of_motorist[i]):
                x = self.random.randrange(self.width)
                y = self.random.randrange(self.height)

                #Create new motorist
                new_id = self.next_id()
                mot = motorist(new_id,(x,y),self,status,batteries=self.batteries[bat_id],moore=self.moore)

                #Randomize charge
                mot.batteries.charge = np.random.uniform(low = 260.0, high= 2600.0)

                #Place agent
                self.grid.place_agent(mot,(x,y))
                self.schedule.add(mot)
                #Tambahkan ke list motor
                self.motorists.append(mot)
                bat_id += 1
                


        
        if configuration == "random":
            #Create stations
            for i in range(self.num_of_stations):
                x = self.random.randrange(self.width)
                y = self.random.randrange(self.height)
                same_coor = True
                while same_coor:
                    same_coor = False
                    for stat in self.stations:
                        if (x,y) == stat.pos:
                            same_coor = True
                            x = self.random.randrange(self.width)
                            y = self.random.randrange(self.height)

                #Create station + assign batteries
                new_id = self.next_id()
                stat = station(new_id, (x,y), self,inventory_size=self.inv_size, charging_port_size=self.cp_size, assigned_batteries=[bat for bat in self.batteries[sum(self.num_of_motorist)+i*(self.inv_size+self.cp_size):sum(self.num_of_motorist)+(i+1)*(self.inv_size+self.cp_size)]])

                self.grid.place_agent(stat,(x,y))
                self.schedule.add(stat)
                #Tambahkan ke list station
                self.stations.append(stat)

        else:
            coordinates = []
            if configuration == "less":
                #4 titik
                coordinates.append((np.floor(self.width*(1/4)).astype(int)-1, np.floor(self.height*(1/4)).astype(int)-1))
                coordinates.append((np.floor(self.width*(1/4)).astype(int)-1, np.floor(self.height*(3/4)).astype(int)-1))
                coordinates.append((np.floor(self.width*(3/4)).astype(int)-1, np.floor(self.height*(1/4)).astype(int)-1))
                coordinates.append((np.floor(self.width*(3/4)).astype(int)-1, np.floor(self.height*(3/4)).astype(int)-1))
        
            elif configuration == "normal":
                #9 titik
                coordinates.append((np.floor(self.width*(1/6)).astype(int)-1, np.floor(self.height*(1/6)).astype(int)-1))
                coordinates.append((np.floor(self.width*(1/6)).astype(int)-1, np.floor(self.height*(3/6)).astype(int)-1))
                coordinates.append((np.floor(self.width*(1/6)).astype(int)-1, np.floor(self.height*(5/6)).astype(int)-1))
                coordinates.append((np.floor(self.width*(3/6)).astype(int)-1, np.floor(self.height*(1/6)).astype(int)-1))
                coordinates.append((np.floor(self.width*(3/6)).astype(int)-1, np.floor(self.height*(3/6)).astype(int)-1))
                coordinates.append((np.floor(self.width*(3/6)).astype(int)-1, np.floor(self.height*(5/6)).astype(int)-1))
                coordinates.append((np.floor(self.width*(5/6)).astype(int)-1, np.floor(self.height*(1/6)).astype(int)-1))
                coordinates.append((np.floor(self.width*(5/6)).astype(int)-1, np.floor(self.height*(3/6)).astype(int)-1))
                coordinates.append((np.floor(self.width*(5/6)).astype(int)-1, np.floor(self.height*(5/6)).astype(int)-1))

                

            elif configuration == "more":
                coordinates.append((np.floor(self.width*(1/8)).astype(int)-1, np.floor(self.height*(1/8)).astype(int)-1))
                coordinates.append((np.floor(self.width*(1/8)).astype(int)-1, np.floor(self.height*(3/8)).astype(int)-1))
                coordinates.append((np.floor(self.width*(1/8)).astype(int)-1, np.floor(self.height*(5/8)).astype(int)-1))
                coordinates.append((np.floor(self.width*(1/8)).astype(int)-1, np.floor(self.height*(7/8)).astype(int)-1))
                coordinates.append((np.floor(self.width*(3/8)).astype(int)-1, np.floor(self.height*(1/8)).astype(int)-1))
                coordinates.append((np.floor(self.width*(3/8)).astype(int)-1, np.floor(self.height*(3/8)).astype(int)-1))
                coordinates.append((np.floor(self.width*(3/8)).astype(int)-1, np.floor(self.height*(5/8)).astype(int)-1))
                coordinates.append((np.floor(self.width*(3/8)).astype(int)-1, np.floor(self.height*(7/8)).astype(int)-1))
                coordinates.append((np.floor(self.width*(5/8)).astype(int)-1, np.floor(self.height*(1/8)).astype(int)-1))
                coordinates.append((np.floor(self.width*(5/8)).astype(int)-1, np.floor(self.height*(3/8)).astype(int)-1))
                coordinates.append((np.floor(self.width*(5/8)).astype(int)-1, np.floor(self.height*(5/8)).astype(int)-1))
                coordinates.append((np.floor(self.width*(5/8)).astype(int)-1, np.floor(self.height*(7/8)).astype(int)-1))
                coordinates.append((np.floor(self.width*(7/8)).astype(int)-1, np.floor(self.height*(1/8)).astype(int)-1))
                coordinates.append((np.floor(self.width*(7/8)).astype(int)-1, np.floor(self.height*(3/8)).astype(int)-1))
                coordinates.append((np.floor(self.width*(7/8)).astype(int)-1, np.floor(self.height*(5/8)).astype(int)-1))
                coordinates.append((np.floor(self.width*(7/8)).astype(int)-1, np.floor(self.height*(7/8)).astype(int)-1))
                

            for coor in coordinates:
                print(coor)

            for i in range(self.num_of_stations):
                #Create station + assign batteries
                new_id = self.next_id()
                stat = station(new_id, coordinates[i], self,inventory_size=self.inv_size, charging_port_size=self.cp_size, assigned_batteries=[bat for bat in self.batteries[sum(self.num_of_motorist)+i*(self.inv_size+self.cp_size):sum(self.num_of_motorist)+(i+1)*(self.inv_size+self.cp_size)]])

                self.grid.place_agent(stat,coordinates[i])
                self.schedule.add(stat)
                #Tambahkan ke list station
                self.stations.append(stat)
                

        self.datacollector = DataCollector(
            model_reporters = {
                "num_of_alive": alive_num,
                "num_of_charging": num_of_charging
            },
            agent_reporters={
                "Position": "pos",
                "Charge": "charge",
                "Alive": "alive",
            }
        )

    #TODO: add a function to draw the probability density
    def draw_prob_des(self):
        total_dis = np.zeros(24*60)
        for i in range(self.num_of_motorist[0]):
            total_dis = total_dis + self.commute_dis
        for i in range(self.num_of_motorist[1]):
            total_dis = total_dis + self.taxi_dis
        for i in range(self.num_of_motorist[2]):
            total_dis = total_dis + self.noise_dis
            
        hour = ["05:00","06:00","07:00","08:00","09:00","10:00","11:00","12:00","13:00","14:00","15:00","16:00","17:00","18:00","19:00","20:00","21:00","22:00","23:00","00:00","01:00","02:00","03:00","04:00"]
        fig, ax = plt.subplots(figsize=[18,6])
        ax.plot(total_dis/max(total_dis))

        ax.set_xticks(np.arange(0,24*60,60))
        ax.set_xticklabels(hour)
        ax.set_ylim([0,1.1])
        ax.set_xlim([0,24*60])
        #ax.set_title('Normalized demand',fontsize = 18)
        ax.set_ylabel('Demand',fontsize = 18)
        ax.set_xlabel('Time', fontsize = 18)

    # Function to plot the number of success and fail
    def plot_reg(self):
        labels = []
        success_charge = [] # array for successful charge attempts
        fail_charge = [] # array for failed charge attempts
        for stat in self.stations:
            labels.append("Stat" + str(stat.unique_id))
            success_charge.append(stat.register[0])
            fail_charge.append(stat.register[1])

        fig, ax = plt.subplots(figsize = (12,8))
        x = np.arange(len(labels))
        width = 0.35
        rects1 = ax.bar(x - width/2, success_charge, width, label = 'Success')
        rects2 = ax.bar(x + width/2, fail_charge, width, label = 'Fail')
        ax.set_ylabel('Number of attempts')
        ax.set_title('Number of successful and failed charging attempts')
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.legend()

        self.autolabel(rects1,ax)
        self.autolabel(rects2,ax)

        fig.tight_layout()
        plt.show()
    
    
    def autolabel(self,rects,ax):
        """Attach a text label above each bar in *rects*, displaying its height."""
        for rect in rects:
            height = rect.get_height()
            ax.annotate('{}'.format(height),
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')



    def step(self):
        self.datacollector.collect(self)
        self.schedule.step()
        self.minute = int(self.schedule.steps%(24*60))

# %%
