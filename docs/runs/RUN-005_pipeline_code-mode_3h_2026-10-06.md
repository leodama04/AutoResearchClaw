# RUN-005 — Seconda prova di 3 ore in modalità codice (kit 0.5.2)

| campo | valore |
|---|---|
| ID / data | RUN-005, 2026-10-06 (14:41–16:45 UTC) |
| tipo | pipeline completa, `ARC_DEADLINE_HOURS=3 ./run.sh relbench` (modalità codice) |
| versione del kit | 0.5.2 (errori visibili, componente verificato nella scheda, ricetta bloccata, codice ufficiale importabile) |
| run id | `rc-20261006-144130-9b9601` (zip `quarto_esperimento_relbench_f1_driver_top3`) |
| durata | 1,98 h di stage; 29/29 completati (`degraded=True`) |
| rapporto automatico | [RUN-005_auto.md](RUN-005_auto.md) (nota: la passata 3 vi appare come "config" per un errore del rapporto, ora corretto) |

## 1. Paper, repository e uso nel codice
- **Letteratura:** 752 paper raccolti; shortlist di 15 con lavori pertinenti (QUARTET, RelGT-AC, RelGT, foundation model per database, MetaSieve…) e alcuni fuori tema (malattie della soia, attacchi a GNN).
- **Schede (stage 6, ~2,5 min):** Qwen ne ha scelte solo 2 (su 4 possibili), entrambe lette dal testo completo:
  - **K1 – QUARTET** (cross-attenzione a 4 rami e cammini casuali per transformer su grafi relazionali): 3 parti lette, nessun repository.
  - **K2 – Relational Graph Transformer (RelGT)**: 2 parti lette.
- **Repository sbagliato.** Lo stage 5 ha associato a RelGT il repository `zjunlp/Relphormer`, codice di un altro paper ("Relphormer: Relational Graph Transformer for **Knowledge Graph** Representations", arXiv 2205.10852), trovato per somiglianza del titolo. Il kit ha dato la precedenza a questo invece che al link scritto nel PDF di RelGT (`github.com/snap-stanford/relgt`), e ha reso importabili 5 moduli di Relphormer (codice per knowledge graph basato su BERT, inutile qui); 7 file esclusi per dipendenze mancanti.
- **Uso nel codice:** 23 tentativi su 30 citano una scheda (K2: codifica posizionale tabellare, generatore GNN-PE e token a 5 elementi, modulo di attenzione locale/globale; K1: fusione con cross-attenzione, encoder di "sketch" topologico). Il codice importato è stato usato **una sola volta** (passata 1, iterazione 3, andata in errore). Il modello vincente non lo usa.
- **Sintesi e ipotesi** ora citano le schede (8 riferimenti ciascuna; nella RUN-004 erano 0); il piano dello stage 9 no.

## 2. Ricerca (stage 13): 30 tentativi in 3 passate
| esito | numero |
|---|---|
| valutazioni valide (10 semi) | 11 |
| rifiutati: `proposed` identico al baseline (modifica non attivata) | 7 |
| rifiutati: nessuna scheda citata | 1 |
| falliti | 11 (8 per la riparazione che sovrascrive `main.py`, 3 errori di codice: assert CUDA, lista di parametri vuota, tensori su dispositivi diversi) |

Gli errori ora sono visibili all'LLM (traceback reali nella storia). Il controllo di attivazione e quello sul componente funzionano; nessun override della ricetta di addestramento.
**Difetto grave trovato:** quando l'esecuzione fallisce, la riparazione automatica dell'LLM restituisce il modello corretto come blocco senza nome; la pipeline lo salvava come `main.py`, e il controllo sui file protetti non veniva applicato dopo la riparazione. Il programma risultante terminava in 2 secondi senza fare nulla (8 tentativi persi).

