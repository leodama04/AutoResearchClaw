# RUN-007 — pipeline in modalità codice "non guidata" (kit 0.6.2): fallita allo stage 13 con HTTP 400

| campo | valore |
|---|---|
| ID / data | RUN-007, 2026-10-10 |
| tipo | pipeline completa (modalità codice, Qwen sceglie da solo paper e architetture) |
| comando | `./run.sh relbench` (manifest non allegato: durata richiesta non nota) |
| manifest | non disponibile in questa analisi |
| versione del kit | 0.6.2 (prima versione senza indicazioni di metodi e senza operatori "scorciatoia") |
| run id (pipeline) | `rc-20261010-133700-9b9601` (zip della cartella `artifacts/`) |
| durata | 0,58 h (35 min, 13:37–14:12); stage 13 fallito dopo 216 s |
| rapporto automatico | [RUN-007_auto.md](RUN-007_auto.md) |

## 1. Obiettivo
Prima run con il kit 0.6.2: nessun nome di metodo, nessuna query scritta da noi, `proposed` che parte dal solo modello ufficiale.
Domanda: Qwen, partendo dalle proprie ricerche, trova e usa paper e codice utili per migliorare il GNN su `driver-top3`?

## 2. Setup
- rel-f1 / driver-top3, ricetta `tuned` bloccata, 10 semi, selezione solo sulla validazione; Qwen3.6-35B-A3B (llama.cpp, contesto 65.536).
- Kit 0.6.2: `ARC_SEED_FILE_MAP="rb_model.py=rb_model_minimal.py"`, `ARC_LIT_YEAR_MIN=2010`, `ARC_REQUIRE_FULLTEXT=1`,
  `ARC_KNOWLEDGE_MAX_CHARS=20000`, `ARC_MAX_TOKENS_MULT=3`, pazienza 60, 30 tentativi senza metriche al massimo.

## 3. Risultati (fatti letti dai file della run)

### 3.1 Letteratura e conoscenza (stage 3–9): ha funzionato, senza indicazioni nostre
- Query scritte da Qwen (`stage-03/queries.json`, `model_queries_extracted: true`): *relational deep learning benchmarks*,
  *graph sage baseline relbench*, *binary classification graph networks*, *schema conditioned feature projection*,
  *table provenance embedding injection*, *parameter efficient graph routing*, *adaptive relational message aggregation*,
  *dynamic graph neighborhood weighting*, *graph neural network applications*. Anno minimo 2010 applicato allo stage 4.
- 414 candidati, 15 in shortlist; 3 scartati perché senza testo completo; 3 schede costruite dal testo completo (stage 6, 815 s):

| scheda | paper | codice ufficiale | file vendorizzati |
|---|---|---|---|
| K1 | QUARTET: Quad-branch cross-Attention and Random-walk Traces… (2026, arXiv 2609.26855) | non trovato | 0 |
| K2 | **RelGNN**: Composite Message Passing for Relational Deep Learning (2025, arXiv 2502.06784) | snap-stanford/RelGNN | 25 (153.657 caratteri) |
| K3 | Boosting Relational Deep Learning with Pretrained Tabular Models (LightRDL, 2025, arXiv 2504.04934) | AntonioLonga/LightRDL | 3 (37.212 caratteri) |

- RelGNN è uno dei metodi più forti in classifica su driver-top3 (85,7 di AUROC di test contro 75,5 di RDL): Qwen lo ha trovato da solo.
- Ipotesi (stage 8): H1 su K2 (instradamento sulle "atomic routes" di RelGNN), H2 su K3, H3 su K1.

### 3.2 Esperimento di riferimento (stage 12): il baseline non è mai stato addestrato
- La GPU era piena: il primo avvio è fallito con `CUDA error: out of memory` già in `torch.cuda.mem_get_info()` (creazione del contesto CUDA).
- La riparazione automatica dello stage 12 ha modificato il codice due volte per un problema dell'ambiente: `try/except` attorno alla
  lettura della memoria in `main.py` e l'embedder del testo spostato su CPU in `rb_text.py`. Terza esecuzione: di nuovo out of memory in
  `model.to(device)` (`rb_train.run_one`), dopo 6,3 s.
- L'unica metrica stampata era quella diagnostica `proposed_identical_to_baseline` (riportata prima dell'addestramento): per questo
  lo stage 12 è risultato "done" e la riparazione "success", e il blocco del codice originale per le run senza dati reali non è scattato.

### 3.3 Raffinamento (stage 13): fallito al primo tentativo
- Tentativo 1: Qwen ha scritto in `rb_config.py` `PROPOSED_OVERRIDES = {'gnn_type': 'relgnn', 'simplified_MP': True}` e
  `PROPOSED_SOURCE = 'K2: RelGNN composite message passing'`, senza toccare `rb_model.py` e senza importare i moduli ufficiali.
  Il modello minimo ignora quelle chiavi: se la run fosse andata a buon fine, il controllo "identico al baseline" l'avrebbe respinta
  e il motivo sarebbe tornato a Qwen.
