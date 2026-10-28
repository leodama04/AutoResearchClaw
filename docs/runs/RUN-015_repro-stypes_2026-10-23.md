# RUN-015 — I tipi delle colonne decisi da un campione casuale spiegano le differenze tra run

| campo | valore |
|---|---|
| ID / data | RUN-015, 2026-10-23 |
| tipo | prova senza LLM (`./run.sh repro-stypes`) |
| comando | `./run.sh repro-stypes` (50 campioni, fino a 4 varianti valutate, task `driver-top3`) |
| versione del kit | 0.6.11 |
| immagine | la stessa di RUN-014 (`arc-relbench:latest`, creata il 2026-10-06 14:38 UTC) |
| durata | circa 15 minuti |

## 1. Obiettivo
Verificare l'ipotesi di RUN-014. Le run salvate cadono in tre gruppi con risultati per seme quasi uguali (RUN-003/005,
RUN-004/008, RUN-006/prova del 23/10), e i gruppi non dipendono né dal codice né dall'immagine. L'ipotesi è che dipendano dai
tipi delle colonne. `rb_data.prepare_data` li decide una volta per run, nel primo esperimento, con `get_stype_proposal` di
RelBench, che guarda un campione casuale di 1000 righe per tabella (`DataFrame.sample` senza seme). Il risultato viene salvato in
`stypes.json` e riusato dagli esperimenti successivi.

## 2. Setup
- Campione estratto 50 volte (semi numpy 0–49) sul database di `rel-f1` caricato come nella pipeline.
- Le 4 varianti di `stypes.json` più frequenti sono state usate ciascuna come cache iniziale di una valutazione completa:
  progetto ufficiale del kit, ricetta `tuned`, semi 100–109, nessun LLM.
- Confronto per seme del test di `baseline_graphsage` con le conferme finali di RUN-003, 004, 005, 006, 008 e con la prova
  del 23/10 (RUN-014).

## 3. Risultati (fatti)

**Varianti dei tipi delle colonne: 7 su 50 campioni.**

| variante | campioni | colonne diverse dalla variante 1 |
|---|---|---|
| 1 | 37/50 | (riferimento) |
| 2 | 5/50 | `qualifying.position` categorica |
| 3 | 3/50 | `constructor_standings.position` categorica |
| 4 | 2/50 | `constructor_standings.position` e `qualifying.position` categoriche |
| 5 | 1/50 | `results.positionOrder` categorica |
| 6 | 1/50 | `results.position` categorica |
| 7 | 1/50 | `qualifying.constructorId` categorica |

Le colonne che cambiano sono cinque, tutte intere: posizioni e un identificativo. In circa tre campioni su quattro sono
numeriche; a volte vengono lette come categorie.

**Baseline con ciascuna variante.** Distanza = differenza media per seme del test di `baseline_graphsage`.

| variante | graphsage test | tuned test | RUN-003 | RUN-004 | RUN-005 | RUN-006 | RUN-008 | prova 23/10 |
|---|---|---|---|---|---|---|---|---|
| 1 | 0,7498 | 0,7856 | 0,043 | 0,043 | 0,042 | **0,0075** | 0,042 | **0,0004** |
| 2 | 0,7683 | 0,7993 | **0,0072** | 0,032 | **0,0063** | 0,040 | 0,033 | 0,040 |
| 3 | 0,7581 | 0,7916 | 0,032 | **0,0058** | 0,031 | 0,048 | **0,0065** | 0,042 |
| 4 | 0,7670 | 0,7914 | 0,034 | 0,034 | 0,034 | 0,030 | 0,033 | 0,029 |

Esempio, seme 105 di `baseline_graphsage`: 0,650 in RUN-003 e RUN-005, 0,667 con la variante 2; 0,754 e 0,753 in RUN-004 e
RUN-008, 0,753 con la variante 3.

## 4. Interpretazione
- **Dimostrato:**
  - Su `rel-f1` il tipo di cinque colonne dipende dal campione casuale usato da RelBench per deciderlo: in 50 campioni si
    ottengono 7 varianti di `stypes.json`.
  - Le varianti riproducono i gruppi delle run salvate, seme per seme.
    - Variante 2 = RUN-003 e RUN-005.
    - Variante 3 = RUN-004 e RUN-008.
    - Variante 1 = RUN-006 e la prova del 23/10.

    La distanza dalla run corrispondente è 0,004–0,0075. Dalle altre è sempre almeno 0,029, cioè 4–7 volte di più.
    Con la variante 1 si ritrova la prova del 23/10 a 0,0004: stesso codice, stesse condizioni.
  - Quindi la differenza tra run con lo stesso codice viene dai tipi delle colonne decisi all'inizio di ogni run. Le distanze di
    0,006–0,0075 dalle run salvate, più grandi dello 0,002 di una ripetizione nella stessa run, si spiegano con codice e
    condizioni non identici (versioni del kit diverse, Qwen sulla GPU).
  - In RUN-014 A e B hanno pescato entrambi la variante 1. La variante 1 esce in 37 campioni su 50, quindi questo succede in
    circa metà dei casi (0,74² ≈ 0,55).
  - La variante sposta la media di `baseline_tuned` fino a circa 0,013 (0,786; 0,799; 0,792; 0,791). A questo si aggiunge il
    non determinismo dell'addestramento, circa 0,01 nella media di `baseline_tuned` a parità di variante (RUN-014). Insieme
    spiegano l'intervallo 0,772–0,802 della Tabella 4 della relazione.
- **Ipotesi non verificate:**
  - Il divario sistematico "sweep contro pipeline" di RUN-002/RUN-003 e i baseline più bassi degli strumenti (RUN-010, 012, 013)
    hanno probabilmente la stessa causa: ogni strumento gira in un container nuovo e pesca la sua variante. Non verificato,
    perché i loro `stypes.json` non sono salvati.
  - I guadagni misurati (per esempio +0,038 di RUN-004, ottenuto con la variante 3) potrebbero cambiare con un'altra variante.
    Da verificare rivalutando i modelli principali con le varianti 1–3.
  - Lo script ufficiale di RelBench (`examples/gnn_entity.py`) usa la stessa funzione e la stessa cache. Se e come fissi il seme
    prima del campione va controllato nel suo codice.
- **Limiti:** 50 campioni; un solo task; le distanze dalle run salvate si basano su 10 semi.

## 5. Decisioni e prossimi passi
- **Relazione e tesi.** Si può scrivere la causa. I confronti appaiati restano validi, perché tutte le condizioni di una run
  usano la stessa variante. I valori assoluti dei baseline di run diverse non sono confrontabili.
- **Correzione proposta per le run future (non applicata).** Rendere deterministici i tipi delle colonne: un `stypes.json`
  fisso nel kit, oppure il campione estratto con un seme fisso. I nuovi baseline non saranno confrontabili con le run passate.
- **Per la tesi.** Rivalutare i modelli principali (RUN-004 e i modelli finali di RUN-008 e RUN-011) con le varianti 1–3, per
  sapere se le conclusioni dipendono dalla variante.

## 6. Errata
- **RUN-014 §4.** Avevo indicato i tipi delle colonne come ipotesi più probabile: ora è dimostrata.
- **Messaggi del 23/10.** Avevo escluso i dati preparati come causa perché le cache di RUN-014 erano identiche. Il motivo era
  che i tre container avevano pescato la stessa variante, non che la preparazione sia deterministica.

## 7. File di riferimento
`artifacts/repro_stypes_<data>/summary_stypes.md`, `stypes_info.json`, `stypes/variant_*.json`, `worlds/v*/results.json`.
