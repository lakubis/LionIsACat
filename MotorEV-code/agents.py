#%%
#Ini adalah script yang diisi dengan agent




# %%
class baterai:
    def __init__(self, capacity, health, percentage):
        #Di sini, baterai memiliki tiga parameter sebagai berikut
        # capacity: spesifikasi baterai, dalam satuan wh
        # health: kesehatan baterai, kapasitas sebenarnya dari baterai = capacity * health. Nilai health berkisar antara 0-1
        # percentage: persentase baterai, kapasitas yang sedang ditanggung oleh baterai adalah capacity * health * percentage. Nilai percentage berkisar di antara 0-1
        self.capacity = capacity
        self.health = health
        self.percentage = percentage
