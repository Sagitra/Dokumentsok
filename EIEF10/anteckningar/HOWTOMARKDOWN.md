# HOWTOMARKDOWN

Den här filen beskriver hur man skriver Markdown i `EIEF10/anteckningar`, baserat på:

- `https://ashki23.github.io/markdown-latex.html#markdown`

Den är också anpassad till hur den nuvarande renderaren i den här appen faktiskt fungerar.

## Viktig skillnad

Guiden ovan visar allmän Markdown- och LaTeX-syntax.

I den här appen fungerar just nu främst:

- rubriker med `#`, `##`, `###`
- kursiv text med `*text*`
- fet text med `**text**`
- punktlistor med `-` eller `*`
- inline-kod med en backtick på varje sida, till exempel `kod`
- kodblock med trippel-backticks
- inline-matte med `$...$`
- blockmatte med `$$ ... $$`

Allt annat bör betraktas som osäkert tills man har testat det i visaren.

## Grundregler

Skriv vanlig text som vanliga stycken.

Lämna en tom rad mellan stycken och mellan större block.

Exempel:

```md
Detta är första stycket.

Detta är andra stycket.
```

## Rubriker

Använd `#` för huvudrubrik, `##` för underrubrik och `###` för nivån under.

Exempel:

```md
# Begrepp
## EMK
### Kort förklaring
```

Rekommendation:

- använd högst `###` i anteckningarna
- håll rubriker korta

## Betoning

Kursiv text:

```md
*kursiv text*
```

Fet text:

```md
**fet text**
```

Inline-kod:

```md
`psi_m`
```

Rekommendation:

- använd inline-kod för filnamn, variabelnamn och kort syntax
- använd inte inline-kod för vanliga meningar

## Listor

Punktlista:

```md
- första punkt
- andra punkt
- tredje punkt
```

Det går också att använda `*`:

```md
* första punkt
* andra punkt
```

Rekommendation:

- använd `-` konsekvent i anteckningarna
- undvik djupa nästlade listor

## Kodblock

Använd tre backticks före och efter blocket.

Du skriver alltså:

- en rad som börjar med tre backticks
- sedan innehållet
- sedan en ny rad med tre backticks

Exempel på innehåll i ett kodblock:

```text
e_a = omega * psi_m
u_a = R_a * i_a + dpsi_a/dt + omega * psi_m
```

Om du vill visa Markdown-kod som exempel, märk gärna blocket med `md`.

Exempel på innehåll i ett Markdown-kodblock:

```text
## Rubrik
Vanlig text
```

## Matematik i text

Inline-matte skrivs med en dollar på varje sida:

```md
EMK:n ges av $e_a = \omega \psi_m$.
```

Exempel i löptext:

```md
vinkelhastigheten $\omega$ ökar
```

## Matematik på egen rad

Blockmatte skrivs med dubbla dollar före och efter formeln:

```md
$$
e_a = \omega \cdot \psi_m
$$
```

Ett större exempel:

```md
$$
u_a = R_a \cdot i_a + \frac{d\psi_a}{dt} + \omega \cdot \psi_m
$$
```

Regler:

- lägg `$$` på egna rader
- ha ingen vanlig text på samma rad som `$$`
- lämna gärna en tom rad före och efter blockmatte

## Vanliga LaTeX-kommandon

### Grekiska bokstäver

```md
\omega
\psi
\phi
\alpha
\beta
\gamma
\delta
\Delta
\lambda
\mu
```

Exempel:

```md
$\omega$, $\psi_m$, $\Delta t$
```

### Index och exponenter

Nedsänkt index:

```md
$u_a$
```

Upphöjt tal:

```md
$x^2$
```

Båda samtidigt:

```md
$x_i^2$
```

### Bråk

```md
\frac{a}{b}
```

Exempel:

```md
$\frac{d\psi_a}{dt}$
```

### Multiplikation

Vanligast i anteckningar:

```md
\cdot
```

Exempel:

```md
$T = \psi_m \cdot i_a$
```

### Rot

```md
\sqrt{x}
```

Exempel:

```md
$\sqrt{R^2 + X^2}$
```

### Relationer och symboler

```md
=
\approx
\neq
<
>
\leq
\geq
\in
\notin
\to
\Rightarrow
\pm
```

Exempel:

```md
$0 \leq x \leq 1$
```

## Rekommenderad stil i anteckningarna

Skriv begrepp så här:

```md
## EMK

Kort definition i vanlig text.

### Kort förklaring

Förklaring i 1 till 3 stycken.

$$
e_a = \omega \cdot \psi_m
$$

- punkt 1
- punkt 2
```

## Så bör formler skrivas

Bra:

```md
$$
u_a = R_a \cdot i_a + \frac{d\psi_a}{dt} + \omega \cdot \psi_m
$$
```

Mindre bra:

```md
$$ u_a = R_a i_a + ... $$
```

Skäl:

- block blir tydligare
- färre renderingsproblem
- lättare att läsa och redigera

## Så bör variabler skrivas i löptext

Bra:

```md
strömmen $i_a$ ökar när hastigheten $\omega$ ökar
```

Undvik:

```md
strömmen ia ökar när hastigheten omega ökar
```

## Så bör filer och källor skrivas

Filnamn skrivs med inline-kod:

```md
`Flik 6_LM.pdf`
```

Sökvägar skrivs också med inline-kod:

```md
`EIEF10/anteckningar/begrepp.md`
```

## Syntax från referensen som inte är säker i den här visaren

Den länkade guiden tar också upp:

- länkar som ``[text](url)``
- bilder som ``![alt](url)``
- citat med ``>``
- horisontella linjer med ``---``
- tabeller
- YAML-header
- HTML inuti markdown

De är giltiga som allmän Markdown-syntax enligt referensen, men de är inte säkert fullt stödda i den nuvarande renderaren här.

Om du vill använda dem, testa först i visaren.

## Kort fusklapp

Rubrik:

```md
## Rubrik
```

Punktlista:

```md
- punkt
```

Inline-kod:

```md
`kod`
```

Inline-matte:

```md
$\psi_m$
```

Blockmatte:

```md
$$
e_a = \omega \cdot \psi_m
$$
```

Kodblock:

Skriv först en rad med tre backticks, sedan innehållet, och avsluta med tre backticks på en egen rad.

## Källa

Sammanfattad och anpassad från:

- `https://ashki23.github.io/markdown-latex.html#markdown`
