# RUN-002 — Conferma dei vincitori dello sweep architetturale su semi nuovi

| campo | valore |
|---|---|
| ID / data | RUN-002, 2026-10-04 |
| tipo | conferma (senza LLM) |
| comando | `RB_SWEEP_MODE=arch RB_SWEEP_ONLY="aggr=max,transformer" RB_SWEEP_SEEDS=10 RB_SWEEP_SEED_OFFSET=100 ./run.sh sweep` |
| versione del kit | 0.2 (il manifest automatico non esisteva ancora) |
| dati | `rel-f1` / `driver-top3`, tabelle ufficiali; ricetta `tuned` (`batch_size` 128) fissa |
| semi | 100–109 (nessuno usato nella scoperta, che usava 0–4) |
| output | `sweep_results.json` nella cartella del repo |

## 1. Obiettivo
Lo sweep architetturale ([RUN-000 §2.4](RUN-000_preliminari_2026-10-04.md)) ha indicato `aggr=max` e `transformer` come grandi miglioramenti, ma erano i due migliori di 14 candidati valutati con 5 semi:
rischio di sovrastima ("winner's curse"). Questa run li rivaluta su semi mai usati per sceglierli.

## 2. Risultati (fatti)
10 semi per configurazione; `baseline` = GraphSAGE ufficiale con la ricetta `tuned`.

| configurazione | val AUROC | test AUROC | picco GPU | tempo/run |
|---|---|---|---|---|
| baseline (ricetta fissa) | 0,7565 ± 0,019 | 0,7617 ± 0,018 | 1,3 GB | 4 s |
| **aggr=max** | **0,8561 ± 0,019** | **0,8123 ± 0,013** | 1,2 GB | 4 s |
| **transformer** | **0,8211 ± 0,043** | **0,8175 ± 0,007** | 2,0 GB | 5 s |

Differenze rispetto al baseline (errore standard = √((s₁² + s₂²)/10)):

| configurazione | Δ val | Δ test |
|---|---|---|
| aggr=max | **+0,100** (+11,9 SE) | **+0,051** (+7,2 SE) |
| transformer | **+0,065** (+4,3 SE) | **+0,056** (+9,0 SE) |

Confronto con la scoperta (semi 0–4): `aggr=max` Δ val +0,103 / Δ test +0,035; `transformer` Δ val +0,088 / Δ test +0,022.

## 3. Interpretazione
- **Dimostrato (su questo split di validazione e test):** entrambi i miglioramenti sono reali e di grande entità. Per `aggr=max` l'effetto sulla validazione si è riprodotto quasi identico (+0,100 contro +0,103) e sul test è risultato maggiore (+0,051 contro +0,035).
  Per `transformer` l'effetto sulla validazione si è ridotto (+0,065 contro +0,088, coerente con una parte di sovrastima da selezione) e sul test è aumentato (+0,056 contro +0,022).
- Il baseline ha test 0,762 in questa run contro 0,780 nella scoperta: la differenza è rumore del baseline (deviazione standard 0,018–0,026), e spiega in parte perché i Δ sul test sono maggiori qui.
- Il Transformer è instabile in validazione (deviazione standard 0,043) ma molto stabile sul test (0,007); `aggr=max` è stabile in entrambi. `aggr=max` è anche la scelta più economica (1,2 GB, come il baseline).
- **Ipotesi non verificate:** perché `max` aiuti (le somme su vicini numerosi, come i risultati di una gara con molti piloti, producono feature di scala molto diversa tra nodi; `max` le satura) — è una spiegazione plausibile, non l'ho testata. Non so se i due effetti si sommano:
  `aggr` ha effetto solo con `gnn_type=sage`, quindi non sono combinabili direttamente.
- **Limiti:** l'errore standard tratta i semi come campioni indipendenti, ma il test è sempre lo stesso insieme di 726 righe (e la validazione di 588): non è dimostrato che il miglioramento si estenda ad altri periodi o ad altri dataset.
  I Δ sono rispetto a `baseline_tuned` (batch 128); rispetto alla ricetta ufficiale il vantaggio apparente sarebbe maggiore ma confuso con l'addestramento più lungo.

## 4. Decisioni e prossimi passi
- `aggr=max` e `transformer` sono i riferimenti per valutare la pipeline: una ricerca autonoma funziona se li ritrova (o trova di meglio).
- Prossima run: pipeline completa in **modalità a configurazioni** (kit 0.3). Si guarderà (a) se l'LLM scopre `max`/`transformer`, (b) se la conferma finale su semi 100–109 coincide con questi numeri, (c) se il paper riporta numeri coerenti.

## 5. File di riferimento
- `sweep_results.json` (tutte le serie per seme), output del terminale incollato nella conversazione.

## 6. Errata (aggiunta dopo RUN-003)
I Δ sul test (+0,051 per `aggr=max`, +0,056 per `transformer`) sono calcolati rispetto a un `baseline_tuned` misurato dallo sweep (test 0,762). La pipeline, sugli stessi semi 100–109 e con la stessa configurazione, misura 0,80 per quel baseline
(RUN-003). Lo sweep e `main.py` danno numeri sistematicamente diversi (causa non identificata; unica differenza di codice trovata: `torch.set_num_threads(1)` in `main.py`). Il vantaggio reale sul test è quindi probabilmente più vicino a +0,01…+0,02.
Il Δ sulla validazione (+0,100) si è invece riprodotto nella pipeline. Test A/B proposto: `RB_SWEEP_THREADS=1`.
