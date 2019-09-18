import pickle

#mydict = {}
mydict = pickle.load(open("linux_default.pickle", "rb"))
#if "89999" not in mydict:
#    mydict["89999"] = 12.0
print(mydict["89999"])
#f = open("gather_linux_default/default.ref", "r")

#for line in f:
#    l = list(filter(None, line.strip().split(' ')))
#    mydict[str(l[0])] = float(l[1])
#f.close()

#pickle.dump(mydict, open("linux_default.pickle", "wb"))

#print(len(mydict.items()))
#for i, v in mydict.items():
#    print(i, v)
