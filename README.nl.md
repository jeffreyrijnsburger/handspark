<p align="center"><img src="icons/handspark.svg" width="96" alt="HandSpark-logo"></p>

# HandSpark

**Een handgebaar. Een beetje magie in je videogesprek.**

HandSpark voegt acht gebarenreacties toe aan je Linux-webcam. Een hartje met
twee handen geeft hartjes; twee duimen omhoog geven vuurwerk; metal horns
met beide handen laten lasers verschijnen. Kies **Teams Effects** als camera
in Teams, Zoom of een andere video-app om de effecten in je gesprek te gebruiken.

Het is een knipoog naar Apples videoreacties op de Mac. De gebaren volgen
dezelfde indeling, met eigen animaties en herkenning via MediaPipe en HaGRID. Er zit geen
Apple-software of Apple-beeldmateriaal in. HandSpark is een onafhankelijk project.

**0.7.0 · MIT-licentie · Linux · Nederlands / Engels**

Download de nieuwste versie:
https://github.com/jeffreyrijnsburger/handspark/releases/latest

![HandSpark met een gegenereerde demo-persoon en de echte lasereffecten](docs/handspark-demo.png)

*De persoon is gegenereerd; de lasers komen uit de app. [Werkwijze](docs/DEMO.md).*

## Installeren

De `.deb` is bedoeld voor **Ubuntu 24.04 op Intel/AMD (amd64), met X11**.
Modellen, effecten en Python-afhankelijkheden zitten erin. OBS 30.2 of nieuwer,
Qt, FFmpeg en een werkende `v4l2loopback`-driver zijn systeemafhankelijkheden.
Windows en macOS worden in 0.7.0 niet ondersteund.

