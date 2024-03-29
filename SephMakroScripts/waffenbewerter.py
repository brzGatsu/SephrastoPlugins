import math
import re

#================= Settings ==================
# Ob der vom Schwert (Ranking 10, 180S) abgeleitete Waffenpreis berechnet werden soll
# Der Wert berechnet sich danach gemäß der "Preise von verbesserten Handwerksprodukten" (Ilaris:61).
# Der Wert gilt als sehr ungefähre Richtung. Einige Preise sind natürlich entsprechend lächerlich
zeige_preis = False
base_price = 180

# Die hier konfigurierten Werte werden in der Regel mit den Waffenwerten multipliziert
# Eine Waffe mit 2W6 Schaden erhält also 2 * ratingTPW6 Bewertungspunkte
ratingTPW6 = 3.5
ratingTPW20 = 10.5
ratingTPPlus = 1
ratingWM = 2
ratingHärte = 0.1

# Bei Bedarf können auch die Waffentalente zur Bewertung beitragen
# Die Liste ist beliebig erweiterbar
ratingTalent = {
    "Einhandhiebwaffen" : 0,
    "Zweihandhiebwaffen" : 0,
    "Einhandklingenwaffen" : 0,
    "Zweihandklingenwaffen" : 0,
    "Infanteriewaffen und Speere" : 0,
    "Lanzenreiten" : 0,
    "Handgemengewaffen" : 0,
    "Schilde" : 0,
    "Unbewaffnet" : 0,
    "Reiten" : 0,
    "Armbrüste" : 0,
    "Blasrohre" : 0,
    "Bögen" : 0,
    "Diskusse" : 0,
    "Kurze Wurfwaffen" : 0,
    "Schleudern" : 0,
    "Wurfspeere" : 0
}

# Waffeneigenschaften können einen festen Wert, aber auch Funktionen zur Berechnung definieren
# Der erste Parameter ist dann die Waffe, der zweite Parameter eine Liste von Waffeneigenschaft-Parametern als strings, z.B. "4" bei Schwer (4)
# Die Liste ist beliebig erweiterbar
ratingEigenschaften = {
    "Kopflastig" : 1,
    "Rüstungsbrechend" : 1,
    "Schild" : 2,
    "Stumpf" : 0,
    "Unberechenbar" : -2,
    "Wendig" : 1,
    "Zweihändig" : -2,
    "Schwer" : lambda waffe, params: int(params[0]) * 0, # immer 0, nur als Beispiel aufgeführt
    "Parierwaffe" : 1,
    "Reittier" : 2,
    "Zerbrechlich" : -1,
    "Niederwerfen" : lambda waffe, params: 4 - int(params[0]) if len(params) == 1 else 4,
    "Umklammern" : lambda waffe, params: -int(params[0]),
    "stationär" : -4
}

# Reichweite und Ladezeit werden durch Funktionen berechnet
def ratingReichweite(waffe):
    # 1 für jede Stufe ab 4
    if waffe.nahkampf or waffe.rw < 4:
        return 0
    return int(round(math.log2(waffe.rw))) - 1

def ratingLadezeit(waffe):
    # -4 für jede Stufe ab LZ 1
    if waffe.nahkampf or waffe.lz == 0:
        return 0

    return -4 * (int(round(math.log2(waffe.lz))) +1)

#================= Implementation ==================
def removeParameters(eigenschaft):
    return re.sub(r"\((.*?)\)", "", eigenschaft, re.UNICODE).strip()

waffen = sorted(datenbank.waffen.values(), key = lambda w: (0 if w.nahkampf else 1, w.talent, w.name))

lastTalent = ""
for waffe in waffen:
    if lastTalent != waffe.talent:
        lastTalent = waffe.talent
        print("\n=== " + waffe.talent + " ===")
    rating = 0
    if waffe.würfelSeiten == 6:
        rating += waffe.würfel * ratingTPW6
    else:
        rating += waffe.würfel * ratingTPW20
    rating += waffe.plus * ratingTPPlus
    rating += waffe.wm * ratingWM
    rating += waffe.härte * ratingHärte
    rating += ratingReichweite(waffe)
    rating += ratingLadezeit(waffe)
    if waffe.talent in ratingTalent:
        rating += ratingTalent[waffe.talent]
    for eigenschaft in waffe.eigenschaften:
        eig = removeParameters(eigenschaft)
        if not eig in ratingEigenschaften:
            continue
        rEig = ratingEigenschaften[eig]
        if not callable(rEig):
            rating += rEig
            continue
        match = re.search(r"\((.*?)\)", eigenschaft, re.UNICODE)
        if not match:
            rating += rEig(waffe, [])
        else:
            rating += rEig(waffe, list(map(str.strip, match.group(1).split(";"))))

    cv = round(rating, 1)
    if zeige_preis:
        print(f"{waffe.name+':' :<40}  {cv:<10} Preis: {round(base_price*2**((cv-10)/ratingTPPlus))} Silbertaler")
    else:
        print(f"{waffe.name+':':<40} {cv}")