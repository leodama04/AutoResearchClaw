# RUN-016 — Ablazione del modello di RUN-004: learning rate e architettura (varianti 3, 1, 2 dei tipi delle colonne)

| campo | valore |
|---|---|
| ID / data | RUN-016, 2026-10-30 (primo tentativo il 2026-10-29, fallito: §2.3) |
| tipo | sweep senza LLM (ablazione), `rb_task/tools/sweep.py` |
| comando | `ch5_runs_2.sh`, funzione `ablation`: `docker run ... arc-relbench:latest` con `ARC_NO_LLM=1`, `RB_SWEEP_CONFIGS_JSON=/app/rb_task/task_spec/ablation_run004.json`, `RB_SWEEP_SEEDS=10`, `RB_SWEEP_SEED_OFFSET=100`, `RB_SWEEP_THREADS=1`, `RB_CACHE_DIR` con `stypes.json` = variante 3, 1, 2 di RUN-015 |
| manifest | nessuno da `run.sh` (container lanciato direttamente per fissare la variante); al suo posto `artifacts/ch5_a_ablation_v{3,1,2}/info.txt` (data, commit, kit, GPU) |
| versione del kit | relbench-kit 0.6.11, commit `25844e5` (nessuna modifica al kit) |
| durata | circa 5 minuti per variante (variante 3 dalle 08:43:58, variante 1 dalle 09:22:00, variante 2 dalle 09:27:14 UTC); GPU libera (40 MiB occupati all'avvio) |

## 1. Obiettivo
RUN-004 è l'unica run della pipeline con un guadagno significativo sul test rispetto a `baseline_tuned` (+0,038, +0,039, +0,032 nelle tre
conferme). Il modello però cambia anche il learning rate (1e-3 invece di 5e-3), allora non ancora bloccato in modalità codice
([RUN-004 §4b e §6](RUN-004_pipeline_code-mode_3h_2026-10-05.md)). Quanto del guadagno viene dal learning rate e quanto
dall'architettura?

## 2. Setup
### 2.1 Configurazioni
Le sette configurazioni di `rb_task/task_spec/ablation_run004.json` (già nel kit dalla 0.5.1), tutte sul modello ufficiale congelato
(`rb_model_official.py`) con la ricetta `tuned` (batch 128, 10 epoche) e le modifiche indicate:

- riferimento: `baseline_tuned` (nessuna modifica, lr 5e-3);
- modello di RUN-004: `gnn_type=gatv2`, `residual=True`, `dropout=0.2`, `norm=layer_norm` (testa), `lr=0.001`;
- stessa architettura con lr 5e-3 (ricetta invariata);
- solo lr 1e-3 (modello ufficiale GraphSAGE);
- solo GATv2 con lr 1e-3;
- modello di RUN-004 senza residual (lr 1e-3);
- aggregazione `max` (il vincitore di RUN-003) con lr 1e-3.

La configurazione "modello di RUN-004" coincide con il modello finale di RUN-004: in `stage-13/experiment_final` di quella run
`rb_model.py` differisce dal modello iniziale solo per 3 righe che filtrano un warning, e il file del modello iniziale coincide con
`rb_model_official.py` attuale salvo la docstring; l'override `aggr: 'mean'` di RUN-004 non ha effetto con GATv2 (`make_conv` non lo usa). Il codice di addestramento e dei dati è
quello del kit 0.6.11, non quello del kit 0.5 usato da RUN-004 (in RUN-017 il modello di RUN-004 è rivalutato con i file della sua run).

### 2.2 Semi, statistiche e varianti
Semi 100–109, gli stessi per tutte le configurazioni; differenze appaiate per seme rispetto al riferimento, IC 95% bootstrap
(10.000 ricampionamenti), test esatto con inversione dei segni, semi in cui la configurazione è meglio (calcolati da
`sweep_results.json`). Per non dipendere dalla variante pescata dal container, `stypes.json` è fissato: prima la variante 3 (quella di
RUN-004 secondo [RUN-015](RUN-015_repro-stypes_2026-10-23.md)), poi la 1 e la 2. I file delle varianti sono quelli scritti da
`repro-stypes` il 29/10 (identici byte per byte nelle cinque esecuzioni e uguali alle varianti di RUN-015: la 2 ha
`qualifying.position` categorica, la 3 `constructor_standings.position` categorica).

### 2.3 Primo tentativo (2026-10-29, `ch5_runs.sh`)
Lo sweep lanciato con `./run.sh sweep` non ha scritto nessuna riga (nemmeno la prima) ed è terminato dopo circa 2,5 minuti; in quel
momento un altro utente occupava 26 GB della GPU. Senza log la causa non si può stabilire. Il file `artifacts/ch5_a_ablation_run004.json`
copiato da quello script è il vecchio `sweep_results.json` di RUN-002 (riferimento 0,7565 / 0,7617, `aggr=max`, `transformer`), **non**
l'ablazione: non va usato.

## 3. Risultati (fatti)
Differenze dal riferimento (`baseline_tuned`) sul test e sulla validazione, 10 semi.

