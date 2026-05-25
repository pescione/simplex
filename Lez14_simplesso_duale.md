# Metodo del simplesso duale

> **Fonte:** conversione fedele delle slide `Lez14.pdf`.
>
> Argomenti della lezione:
> - analisi duale del metodo del simplesso;
> - metodo del simplesso duale;
> - riferimento indicato nelle slide: Fi 4.6, 4.7.

---

## 1. Metodo del Simplesso in forma matriciale

### Input

- $A, b, c$
- $B = [A_{B(1)}, \ldots, A_{B(m)}]$, cioè una **base ammissibile iniziale**.

### Output

- $x$ soluzione ottima, oppure
- `illim = true`, cioè problema illimitato.

### Algoritmo

```text
Init.
    illim := false
    opt := false

Main Loop
    while (illim = false and opt = false)
        calcola B^{-1}

        Test Opt(B^{-1}) → \bar c, opt

        if (opt = true) then
            return [x_B, x_F] = [B^{-1}b, 0]
        else
            scegli h ∉ {B(1), ..., B(m)} con \bar c_h < 0

            Test Illim(B^{-1}, h) → \bar A_h, illim

            if (illim = true) then
                STOP: problema illimitato
            else
                calcola
                    t := argmin_{i∈{1,...,m}} { \bar b_i / \bar a_{ih} : \bar a_{ih} > 0 }

                Update B:
                    B(t) := h
            end if
        end if
    end while
```

---

## 2. Test di ottimalità del simplesso primale

### Test Opt

#### Input

- $B^{-1}$

#### Output

- $\bar c$
- $opt \in \{true,false\}$

#### Procedura

```text
Init.
    opt := false

calcola
    u^T = c_B^T B^{-1}
    \bar c_F^T := c_F^T - u^T F

Test
    if \bar c_F ≥ 0 then
        opt := true
```

---

## 3. Condizioni di ottimalità in forma standard

Il metodo del Simplesso si applica a problemi in **forma standard**.

Per una coppia primale-duale di vettori:

$$
x \in \mathbb{R}^n, \qquad u \in \mathbb{R}^m
$$

le condizioni di ottimalità sono:

1. **Ammissibilità primale**

$$
Ax = b, \qquad x \ge 0
$$

2. **Ammissibilità duale**

$$
u^T A \le c^T
$$

3. **Scarto complementare**

$$
(c^T - u^T A)x = 0
$$

Infatti, l’altra condizione di scarto complementare

$$
u^T(Ax-b)=0
$$

è sempre verificata quando $Ax=b$.

Quindi:

> I vettori $x \in \mathbb{R}^n$ e $u \in \mathbb{R}^m$ sono soluzioni ottime rispettivamente per il problema primale e duale **se e solo se** valgono:
>
> $$(i)\; Ax=b,\ x\ge 0$$
>
> $$(ii)\; u^TA\le c^T$$
>
> $$(iii)\; (c^T-u^TA)x=0$$

---

## 4. Analisi duale del metodo del simplesso primale

Alla generica iterazione, il metodo del simplesso calcola i vettori:

$$
x = (B^{-1}b,0) \ge 0
$$

$$
u^T = c_B^T B^{-1}
$$

$$
\bar c^T = c^T - u^T A
$$

Il metodo si arresta quando:

$$
\bar c \ge 0
$$

### Cosa è sempre vero durante il simplesso primale

- La soluzione di base ammissibile corrente $x$ è ammissibile per il problema primale.

Quindi la condizione:

$$
(i)\quad Ax=b,\ x\ge 0
$$

è soddisfatta.

- Inoltre:

$$
(c^T-u^TA)x
= (c_B^T-u^TB)x_B + (c_F^T-u^TF)x_F
=0
$$

Quindi anche la condizione di scarto complementare:

$$
(iii)\quad (c^T-u^TA)x=0
$$

è soddisfatta.

### Cosa non è sempre vero durante il simplesso primale

La condizione:

$$
(ii)\quad u^TA \le c^T
$$

è soddisfatta solo quando:

$$
\bar c^T = c^T - u^T A \ge 0
$$

cioè quando il **Test Opt** restituisce `true` e il metodo si arresta.

Quindi, alla generica iterazione:

> Il vettore $u^T = c_B^T B^{-1}$ **non è necessariamente una soluzione ammissibile del problema duale**, mentre lo diventa alla terminazione.

