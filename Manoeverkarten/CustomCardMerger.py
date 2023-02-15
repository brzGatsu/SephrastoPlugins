from PySide6 import QtWidgets, QtCore, QtGui
from EventBus import EventBus
from Wolke import Wolke
import tempfile
import PdfSerializer
import os
import re
import math
from Hilfsmethoden import Hilfsmethoden, WaffeneigenschaftException
import Objekte
from CharakterPrintUtility import CharakterPrintUtility
from DatenbankEinstellung import DatenbankEinstellung
from Fertigkeiten import Vorteil, VorteilLinkKategorie
import lxml.etree as etree
import PathHelper
import platform
import shutil
import yaml
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pypdfium2 as pdfium

class CustomCardMerger:
    @staticmethod
    def merge(pluginCardsFolder, ohneHintergrund):
        inipath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Data", "StandardIlarisConfig.ini")
        messageBox = QtWidgets.QMessageBox()
        messageBox.setIcon(QtWidgets.QMessageBox.Question)
        messageBox.setWindowTitle("Eigene Konfiguration laden?")
        messageBox.setText("Die Zusammenführung benötigt eine Konfigurationsdatei. Möchtest du die Standardkonfiguration, oder eine eigene laden?")
        messageBox.addButton("Standard", QtWidgets.QMessageBox.YesRole)
        messageBox.addButton("Eigene", QtWidgets.QMessageBox.YesRole)
        result = messageBox.exec()
        if result == 1:
            inipath, _ = QtWidgets.QFileDialog.getOpenFileName(None,"Konfigurationsdatei laden...", "","YAML-Datei (*.ini)")
            if inipath == "":
                return
        multisave = {} # cardname : [newcardname1, newcardname2, ...], ...
        removePluginCardCategories = [] # Categoryname1, Categoryname2, ...
        renamePluginCards = {} # cardname : newcardname, ...
        with open(inipath, 'r', encoding="utf-8") as infile:
            ini = yaml.safe_load(infile)
            for el in ini["DBExport_Einzel_HandgemachteKartenMehrfachSpeichern"]:
                for key in el:
                    multisave[key] = el[key]
            for el in ini["DBExport_Einzel_PluginKartenKategorienLöschen"]:
                removePluginCardCategories.append(el)
            for el in ini["DBExport_Einzel_PluginKartenUmbenennen"]:
                for key in el:
                    renamePluginCards[key] = el[key]

        srcPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Data", "Manöverkarten.pdf")
        if ohneHintergrund:
            srcPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Data", "Manöverkarten_ohne_Hintergrund.pdf")
        messageBox = QtWidgets.QMessageBox()
        messageBox.setIcon(QtWidgets.QMessageBox.Question)
        messageBox.setWindowTitle("Eigene handgemachte Manöverkarten laden?")
        messageBox.setText("Die Zusammenführung benötigt die Datei mit den handgemachten Manöverkarten. Möchtest du die von Gatsu, oder eine eigene laden?")
        messageBox.addButton("Karten von Gatsu", QtWidgets.QMessageBox.YesRole)
        messageBox.addButton("Eigene", QtWidgets.QMessageBox.YesRole)
        result = messageBox.exec()
        if result == 1:
            srcPath, _ = QtWidgets.QFileDialog.getOpenFileName(None,"Handgemachte Manöverkarten auswählen...","","PDF-Datei (*.pdf)")
            if srcPath == "":
                return

        # first delete plugin cards
        for file in PathHelper.listdir(pluginCardsFolder):
            filePath = os.path.join(pluginCardsFolder,file)
            category = file.split("_")[0]
            if file[:-4] in renamePluginCards:
                os.rename(filePath, os.path.join(pluginCardsFolder,renamePluginCards[file[:-4]] + ".pdf"))
            elif category in removePluginCardCategories:
                os.remove(filePath)

        # split manual cards into subfolder
        dstPath = os.path.join(pluginCardsFolder, "converted")
        if os.path.isdir(dstPath):
            shutil.rmtree(dstPath)
        os.mkdir(dstPath)

        # give manual cards proper name and move into plugin card folder
        cpdfPath = os.path.join("Bin", platform.system(), "cpdf", "cpdf")
        call = [cpdfPath, "-split", srcPath, "-o", os.path.join(dstPath, "page%%%.pdf")]
        PdfSerializer.check_output_silent(call)
        deckname = "Handgemacht"
        for file in PathHelper.listdir(dstPath):
            pdf = pdfium.PdfDocument(os.path.join(dstPath,file))
            page = pdf[0]
            textpage = page.get_textpage()
            text_all = textpage.get_text_range().split("\n")
            textpage.close()
            page.close()
            pdf.close()
            kartenName = text_all[1]

            
            if kartenName.startswith("Ilaris"):
                deckname = "".join(c for c in "".join(text_all[2:]) if c not in "\/:*?<>|+‘´`'!?[]{}(),\r").replace("&", "und").strip()
            
            if kartenName.startswith("Ilaris") or kartenName.startswith("Druckanleitung"):
                os.remove(os.path.join(dstPath,file))
                continue

            kartenName = kartenName.replace(" / ", " oder ").replace("/", " oder ").replace("&", "und")
            chop = [" (passiv)", " (Passiv)", " (einfach)", " (voll)", " (Sinn)", " (Tier)", " [Fertigkeit oder Attribut]"]
            for suffix in chop:
                if kartenName.endswith(suffix):
                    kartenName = kartenName[:-len(suffix)]
            kartenName = "".join(c for c in kartenName if c not in "\/:*?<>|+‘´`'!?[]{}(),\ufffe").strip()
            dstName = f"{deckname}_{kartenName}"
            dstPathRenamed = os.path.join(pluginCardsFolder, dstName + ".pdf")
            if os.path.isfile(dstPathRenamed):
                if text_all[2].startswith("FK"):
                    dstPathRenamed = os.path.join(pluginCardsFolder, f"{deckname}_{kartenName} (FK).pdf")
            os.rename(os.path.join(dstPath,file), dstPathRenamed)

            if dstName in multisave:
                remove = True
                for name in multisave[dstName]:
                    if f"{deckname}_{name}" == dstName:
                        remove = False
                        continue
                    shutil.copyfile(dstPathRenamed,os.path.join(dstPath, f"{deckname}_{name}.pdf"))

                if remove:
                    os.remove(dstPathRenamed)

        if os.path.isdir(dstPath):
            shutil.rmtree(dstPath)

        if "PIL" in sys.modules:
            messageBox = QtWidgets.QMessageBox()
            messageBox.setIcon(QtWidgets.QMessageBox.Question)
            messageBox.setWindowTitle("Karten in Bilder konvertieren?")
            messageBox.setText("Möchtest du die Karten in Bilder konvertieren, z. B. für den Discord Bot?")
            messageBox.addButton("Ja", QtWidgets.QMessageBox.YesRole)
            messageBox.addButton("Ja (ohne Kategorie im Namen)", QtWidgets.QMessageBox.YesRole)
            messageBox.addButton("Nein", QtWidgets.QMessageBox.NoRole)
            result = messageBox.exec()
            if result == 0 or result == 1:
                dstPath = os.path.join(pluginCardsFolder, "bilder")
                if os.path.isdir(dstPath):
                    shutil.rmtree(dstPath)
                os.mkdir(dstPath)
                for file in PathHelper.listdir(pluginCardsFolder):
                    if not os.path.isfile(os.path.join(pluginCardsFolder,file)):
                        continue
                    pdf = pdfium.PdfDocument(os.path.join(pluginCardsFolder,file))
                    page = pdf.get_page(0)
                    image = page.render_to(
                        pdfium.BitmapConv.pil_image,
                        scale=300/72,
                        rotation=0,
                        crop=(0, 0, 0, 0),
                        fill_colour=(255, 255, 255, 255),
                        draw_annots=True,
                        greyscale=False,
                        optimise_mode=pdfium.OptimiseMode.NONE,
                    )

                    name = os.path.splitext(os.path.basename(file))[0]
                    if result == 1:
                        index = name.find("_")
                        name = name[index+1:]
                    image.save(os.path.join(dstPath, name + ".png"))
                    image.close()
                    page.close()
                    pdf.close()