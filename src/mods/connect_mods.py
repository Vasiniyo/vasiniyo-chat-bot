import os

mods_in = "./mods.txt"
mods_out = "./src/mods/__init__.py"

if os.access(mods_in, os.F_OK) == True:
    # if os.path.exists(file_path):
    mods = ""

    with open(mods_in) as file:
        for line in file.readlines():
            mods += "from . import " + line

    mods += "from .register import *"

    with open(mods_out, "w") as file:
        file.write(mods)