- La run del tentativo è partita; dopo la run è scattata la riparazione (l'esito preciso della run non è stato salvato: l'eccezione ha
  interrotto lo stage prima di scrivere `refinement_log.json`). Il prompt di riparazione conteneva **tutti** i file del progetto:

| parte del prompt di riparazione | caratteri | token (stima, tokenizer Qwen) |
|---|---|---|
| file del progetto, totale | 241.856 | 57.902 |
| di cui `vendor_*.py` (RelGNN + LightRDL) | 192.182 | 45.514 |
| KNOWLEDGE.md (schede) | 19.299 | 5.384 |
| 3 skill del progetto | 6.251 | 1.638 |
| **totale stimato** | | **~65.200 + stderr** |

  Il contesto di llama-server è 65.536 token: la richiesta lo supera e il server risponde **HTTP 400**; il codice dello stage 13
  rilancia l'errore e l'intera pipeline si ferma ("12/13 stages done, 1 failed").
- Riprodotto in un test (`rb_task/tests/test_stage13_robustness.py`): con il kit 0.6.2 il test si ferma con lo stesso
  `RuntimeError: All models failed. Last error: HTTP Error 400: Bad Request`.

## 4. Interpretazione
- **Dimostrato:**
  - La parte "non guidata" funziona: query di Qwen, paper con testo completo, scelta di RelGNN con il suo codice ufficiale, ipotesi
    ancorate alle schede. Nessuna di queste scelte è venuta da noi.
  - Il fallimento è un difetto del kit, deterministico: i prompt di riparazione mostravano il codice vendorizzato (il filtro c'era solo
    nel prompt di miglioramento). In RUN-006 il vendor di RelGT era ~60.000 caratteri e il prompt ci stava; RelGNN ne porta 153.657
    perché il vendoring prendeva anche gli script di addestramento (11 file con argparse) e una copia di relbench inclusa nel repo
    (6 file, identica a relbench 1.1.0).
  - Il baseline non è stato addestrato perché la GPU era occupata; la riparazione dello stage 12 ha "corretto" il codice per un
    problema che era dell'ambiente.
- **Ipotesi non verificate:**
  - Chi occupava la GPU (altri utenti, come nelle run precedenti, o un processo rimasto da una run precedente): `nvidia-smi` di quel
    momento non è disponibile.
  - Il motivo esatto del fallimento della run del tentativo 1 (probabilmente di nuovo out of memory) e il messaggio di llama-server
    (si legge con `grep -n "exceed\|context" ~/AutoResearchClaw/llama-server.log | tail`).
- **Cosa è andato storto (difetti trovati):**
  1. prompt di riparazione con il codice vendorizzato → oltre il contesto → HTTP 400;
  2. un errore dell'LLM fa fallire tutto lo stage 13 invece del solo tentativo;
  3. la riparazione parte anche per i warning su stderr, non solo per i crash (una run riuscita può essere "riparata" e rieseguita);
  4. vendoring di script e di copie di librerie;
  5. la storia mostrata a Qwen è `run_summaries[:20]`, le prime 20 voci: in una run lunga Qwen smette di vedere gli ultimi tentativi;
  6. GPU piena non riconosciuta come problema dell'ambiente; metrica diagnostica riportata troppo presto.
- **Limiti:** la stima in token usa il vocabolario della famiglia Qwen (`qwen.tiktoken`), non quello esatto di Qwen3.6; la conclusione
  non cambia (vendor + resto superano il contesto anche con un margine del 10%).

## 5. Decisioni e prossimi passi
- Kit **0.6.3** (vedi `docs/CHANGELOG_KIT.md`): solo correzioni dei difetti 1–6; nulla cambia in ciò che viene detto a Qwen su paper e
  architetture. Con il nuovo vendoring RelGNN diventa 8 moduli (~37.500 caratteri) e i prompt di riparazione scendono a ~16.000 token.
- Prima di rilanciare: `./run.sh vram` (o `nvidia-smi`) per vedere chi occupa la GPU; `./run.sh relbench` ora si ferma da solo se ci sono
  meno di 27,5 GB liberi.
- Rilanciare prima un test breve (`ARC_DEADLINE_HOURS=3 ./run.sh relbench`) e controllare in `stage-13/refinement_log.json` che i tentativi
  vengano valutati; poi la run da 24 ore.

## 6. Errata
Nessuna correzione a documenti precedenti. Nota: il problema 3 (riparazione per i warning) riguardava anche RUN-004/005/006
(17/29, 11/31 e 13/30 tentativi passati da una riparazione); dai rapporti salvati non si può dire quanti fossero run già riuscite.

## 7. File di riferimento
- `rc-20261010-133700-9b9601/stage-13/stage_health.json` (errore), `stage-13/experiment_v1/` (tentativo 1 con i 28 file vendor).
- `stage-12/stage12_repairs.json`, `stage-12/runs/run-1.json` (out of memory), `stage-12/experiment_before_repair` / `experiment_repaired`.
- `stage-06/knowledge_meta.json` (paper, repository, file vendorizzati e scartati), `stage-06/KNOWLEDGE.md`, `stage-03/queries.json`.
