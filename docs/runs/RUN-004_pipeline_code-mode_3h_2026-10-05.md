# RUN-004 — Prova di 3 ore in modalità codice con schede dai paper (kit 0.5)

| campo | valore |
|---|---|
| ID / data | RUN-004, 2026-10-05 (18:34–20:39 UTC) |
| tipo | pipeline completa, `ARC_DEADLINE_HOURS=3 ./run.sh relbench` (modalità codice) |
| versione del kit | 0.5 |
| run id | `rc-20261005-183409-9b9601` (zip `terzo_esperimento_relbench_f1_driver_top3`) |
| durata | 2,03 h di stage; 29/29 completati; lo stage 13 si è fermato per la scadenza globale |
| rapporto automatico | [RUN-004_auto.md](RUN-004_auto.md) |

## 1. Obiettivo
Verificare le modifiche chieste dal professore: letteratura dal 2010, lettura del testo completo dei paper in schede di implementazione,
uso obbligatorio delle schede nella scrittura del codice, Qwen libero di scrivere codice, scadenza per run lunghe.

## 2. Cosa ha funzionato
| modifica | esito |
|---|---|
| `year_min` 2010 e query curate | sì: 18 query (11 curate), 586 paper dal 2010 al 2026 (51 del 2010–2014). Shortlist più pertinente (RelGT, RelGT-AC, HetGNN, GIN…); RelGNN questa volta non c'è |
| lettura dei PDF e schede (stage 6, ~4 min) | sì: 4 schede, 3 dal testo completo (RelGT, From Schema to Signal, QUARTET; 2–4 parti lette ciascuno), 1 solo abstract |
| fedeltà della scheda RelGT (K2) | verificata sul PDF: +10,56 % su driver-top3 (0,7554 → 0,8352), K = 300 vicini, B = 4096 centroidi, lr 1e-4, L ∈ {1, 4, 8}, dropout {0,3; 0,4; 0,5}, batch 256, 10–20M parametri: tutto corretto |
| conoscenza nei prompt di scrittura del codice | sì: 28 tentativi su 29 citano una scheda (K2 o K3); 1 rifiutato perché senza citazione |
| tentativi ispirati ai paper | sì, nelle intenzioni: RelGT (encoder di token a 5 elementi, `RelGTConv`, attenzione temporale) in 9 tentativi, l'aggregatore RAM di K3 in 1 |
| margine di miglioramento | sì: 0,8229 non è stato accettato contro 0,8200 (differenza < 0,005) |
| scadenza globale | sì: `stop_reason = global_deadline` nella terza passata |
| paper | descrive il modello vero (GATv2, LayerNorm, residual, dropout, lr 1e-3); qualità 8/10; nessun metodo inventato. 9 numeri non trovano riscontro diretto (probabilmente intervalli calcolati da chi scrive): da controllare |

## 3. Risultati
**Modello migliore** (passata 1, iterazione 8; mai superato oltre il margine): `gnn_type=gatv2`, `residual=True`, `dropout=0.2`, `norm=layer_norm` (testa),
`lr=0.001`; dichiarato come `"K2: GATv2 attention-based aggregation with LayerNorm and dropout"`. Validazione 0,8200 (10 semi).

**Conferma su semi nuovi 100–109 (passata 1):**

| condizione | validazione | test |
|---|---|---|
| baseline_graphsage (ufficiale) | 0,7199 ± 0,0557 | 0,7559 ± 0,0219 |
| baseline_tuned | 0,7755 ± 0,0116 | 0,7923 ± 0,0242 |
| **proposed** | **0,8262 ± 0,0246** | **0,8300 ± 0,0091** |

Differenze appaiate: test proposed − tuned **+0,0376** (IC 95 % [+0,025, +0,049], 9 semi su 10, p = 0,004); test proposed − ufficiale +0,074 (10/10).
La conferma della terza passata dà numeri equivalenti (test +0,032, p = 0,004). **È il primo miglioramento sul test statisticamente supportato rispetto al baseline equo.**
In classifica (colonna driver-top3) 83,0 sarebbe vicino a RelGT (83,5), sopra Rel-LLM (82,2), sotto RelGNN (85,7).

## 4. Cosa non ha funzionato
1. **L'LLM non vedeva i propri errori.** Il log salvava solo i primi 2000 caratteri dello stderr, riempiti da un avviso di `torch_frame` ("Weights only load failed"); il traceback vero era tagliato.
   16 tentativi su 29 sono falliti. Ricostruendo il codice su dati finti: `add_self_loops=True` su GATv2 tra tipi di nodo diversi (4 volte), argomenti inesistenti (`add_self_loops`, `attn_drop`; 3), import sbagliati
   (`HeteroGraphSAGE` da `torch_geometric.nn`, `BatchNorm` da `torch.nn`; 2), forme dei tensori (2), `n_id` assente, `Embedding` con un intero, e 3 volte `rb_model.py` restituito incompleto (senza `build_model`).
