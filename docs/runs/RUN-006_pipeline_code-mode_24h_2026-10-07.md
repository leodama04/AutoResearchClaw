# RUN-006 — Run "da 24 ore" in modalità codice (kit 0.5.3)

| campo | valore |
|---|---|
| ID / data | RUN-006, 2026-10-07 (08:54–11:10 UTC) |
| tipo | pipeline completa, `ARC_DEADLINE_HOURS=24 ./run.sh relbench` (modalità codice) |
| versione del kit | 0.5.3 |
| run id | `rc-20261007-085443-9b9601` (zip `quinto_esperimento_relbench_f1_driver_top3`) |
| durata | **2,21 h** invece di 24: vedi §1 |
| rapporto automatico | [RUN-006_auto.md](RUN-006_auto.md) |

## 1. Perché è durata solo 2 ore (errore mio)
Il codice originale della pipeline limita ogni passata di raffinamento a **10 iterazioni** (`max_iterations = min(richieste, 10)` in `_execution.py`)
e fa al massimo 3 passate (`MAX_DECISION_PIVOTS = 2`): 30 iterazioni in tutto, qualunque sia la scadenza. Ogni passata si è fermata con
`max_iterations_reached` dopo 10 iterazioni. I miei test non lo avevano rilevato perché usavano meno di 10 iterazioni; la stima di
"circa 450 iterazioni in 24 ore" era quindi sbagliata. Kit 0.6: `ARC_MAX_REFINE_ITERS` (1000 in `./run.sh relbench`).

## 2. Paper, repository, codice ufficiale
- **Letteratura:** 587 paper; shortlist di 15 (foundation model per database, RelGT, QUARTET, RelGT-AC, MetaSieve, HetGNN, GIN…).
- **Schede:** Qwen ne ha scelte 2, entrambe lette dal testo completo: **K1 – RelGT** e **K2 – QUARTET**. Il paper con il solo abstract
  (BigComp 2026) era nella shortlist ma non è stato scelto.
- **Repository:** lo stage 5 aveva associato di nuovo Relphormer a RelGT; il kit l'ha **scartato** e ha preso il link del PDF,
  `github.com/snap-stanford/relgt`. Tutti e 5 i moduli di RelGT sono stati resi importabili (`model`, `local_module`, `encoders`,
  `codebook`, `utils`), grazie a `einops` e `h5py` aggiunti all'immagine. QUARTET: nessun codice trovato.

## 3. Raffinamento: 30 tentativi, nessun miglioramento
| esito | numero |
|---|---|
| valutazioni valide | 4, tutte peggiori del baseline (0,7165; 0,7105; 0,6767; 0,6865 contro 0,7737) |
| rifiutati: nessuna modifica rispetto alla versione migliore | 9 |
| rifiutati: componente non presente nella scheda | 5 (tutti "multi-head attention aggregation" con GATv2/Transformer) |
| rifiutati: `proposed` identico al baseline | 2 |
| falliti con errore | 10 (forme dei tensori, `add_self_loops` su GATv2, import circolare di `rb_train`, `gnn_type` non registrato, argomenti sbagliati…) |

**Uso del codice ufficiale di RelGT:** 5 tentativi lo hanno importato (`encoders`, `local_module`, `codebook`, `utils`), e Qwen ha creato
un file `rb_relgt.py`. Nessuno ha funzionato: errori di forma (`mat1 and mat2 shapes cannot be multiplied`), argomenti sbagliati, indice vuoto,
e una volta il codice c'era ma non era attivato. Il problema è l'adattatore: RelGT lavora su insiemi di token per seme (seme + K vicini, con tipo,
salti e tempo), mentre il nostro batch è un grafo eterogeneo.
**Implementazioni scritte da zero:** `rb_quartet.py` (cross-attenzione ispirata a QUARTET, 0,7165), un'attenzione locale "relgt_local" (0,7105),
un gate di attenzione relazionale (0,6865): tutte peggiori del baseline.

**I 9 tentativi "nessuna modifica"** hanno probabilmente modificato solo file protetti (le cui modifiche vengono scartate) o non hanno restituito codice;
le risposte dell'LLM non sono salvate, quindi non posso distinguerle. Ognuno è costato ~2 minuti di esecuzione inutile.

**Conferma (semi 100–109):** baseline_tuned test 0,7717, proposed 0,7717: nessuna differenza (il modello finale è il baseline).
**Paper:** "When FeaGate Falls Short: Recipe Optimization Dominates…", qualità 2/10 (Reject): tabelle in contrasto con i dati.

## 4. Indicazioni del professore (dopo il messaggio sulla RUN-004)
1. Se il codice ufficiale esiste va usato: copiarlo, non riscriverlo, per evitare errori e allucinazioni.
2. Senza codice, i paper importanti si possono implementare.
3. Prendere codice generico citando un paper va bene se è pertinente: conta il miglioramento.
4. Su arXiv c'è sempre il testo completo: i paper con il solo abstract (da altre fonti) vanno scartati.
5. Verificare quanto il sistema riesce a riusare il codice esistente; poi una run vera da 24 ore per vedere quante iterazioni fa.

## 5. Decisioni (kit 0.6)
- Tetto di 10 iterazioni rimosso (`ARC_MAX_REFINE_ITERS=1000`); la scadenza globale ferma la run. Pazienza 60, tolleranza 30 tentativi senza metriche.
- **Ponte dati `rb_tokens.py`** (sola lettura): `seed_token_sets(batch, x_dict, entity_table, k)` produce gli insiemi di token per seme
  (seme in posizione 0, ordinati per salti, con tipo di nodo, salti e tempo relativo). Verificato: i token passano nel `RelGTLayer` ufficiale.
- **Codice ufficiale per primo** nelle istruzioni, nella specifica e nella skill `paper-to-code`, con un esempio d'uso di `RelGTLayer`.
- **Uso del codice misurato:** ogni tentativo registra i moduli ufficiali importati (`arc_official_code`); la storia mostra all'LLM se ha importato
  codice ufficiale e quali modifiche sono state scartate dalla guardia.
- **Tentativi identici non eseguiti** (risparmio di ~2 min ciascuno), senza far scattare la riparazione automatica.
- **Codice generico ammesso** se pertinente (controllo sul componente disattivato per default, `ARC_REQUIRE_COMPONENT_MATCH=1` per riattivarlo);
  resta obbligatoria la citazione della scheda.
- **Solo paper con testo completo** nelle schede (`ARC_REQUIRE_FULLTEXT=1`): i paper senza versione arXiv (anche cercata per titolo) vengono scartati.
