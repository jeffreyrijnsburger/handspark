<p align="center"><img src="icons/handspark.svg" width="96" alt="HandSpark-logo"></p>

# HandSpark

**Een handgebaar. Een beetje magie in je videogesprek.**

HandSpark voegt acht gebarenreacties toe aan je Linux-webcam. Een hartje met
twee handen geeft hartjes; twee duimen omhoog geven vuurwerk; metal horns
met beide handen laten lasers verschijnen. Kies **Teams Effects** als camera
in Teams, Zoom of een andere video-app om de effecten in je gesprek te gebruiken.

Het is een knipoog naar Apples videoreacties op de Mac. De gebaren volgen
dezelfde indeling, met eigen animaties en herkenning via MediaPipe. Er zit geen
Apple-software of Apple-beeldmateriaal in. HandSpark is een onafhankelijk project.

**0.3.0 · MIT-licentie · Linux · Nederlands / Engels**

Download de nieuwste versie:
https://github.com/jeffreyrijnsburger/handspark/releases/latest

![HandSpark met een gegenereerde demo-persoon en de echte lasereffecten](docs/handspark-demo.png)

*De persoon is gegenereerd; de lasers komen uit de app. [Werkwijze](docs/DEMO.md).*

## Installeren

De `.deb` is bedoeld voor **Ubuntu 24.04 op Intel/AMD (amd64), met X11**.
Modellen, effecten en Python-afhankelijkheden zitten erin. OBS 30.2 of nieuwer,
Qt, FFmpeg en een werkende `v4l2loopback`-driver zijn systeemafhankelijkheden.
Windows en macOS worden in 0.3.0 niet ondersteund.

Volg de installatieopdrachten in [README.md](README.md#install-the-release).
Gebruik voor Ubuntu 24.04 OBS uit `noble-backports`. Open **HandSpark** uit het
toepassingenmenu en kies in Teams **Instellingen → Apparaten → Camera → Teams Effects**.
In Zoom kies je **Instellingen → Video → Camera → Teams Effects**.
Je microfoon blijft rechtstreeks in je video-app ingesteld.

## Gebaren

| Gebaar | Effect |
| --- | --- |
| Hartje maken met twee handen | Hartjes |
| Eén vredesteken (V) | Ballonnen |
| Eén duim omhoog | Duimpje omhoog |
| Eén duim omlaag | Duimpje omlaag |
| Twee duimen omlaag | Regen |
| Twee vredestekens | Confetti |
| Twee duimen omhoog | Vuurwerk |
| Metal horns met **beide** handen | Lasers |

Houd je handen duidelijk in beeld en het gebaar ongeveer een seconde vast.
Sluit bij duimen omhoog/omlaag je andere vingers en strek je duim volledig.
De animaties duren vijf seconden. Tussen reacties zit zes seconden pauze.
Laat hetzelfde gebaar los voordat je het herhaalt.
Lasers, vuurwerk, ballonnen en confetti verschijnen achter je lichaam.

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
lopende reactie. Sluiten van het venster laat de camera aan; **Camera stoppen**
zet hem uit. De toepassing start niet automatisch bij aanmelden.

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