2. **Citazione solo nominale.** Il vincitore cita K2 (RelGT) ma implementa GATv2, che non è nella scheda: il controllo verificava solo che ci fosse un id valido.
3. **Ricetta modificata.** In modalità codice gli override accettavano `lr` (e `batch_size`, `weight_decay`, `temporal_strategy`): il vincitore usa lr 1e-3 invece di 5e-3, quindi il guadagno non è attribuibile solo all'architettura.
4. **Ipotesi non collegate alle schede.** Lo stage 8 usa prompt di "prospettive" e una sintesi che non ricevevano la conoscenza; le ipotesi sono di nuovo inventate (0 citazioni). Il piano (stage 9) cita K2.
5. **Nessuna ripartenza tra le passate.** La ripartenza dalla versione migliore era attiva solo in modalità configurazioni: le passate 2 e 3 sono ripartite dal codice ufficiale.
6. **Nessun repository clonato** allo stage 5 (causa non nota, il log non c'è); il PDF di RelGT contiene però il link al codice ufficiale (`github.com/snap-stanford/relgt`).
7. **Scelta dei paper migliorabile:** solo K2 descrive un'architettura da portare; K1 (solo abstract) e K3 (retrieval) richiedono componenti esterni.

## 4b. Interpretazione
- **Dimostrato:** la catena paper → scheda → prompt funziona e le schede sono fedeli; il modello trovato migliora il test di circa 3–4 punti rispetto al baseline equo, su semi nuovi.
- **Non dimostrato:** che il guadagno venga dai paper. Il vincitore è un GATv2 con residual e LayerNorm, opzioni già presenti nel codice, più un learning rate diverso.
  Nello sweep di RUN-000, GATv2 da solo (lr 5e-3) era peggiore del baseline; quanto conti lr 1e-3 va misurato con l'ablazione (§6).
- **Limiti:** una sola run; stessa validazione usata per scegliere; divario sweep/pipeline ancora da chiarire.

## 5. Tempi (per pianificare 24 h)
Una valutazione completa dura ~119 s; un'iterazione con l'LLM ~190 s → circa 450 iterazioni in 24 h (stima). Lo stage 6 con 4 paper ~4 min.

## 6. Decisioni (kit 0.5.1)
- Stderr: si conserva la fine (traceback) e anche dopo la riparazione; l'avviso di torch_frame è silenziato; nella storia per l'LLM c'è solo l'estratto dell'errore.
- `PROPOSED_SOURCE` deve nominare un componente descritto nella scheda citata (≥ 60 % delle parole); il vincitore di RUN-004 sarebbe stato rifiutato.
- Ricetta bloccata anche in modalità codice (`locked_keys`: lr, batch_size, epochs, weight_decay…; `ARC_LOCK_RECIPE=0` per sbloccare).
- Ripartenza e memoria tra le passate anche in modalità codice.
- Schede anche alla sintesi (stage 7) e alla sintesi delle ipotesi (stage 8); link al codice ufficiale estratti dai PDF e clonati.
- Skill `relbench-gnn-code` aggiornata con gli errori PyG osservati.
- Ablazione pronta: `RB_SWEEP_CONFIGS_JSON=/app/rb_task/task_spec/ablation_run004.json RB_SWEEP_THREADS=1 RB_SWEEP_SEEDS=10 ./run.sh sweep`.

## 7. File di riferimento
`stage-06/knowledge_meta.json`, `stage-06/impl_cards/`, `stage-06/papers/`, `stage-13*/refinement_log.json`, `stage-13*/confirmation.json`, `stage-23/paper_final_verified.md`.

## Aggiornamento 2026-10-06: perché nessun repository
Lo stage 5 cerca il codice solo per i primi 5 paper della shortlist, con DuckDuckGo e con la ricerca GitHub sul titolo. In questa run i primi 5 erano lavori del 2026
(RelGT-AC, foundation model per database, viste SQL, augmentation con LM, attacchi avversari) e la ricerca non ha restituito nulla; RelGT era 8° e non è stato cercato.
Il codice ufficiale di RelGT esiste (`github.com/snap-stanford/relgt`, 816 KB, 6 file Python; i moduli del modello dipendono solo da torch, PyG, numpy ed einops)
ed è citato sia nel PDF sia nel README con l'id arXiv. Kit 0.5.2: ricerca per i paper delle schede e codice importabile (vedi CHANGELOG).
