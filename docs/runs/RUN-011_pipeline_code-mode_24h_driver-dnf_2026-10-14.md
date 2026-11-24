# RUN-011 — pipeline "24 h" in modalità codice, non guidata, su driver-dnf

| campo | valore |
|---|---|
| ID / data | RUN-011, 2026-10-14/15 |
| tipo | pipeline completa, modalità codice, Qwen sceglie da solo paper e architetture; task **driver-dnf** |
| comando | `RB_TASK=driver-dnf ARC_DEADLINE_HOURS=24 ./run.sh relbench` (manifest non allegato: è in `docs/runs/_manifests/`) |
| versione del kit | 0.6.7 o 0.6.8 (la pipeline è identica dalla 0.6.4 alla 0.6.8; le versioni successive cambiano solo gli strumenti) |
| run id | `rc-20261014-152719-4d33ce` (zip `settimo_esperimento_relbench_f1_driverdnf.zip`) |
| durata | **23,5 h** (14/10 15:27 → 15/10 14:59 UTC); stage 13: 22,8 h, quasi tutte nella prima passata |
| rapporto automatico | [RUN-011_auto.md](RUN-011_auto.md) |

## 1. Obiettivo
Secondo task per la tabella incrociata chiesta dal correlatore ("ottimizzare il task 1 e il task 2, poi usare la soluzione dell'uno
sull'altro"). Stesso protocollo di RUN-008, su driver-dnf: il pilota non terminerà (DNF) una gara nei 30 giorni successivi?
Classificazione binaria, AUROC.

## 2. Setup
Come RUN-008: ricetta `tuned` bloccata (10 epoche, batch 128, lr 0,005), 10 semi, selezione solo sulla validazione, test nascosto a
Qwen, conferma su semi 100–109, ricontrollo su semi 200–209, margine 0,005, pazienza 60 tentativi validi. Con le correzioni della 0.6.4:
specifiche, topic e prompt riempiti dal registro dei task (`RB_TASK=driver-dnf`); ripartenza tra le passate solo da versioni accettate.
Una valutazione completa (3 condizioni × 10 semi) dura ~535 s, contro ~110 s su driver-top3.

## 3. Risultati (fatti letti dai file della run)

### 3.1 Letteratura, paper e repository (stage 3–6)
- **Query scritte da Qwen** (8): *RelBench benchmark evaluation metrics*, *GraphSAGE relational modifications*, *Relation conditioned
  feature routing*, *Statistical validation ROC AUC*, *Improving graph neural networks survey*, *Improving graph neural networks
  benchmark*, *graph neural networks relational*, *Improving graph neural comparison*. Anno minimo 2010.
- 301 candidati → 15 in shortlist (tra gli altri RelGT-AC, MetaSieve, QUARTET, RelBench, HetGNN, GIN e diversi lavori non pertinenti
  da Zenodo); **RelGNN e RelGT non sono nella shortlist**. 2 schede dal testo completo, 5 paper scartati perché senza testo completo:

| scheda | paper | codice ufficiale | vendorizzato |
|---|---|---|---|
| K1 | QUARTET (2026, arXiv 2609.26855): cross-attention, random walk, transformer per grafi relazionali | non trovato | — |
| K2 | Relational Graph Neural Network Design via Progressive Neural Architecture Search (2021, arXiv 2105.14490): aggregazione "a scala" (*ladder*), i messaggi di ogni salto elaborati separatamente e concatenati, più una ricerca NAS delle dimensioni | `kimiyoung/planetoid`, preso dal link nel PDF: è il codice dei dataset di un altro lavoro (Theano/Lasagne, Python 2) | nessuno (dipendenze mancanti); la scheda stessa dice che non è riusabile |

- Nessun repository clonato allo stage 5. **In questa run non c'era codice ufficiale utilizzabile.**
- Ipotesi (stage 8): H1 campionamento causale (da K1), H2 aggregazione a scala con salti separati (da K2), H3 baseline "snellito" come
  test contrario.

### 3.2 Riferimento (stage 12, semi 0–9)

| condizione | val AUROC | test AUROC |
|---|---|---|
| baseline_graphsage (ricetta ufficiale) | 0,713 ± 0,008 | 0,727 ± 0,014 |
| baseline_tuned (batch 128) | 0,762 ± 0,024 | 0,742 ± 0,012 |
| proposed all'inizio (codice identico a baseline_tuned) | 0,769 ± 0,018 | 0,731 ± 0,011 |

### 3.3 Raffinamento (stage 13)

| passata | tentativi | durata | partenza | migliore (val) | miglioramenti accettati |
|---|---|---|---|---|---|
| 1 | 206 | 22,3 h | modello ufficiale (0,769) | 0,8155 (tentativo 88) | 3 (tentativi 24, 34, 88) |
| 2 | 1 | 0,4 h | tentativo 88, la versione accettata | nessun nuovo migliore | 0 |
| 3 | 0 | 0,15 h | tentativo 88 | — | 0 |

La passata 1 si è fermata per pazienza (60 tentativi validi senza miglioramenti dopo il tentativo 88); le passate 2 e 3, chieste dallo
stage 15, si sono fermate per la scadenza globale. Con ~535 s per valutazione una sola passata occupa quasi tutte le 24 ore. La
ripartenza della passata 2 dalla versione accettata conferma la correzione della 0.6.4.

Esito dei 207 tentativi: 106 valutati (51%); 76 interrotti alla prima esecuzione, di cui 26 recuperati dalla riparazione; 47 identici
al migliore e quindi non eseguiti; 4 respinti dai controlli; 0 errori dell'LLM. Tempo della passata 1: 17,3 h di esecuzioni, il resto
nelle chiamate a Qwen. Errori più frequenti nei crash: `rb_model.py` riscritto senza `build_model` (15), `ModuleDict` con chiavi tupla
(i tipi di arco; 7), firme di `forward` sbagliate (7), import inesistenti da `torch_frame.nn` (3), forme dei tensori incompatibili (4).

### 3.4 Che codice ha scritto

| famiglia | tentativi | valutati | val media (max) | test media (max) | da dove viene |
|---|---|---|---|---|---|
| "Ladder" (K2) | 181 | 95 | 0,781 (0,818) | 0,699 (0,746) | cita K2 in 182 tentativi |
| di cui varianti più vicine alla scheda (nomi con *hop*, *concat*, *multi_scale*, *dense*) | 40 | 34 | 0,785 | 0,703 | componenti 1–2 della scheda K2; per esempio `k2_hop_sep` separa i nodi per salto con `num_sampled_nodes` |
| Attention (GATv2, ResGated, …) | 6 | 4 | 0,781 (0,801) | 0,711 (0,718) | operatori standard di PyG |
| QUARTET (K1) | 3 | 1 | 0,676 | 0,697 | K1 |
| Altro (jumping knowledge, multi-scala, pesi per arco) | 10 | 5 | 0,769 (0,810) | 0,706 (0,720) | — |
| nessuna modifica leggibile | 6 | 0 | — | — | — |

Riferimento: `baseline_tuned` sugli stessi semi (0–9) ha test 0,742. Dei 106 modelli valutati, 76 superano `baseline_tuned` in
validazione e **solo 2** sul test.

**Modello finale** (`experiment_final`, = tentativo 88): `rb_model.py` +97/−22 righe, `rb_config.py` 2 righe;
`PROPOSED_OVERRIDES = {'aggr': 'max', 'dropout': 0.15, 'gnn_type': 'k2_ladder', 'residual': True}`,
`PROPOSED_SOURCE = 'K2: Pre-LayerNorm Ladder Aggregation with GELU & Residuals'`. `LadderHeteroSAGE`: GraphSAGE eterogeneo
(`HeteroConv` di `SAGEConv`, somma tra tipi di arco) con aggregazione `max`, LayerNorm prima di ogni strato (una per tipo di nodo,
condivisa dai due strati), GELU, dropout 0,15, connessione residua con proiezione lineare; testa MLP a 2 strati con dropout 0,1.
**Nonostante il nome, non separa i salti e non concatena niente**: il componente della scheda K2 non c'è, la citazione è nominale
come in RUN-004 e RUN-008. Le varianti più vicine alla scheda (40 tentativi) non sono andate meglio. Non usa codice dei paper.

### 3.5 Conferma su semi nuovi (100–109), stesso modello tre volte

| passata | proposed val | proposed test | baseline_tuned test | baseline_graphsage test | Δ test proposed − tuned (IC 95%, p, semi meglio) |
|---|---|---|---|---|---|
| 1 | 0,814 ± 0,006 | 0,716 ± 0,016 | 0,732 ± 0,009 | 0,734 ± 0,017 | −0,016 ([−0,026, −0,006], p = 0,016, 2/10) |
| 2 | 0,814 ± 0,005 | 0,714 ± 0,013 | 0,734 ± 0,017 | 0,733 ± 0,009 | −0,020 ([−0,031, −0,009], p = 0,012, 1/10) |
| 3 (finale) | 0,814 ± 0,004 | 0,711 ± 0,014 | 0,731 ± 0,019 | 0,726 ± 0,011 | **−0,020 ([−0,027, −0,013], p = 0,004, 1/10)** |

In validazione il guadagno è netto e su tutti i semi (+0,043 / +0,051 / +0,048, 10/10, p = 0,002). **Sul test il modello è peggiore
del baseline in modo significativo**, in tutte e tre le conferme. Anche `baseline_tuned` rispetto a `baseline_graphsage` guadagna
+0,05/+0,06 in validazione (p = 0,002) e niente sul test (−0,003, +0,001, +0,005).

Riferimenti (test): RDL nel paper 0,7262; RelGNN nel paper 0,7529; checkpoint di RelGNN con il nostro codice 0,7489 (RUN-009);
il modello di RUN-008, ottimizzato su driver-top3 e allenato qui senza modifiche, −0,001 rispetto a `baseline_tuned` (RUN-010).

### 3.6 Validazione e test non vanno insieme
Su 106 tentativi valutati la correlazione di rango tra validazione e test è **0,13**. I 10 tentativi con la validazione più alta
(0,815–0,818) hanno test tra 0,690 e 0,721, tutti sotto il baseline; i 10 migliori sul test (0,728–0,746) hanno validazione tra 0,725
e 0,811.

### 3.7 Analisi e paper (stage 14–23)
- Lo stage 15 ha chiesto tre volte di rifare il raffinamento citando, tra l'altro, `proposed_identical_to_baseline: 1.0` come prova
  che il modello proposto non era stato eseguito. È il valore dello stage 12, dove il modello non è ancora modificato; nei riassunti
  del raffinamento e nelle conferme vale 0. Lo stesso errore di lettura di RUN-008 (difetto 4 di quel documento, ancora aperto).
- Paper "K2: Validation-Test Divergence in Pre-LayerNorm Ladder Aggregation for Driver-DNF Prediction": il risultato principale è
  riportato onestamente (validazione +4,8 punti, test −2,0, p = 0,004), ma chiama il metodo "K2" (l'identificativo della scheda) e
  inventa le suddivisioni del dataset (training 2010–2018, validazione 2019–2020, test dal 2021; in realtà validazione dal 2005 e test
  dal 2010). Revisione automatica 7/10; 21/21 citazioni verificate.

## 4. Interpretazione
- **Dimostrato:**
  - La pipeline funziona su un secondo task senza modifiche: 23,5 h, 207 tentativi, nessun errore dell'LLM.
  - **23 ore di ricerca su driver-dnf hanno prodotto un modello peggiore del baseline sul test** (−0,020, p = 0,004, meglio su 1 seme
    su 10), pur essendo molto migliore in validazione (+0,048 su tutti i semi). Il risultato è confermato tre volte.
  - Sul test di driver-dnf il modello trovato su driver-dnf fa peggio di quello trovato su driver-top3 (−0,020 contro −0,001, RUN-010).
  - Validazione e test sono scollegati anche su questo task (correlazione 0,13; su driver-top3 0,05). Lo stesso vale per la ricetta:
    il batch da 128 migliora molto la validazione e per niente il test.
  - Questa volta Qwen ha seguito con costanza l'idea di un paper (181 tentativi su 207 citano l'aggregazione a scala di K2) e ha
    provato anche varianti più vicine alla scheda (40 tentativi), ma il vincitore è la variante che di K2 ha solo il nome.
- **Ipotesi non verificate:**
  - Validazione (dal 2005) e test (dal 2010) sono periodi diversi, e una selezione ripetuta su più di cento modelli si adatta alla
    validazione. Aggregazione `max` e normalizzazioni migliorano la validazione anche su driver-top3 (RUN-000, RUN-003, RUN-008):
    potrebbero essere modifiche che si adattano a quel periodo.
- **Difetti del kit trovati:**
  1. lo stage 14/15 legge `proposed_identical_to_baseline` dello stage 12 come un errore (già in RUN-008): qui ha prodotto tre REFINE
     senza tempo per eseguirli;
  2. il paper non riceve le statistiche vere del dataset e le inventa, e prende come nome del metodo l'identificativo della scheda;
  3. il link al codice preso dal PDF può essere il codice di un altro lavoro citato (qui `planetoid`); innocuo perché non vendorizzato;
  4. il rapporto automatico mostrava il topic di `config.yaml` (driver-top3) invece di quello usato dalla run: corretto nel kit 0.6.10.
- **Limiti:** una sola run; una sola finestra di validazione e di test.

## 5. Decisioni e prossimi passi
- Completare la tabella incrociata: allenare il vincitore di questa run su driver-top3 (e driver-position), senza LLM:
  `./run.sh transfer --projects artifacts/rc-20261014-152719-4d33ce --tasks driver-top3,driver-dnf,driver-position`.
- Portare ai relatori il risultato di due run lunghe su due task: con la selezione sulla validazione, più iterazioni migliorano solo la
  validazione; su driver-dnf il modello scelto è peggiore del baseline sul test. Decisione loro se cambiare il criterio (più finestre
  temporali, finestre più recenti, penalità sulla varianza tra semi).
- Da decidere: correggere il difetto 1 (stage 14/15 e `proposed_identical_to_baseline`) prima della prossima run lunga.

## 6. Errata
Nessuna. Aggiornamento 2026-10-15: allenato su driver-top3 (RUN-013) il modello finale di questa run migliora il test di
+0,032 (p = 0,006, 9 semi su 10), mentre su driver-dnf resta peggiore del baseline (−0,030).

Aggiornamento 2026-10-30 ([RUN-017](RUN-017_varianti-stypes_modelli_2026-10-30.md)): rivalutato con i file della run e le varianti
1–3 dei tipi delle colonne, il modello finale è peggiore del baseline su driver-dnf con le varianti 1 e 3 (−0,021, p = 0,002;
−0,038, p = 0,014) e uguale con la variante 2 (−0,004 e +0,002 in due valutazioni). La conclusione del §4 ("peggiore del baseline
sul test") vale quindi con 2 varianti su 3. La variante usata da questa run non si può identificare: su driver-dnf le varianti
spostano i baseline quanto una ripetizione della valutazione. Su driver-top3 il guadagno di RUN-013 c'è solo con la variante 1
(+0,033, p = 0,012; varianti 2 e 3: +0,008, p = 0,46, e +0,004, p = 0,60).

## 7. File di riferimento
- `stage-13_v1/`, `stage-13_v2/`, `stage-13/`: `refinement_log.json`, `experiment_v*/`, `confirmation.json`, `experiment_final/`.
- `stage-03/queries.json`, `stage-05/shortlist.jsonl`, `stage-06/knowledge_meta.json`, `stage-06/cards/K2_implementation_card.md`.
- `stage-08/hypotheses.md`, `stage-12/runs/run-1.json`, `stage-15*/decision.md`, `stage-20/quality_report.json`, `deliverables/paper_final.md`.
