import os
import shutil
import zipfile

version = "4.1.0"
dir_path = os.path.dirname(os.path.realpath(__file__))
build_path = os.path.join(dir_path,  "build")
os.makedirs(build_path)

includes = [
    "CharakterAssistent",
    "CharakterToText",
    "Hexalogien",
    "Manoeverkarten",
    "RuestungenPlus",
    "SephMakro",
    "SephMakroScripts",
    "Tierbegleiter",
    "Tragkraft",
    "WaffenPlus",
    "Zaubertricks"
]

print("Copying plugins to build folder")
for include in includes:
    shutil.copytree(include, os.path.join(build_path, include))

print("Removing unneeded folders")
removeSubfiles = [
    "UI",
    "__pycache__"
]

for include in includes:
    for subfile in removeSubfiles:
        filepath = os.path.join(build_path, include, subfile)
        if os.path.isdir(filepath) or os.path.isfile(filepath):
            try:
                shutil.rmtree(filepath)
            except OSError:
                os.remove(filepath)

print("Zipping")
zipfilename = f"Plugins_v{version}"
shutil.make_archive(zipfilename, 'zip', build_path)
zipfilename += ".zip"
shutil.move(zipfilename, os.path.join(build_path, zipfilename))

#with zipfile.ZipFile(os.path.join(build_path, f"Plugins_v{version}.zip"), mode="w") as archive:

    #archive.write("hello.txt")