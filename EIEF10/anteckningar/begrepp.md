# Begrepp

## EMK

`EMK` står för `elektromotorisk kraft`. I kursmaterialet används begreppet för den spänning som induceras i en lindning när det magnetiska flödet ändras relativt lindningen.

### Grundidé

I `Flik 5_Elmek.pdf` beskrivs ankarlindningen som den lindning där EMK induceras. Det kan ske antingen för att huvudflödet roterar relativt lindningen, eller för att lindningen roterar relativt huvudflödet.

I `Flik 6_LM.pdf` förklaras att den inducerade spänningen i en likströmsmaskin ofta kallas mot-EMK, eftersom den enligt Lenz lag motverkar den ström som orsakar den. När motorn står stilla är hastigheten noll, och då har ingen mot-EMK byggts upp ännu. Därför kan startströmmen bli hög.

### Grundekvationer

För likströmsmaskinen gäller sambandet:

$$
e_a = \omega \cdot \psi_m
$$

Det betyder att EMK:n ökar när

- vinkelhastigheten $\omega$ ökar
- det sammanlänkade flödet $\psi_m$ ökar

I likströmsmaskinens rotorkrets kan spänningsekvationen skrivas som:

$$
u_a = R_a \cdot i_a + \frac{d\psi_a}{dt} + e_a
$$

eller omarrangerat:

$$
\frac{d\psi_a}{dt} = u_a - e_a - R_a \cdot i_a
$$

Om man antar linjär ankarkrets så att $\psi_a = L_a i_a$, får man också:

$$
L_a \frac{di_a}{dt} = u_a - e_a - R_a \cdot i_a
$$

### Tolkning

EMK är alltså inte en extra matningsspänning, utan en internt inducerad spänning i maskinen.

Praktiskt betyder det:

- låg hastighet ger låg EMK
- hög hastighet ger hög EMK
- högre EMK minskar den ström som en given matningsspänning driver genom rotorn

Det är därför motorn vid start kan ta stor ström, medan strömmen sjunker när motorn kommer upp i varv.

### Specialfall: stationär märkdrift

I märkdrift menar man normalt stationär märkdrift. Då antar man att driftfallet är konstant i tiden, så att ström, varvtal och flöden inte förändras. Därför blir

$$
\frac{d\psi_a}{dt} = 0
$$

Insatt i den allmänna rotorekvationen ger detta:

$$
0 = u_a - e_a - R_a \cdot i_a
$$

vilket kan skrivas som:

$$
e_a = u_a - R_a \cdot i_a
$$

Vid märkdrift sätter man sedan in märkstorheterna

- $u_a = u_n$
- $i_a = i_n$

och får:

$$
e_a = u_n - R_a \cdot i_n
$$

Detta är alltså inte en ny ekvation, utan den vanliga spänningsekvationen i det speciella fallet att maskinen går i stationär märkdrift.

### Specialfall: spänningstidsyta för en puls

När likströmsmaskinen matas med pulserad spänning, till exempel från en chopper eller en fyrkvadrantomvandlare, utgår man från:

$$
L_a \frac{di_a}{dt} = u_a - e_a - R_a \cdot i_a
$$

Under ett kort switchintervall gör man ofta två approximationer:

- den inducerade spänningen $e_a$ hinner nästan inte ändras
- resistansfallet $R_a i_a$ är litet jämfört med den pålagda puls-spänningen

Då kan ekvationen approximeras till:

$$
L_a \frac{di}{dt} \approx U - e_a
$$

här är $U$ den spänningsnivå som omvandlaren lägger på under just det intervallet.

Om spänningen hålls ungefär konstant under tiden $\Delta t$, kan derivatan approximeras med en ändringskvot:

$$
\frac{di}{dt} \approx \frac{\Delta i}{\Delta t}
$$

Insatt i ekvationen ger detta:

$$
L_a \frac{\Delta i}{\Delta t} \approx U - e_a
$$

och efter omarrangering:

$$
\Delta t\,(U - e_a) = L_a\,\Delta i
$$

