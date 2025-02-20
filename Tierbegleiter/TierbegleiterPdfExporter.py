from PySide6 import QtWidgets, QtCore, QtGui
from QtUtils.ProgressDialogExt import ProgressDialogExt
import PdfSerializer
from Wolke import Wolke
from Hilfsmethoden import Hilfsmethoden
import re
import os
import tempfile
import copy

class TierbegleiterPdfExporter:
    def __init__(self):
        pass

    def categoryHeading(self, text):
        return "<h2>" + text + "</h2>"

    def ruleHeading(self, text):
        return "<h3>" + text + "</h3>"

    def createPdf(self, path, tierbegleiter, charakterbogen, datenbank):
        try:
            dlg = ProgressDialogExt(minimum = 0, maximum = 100)
            dlg.disableCancel()
            dlg.setWindowTitle("Exportiere Tierbegleiter")
            dlg.show()
            QtWidgets.QApplication.processEvents() #make sure the dialog immediatelly shows

            dlg.setLabelText("Befülle Formularfelder")
            fields = copy.copy(tierbegleiter.attributModsMerged)
            fields["WSStern"] = fields["WS*"]

            scriptAPI = Hilfsmethoden.createScriptAPI()
            scriptAPI.update({ "WS" : tierbegleiter.attributModsMerged["WS"], "KO" : tierbegleiter.attributModsMerged["KO"] })
            fields["DH"] = datenbank.einstellungen["Tierbegleiter Plugin: DH Script"].evaluateScript(scriptAPI)

            talentModifierList = sorted([mod for mod in tierbegleiter.talentModsMerged if mod.name.strip()], key = lambda mod: mod.name) 
            for i in range(0, charakterbogen.maxFertigkeiten):
                if i < len(talentModifierList):
                    fields['Talent.' + str(i)] = talentModifierList[i].name
                    fields['TalentPW.' + str(i)] = talentModifierList[i].mod

            vorteilModifierList = sorted([mod for mod in tierbegleiter.vorteilModsMerged if mod.name.strip()], key = lambda mod : mod.name)
            for i in range(0, charakterbogen.maxVorteile):
                if i < len(vorteilModifierList):
                    fields['Vorteil.' + str(i)] = vorteilModifierList[i].name

            fields["Name"] = tierbegleiter.name
            fields["Spezies"] = tierbegleiter.definition.name
            fields["Nahrung"] = tierbegleiter.nahrung

            charsPerLine = 80
            text = tierbegleiter.hintergrund.split("\n")
            if len(text[-1]) < charsPerLine:
                text[-1] += " " * (int(charsPerLine * 1.5) - len(text[-1])) # space has less width, so add 50%
            fields["Hintergrund"] = "\n".join(text)

            text = tierbegleiter.aussehen.split("\n")
            if len(text[-1]) < charsPerLine:
                text[-1] += " " * (int(charsPerLine * 1.5) - len(text[-1])) # space has less width, so add 50%
            fields["Aussehen"] = "\n".join(text)

            waffen = copy.copy(tierbegleiter.waffenMerged)
            while len(waffen) > 3:
                removed = False
                for w in waffen:
                    if not "Reiterkampf" in w.name and ("Zerbrechlich" in w.eigenschaften or "Verletzlich" in w.eigenschaften):
                        waffen.remove(w)
                        removed = True
                        break
                if not removed:
                    break

            for i in range(0, 3):
                if i < len(waffen):
                    fields['Waffe.' + str(i)] = waffen[i].name
                    fields['WaffeRW.' + str(i)] = waffen[i].rw
                    fields['WaffeEig.' + str(i)] = waffen[i].eigenschaften
                    fields['WaffeAT.' + str(i)] = waffen[i].at if waffen[i].at is not None else "-"
                    fields['WaffeVT.' + str(i)] = waffen[i].vt if waffen[i].vt is not None else "-"
                    fields['WaffeTP.' + str(i)] = waffen[i].getTP()

            for i in range(len(tierbegleiter.ausruestung)):
                fields['Ausruestung.' + str(i)] = tierbegleiter.ausruestung[i]

            tiervorteile = [mod for mod in vorteilModifierList if mod.name in datenbank.tiervorteile]
            for waffe in tierbegleiter.waffenMerged:
                eigenschaften = list(map(str.strip, waffe.eigenschaften.split(",")))
                for eig in eigenschaften:
                    name = re.sub(r"\((.*?)\)", "", eig, re.UNICODE).strip() # remove parameters
                    if name in datenbank.tiervorteile:
                        hatVorteil = False
                        for vorteilMod in tiervorteile:
                            if vorteilMod.name == name:
                              hatVorteil = True
                              break
                        if hatVorteil:
                            continue
                        tiervorteile.append(datenbank.tiervorteile[name])
            tiervorteile = sorted(tiervorteile, key = lambda vort: vort.name)

            addRules = tierbegleiter.regelnAnhaengen and (len(tiervorteile) > 0)
            handle, tmpTierbegleiterPath = tempfile.mkstemp()
            os.close(handle)

            flatten = not tierbegleiter.formularEditierbar
            PdfSerializer.write_pdf(charakterbogen.filePath, fields, tmpTierbegleiterPath, flatten)

            bookmarks = []
            for i in range(PdfSerializer.getNumPages(charakterbogen.filePath)):
                text = "Charakterbogen"
                if i < len(charakterbogen.seitenbeschreibungen):
                    text = charakterbogen.seitenbeschreibungen[i]
                bookmarks.append(PdfSerializer.PdfBookmark("S. " + str(i+1) + " - " + text, i+1))
            i += 1

            if tierbegleiter.bild is not None:
                # The approach is to convert the image to pdf and stamp it over the char sheet with pdftk
                dlg.setLabelText("Stemple Charakterbild")
                dlg.setValue(30)
                image_pdf = PdfSerializer.convertJpgToPdf(tierbegleiter.bild, charakterbogen.getImageSize(0, [193, 254]), charakterbogen.getImageOffset(0), charakterbogen.getPageLayout())
                stamped_pdf = PdfSerializer.stamp(tmpTierbegleiterPath, image_pdf)
                os.remove(image_pdf)
                os.remove(tmpTierbegleiterPath)
                tmpTierbegleiterPath = stamped_pdf

            if addRules:
                dlg.setLabelText("Erstelle Regelanhang")
                dlg.setValue(50)
                fields = {}
                rules = ["<h1>Regeln für " + (tierbegleiter.name or "namenloses Tier") + "</h1>"]

                if any(v.wirkung and not v.manöver for v in tiervorteile):
                    rules.append(self.categoryHeading("Tiervorteile"))
                    for vorteilMod in tiervorteile:
                        if vorteilMod.wirkung and not vorteilMod.manöver:
                            rules.append("<article>")
                            rules.append(self.ruleHeading(vorteilMod.name))
                            rules.append(vorteilMod.wirkung)
                            rules.append("</article>")

                if any(v.wirkung and v.manöver for v in tiervorteile):
                    rules.append(self.categoryHeading("Manöver und Waffeneigenschaften"))
                    for vorteilMod in tiervorteile:
                        if vorteilMod.wirkung and vorteilMod.manöver:
                            rules.append("<article>")
                            rules.append(self.ruleHeading(vorteilMod.name))
                            rules.append(vorteilMod.wirkung)
                            rules.append("</article>")
                rules = "".join(rules).replace("\n", "<br>")
                html = ""
                with open(charakterbogen.regelanhangPfad, 'r', encoding="utf-8") as infile:
                    rules = rules.replace("$sephrasto_dir$", "file:///" + os.getcwd().replace('\\', '/'))
                    rules = rules.replace("$regeln_dir$", "file:///" + Wolke.Settings['Pfad-Regeln'].replace('\\', '/'))
                    rules = rules.replace("$plugins_dir$", "file:///" + Wolke.Settings['Pfad-Plugins'].replace('\\', '/'))
                    html = infile.read()
                    html = html.replace("{sephrasto_dir}", "file:///" + os.getcwd().replace('\\', '/'))
                    html = html.replace("{rules_content}", rules)
                    html = html.replace("{rules_font_size}", str(tierbegleiter.regelnGroesse))
                baseUrl = QtCore.QUrl.fromLocalFile(QtCore.QFileInfo(charakterbogen.regelanhangPfad).absoluteFilePath())
                rulesFile = PdfSerializer.convertHtmlToPdf(html, baseUrl, charakterbogen.getRegelanhangPageLayout(), 100)

                for j in range(1, PdfSerializer.getNumPages(rulesFile)+1):
                    bookmarks.append(PdfSerializer.PdfBookmark("S. " + str(i+1) + " - Regelanhang " + str(j), i+1))
                    i += 1

                if charakterbogen.regelanhangHintergrundPfad:
                    tmpRulesFile = PdfSerializer.addBackground(rulesFile, charakterbogen.regelanhangHintergrundPfad)
                    os.remove(rulesFile)
                    rulesFile = tmpRulesFile

                tmp = PdfSerializer.concat([tmpTierbegleiterPath, rulesFile])
                os.remove(tmpTierbegleiterPath)
                os.remove(rulesFile)
                tmpTierbegleiterPath = tmp

            dlg.setLabelText("Füge Lesezeichen hinzu")
            dlg.setValue(80)
            PdfSerializer.addBookmarks(tmp, bookmarks, path)
            os.remove(tmp)

            dlg.setLabelText("Optimiere Dateigröße")
            dlg.setValue(90)
            PdfSerializer.squeeze(path, path)
            dlg.setValue(100)
        finally:
            dlg.hide()
            dlg.deleteLater()

        if Wolke.Settings['PDF-Open']:
            Hilfsmethoden.openFile(path)