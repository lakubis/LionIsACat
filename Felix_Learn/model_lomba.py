# %%
from random import random
import numpy as np
from mesa import Agent,Model
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector

#%%

def alive_num(model):
    num_of_alive = 0
    for motor in model.motorists:
        if motor.alive:
            num_of_alive += 1
    return num_of_alive

class battery(Agent):
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

        #Nama object
        self.agent_name = "motorist"

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
                self.target_station.inventory_full.remove(self.batteries)
                #print("Motor dengan id: " + str(self.unique_id) + " menukar baterai " + str(empty_bat.unique_id) + " dengan " + str(self.batteries.unique_id))
                
                #Setelah itu hilangkan target station
                self.target_station = None

            elif (len(self.target_station.inventory_full) == 0):
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
                self.target_station.cp_full.remove(self.batteries)
                
                #Hilangkan target station
                self.target_station = None
            elif (len(self.target_station.cp_full) == 0):
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
        if abs(self.pos[0]-self.target_station.pos[0]) > 0:
            #next_moves = self.model.grid.get_neighborhood(self.pos,self.moore,False)
            #print(next_moves)
            if (self.target_station.pos[0] - self.pos[0]) > 0:
                #Gerak ke kanan
                self.model.grid.move_agent(self,(self.pos[0] + 1,self.pos[1]))
            else:
                #Gerak ke kiri
                self.model.grid.move_agent(self,(self.pos[0] - 1,self.pos[1]))
        elif abs(self.pos[1] - self.target_station.pos[1]) > 0:
            if (self.target_station.pos[1]-self.pos[1]) > 0:
                #Gerak ke atas
                self.model.grid.move_agent(self,(self.pos[0],self.pos[1] + 1))
            else:
                #Gerak ke bawah
                self.model.grid.move_agent(self,(self.pos[0],self.pos[1] - 1))
        else:
            raise Exception("Sudah berada di lokasi tapi masih disuruh gerak")

    def set_target_station(self):
        #Kalau misalnya ada target lama, dia akan diexclude dari pencarian target
        stats = self.model.stations.copy()
        if self.target_station == None:
            pass
        else:
            stats.remove(self.target_station)

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

    #TODO: Buat probabilitas geraknya, agar ada distribusi penggunaan
    def moving_probability(self):
        pass

    def step(self):
        #Cek persentase baterai, kalau baterai <= 10 persen, maka cari station
        if self.alive:
            if (self.batteries.charge/self.batteries.real_cap) > 0.1:
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
    num_of_motorist: Jumlah motor
    num_of_stations: Jumlah station
    '''
    def __init__(self,num_of_motorist, num_of_stations, inv_size, cp_size, width = 20,height = 20, moore = False, configuration = "random"):
    
        #Jumlah motor
        self.num_of_motorist = num_of_motorist
        #Jumlah station
        self.num_of_stations = None
        if configuration == "random":
            self.num_of_stations = num_of_stations
        elif configuration == "less":
            self.num_of_stations = 5
        elif configuration == "normal":
            self.num_of_stations = 9
        elif configuration == "more":
            self.num_of_stations = 13
        print(self.num_of_stations)

        #Jumlah inventory
        self.inv_size = inv_size
        #Jumlah charging port
        self.cp_size = cp_size
        #Jumlah baterai = jumlah motor yang ada + jumlah station*Kapasitas station
        self.num_of_batteries = self.num_of_motorist + self.num_of_stations*(self.inv_size + self.cp_size)

        #Gerak Moore atau von Neumann
        self.moore = moore

        #Definisikan ukuran grid
        self.width = width
        self.height = height

        #Definisikan grid dan schedule
        self.grid = MultiGrid(width, height, True)
        
        #TODO:Nanti schedule harus coba dimodifikasi sendiri (tapi ga begitu penting)
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
            mot = motorist(new_id,(x,y),self,batteries=self.batteries[i],moore=self.moore)


            #Place agent
            self.grid.place_agent(mot,(x,y))
            self.schedule.add(mot)
            #Tambahkan ke list motor
            self.motorists.append(mot)

        if configuration == "random":
            #Create stations
            for i in range(self.num_of_stations):
                #TODO: Coba cari bagaimana caranya biar station bisa tersebar merata di mapnya
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
                stat = station(new_id, (x,y), self,inventory_size=self.inv_size, charging_port_size=self.cp_size, assigned_batteries=[bat for bat in self.batteries[self.num_of_motorist+i*(self.inv_size+self.cp_size):self.num_of_motorist+(i+1)*(self.inv_size+self.cp_size)]])

                self.grid.place_agent(stat,(x,y))
                self.schedule.add(stat)
                #Tambahkan ke list station
                self.stations.append(stat)

        else:
            coordinates = []
            if configuration == "less" or configuration == "normal" or configuration == "more":
                #tambahkan pojok2
                coordinates.append((0,0))
                coordinates.append((self.width-1,0))
                coordinates.append((0, self.height-1))
                coordinates.append((self.width-1,self.height-1))
                #tambah titik tengah
                coordinates.append((np.floor(self.width/2).astype(int)-1, np.floor(self.height/2).astype(int)-1))
        
            if configuration == "normal" or configuration == "more":
                #Tambahkan titik2 samping
                coordinates.append((np.floor(self.width/2).astype(int)-1, 0))
                coordinates.append((np.floor(self.width/2).astype(int)-1, self.height-1))
                coordinates.append((0, np.floor(self.height/2).astype(int)-1))
                coordinates.append((self.width-1, np.floor(self.height/2).astype(int)-1))

            if configuration == "more":
                #tambahkan titik2 intermediet
                coordinates.append((np.floor(self.width/4).astype(int)-1, np.floor(self.height/4).astype(int)-1))
                coordinates.append((np.floor(self.width/4).astype(int)-1, np.floor(self.height*(3/4)).astype(int)-1))
                coordinates.append((np.floor(self.width*(3/4)).astype(int)-1, np.floor(self.height/4).astype(int)-1))
                coordinates.append((np.floor(self.width*(3/4)).astype(int)-1, np.floor(self.height*(3/4)).astype(int)-1))

            for i in range(self.num_of_stations):
                #Create station + assign batteries
                new_id = self.next_id()
                stat = station(new_id, coordinates[i], self,inventory_size=self.inv_size, charging_port_size=self.cp_size, assigned_batteries=[bat for bat in self.batteries[self.num_of_motorist+i*(self.inv_size+self.cp_size):self.num_of_motorist+(i+1)*(self.inv_size+self.cp_size)]])

                self.grid.place_agent(stat,coordinates[i])
                self.schedule.add(stat)
                #Tambahkan ke list station
                self.stations.append(stat)

        #TODO: Lengkapi data collector
        self.datacollector = DataCollector(
            model_reporters = {
                "num_of_alive": alive_num
            },
            agent_reporters={
                "Position": "pos",
                "Charge": "charge",
                "Alive": "alive",
                "Full_battery": lambda a: len(a.inventory_full) if a.agent_name == "station" else None,
                "Empty_battery": lambda a: len(a.inventory_empty) if a.agent_name == "station" else None,
                "CP_full": lambda a: len(a.cp_full) if a.agent_name == "station" else None,
                "CP_empty": lambda a: len(a.cp_empty) if a.agent_name == "station" else None
            }
        )

    def step(self):
        self.datacollector.collect(self)
        self.schedule.step()
