# RUN-014 — Perché i baseline cambiano tra una run e l'altra (prova tra container, senza LLM)

| campo | valore |
|---|---|
| ID / data | RUN-014, 2026-10-23 (cartella `artifacts/repro_20261023-155224`) |
| tipo | prova di riproducibilità, senza LLM (`./run.sh repro-check`) |
| comando | `./run.sh repro-check` (task `driver-top3`) |
| versione del kit | 0.6.11 |
| immagine | `arc-relbench:latest`, `sha256:e64223c2…`, creata il 2026-10-06 14:38 UTC |
| durata | circa 20 minuti |

## 1. Obiettivo
Domanda nata dalla revisione della relazione di tirocinio: sugli stessi semi 100–109 `baseline_tuned` vale da 0,772 (RUN-006)
a 0,802 (RUN-003). Prima di questa prova, dai file salvati delle run (tre conferme per run in RUN-003–RUN-006) risultava:
- dentro una run le conferme coincidono quasi seme per seme (`baseline_graphsage`: in media 0,002 di differenza per seme;
  `baseline_tuned`: medie entro 0,006);
- tra run diverse gli stessi semi danno risultati diversi (`baseline_graphsage`: 0,035 per seme), anche quando tutti i file
  eseguiti per i baseline sono identici byte per byte (RUN-005 contro RUN-006).

Le ipotesi da verificare erano due: i dati preparati all'inizio di ogni run (tipi delle colonne, tabelle materializzate,
embedding del testo, salvati in `/tmp` del container) e le versioni delle librerie.

## 2. Setup
Tre container come tre run, tutti con il progetto ufficiale del kit (nessun modello di Qwen), ricetta `tuned`, semi 100–109,
nessun LLM caricato:
- A: cache dei dati vuota, `main.py` eseguito due volte;
- B: come A;
- C: cache copiata da A, eseguito una volta.

## 3. Risultati (fatti)

| container | esecuzione | cache | baseline_graphsage test | baseline_tuned test |
|---|---|---|---|---|
| A | 1 | nuova | 0,7509 | 0,7784 |
| A | 2 | di A1 | 0,7501 | 0,7759 |
| B | 1 | nuova | 0,7497 | 0,7797 |
| B | 2 | di B1 | 0,7504 | 0,7793 |
| C | 1 | da A | 0,7501 | 0,7854 |

Differenza media per seme (test):

| confronto | baseline_graphsage | baseline_tuned |
|---|---|---|
| stesso container | 0,0021 | 0,0106 |
| A vs B | 0,0019 | 0,0141 |
| A vs C | 0,0019 | 0,0132 |
| B vs C | 0,0008 | 0,0104 |

- **Cache dei dati**: A, B e C identiche byte per byte (10 file).
- **Librerie e GPU**: identiche nei tre container (stessa immagine, stessa RTX 5090 `50f3fe07…`).
- **Immagine**: creata il 2026-10-06 14:38 UTC; gli strati con PyTorch, PyG, PyTorch Frame e RelBench risalgono al 3–4/10.

Confronto per seme di `baseline_graphsage` con le run salvate (conferma finale; differenza media per seme da B1):

| run | data | distanza da oggi | |
|---|---|---|---|
| RUN-003 | 4/10 | 0,044 | come RUN-005 |
| RUN-004 | 5/10 | 0,043 | come RUN-008 |
| RUN-005 | 6/10 | 0,042 | come RUN-003 |
| RUN-006 | 7/10 | 0,007 | **come oggi** |
| RUN-008 | 13/10 | 0,042 | come RUN-004 |

Tra le run salvate la distanza per seme è 0,003 tra RUN-003 e RUN-005, 0,004 tra RUN-004 e RUN-008, 0,007 tra RUN-006 e oggi;
tra run di gruppi diversi è sempre tra 0,032 e 0,050.

## 4. Interpretazione
- **Dimostrato:**
  - Con l'immagine attuale e senza LLM, container diversi danno gli stessi risultati di due esecuzioni nello stesso container:
    la differenza tra container è dello stesso ordine del non determinismo dell'addestramento (0,001–0,002 per seme per
    `baseline_graphsage`, circa 0,01 per `baseline_tuned`).
  - La preparazione dei dati di oggi è stata deterministica: tre cache costruite separatamente sono identiche byte per byte.
  - Le librerie non spiegano la differenza tra RUN-005 e RUN-006: l'immagine attuale è stata creata 3 minuti prima
    dell'inizio di RUN-005 (2026-10-06 14:41 UTC) e non è più stata ricostruita, quindi RUN-005, RUN-006 e tutte le run
    successive l'hanno usata.
  - Le run salvate cadono in pochi gruppi con risultati per seme quasi uguali: RUN-003 e RUN-005, RUN-004 e RUN-008,
    RUN-006 e la prova di oggi. I gruppi non seguono la versione del codice (RUN-003 e RUN-005 hanno `main.py` e `rb_train.py`
    diversi, RUN-005 e RUN-006 identici) né l'immagine.
- **Ipotesi non verificata (la più probabile):** i tipi delle colonne. `rb_data.prepare_data`, quando `stypes.json` non c'è
  ancora (cioè nel primo esperimento di ogni run), chiama `get_stype_proposal` di RelBench, che decide il tipo di ogni colonna
  guardando un campione **casuale** di 1000 righe per tabella (`df.sample(min(1_000, len(df)))`, senza seme; prima di
  `prepare_data` nessuno fissa il seme di numpy: verificato nel codice). Se per qualche colonna il tipo dipende dal campione,
  ogni run sceglie una delle poche varianti possibili e la usa per tutti i suoi esperimenti: risultati stabili dentro la run,
  diversi tra le run, in pochi gruppi discreti. Spiegherebbe anche perché oggi A e B coincidono: hanno pescato la stessa
  variante, possibile se una variante è frequente.
- **Limiti:** una sola giornata; nessun LLM caricato (le run della pipeline girano con Qwen sulla stessa GPU); tre container.

## 5. Decisioni e prossimi passi
- `./run.sh repro-stypes` (kit 0.6.11): estrae il campione 50 volte, conta le varianti dei tipi delle colonne e allena i baseline
  con ognuna, confrontando i risultati per seme con quelli delle run salvate. Se le varianti riproducono i gruppi
  (RUN-003/005, RUN-004/008, RUN-006/oggi), la causa è dimostrata.
- Se è confermata, la correzione per le run future è fissare i tipi delle colonne (un `stypes.json` nel kit, o un seme per il
  campione), ricordando che cambia i numeri dei baseline rispetto alle run passate.
- Per la relazione e la tesi resta vero che ogni confronto è fatto dentro la stessa run, sugli stessi semi.

## 6. Errata
- Aggiornamento: l'ipotesi del §4 è stata verificata in RUN-015. Le varianti dei tipi delle colonne riproducono i gruppi delle run salvate, e oggi A e B avevano pescato la stessa variante.
Nel messaggio del 23/10 l'ipotesi "i dati preparati" era formulata come differenza tra container; oggi i dati preparati sono
risultati identici tra container. Resta possibile che varino tra run per il campione casuale (§4).

## 7. File di riferimento
`artifacts/repro_20261023-155224/summary.md`, `A|B|C/info.json`, `A|B|C/run*/results.json`, `image.txt`.