Detta kallas spänningstidsytan för en puls.

Tolkningen är att:

- större spänningsskillnad $U - e_a$ ger snabbare strömändring
- längre pulstid $\Delta t$ ger större strömändring
- större induktans $L_a$ gör att strömmen ändras långsammare

Sambandet används därför för att uppskatta strömrippel i pulsmatade likströmsmaskiner.

### Viktigt i kursen

I kursens tentor, övningar och lösningsförslag används EMK ofta för att

- beräkna varvtal från spänning och flöde
- förstå varför startströmmen blir hög
- koppla ihop elektrisk modell och mekanisk hastighet
- uppskatta strömrippel vid pulsmatning

### Lokala källor

Följande ställen användes som underlag:

- `EIEF10/Kurskompendium/Flik 5_Elmek.pdf`: sidan `7-5`
- `EIEF10/Kurskompendium/Flik 6_LM.pdf`: sidorna `8-3`, `8-4`, `8-5`, `8-6`, `8-7`
- `EIEF10/Formelblad/formelblad.html`: avsnittet om likströmsmaskin och spänningstidsyta
- `EIEF10/Lösningsförslag/Losning EIEF10-20140530.pdf`: sidan `1`
- `EIEF10/Lösningsförslag/Losning EIEF10-20160603.pdf`: `LM 5`, där sambandet används för en spänningspuls

### En mening att minnas

`EMK är den inducerade spänningen i lindningen, och i en motor uppträder den ofta som en motspänning som växer med varvtalet.`

## Varför kan man skriva $\frac{d\psi_s}{dt} \approx u_s$?

### Utgångspunkt

I kursmaterialet för asynkronmaskinen skrivs statorekvationen som:

$$
\frac{d\psi_s}{dt} = u_s - R_s \cdot i_s
$$

Här är

- $u_s$ statorspänningsvektorn
- $R_s i_s$ spänningsfallet över statorlindningarnas resistans
- $\psi_s$ det sammanlänkade statorflödet

### Varför får man approximera?

Approximationen bygger på att termen $R_s i_s$ ofta är liten jämfört med $u_s$. Då blir skillnaden mellan

$$
u_s - R_s i_s
$$

och

$$
u_s
$$

liten, och man kan därför skriva:

$$
\frac{d\psi_s}{dt} \approx u_s
$$

Det betyder inte att resistansen är exakt noll, utan att resistansspänningsfallet är så litet att det kan försummas i just den analysen.

### Fysikalisk tolkning

Om man försummar $R_s i_s$ så bestäms flödesvektorns förändring nästan helt av den pålagda spänningsvektorn. Därför brukar man säga att:

- flödesvektorns spets rör sig i spänningsvektorns riktning
- hastigheten hos flödesvektorns spets är proportionell mot spänningsvektorns längd

Det är precis detta som används när man förklarar hur spänningsvektorer driver statorflödet i en asynkronmaskin.

### När är approximationen rimlig?

Approximationen är ofta bra när

- matningsspänningen är relativt stor
- statorresistansen är liten
- man inte arbetar vid alltför låga varvtal eller frekvenser

I de fallen dominerar spänningen $u_s$, medan resistansfallet $R_s i_s$ bara blir en liten korrektion.

### När är approximationen inte lika bra?

Vid låga varvtal eller låga frekvenser blir spänningen mindre, och då blir resistansfallet $R_s i_s$ inte längre försumbart. Då kan man inte utan vidare skriva

$$
\frac{d\psi_s}{dt} \approx u_s
$$

utan man måste ta med resistanstermen för att få rätt flöde och rätt moment.

### Kort sammanfattning

Man får approximera till bara $u_s$ därför att statorresistansens spänningsfall ofta är mycket mindre än den pålagda statorspänningen. Då är det spänningen som i första approximation styr hur statorflödet förändras.

### Lokala källor