---

## 5. Idea del metodo del simplesso duale

Le condizioni di ottimalità sono:

$$
(i)\quad Ax=b,\ x\ge 0 \qquad \text{ammissibilità primale}
$$

$$
(ii)\quad u^TA\le c^T \qquad \text{ammissibilità duale}
$$

$$
(iii)\quad (c^T-u^TA)x=0 \qquad \text{scarto complementare}
$$

Il metodo del simplesso duale rovescia il punto di vista rispetto al simplesso primale.

### Nel simplesso primale

Durante l’esecuzione si mantengono:

- ammissibilità primale;
- scarto complementare.

L’ammissibilità duale arriva solo alla fine.

### Nel simplesso duale

Si sviluppa un algoritmo che mantiene sempre:

- ammissibilità duale;
- scarto complementare.

Mentre l’ammissibilità primale viene ottenuta solo alla terminazione.

Quindi:

> $x$ è una **soluzione di base non ammissibile** durante l’esecuzione.
>
> Il metodo si arresta quando certifica l’ammissibilità primale.

Il metodo si applica al problema primale:

$$
\min\{c^T x : Ax=b,\ x\ge 0\}
$$

---

## 6. Metodo del simplesso duale: implementazione tableau

Il metodo richiede un tableau iniziale in **forma canonica** del tipo:

```text
             x_1  ...  x_t  ...  x_m | x_{m+1} ... x_h ... x_n | RHS
---------------------------------------------------------------------
riga 0       0    ...   0   ...   0  | \bar c_{m+1} ... \bar c_h ... \bar c_n | \bar c_0 = -z
---------------------------------------------------------------------
x_1          1    ...   0   ...   0  | \bar a_{1,m+1} ... ... \bar a_{1,n} | \bar b_1
...
x_t          0    ...   1   ...   0  | \bar a_{t,m+1} ... \bar a_{t,h} ... \bar a_{t,n} | \bar b_t
...
x_m          0    ...   0   ...   1  | \bar a_{m,m+1} ... ... \bar a_{m,n} | \bar b_m
```

con:

$$
\bar c_1,\ldots,\bar c_n \ge 0
$$

cioè con **ammissibilità duale**.

Se inoltre:

$$
\bar b_1,\ldots,\bar b_m \ge 0
$$

allora il tableau è **ottimo**.

---

## 7. Scelta della variabile uscente

Se non vale:

$$
\bar b_1,\ldots,\bar b_m \ge 0
$$

allora si seleziona una variabile di base $x_i$ per cui:

$$
\bar b_i < 0
$$

Questa è la **variabile uscente**.

Supponiamo di scegliere $x_t$, con:

$$
\bar b_t < 0
$$

Si hanno due casi.

---

### Caso 1: tutti i coefficienti della riga sono non negativi

Se:

$$
\bar a_{tj} \ge 0, \qquad j=1,\ldots,n
$$

allora:

$$
\sum_{j=1}^n \bar a_{tj}x_j \ge 0
$$

per ogni:

$$
x \ge 0
$$

Quindi l’equazione associata alla riga $t$ del tableau **non può essere soddisfatta**, perché il termine noto è negativo:

$$
\bar b_t < 0
$$

Conclusione:

> Il problema è **inammissibile**.

---

### Caso 2: esiste almeno un coefficiente negativo nella riga

Se esistono indici $j$ tali che:

$$
\bar a_{tj}<0
$$

allora facendo pivot su un elemento $(t,j)$ con coefficiente negativo, il termine noto $\bar b_t$ diventa positivo.

---

## 8. Scelta della variabile entrante

Scegliamo un elemento della riga uscente con coefficiente negativo:

$$
\bar a_{th}<0
$$

L’operazione di pivot calcola i nuovi valori nella riga 0:

$$
\tilde c_j := \bar c_j - \frac{\bar c_h}{\bar a_{th}}\bar a_{tj},
\qquad j=1,\ldots,n
$$

Inoltre:

$$
\tilde c_0 = \bar c_0 - \frac{\bar c_h}{\bar a_{th}}\bar b_t
$$

Per mantenere l’ammissibilità duale, bisogna imporre:

$$
\tilde c_j \ge 0
$$

cioè:

$$
\bar c_j \ge \frac{\bar c_h}{\bar a_{th}}\bar a_{tj}
$$

