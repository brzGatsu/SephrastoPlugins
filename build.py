import os
import shutil

version = "5.1.0"
dir_path = os.path.dirname(os.path.realpath(__file__))
build_path = os.path.join(dir_path,  "build")
os.makedirs(build_path)

includes = [
    "CharakterToText",
    "DrachentoeterKampfregeln",
    "FertigkeitenPlus",
    "FoundryVTT",
    "Hexalogien",
    "Manoeverkarten",
    "RuestungenPlus",
    "SephMakro",
    "SephMakroScripts",
    "Tierbegleiter",
    "WaffenPlus",
    "Zaubertricks",
    "Historie",
    "Kreaturen"
]

print("Copying plugins to build folder")
for include in includes:
    shutil.copytree(include, os.path.join(build_path, include))

print("Removing unneeded folders")
removeSubfiles = [
    "UI",
    "docs",
    "__pycache__",
    "Data/Doc/assets/external/unpkg.com/mermaid@10.7.0",
    ".cache"
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
print("Done")