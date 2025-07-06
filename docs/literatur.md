# Inhaltsverzeichnis

- [Radiomodul](#radiomodul)
- [Link Budget](#link-budget)
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

# Link Budget

Mithilfe einer Link Budget Berechnung (Leistungsübertragungsbilanz) lassen sich wahlweise die maximale Reichweite oder einzelne Parameter bei fester Reichweite berechnen.
Theorie zum Link Budget ist im Detail [hier](https://s.campbellsci.com/documents/us/technical-papers/link-budget.pdf) beschrieben.
[Hier](https://de.wikipedia.org/wiki/Leistungs%C3%BCbertragungsbilanz), [hier](https://en.wikipedia.org/wiki/Link_budget) und [hier](https://www.sss-mag.com/pdf/an9804.pdf) sind weitere Infors zu finden.

Allgemeine Formel (alle Größen in dB) für ein Link Budget beschreibt die Signalstärke am Empfänger und beinhaltet Größen, die die Empfangsstärke erhöhen (positives Vorzeichen) oder verringern (negatives Vorzeichen):

$P_\text{RX} = P_\text{TX} + G_\text{TX} - L_\text{TX} - L_\text{FS} - L_\text{M} + G_\text{RX} - L_\text{RX}$

Die Sendeleistung $P_\text{TX}$, der Gewinn der Sendeantenne $G_\text{TX}$ und die Übertragungsverluste (bspw. durch Kabeldämpfung) auf Sendeseite $L_\text{TX}$ sind sogenannte Senderparameter.
Die Signalstärke am Empfänger $P_\text{RX}$, der Gewinn der Empfangsantenne $G_\text{RX}$ und die Übertragungsverluste auf Empfangsseite $L_\text{RX}$ sind Empfängerparameter.
Die Freiraumdämpfung $L_\text{FS}$ und die übrigen Verluste während der Ausbreitung $L_\text{M}$ werden im Begriff Pfadverlust zusammengefasst.

Diese anderen Verluste sind z.B. Absorptionsverluste in der Atmosphäre, Verluste durch Diffraktion und Abschattung sowie Verluste durch Beugung an Hindernissen innerhalb der Fresnelzone (evtl. als Fading auftretend).

Die Freiraumdämpfung beschreibt die reduzierte Leistungsdichte einer EM-Welle bei steigendem Abstand zur Quelle:

$L_\text{FS} = 20 \cdot \text{log}_{10}\left(\frac{4 \pi r f}{c}\right)$ (mit $r$ als Abstand zur Sendeantenne und $f$ als verwendete Frequenz)

Die Formel für das Link Budget kann umgestellt werden, damit die maximal toleriebaren Verluste durch die Übertragung auf Sender- und Empfängerseite, sowie die Verluste durch die Übertragung berechnet werden können:

$L_\text{TX} + L_\text{RX} + L_\text{M} = P_\text{TX} - P_\text{RX} + G_\text{TX} + G_\text{RX} - L_\text{FS}$

Folgende Größen sind durch das Datenblatt des Radiomoduls gegeben:
$P_\text{TX} = 27 \text{dBm}$, $P_\text{RX, typ} = -118 \text{dBm}$, $P_\text{RX, min} = -114 \text{dBm}$

Eine QFH-Antenne, die gewählte Sendeantenne, hat keinen nennenswerten Gewinn:
$G_\text{TX} = 0$

Die für die Bodenstation gewählte Helixantenne kann je nach Bedarf angepasst werden, wobei ein höherer Gewinn eine genauere Ausrichtung der Antenne bedingt. 
Ein guter Startpunkt ist:
$G_\text{RX} = 10 \text{dBi}$

Die Freiraumdämpfung für die gewünschte maximale Reichweite von $18 \text{km}$ beträgt nach der oben gegebenen Formel:
$L_\text{FS} \approx 116 \text{dB}$

Somit gilt $L_\text{TX} + L_\text{RX} + L_\text{M} \approx 39 \text{dB}$ für $P_\text{RX, typ}$ und $L_\text{TX} + L_\text{RX} + L_\text{M} \approx 35 \text{dB}$ für $P_\text{RX, min}$.

Dieser Wert abzüglich der realen $L_\text{TX}$, $L_\text{RX}$ und $L_\text{M}$ wird als Fade Margin bezeichnet und ist eine Art Puffer.
Für zuverlässige Verbindungen, sollte dieser Wert größer als 20 oder 30 dB sein, nie jedoch kleiner als 10 dB.
Die realen Werte für  $L_\text{TX}$, $L_\text{RX}$ und $L_\text{M}$ können durch Messungen bestimmmt werden und wie die gesamte Formel schrittweise verifiziert und nachjustiert werden.

Ist die Fade Margin zu klein, kann mithilfe einer stärkeren Richtwirkung der Empfangsantenne oder dem Einbau eines Verstärkers das Empfangssignal verstärkt werden.
Ist die Fade Margin groß, kann beispielsweise die Datenrate erhöht werden oder die Richtwirkung der Empfangsantenne verringert werden.

[Hier}(linkbudget_beispiel.py) steht ein Python-Skript zur Verfügung, das die Berechnung des Link Budgets für einen exemplarischen Flugverlauf inklusive einer [graphischen Ausgabe](linkbudget_beispiel.png) zeigt.

Anmerkung: Reflexionsverluste als Teil von $L_\text{M}$ können wie in Kapitel 5.3 [hier](https://s.campbellsci.com/documents/us/technical-papers/link-budget.pdf) berechnet werden.

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