che si può scrivere come:

$$
\bar c_j \ge \frac{\bar c_h}{-\bar a_{th}}(-\bar a_{tj}),
\qquad j=1,
\ldots,n
$$

Poiché:

$$
\bar c_j \ge 0
$$

questa condizione è sempre vera se:

$$
\bar a_{tj}\ge 0
$$

Se invece:

$$
\bar a_{tj}<0
$$

allora la condizione diventa:

$$
\bar c_j \ge \frac{\bar c_h}{-\bar a_{th}}(-\bar a_{tj})
$$

ovvero:

$$
\frac{\bar c_j}{|\bar a_{tj}|}
\ge
\frac{\bar c_h}{|\bar a_{th}|}
$$

Quindi la variabile entrante $h$ è individuata da:

$$
h := \arg\min_{j=1,\ldots,n}
\left\{
\frac{\bar c_j}{|\bar a_{tj}|}:\ \bar a_{tj}<0
\right\}
$$

---

## 9. Convergenza

La scelta della variabile uscente mira a:

> ridurre l’inammissibilità primale, cioè scegliere una riga con $\bar b_t<0$.

La scelta della variabile entrante mira a:

> mantenere l’ammissibilità duale, cioè mantenere $\bar c\ge 0$.

La variazione del valore della funzione obiettivo è:

$$
\tilde z-z
=\bar c_0-\tilde c_0
=\frac{\bar c_h\bar b_t}{\bar a_{th}}
=\bar c_h\left|\frac{\bar b_t}{\bar a_{th}}\right|
\ge 0
$$

Quindi, se:

$$
\bar c_h \ne 0
$$

cioè in assenza di **degenerazione duale**, il valore della soluzione “più che ottima” peggiora ad ogni iterazione.

In presenza di degenerazione duale, la convergenza è garantita dall’applicazione di regole di pivoting anticiclaggio, ad esempio:

> la **regola di Bland**.

---

## 10. Interpretazione geometrica

Geometricamente, invece di esplorare i vertici ammissibili come nel simplesso primale, il simplesso duale parte da soluzioni di base:

- **non ammissibili**;
- “più che ottime”.

Poi procede avvicinandosi verso soluzioni di base ammissibili.

Nelle slide è mostrata una figura con gli assi $x_1$ e $x_2$, alcuni punti indicati come $A$, $B$, $C$ e un punto $P$ esterno/non ammissibile da cui il metodo si avvicina alla regione ammissibile.

---

## 11. Esempio

Consideriamo il problema:

$$
\min 3x_1+4x_2+5x_3
$$

soggetto a:

$$
2x_1+2x_2+x_3\ge 6
$$

$$
x_1+2x_2+3x_3\ge 5
$$

$$
x_1,x_2,x_3\ge 0
$$

Introducendo le variabili di surplus $x_4,x_5$, il problema diventa:

$$
\min 3x_1+4x_2+5x_3
$$

soggetto a:

$$
2x_1+2x_2+x_3-x_4=6
$$

$$
x_1+2x_2+3x_3-x_5=5
$$

$$
x_1,x_2,x_3,x_4,x_5\ge 0
$$

Da cui il tableau:

```text
 3   4   5   0   0   0
 2   2   1  -1   0   6
 1   2   3   0  -1   5
```

Applicando il simplesso primale si eseguirebbe la **FASE I**.

---

## 12. Esempio: tableau iniziale per il simplesso duale

Cambiando segno alle righe si ottiene un tableau iniziale per il simplesso duale:

```text
 3   4   5   0   0   0
-2  -2  -1   1   0  -6
-1  -2  -3   0   1  -5
```

Scegliamo $x_4$ come variabile uscente, cioè la riga:

$$
t=1
$$

Poiché nella riga 1 abbiamo coefficienti negativi, scegliamo la variabile entrante usando:

$$
h=\arg\min\left\{
\frac{\bar c_j}{|\bar a_{tj}|}:\ j\in\{1,\ldots,n\},\ \bar a_{tj}<0
\right\}
$$

Quindi:

$$
h=\arg\min\left\{
\frac{\bar c_1}{|\bar a_{11}|}=\frac{3}{2},
\frac{\bar c_2}{|\bar a_{12}|}=2,
\frac{\bar c_3}{|\bar a_{13}|}=5
\right\}=1
$$

