# Inhaltsverzeichnis

- [Radiomodul](#radiomodul)
- [Platinendesign](#platinendesign)
- [Antennendesign](#antennendesign)
- [Antennenmessungen](#antennenmessungen)
- [Impedanzanpassung von Antennen](#impedanzanpassung-von-antennen)

# Radiomodul

Wir verwenden mehrere ähnliche Radiomodule der RC232-Produktfamilie des Herstellers Radiocrafts.
Die gesamte Produktfamilie ist [hier](https://radiocrafts.com/products/rc232/) zu finden.

Der Frequenzbereich zwischen 869,40 MHz und 869,65 MHz erlaubt eine hohe Sendeleistung, nachzulesen [hier](https://www.bundesnetzagentur.de/SharedDocs/Downloads/DE/Sachgebiete/Telekommunikation/Unternehmen_Institutionen/Frequenzen/Allgemeinzuteilungen/FunkanlagenGeringerReichweite/2018_05_SRD_pdf.pdf?__blob=publicationFile&v=2).

Relevant sind für uns vor allem die RC1180HP und RC1780HP Module, die die zulässige Sendeleistung von 500 mW (27 dBm) vollständig ausreizen.
Die entsprechenden Datenblätter sind unter folgenden Links zu finden:
- RC1180HP-RC232: [Link](https://radiocrafts.com/uploads/RC11xxHP-RC232_Data_Sheet.pdf)
- RC1780HP-RC232: [Link](https://radiocrafts.com/uploads/RC17xxHP-RC232_Datasheet.pdf)

Radiocrafts bietet verschiedene Anleitungen und Application Notes (AN) zum Umgang mit dem Modulen an.
- Radiocrafts RC232 Bedienungsanleitung: [Link](https://radiocrafts.com/uploads/RC232_user_manual.pdf)
- Radiocrafts Application Notes (AN) Übersicht: [Link](https://radiocrafts.com/resources/document-library/?rs=Application%20Notes)
- Radiocrafts AN001: Hints And Tips When Using RC1XX0 RF Modules: [Link](https://radiocrafts.com/uploads/AN001_Hints_and_Tips__Using_RC1xx0.pdf)
- Radiocrafts AN020: RF Module Troubleshotting: [Link](https://radiocrafts.com/uploads/AN020_RF_Module_Troubleshooting_Guide.pdf)
- Radiocrafts AN026: One Commong Footprint For Many Technologies: [Link](https://radiocrafts.com/uploads/AN026_One_Common_Footprint_For_Many_Technologies.pdf)

# Platinendesign

Radiocrafts bietet eine Application Note über das Design von RF-Platinen an, die AN061 (RF PCB Layout Recommendations): [Link](https://radiocrafts.com/uploads/AN061_RF_PCB_Layout_Recommendations.pdf)

Weitere Richtlinien zum Design von RF-Platinen: [Link](https://www.proto-electronics.com/blog/routing-guidelines-rf-pcb)

# Antennendesign

Viele Informationen zu Antennen:
[antenna-theory.com](https://www.antenna-theory.com/)

Informationen zu QFH-Antennen:
[jcoppens.com](https://jcoppens.com/ant/qfh/index.en.php)

Informationen zum Anschluss von QFH-Antennen:
[jcoppens.com](https://jcoppens.com/ant/qfh/adapt.en.php)

Informationen zu Helixantennen:
[jcoppens.com](https://jcoppens.com/ant/helix/index.en.php)

Artikel zu Helixantennen: [Link](https://www.microwaves101.com/encyclopedias/helix-antennas)

# Antennenmessungen

Viele Informationen zu Antennenmessungen:
[antenna-theory.com](https://www.antenna-theory.com/measurements/antenna.php)

Grundlagen zu Messgrößen bei Messungen mit einem VNA (S-Parameter):
[Youtube](https://youtu.be/-Pi0UbErHTY?si=Z9UQJC-R-1Vzc-xW)

Grundlagen zu Messgrößen bei Messungen mit einem VNA (Smith-Chart):
[Youtube](https://youtu.be/TsXd6GktlYQ?si=DfGhaZ3w0biYOcfI)

Antenne mit einem VNA vermessen und mit 4NEC2 simulieren:
[Youtube](https://youtu.be/l2c46uA50zg?si=s27nZCh-ScBlFWUF)

Antenne mit einem VNA vermessen:
[Youtube](https://youtu.be/rbXq0ZwjETo?si=DdEQ7rzXj86T0cxC)

Grundlagen zur Benutzung eines VNAs:
[Youtube](https://youtu.be/91ZRTFZ40rw?si=-yBII5ZVjXriQ2fS)

Design eines L-Matching Netzwerks mit einem VNA und einem Smith-Chart:
[Youtube](https://youtu.be/IgeRHDI-ukc?si=xvtN1C7xtP1WACcb)

# Impedanzanpassung von Antennen

Mehrteiliger Artikel zur Impedanzanpassung: [Link](https://www.electronicdesign.com/technologies/analog/whitepaper/21133206/back-to-basics-impedance-matching)

Kurzer Artikel zur Impedanzanpassung: [Link](https://www.escatec.com/blog/antenna-matching)