Volg de installatieopdrachten in [README.md](README.md#install-the-release).
Gebruik voor Ubuntu 24.04 OBS uit `noble-backports`. Open **HandSpark** uit het
toepassingenmenu en kies in Teams **Instellingen → Apparaten → Camera → Teams Effects**.
In Zoom kies je **Instellingen → Video → Camera → Teams Effects**.
Je microfoon blijft rechtstreeks in je video-app ingesteld.

## Gebaren

| Gebaar | Effect |
| --- | --- |
| 🫶 Hartje maken met twee handen | <img src="icons/heart.svg" width="24" height="24" alt=""> Hartjes |
| ✌️ Eén vredesteken (V) | <img src="icons/balloons.svg" width="24" height="24" alt=""> Ballonnen |
| 👍 Eén duim omhoog | <img src="emoji/emoji_u1f44d.png" width="24" height="24" alt=""> Duimpje omhoog |
| 👎 Eén duim omlaag | <img src="emoji/emoji_u1f44e.png" width="24" height="24" alt=""> Duimpje omlaag |
| 👎👎 Twee duimen omlaag | <img src="icons/rain.svg" width="24" height="24" alt=""> Regen en bliksem |
| ✌️✌️ Twee vredestekens (V) | <img src="icons/confetti.svg" width="24" height="24" alt=""> Confetti |
| 👍👍 Twee duimen omhoog | <img src="icons/fireworks.svg" width="24" height="24" alt=""> Vuurwerk |
| 🤘🤘 Metal horns met **beide** handen | <img src="icons/lasers.svg" width="24" height="24" alt=""> Lasers |

Voor duim omhoog/omlaag gebruikt HandSpark ook een klein HaGRID-model dat de
hand op het beeld beoordeelt. Dat ondersteunt natuurlijke houdingen naast de
handpunten van MediaPipe. Het werkt lokaal en zit in de download; je hoeft er
geen dataset voor te installeren. Zie [herkenning en validatie](docs/HAGRID.md).

Houd je handen duidelijk in beeld en het gebaar ongeveer een seconde vast.
Voor duim omhoog/omlaag krul je de andere vingers en wijs je de duim duidelijk
omhoog of omlaag. Een losse vuist en een licht gekantelde hand zijn prima.
De animaties duren vijf seconden. Tussen reacties zit zes seconden pauze.
Laat hetzelfde gebaar los voordat je het herhaalt.
Lasers, vuurwerk, ballonnen en confetti verschijnen achter je lichaam.

De regenreactie heeft een belichte wolk, vallende druppels en twee vertakte
bliksemflitsen. De gouden duim omhoog springt in beeld met een klein knikje en ronde confettistipjes.
De duim omlaag verschijnt in een glanzende bubbel.

## Camera-uitvoer

Bij **Camera-uitvoer** kies je 360p, 540p of 720p, altijd met 30 fps.
De standaard is **360p / 30 fps**; dit is het beeld dat de virtuele camera
aan je video-app levert. Wijzigen herstart de camera kort. Doe dit voor een gesprek.
Teams bepaalt daarna zelf de verzendkwaliteit; minder vertraging is niet gegarandeerd.

De instelling **Voorbeeld** geldt alleen voor het venster. Met de CLI:

```sh
handspark output --resolution 360
handspark restart
handspark output --json
```

## Bedienen en taal

Het livevoorbeeld toont maximaal 30 fps. Onder **Voorbeeld** kies je **360p,
540p of 720p** en **15, 24 of 30 fps**. Standaard staat het op 360p/30 fps.
De keuze wordt direct toegepast en onthouden. Hiermee verander je het
voorbeeldvenster; de aparte instelling hierboven bepaalt de uitvoer voor je gesprek.

In het venster zie je het uiteindelijke camerabeeld en acht reactieknoppen.
**Automatische reacties** pauzeert de gebarenherkenning.
**Effecten achter mij** bedient het personenmasker. **Effect stoppen** wist de
lopende reactie. **Camera uitschakelen** stopt het camerabeeld, de virtuele
camera en de reacties van HandSpark voor je video-app. Met **Camera inschakelen**
zet je ze weer aan.

HandSpark start standaard in het systeemvak, met de camera actief en zonder
zichtbaar venster of livevoorbeeld. Open de bediening via het icoon bij de klok
en **HandSpark openen**. Zet **Starten in systeemvak** uit als het venster bij
volgende starts direct moet verschijnen. Open je HandSpark terwijl het al
draait, dan verschijnt de bediening. Deze keuze staat los van het kruisje.
Zonder ingeschakeld en beschikbaar systeemvak opent het venster wel. Ook een
fout bij het starten van de camera opent de bediening, zodat je opnieuw kunt proberen.

Bij **Bij sluiten (×)** kies je wat het kruisje doet. De keuze wordt onthouden:

- **Camera en OBS afsluiten** (standaard): stopt beeld en reacties en sluit
  de OBS af die HandSpark zelf heeft gestart. Een apart gestarte OBS blijft open.
- **Camera aan laten**: sluit het HandSpark-venster en laat de camera draaien.
  Open HandSpark opnieuw of gebruik `handspark stop` om hem uit te schakelen.
- **Verbergen in systeemvak**: verbergt het venster, met camera en reacties
  actief. Het verborgen livevoorbeeld pauzeert om rekenkracht te besparen.

**Icoon in systeemvak tonen** is instelbaar en staat standaard aan waar ondersteund.
Via het icoon bij de klok kun je HandSpark openen, de camera bedienen of
**Afsluiten** kiezen. **Afsluiten** stopt altijd de camera en de door HandSpark
gestarte OBS, ongeacht de instelling van het kruisje. Zet je het icoon uit,
dan start HandSpark weer met een zichtbaar venster en verandert verbergen bij
sluiten in afsluiten. Zonder beschikbaar systeemvak
valt verbergen veilig terug op afsluiten. Na een OBS-fout start de camera pas
weer als je hem zelf inschakelt. Automatisch starten bij aanmelden staat voor
nieuwe installaties uit.

```sh
handspark on-start tray        # Starten in systeemvak (standaard)
handspark on-start window      # Starten met zichtbaar venster
handspark on-close stop        # Camera en OBS afsluiten
handspark on-close background  # Camera aan laten
handspark on-close tray        # Verbergen in systeemvak
handspark tray off             # Systeemvakicoon uit
```

Onderaan kies je **Nederlands** of **English**. De taal verandert direct en
wordt onthouden. De standaard voor nieuwe installaties is Engels; een bestaande Nederlandse keuze blijft behouden. Via de terminal kan het ook:

```sh
handspark language nl
handspark language en
handspark react lasers
handspark cancel
handspark stop
```

Alle verwerking gebeurt lokaal. Er worden geen camerabeelden opgenomen of
geüpload. Bij weinig licht, snelle bewegingen of verborgen vingers kan de
herkenning of het masker afwijken; je kunt reacties ook handmatig starten.

## Voor ontwikkelaars en AI-agents

De software mag vrij gebruikt, aangepast en verspreid worden onder de
MIT-licentie. Agents vinden instructies in [AGENTS.md](AGENTS.md), `llms.txt`
en [docs/CLI.md](docs/CLI.md). `handspark commands --json` toont de bediening.
De JSON-status bevat geen camerabeeld en start de camera niet.

De volledige technische uitleg, installatie, probleemoplossing en credits staan
in [README.md](README.md). Bouwen en testen: [docs/BUILDING.md](docs/BUILDING.md).