Dunque entra $x_1$.

---

## 13. Esempio: primo pivot

Eseguiamo:

$$
PIVOT(1,1)
$$

ottenendo il nuovo tableau:

```text
0   1   7/2   3/2   0   -9
1   1   1/2  -1/2   0    3
0  -1  -5/2  -1/2   1   -2
```

L’unica riga con:

$$
\bar b_t<0
$$

è:

$$
t=2
$$

quindi $x_5$ è la variabile uscente.

Per la variabile entrante:

$$
h=\arg\min\left\{
\frac{\bar c_2}{|\bar a_{22}|}=1,
\frac{\bar c_3}{|\bar a_{23}|}=\frac{7}{5},
\frac{\bar c_4}{|\bar a_{24}|}=3
\right\}=2
$$

Dunque entra $x_2$.

---

## 14. Esempio: secondo pivot e soluzione ottima

Eseguiamo:

$$
PIVOT(2,2)
$$

ottenendo il nuovo tableau:

```text
0   0   1     1     1   -11
1   0  -2    -1     1     1
0   1   5/2   1/2  -1     2
```

La soluzione è:

$$
(x_1,x_2,x_3,x_4,x_5)=(1,2,0,0,0)
$$

Questa soluzione è ammissibile primale, quindi è **ottima**.

---

## 15. Se aggiungessimo un vincolo?

Supponiamo di aggiungere il vincolo:

$$
3x_1+x_2+x_3\le 4
$$

Questo vincolo **non è soddisfatto** dalla soluzione ottima precedente.

Aggiungendo la variabile slack è possibile includerlo nel tableau:

```text
0   0   1     1     1   0   -11
1   0  -2    -1     1   0     1
0   1   5/2   1/2  -1   0     2
3   1   1     0     0   1     4
```

---

## 16. Di nuovo simplesso duale

Mettendo in forma canonica con la slack in base, si ottiene:

```text
0   0   1     1     1   0   -11
1   0  -2    -1     1   0     1
0   1   5/2   1/2  -1   0     2
0   0   9/2   5/2  -2   1    -1
```

Poiché:

$$
\bar b_3<0
$$

non abbiamo ammissibilità primale.

Applicando nuovamente il simplesso duale si individua l’elemento di pivot:

$$
(3,5)
$$

Il nuovo tableau, ottimo, è:

```text
0   0   13/4   9/4   0    1/2   -23/2
1   0    1/4   1/4   0    1/2     1/2
0   1    1/4  -3/4   0   -1/2     5/2
0   0   -9/4  -5/4   1   -1/2     1/2
```

La nuova soluzione ottima è:

$$
(x_1,x_2,x_3,x_4,x_5,x_6)=\left(\frac12,\frac52,0,0,\frac12,0\right)
$$

---

## 17. Schema operativo del simplesso duale

Questa sezione riassume fedelmente la logica applicativa delle slide.

### Precondizione

Serve un tableau canonico con:

$$
\bar c_j\ge 0 \quad \forall j
$$

cioè ammissibilità duale.

### Passo 1: test di ottimalità

Se:

$$
\bar b_i\ge 0 \quad \forall i
$$

allora il tableau è ottimo.

### Passo 2: scelta della variabile uscente

Se esiste una riga con:

$$
\bar b_t<0
$$

allora la variabile di base associata a quella riga esce dalla base.

### Passo 3: test di inammissibilità

Se nella riga $t$ vale:

$$
\bar a_{tj}\ge 0 \quad \forall j
$$

allora il problema è inammissibile.

### Passo 4: scelta della variabile entrante

Se esistono coefficienti negativi nella riga $t$, scegliere:

$$
h := \arg\min_{j}\left\{
\frac{\bar c_j}{|\bar a_{tj}|}:\ \bar a_{tj}<0
\right\}
$$

### Passo 5: pivot

Eseguire il pivot sull’elemento:

$$
(t,h)
$$

Il pivot serve a:

- ridurre l’inammissibilità primale;
- mantenere l’ammissibilità duale.

---

## 18. Frase chiave da ricordare

> Il simplesso duale mantiene sempre ammissibilità duale e scarto complementare, mentre recupera l’ammissibilità primale iterazione dopo iterazione.
>
> Quando anche $\bar b\ge 0$, la soluzione è ottima.