- `EIEF10/Kurskompendium/Flik 8_AM.pdf`: ekvationerna `(10.9)` och `(10.10)`
- `EIEF10/Kurskompendium/Flik 8_AM.pdf`: texten direkt efter `(10.10)`, där tolkningen av flödesvektorn ges
- `EIEF10/Kurskompendium/Flik 8_AM.pdf`: avsnittet om spänningsvektorer och flödespolygon, där approximationen används
- `EIEF10/Övningar/Exercises2016.pdf`: uppgifterna där man uttryckligen antar `R_s = 0`

## Omvandlingar mellan $U_n$, $U_{fas}$, $U_h$, $i$ och $\psi$

### Grundregel

I kursen blandas ofta tre olika typer av storheter:

- fasstorhet
- huvudstorhet
- vektorstorhet

Dessutom måste man hålla isär:

- effektivvärde, RMS
- toppvärde

Det är här faktorer som $\sqrt{2}$ och $\sqrt{3}$ kommer in.

### Vad betyder symbolerna?

I den här kursen används ofta:

- $U_{fas}$ = fasspänningens effektivvärde
- $U_h$ = huvudspänningens effektivvärde
- $\hat U_{fas}$ = fasspänningens toppvärde
- $I_f$ = fasströmmens effektivvärde
- $\hat I_f$ = fasströmmens toppvärde
- $\lvert \bar u_s \rvert$ = spänningsvektorns längd
- $\lvert \bar i_s \rvert$ = strömvektorns längd
- $\lvert \bar \psi_s \rvert$ eller $\lvert \bar \psi_m \rvert$ = flödesvektorns längd

I det här avsnittet betyder alltså versalt $I_f$ fasström. Det ska inte blandas ihop med litet $i_f$, som ofta används för fältström i likströmsmaskiner.

### När använder man $\sqrt{2}$?

$\sqrt{2}$ används när man går mellan effektivvärde och toppvärde för en sinusformad storhet:

$$
\hat U_{fas} = \sqrt{2}\,U_{fas}
$$

$$
U_{fas} = \frac{\hat U_{fas}}{\sqrt{2}}
$$

och på samma sätt för ström:

$$
\hat I_f = \sqrt{2}\,I_f
$$

$$
I_f = \frac{\hat I_f}{\sqrt{2}}
$$

Alltså:

- gånger $\sqrt{2}$ när du går från RMS till toppvärde
- dividera med $\sqrt{2}$ när du går från toppvärde till RMS

### När använder man $\sqrt{3}$ för spänning?

För ett symmetriskt trefassystem gäller mellan huvudspänning och fasspänning:

$$
U_h = \sqrt{3}\,U_{fas}
$$

$$
U_{fas} = \frac{U_h}{\sqrt{3}}
$$

Alltså:

- gånger $\sqrt{3}$ när du går från fasspänning till huvudspänning
- dividera med $\sqrt{3}$ när du går från huvudspänning till fasspänning

### Spänningsvektor vid effektinvariant transformation

I formelbladet står:

$$
\bar u_s(t) = \sqrt{\frac{3}{2}}\,\hat u_{fas}\,e^{j\omega t} = U_h\,e^{j\omega t}
$$

Det betyder att spänningsvektorns längd blir:

$$
\lvert \bar u_s \rvert = U_h
$$

alltså samma som huvudspänningens effektivvärde.

Samma samband kan därför skrivas:

$$
\lvert \bar u_s \rvert = U_h = \sqrt{3}\,U_{fas} = \sqrt{\frac{3}{2}}\,\hat U_{fas}
$$

Detta är ett av de viktigaste sambanden i kursen.

### Strömvektor vid effektinvariant transformation

I formelbladet står:

$$
\bar i_s(t) = \sqrt{\frac{3}{2}}\,\hat I_f\,e^{j(\omega t-\varphi)} = \sqrt{3}\,I_f\,e^{j(\omega t-\varphi)}
$$

Det betyder att strömvektorns längd blir:

$$
\lvert \bar i_s \rvert = \sqrt{3}\,I_f
$$

eller också:

$$
\lvert \bar i_s \rvert = \sqrt{\frac{3}{2}}\,\hat I_f
$$

Alltså:

- från fasström RMS till vektorlängd: gånger $\sqrt{3}$
- från fasström toppvärde till vektorlängd: gånger $\sqrt{3/2}$
- från vektorlängd till fasström RMS: dividera med $\sqrt{3}$

### Viktigt om linjeström och fasström

För ström måste man först veta om uppgiften avser fasström eller linjeström.

I Y-koppling gäller:

$$
I_h = I_f
$$

I D-koppling gäller:

$$
I_h = \sqrt{3}\,I_f
$$

Det betyder att man inte får använda $\sqrt{3}$ blint på strömmar utan först kontrollera om det är fasström eller linjeström som är given.

### Flödesvektor

För flöde används ofta samma idé som för spänning och ström vid effektinvariant transformation.

Om en uppgift ger sammanlänkat flöde i en fas som toppvärde, gäller:

$$
\lvert \bar \psi \rvert = \sqrt{\frac{3}{2}}\,\hat \psi_{fas}
$$

Om fasflödet i stället ges som effektivvärde, blir:

$$
\lvert \bar \psi \rvert = \sqrt{3}\,\psi_{fas}
$$

Alltså:

- fasflöde toppvärde till vektorlängd: gånger $\sqrt{3/2}$
- fasflöde RMS till vektorlängd: gånger $\sqrt{3}$

I många synkronmaskinsuppgifter står det till exempel att magnetiseringen är ett visst sammanlänkat flöde i en fas. Då måste man kontrollera om det är toppvärde eller effektivvärde innan man gör om det till vektorlängd.

### Kort tabell

För symmetriska sinusformade storheter och effektinvariant transformation:

- fas RMS till fas topp: gånger $\sqrt{2}$
- fas topp till fas RMS: dela med $\sqrt{2}$
- fasspänning RMS till huvudspänning RMS: gånger $\sqrt{3}$
- huvudspänning RMS till fasspänning RMS: dela med $\sqrt{3}$
- fas topp till vektorlängd: gånger $\sqrt{3/2}$
- fas RMS till vektorlängd: gånger $\sqrt{3}$
- vektorlängd till fas RMS: dela med $\sqrt{3}$
- vektorlängd till fas topp: gånger $\sqrt{2/3}$

### Hur man brukar tänka i uppgifter

Om du får en märkspänning $U_n = 400$ V för en trefasmaskin, så är det ofta huvudspänningens effektivvärde. Då gäller:

$$
U_h = U_n = 400\text{ V}
$$

och fasspänningen blir:

$$
U_{fas} = \frac{400}{\sqrt{3}} \text{ V}
$$

Spänningsvektorns längd blir samtidigt:

$$
\lvert \bar u_s \rvert = U_h = 400\text{ V}
$$

Om du i stället får en fasström på 10 A effektivvärde, blir strömvektorns längd:

$$
\lvert \bar i_s \rvert = \sqrt{3}\cdot 10 = 17.3\text{ A}
$$

### Vanliga misstag

- att blanda ihop huvudspänning och fasspänning
- att använda $\sqrt{2}$ när man egentligen ska använda $\sqrt{3}$
- att använda $\sqrt{3}$ på ström utan att först veta om det är fasström eller linjeström
- att glömma om en given flödesstorhet är toppvärde eller effektivvärde
- att blanda ihop fasstorhet och vektorstorhet

### Lokala källor

- `EIEF10/Formelblad/formelblad.html`: vektorformlerna för $\bar u_s$, $\bar i_s$ och $\bar \psi_s$
- `EIEF10/Kurskompendium/Flik 10_Appendix B.pdf`: effektinvariant transformation
- `EIEF10/Lösningsförslag/Losning EIEF10-20160603.pdf`: uppgifter där huvudspänning, vektorlängd och flödesvektor kopplas ihop
- `EIEF10/Lösningsförslag/Losning EIEF10-20140530.pdf`: exempel där fasström omvandlas till vektorlängd
