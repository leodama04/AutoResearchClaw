# RUN-008 — pipeline "24 h" in modalità codice, non guidata (kit 0.6.3)

| campo | valore |
|---|---|
| ID / data | RUN-008, 2026-10-13/14 |
| tipo | pipeline completa, modalità codice, Qwen sceglie da solo paper e architetture |
| comando | `ARC_DEADLINE_HOURS=24 ./run.sh relbench` (manifest non allegato) |
| versione del kit | 0.6.3 (verificato dal vendoring: 8 moduli RelGNN, script e copia di relbench esclusi) |
| run id | `rc-20261013-131020-9b9601` (zip `sesto_esperimento_relbench_f1_drivertop3_24h.zip`) |
| durata | **15,2 h** (13:10 → 04:24 UTC); stage 13: 14,5 h in tre passate |
| rapporto automatico | [RUN-008_auto.md](RUN-008_auto.md) |

## 1. Obiettivo
Prima run lunga completa con il kit corretto dopo RUN-007: Qwen sceglie paper e codice dalle sue ricerche, parte dal solo modello
ufficiale e ha fino a 24 ore per migliorare `driver-top3`. Domande: usa i paper e il codice ufficiale? Migliora il test?

## 2. Setup
Come RUN-007 (ricetta `tuned` bloccata: 10 epoche, batch 128, lr 0,005; 10 semi; selezione solo sulla validazione; test nascosto a
Qwen; conferma su semi 100–109; ricontrollo su semi 200–209; margine 0,005), con le correzioni del kit 0.6.3.
GPU all'avvio dello stage 12: 9,0 GB liberi.

## 3. Risultati (fatti letti dai file della run)

### 3.1 Letteratura, paper e repository (stage 3–6)
- **Query scritte da Qwen** (12): *improve graph neural networks*, *graphSAGE baseline modifications*, *relational deep learning tasks*,
  *binary classification graph models*, *relational feature encoding networks*, *adaptive message passing graph*,
  *pairwise interaction module design*, *class imbalance handling graphs*, *RelBench driver top three*, *compute efficient neural pipelines*,
  *statistical validation graph models*, *ablation studies neural nets*. Anno minimo 2010.
- 500 candidati → 15 in shortlist → 3 schede dal testo completo (altri 3 paper scartati perché senza testo completo):

| scheda | paper | codice ufficiale | vendorizzato |
|---|---|---|---|
| K1 | QUARTET (2026, arXiv 2609.26855): cross-attention, random walk, transformer per grafi relazionali | non trovato | — |
| K2 | **RelGNN** (2025, arXiv 2502.06784): message passing composito su "atomic routes" | snap-stanford/RelGNN | 8 moduli (11 script e 28 file della copia di relbench esclusi) |
| K3 | LightRDL (2025, arXiv 2504.04934): modelli tabulari preaddestrati + GNN | AntonioLonga/LightRDL | 3 moduli |

- Lo stage 5 originale ha clonato anche i repository di HAN e GAug (due paper della shortlist): mai usati.
- Ipotesi (stage 8): H1 instradamento sulle atomic routes (da RelGNN), H2 fusione spettrale-tabulare (da LightRDL).

### 3.2 Riferimento (stage 12, semi 0–9)

| condizione | val AUROC | test AUROC |
|---|---|---|
| baseline_graphsage (ricetta ufficiale) | 0,697 ± 0,055 | 0,763 ± 0,035 |
| baseline_tuned (batch 128) | 0,766 ± 0,020 | 0,793 ± 0,016 |
| proposed all'inizio (codice identico a baseline_tuned) | 0,768 ± 0,019 | 0,791 ± 0,029 |

Rumore di fondo: `proposed` e `baseline_tuned` qui sono lo stesso modello con gli stessi semi, eppure per singolo seme il test differisce fino a
0,056 (seme 8: 0,800 contro 0,744); le medie differiscono di 0,002. Sulla conferma (semi 100–109), `baseline_tuned` misurato tre volte con lo
stesso codice dà 0,798 / 0,792 / 0,790 sul test: l'addestramento su GPU non è deterministico.

### 3.3 Raffinamento (stage 13): tre passate, 366 tentativi

| passata | tentativi | durata | partenza | migliore (val) | miglioramenti accettati |
|---|---|---|---|---|---|
| 1 | 151 | 5,8 h | modello ufficiale (0,768) | 0,879 (tentativo 19, attention) | 2 (tentativi 11 e 19) |
| 2 | 110 | 4,5 h | tentativo 31 della passata 1 (0,884) | nessun nuovo migliore | 0 |
| 3 | 105 | 4,2 h | tentativo 34 della passata 2 (0,886) | nessun nuovo migliore | 0 |

Ogni passata si è fermata per pazienza (60 tentativi validi senza miglioramento); dopo tre passate lo stage 15 non può chiedere altre
ripartenze e la pipeline è passata alla scrittura del paper. Per questo la run è durata 15,2 h e non 24.