| configurazione | variante 3 | variante 1 | variante 2 |
|---|---|---|---|
| `baseline_tuned` (riferimento): val / test | 0,7710 / 0,7941 | 0,7595 / 0,7778 | 0,7872 / 0,8026 |
| modello di RUN-004 (GATv2, residual, dropout 0,2, LayerNorm nella testa, lr 1e-3) | test +0,036 [+0,023, +0,050], p = 0,002, 10/10; val +0,054 (p = 0,004) | test +0,048 [+0,036, +0,061], p = 0,002, 10/10; val +0,063 (p = 0,002) | test +0,025 [+0,016, +0,034], p = 0,002, 10/10; val +0,064 (p = 0,002) |
| stessa architettura, lr 5e-3 (ricetta invariata) | test +0,019 [+0,003, +0,035], p = 0,057, 7/10; val −0,027 (p = 0,246) | test +0,024 [−0,008, +0,050], p = 0,178, 8/10; val −0,036 (p = 0,219) | test +0,012 [−0,000, +0,025], p = 0,115, 6/10; val −0,007 (p = 0,668) |
| solo lr 1e-3 (modello ufficiale) | test −0,020 [−0,043, +0,000], p = 0,125, 4/10; val −0,002 (p = 0,736) | test +0,006 [−0,013, +0,026], p = 0,574, 5/10; val +0,017 (p = 0,037) | test −0,024 [−0,035, −0,013], p = 0,002, 0/10; val −0,004 (p = 0,109) |
| solo GATv2 + lr 1e-3 | test −0,029 [−0,050, −0,010], p = 0,021, 1/10; val −0,037 (p = 0,002) | test −0,017 [−0,044, +0,009], p = 0,283, 5/10; val −0,018 (p = 0,018) | test −0,036 [−0,053, −0,020], p = 0,004, 1/10; val −0,059 (p = 0,002) |
| modello di RUN-004 senza residual | test −0,039 [−0,061, −0,019], p = 0,008, 1/10; val −0,029 (p = 0,008) | test −0,007 [−0,024, +0,010], p = 0,439, 3/10; val −0,030 (p = 0,010) | test −0,034 [−0,064, −0,008], p = 0,037, 2/10; val −0,066 (p = 0,002) |
| aggregazione max + lr 1e-3 | test +0,035 [+0,020, +0,051], p = 0,002, 10/10; val +0,079 (p = 0,002) | test +0,048 [+0,031, +0,067], p = 0,002, 10/10; val +0,084 (p = 0,002) | test +0,024 [+0,014, +0,033], p = 0,004, 9/10; val +0,082 (p = 0,002) |

Correlazione di rango validazione–test tra le 7 configurazioni (stampata dallo strumento): +0,82 (variante 3), +0,57 (variante 1),
+0,82 (variante 2).

## 4. Interpretazione
- **Dimostrato:**
  - Il modello di RUN-004 riproduce il suo guadagno con tutte e tre le varianti: da +0,025 a +0,048 sul test, p = 0,002, meglio su
    tutti i 10 semi. Il risultato di RUN-004 non dipende dalla variante dei tipi delle colonne (vedi anche RUN-017).
  - **Con il learning rate della ricetta (5e-3) la stessa architettura non dà un guadagno significativo**: da +0,012 a +0,024 sul test
    (p tra 0,057 e 0,178) e una validazione **più bassa** del riferimento (da −0,007 a −0,036). Con la ricetta bloccata non sarebbe
    stata scelta.
  - Il learning rate da solo non basta: sul modello ufficiale lr 1e-3 dà da −0,024 a +0,006 sul test (con la variante 2 è
    significativamente peggiore, p = 0,002). Anche GATv2 da solo con lr 1e-3 e il modello di RUN-004 senza connessioni residue sono
    peggiori o uguali al riferimento.
  - Il guadagno richiede quindi il learning rate più basso **insieme** alle altre modifiche, in particolare alle connessioni residue.
  - L'aggregazione `max` con lr 1e-3 dà lo stesso guadagno del modello di RUN-004 (da +0,024 a +0,048, p ≤ 0,004), con una
    validazione più alta. L'architettura GATv2 trovata in RUN-004 non è quindi l'ingrediente specifico del guadagno.
- **Ipotesi non verificate:**
  - Perché il learning rate più basso aiuta solo insieme alle altre modifiche (per esempio perché le connessioni residue e la
    normalizzazione rendono stabile un addestramento che con lr 5e-3 oscilla); non misurato.
  - Se il guadagno resti con più epoche o con altri valori del learning rate: provati solo 5e-3 e 1e-3, 10 epoche.
- **Cosa è andato storto:** il primo tentativo (§2.3).
- **Limiti:** 10 semi; un solo task; una valutazione per variante (il non determinismo dell'addestramento su GPU vale circa 0,01 per
  `baseline_tuned`, RUN-014); le configurazioni sono state scelte guardando il risultato di RUN-004.

## 5. Decisioni e prossimi passi
- Tesi: il guadagno di RUN-004 è reale e robusto alle varianti, ma è legato al cambio del learning rate, che il protocollo ha poi
  bloccato; con la ricetta fissa l'architettura trovata non migliora il test in modo significativo e peggiora la validazione.
- Nessuna modifica al kit.

## 6. Errata
Nessuna. Da aggiungere come aggiornamento in [RUN-004 §4b](RUN-004_pipeline_code-mode_3h_2026-10-05.md): l'ablazione è stata fatta qui.

## 7. File di riferimento
`artifacts/ch5_a_ablation_v{3,1,2}/sweep_results.json` (valori per seme), `log.txt`, `info.txt`; `artifacts/ch5_runs_2.log`;
`rb_task/task_spec/ablation_run004.json`; varianti: `artifacts/ch5_c_run004_top3/stypes/variant_{1,2,3}.json`.
