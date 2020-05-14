import bmemcached

mc = bmemcached.Client('192.168.1.230:11211')
s = ""

#for i in range(0,14912000):
#for i in range(0, 2000):
#    s+="a"
#mc.set("a", s)
#print(len(s))
value = mc.get("a")
print(len(value))