Esito dei 366 tentativi: 190 valutati (52%); 141 crash alla prima esecuzione (39%), di cui 46 recuperati dalla riparazione; 70 identici
al migliore e quindi non eseguiti (19%); 12 respinti dai controlli (7 senza scheda citata, 5 identici al baseline); 0 errori dell'LLM.
Tempo: metà circa delle 14,5 h è andata nelle chiamate a Qwen, il resto nelle esecuzioni (~110 s per tentativo valido, ~11 s per un crash).

Errori più frequenti nei crash: `rb_model.py` riscritto senza la funzione `build_model` (39), argomenti inesistenti passati agli operatori di
PyG (`root_weight`, `add_self_loops`, `dropout`, `pre_norm`: 40 in tutto), `GATv2Conv` con self-loop su archi bipartiti (11), firma di `MLP` sbagliata (8).

### 3.4 Che codice ha scritto (famiglie di architetture)

| famiglia | tentativi | valutati | val media (max) | test media (max) | da dove viene |
|---|---|---|---|---|---|
| RelGNN | 83 | 72 | 0,741 (0,809) | 0,733 (0,786) | K2, **codice ufficiale importato** |
| Attention / Transformer | 130 | 30 | 0,800 (0,884) | 0,750 (0,810) | `TransformerConv` per tipo di arco; cita K1 ("local attention") |
| GATv2 | 120 | 69 | 0,837 (0,890) | 0,764 (0,811) | `GATv2Conv` + GraphNorm + residual; cita K1, ma GATv2 e GraphNorm non sono in nessuna scheda |
| Altro | 33 | 19 | 0,746 (0,874) | 0,779 (0,810) | GraphSAGE con LayerNorm e residual, MLP sulle feature (ispirato a K3), GINE, LightRDL (1, crash) |

Riferimento: `baseline_tuned` sugli stessi semi ha test medio 0,786 (0,775–0,797).

**Codice ufficiale usato davvero.** In 86 tentativi Qwen ha importato i moduli vendorizzati (`RelGNN_Model` in 77, `get_atomic_routes` in 73,
LightRDL in 1). Il modello ufficiale di RelGNN veniva chiamato direttamente (`return self.gnn(batch, entity_table)`) e le run andavano a buon
fine: rispetto a RUN-006 (codice di RelGT mai funzionante) è il primo uso riuscito del codice di un paper. Però:
- sempre con 2 layer, 4 teste e 128 canali. Il repository contiene la configurazione degli autori per `driver-top3` (`get_configs` in
  `vendor_relgnn_utils.py`: 1 layer, 2 teste, `simplified_MP=True`, batch 256), elencata nella mappa del codice ma mai usata; la scheda K2
  dice "iperparametri non specificati";
- con la nostra ricetta (10 epoche, 110 aggiornamenti) RelGNN resta sotto il baseline (test 0,733 contro 0,786) e lontanissimo dal valore del
  paper (85,69). Non sappiamo se dipenda dagli iperparametri, dalla durata dell'addestramento o da altro.
- dopo decine di tentativi RelGNN "did NOT improve", Qwen ha continuato a riproporlo quasi identico (35, 19 e 29 per passata).

**Modello finale** (`experiment_final`, = tentativo 34 della passata 2): `rb_model.py` +90/−29 righe, `rb_config.py` 2 righe.
`HeteroGATv2SAGE`: per ogni tipo di arco un `GATv2Conv` (4 teste, `concat=False`, senza self-loop, dropout 0,2), media tra tipi di arco,
connessione residua, `GraphNorm` per tipo di nodo; anche la testa MLP usa `GraphNorm`; 2 layer, 128 canali.
`PROPOSED_SOURCE = 'K1: GATv2 attention aggregation with GraphNorm & residual connections'`: citazione nominale, come in RUN-004.
Non usa nessun file vendorizzato.

### 3.5 Conferma su semi nuovi (100–109)

| passata | proposed val | proposed test | baseline_tuned test | Δ test (IC 95%, p) |
|---|---|---|---|---|
| 1 | 0,877 ± 0,007 | 0,796 ± 0,025 | 0,798 ± 0,020 | −0,002 ([−0,020, +0,017], p = 0,87) |
| 2 | 0,874 ± 0,023 | 0,720 ± 0,092 | 0,792 ± 0,020 | −0,073 ([−0,136, −0,018], p = 0,055) |
| 3 (finale) | 0,886 ± 0,010 | 0,777 ± 0,033 | 0,790 ± 0,020 | −0,012 ([−0,041, +0,013], p = 0,43) |

In validazione il guadagno è grande e su tutti i semi (+0,098 / +0,097 / +0,109, 10 semi su 10, p = 0,002). Sul test nessuna passata migliora.
Il baseline con la ricetta ufficiale ha test 0,755 ± 0,021: coincide con il paper di RelBench (75,54).

### 3.6 Validazione e test non vanno insieme
Su 190 tentativi valutati la correlazione di rango tra validazione e test è **0,05** (praticamente nulla). I 10 tentativi con la validazione
più alta hanno test tra 0,780 e 0,805; i 10 migliori sul test (fino a 0,811, cioè +0,02/+0,03 sul baseline) hanno validazione qualsiasi
(da 0,68 a 0,89).
Scegliendo sulla validazione la pipeline non può trovarli (e scegliere sul test non è ammesso).