**Modello migliore:** opzione chiamata dall'LLM `gnn_type="relphormer"`, che in realtà è `TransformerConv` di PyG (4 teste, dropout sull'attenzione 0,3) + dropout 0,3 + LayerNorm nella testa; 14 righe cambiate; dichiarato "K2: Local Attention Module". È una versione semplificata dell'attenzione locale (attenzione sui vicini, non sui token del paper) ed è quasi l'operatore `transformer` già presente nel codice di partenza.

## 3. I "miglioramenti" erano rumore
Nella passata 3 lo **stesso identico codice** (stessi file, verificato con hash) è stato valutato tre volte: validazione **0,7901, 0,8060, 0,8164**. Le due accettazioni come miglioramento (+0,016 e +0,010) sono variazioni casuali, più grandi del margine di 0,005. Il baseline nella stessa run varia poco (0,782–0,785); il Transformer con dropout molto di più.

**Conferma su semi nuovi (100–109):**

| condizione | validazione | test |
|---|---|---|
| baseline_graphsage | 0,7345 ± 0,0539 | 0,7653 ± 0,0430 |
| baseline_tuned | 0,7847 ± 0,0083 | 0,7936 ± 0,0151 |
| proposed | 0,8002 ± 0,0315 | 0,8017 ± 0,0269 |

Test proposed − tuned **+0,008** (IC 95 % [−0,013, +0,029], 5 semi su 10, p = 0,49): **nessun miglioramento**. In validazione +0,016 (p = 0,064): molto meno dello 0,8164 della selezione.

## 4. Paper
Intitolato "Relphormer: Normalization and Dropout Improve RelBench GraphSAGE Baseline": prende il nome dall'opzione scelta dall'LLM (che coincide con un altro paper), non nomina mai `TransformerConv`, dichiara significativo p = 0,064, numeri incoerenti. Valutazione interna 2/10 ("Reject"); 8/8 citazioni verificate.

## 5. Interpretazione
- **Funziona:** errori visibili, ricetta bloccata, controllo del componente (niente citazioni di facciata come il GATv2 di RUN-004), ripartenza tra passate in modalità codice, schede fino alle ipotesi.
- **Non funziona ancora:** il codice ufficiale importato era di un altro paper; la riparazione sovrascriveva `main.py`; la selezione accetta il rumore; il paper usa il nome dell'opzione come nome del metodo.
- **Risultato scientifico:** nessun miglioramento sul test rispetto al baseline equo. Il +0,038 di RUN-004 resta l'unico risultato positivo (e va ancora attribuito con l'ablazione).

## 6. Decisioni (kit 0.5.3)
- **Repository verificato:** precedenza al link nel PDF; un repository trovato da una ricerca è accettato solo se il suo README cita l'id arXiv o un titolo lungo e specifico. Verificato sui repository reali: Relphormer scartato, `snap-stanford/relgt` accettato.
- **Riparazione:** un blocco senza nome va nel file a cui appartiene (`build_model` → `rb_model.py`), un file protetto modificato dalla riparazione viene spostato o ripristinato, e il controllo dei file protetti vale anche dopo la riparazione.
- **Tentativo identico alla versione migliore** rifiutato (rieseguire lo stesso codice misura solo rumore).
- **Ricontrollo prima di accettare:** un candidato che supera il migliore viene rivalutato su altri 10 semi (offset 200) e si usa la media delle due valutazioni.
- **File del metodo:** contiene le righe di codice cambiate, con la regola di usare i nomi standard degli operatori.
- **Specifica:** nomi delle opzioni descrittivi, non presi da paper non implementati.

## 7. File di riferimento
`stage-05/code_repos.json`, `stage-06/knowledge_meta.json`, `stage-06/impl_cards/`, `stage-06/vendor/`, `stage-13*/refinement_log.json`, `stage-13/confirmation.json`, `stage-13_v1/refine_sandbox_v2_fix/_project_1/main.py` (il `main.py` sovrascritto).
