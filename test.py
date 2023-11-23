from os import listdir
from os.path import isfile, join
from settings import *
path = os.path.join(LOCAL_DIR, "music")

onlyfiles = [f for f in listdir(path) if isfile(join(path, f))]
print(onlyfiles)