### 3.7 Analisi e paper (stage 14–23)
- Lo stage 15 ha chiesto due volte di rifare il raffinamento anche perché ha letto `proposed_identical_to_baseline: 1.0` (che allo stage 12 è
  atteso: il modello non è ancora stato modificato) come "il modello proposto non è mai stato eseguito".
- Paper "RAGN: Residual Attention and GraphNorm…": il risultato principale è riportato onestamente (val +0,11, test pari al baseline, p = 0,434).
  Però inventa le statistiche del dataset (1.247 piloti, split 2020/2021/2022 con 2.104/368/401 righe; in realtà 1.353/588/726 righe, validazione
  2005–2008, test 2010–2013) e scrive che il modello usa i moduli vendorizzati di RelGNN e LightRDL (falso). Revisione automatica 5/10.

## 4. Interpretazione
- **Dimostrato:**
  - La parte non guidata funziona: query di Qwen, scelta di RelGNN e LightRDL, codice ufficiale scaricato, vendorizzato e importato davvero
    (86 tentativi). Il kit 0.6.3 ha retto 15 ore senza errori dell'LLM.
  - Il numero di riferimento del baseline ufficiale è riprodotto (test 0,755 contro 75,54 del paper).
  - L'architettura scelta (GATv2 + GraphNorm + residual) migliora molto la validazione ma **non** il test.
  - Su questo task la validazione non è una guida affidabile per il test (correlazione 0,05 su 190 modelli; già in RUN-000: +0,16).
- **Ipotesi non verificate:**
  - Perché validazione e test divergono: periodi diversi (2005–2008 contro 2010–2013) e selezione ripetuta su 588 righe (si "impara" la validazione).
  - `GraphNorm` normalizza con le statistiche del batch anche in valutazione: le predizioni dipendono dalla composizione del batch e potrebbero
    adattarsi alla distribuzione della validazione. Da verificare con un'ablazione (GraphNorm → BatchNorm).
  - Perché RelGNN rende così poco: configurazione (2 layer invece di 1, 4 teste invece di 2) e/o addestramento troppo corto per questo modello.
- **Difetti del kit trovati:**
  1. la ripartenza tra passate prende il valore più alto di qualsiasi tentativo, anche non accettato: la passata 2 è partita dal tentativo 31
     (mai ricontrollato, test 0,742) e infatti la sua conferma è la peggiore (test 0,720);
  2. il file del metodo conta le righe rispetto a `rb_model_official.py` (306) invece che rispetto al modello di partenza (+90/−29) ed elenca i
     file vendorizzati come "nuovi file": da qui il paper ha dedotto che il modello li usa;
  3. il paper non riceve le statistiche vere del dataset e le inventa;
  4. la metrica `proposed_identical_to_baseline` dello stage 12 viene fraintesa dall'analisi;
  5. la configurazione per task degli autori di RelGNN non arriva nella scheda;
  6. con pazienza 60 e al massimo tre passate la run finisce dopo ~15 h anche con 24 h a disposizione.
- **Limiti:** 726 righe di test e 588 di validazione; il test delle conferme oscilla di ~0,008 tra ripetizioni identiche.

## 5. Decisioni e prossimi passi
- Collegato alla call con il correlatore:
  1. valutare il checkpoint ufficiale di RelGNN (Hugging Face) per sapere se 85,69 si riproduce nel nostro ambiente;
  2. addestrare RelGNN con la configurazione degli autori per driver-top3 (1 layer, 2 teste, `simplified_MP`, batch 256) e con più epoche:
     è la domanda sui training step;
  3. tabella con i vincitori delle run (questa e le precedenti) anche su driver-dnf e driver-position.
- Da discutere con i relatori prima di altre run lunghe: con questa validazione, più iterazioni ottimizzano solo la validazione.
  Possibili alternative (decisione loro): selezione su più finestre temporali, sulle finestre di validazione più recenti, o un criterio che
  penalizzi la varianza tra semi.
- Kit 0.6.4 (fatto, 2026-10-14): corretto il difetto 1 (ripartenza solo da versioni accettate) e reso il task configurabile
  (`RB_TASK`) per la run su driver-dnf. I difetti 2–5 restano: riguardano il testo del paper e la scheda di RelGNN, non i numeri;
  nella tesi si usano i numeri di questo documento, non il paper generato.

## 6. Errata
Nessuna.

## 7. File di riferimento
- `stage-13_v1/`, `stage-13_v2/`, `stage-13/`: `refinement_log.json`, `experiment_v*/`, `confirmation.json`.
- `stage-06/knowledge_meta.json`, `stage-06/KNOWLEDGE.md`, `stage-03/queries.json`, `stage-12/runs/run-1.json`.
- `stage-15*/decision.md`, `stage-20/quality_report.json`, `deliverables/paper_final.md`, `deliverables/paper.pdf`.
