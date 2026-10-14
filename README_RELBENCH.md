# AutoResearchClaw su RelBench v1 (rel-f1 / driver-top3)

## Contenuto del kit (da copiare nella root di ~/AutoResearchClaw)
- `rb_task/seed_project/`  GNN ufficiale RelBench in file piccoli (punto di partenza che la pipeline migliora)
- `rb_task/task_spec/`     specifica del task iniettata nei prompt (`full.md`, `short.md`)
- `rb_task/patches/`       patch al codice della pipeline (+ moduli di supporto)
- `rb_task/tests/`         test di fumo su dati finti + script di prefetch del Dockerfile
- `config.arc.relbench.yaml`, `Dockerfile.arc-relbench`, `run.sh`, `docker-entrypoint.sh`

## Ordine dei passi
```bash
cd ~/AutoResearchClaw
chmod +x run.sh docker-entrypoint.sh
python3 rb_task/patches/apply_relbench_patches.py   # patch al codice (idempotente, crea .bak)
./run.sh build-relbench                              # immagine arc-relbench (la parte llama.cpp riusa la cache)
./run.sh smoke                                       # 1-2 min: stack + GNN su dati finti, senza LLM
./run.sh baseline                                    # GNN ufficiale + seed: il numero da battere, senza LLM
./run.sh sweep                                       # ~10 min, senza LLM: la validazione e' una guida affidabile per il test?
WITH_LLM=1 ./run.sh baseline                         # idem con Qwen caricato: mostra la VRAM davvero libera
./run.sh relbench                                    # pipeline completa fino al paper
```
Se `smoke` o `baseline` falliscono, fermarsi e leggere l'errore: la pipeline non puo' funzionare senza.

## Variabili utili
`ARC_REFINE_PATIENCE` (default 3: tentativi consecutivi senza miglioramento prima di fermarsi),
`ARC_MAX_TOKENS_MULT` (default 3), `ARC_STAGE12_REPAIRS` (default 3), `LLAMA_CTX` (default 65536 per relbench),
`RB_TIME_BUDGET_SEC` (default 1500).

## Protocollo scientifico (applicato dal codice, non solo dai prompt)
- `primary_metric` = AUROC di VALIDAZIONE media sui semi della condizione `proposed` (maximize).
- Le metriche di test sono calcolate una volta per modello dal checkpoint scelto sulla validazione, finiscono nei
  risultati (per il paper) ma vengono tolte dal contesto mostrato all'LLM durante il raffinamento (stage 13).
- Ogni tentativo di raffinamento (cosa e' cambiato, metrica di validazione, migliorato o no) viene passato all'LLM.

## Problemi noti
- **Hash dei task non piu' validi.** Alcuni file su relbench.stanford.edu sono stati modificati dopo la release 1.1.0
  (osservato: `rel-f1/tasks/driver-dnf.zip`), quindi `get_task(..., download=True)` puo' dare "SHA256 hash ... does not match".
  `rb_loader.py` usa prima la cache locale; se il file del server non coincide calcola le tabelle del task dal database con la
  definizione di relbench 1.1.0. Il build stampa, per ogni task, `source={'db': ..., 'task': 'download' | 'local'}`:
  se per `driver-top3` vedi `local`, i numeri sono la definizione "v1.1.0" ricalcolata e non le tabelle scaricate dal server.
- **pandas 3** rompe relbench 1.1.0 (`to_unix_time`): il Dockerfile fissa `pandas<3`.
- **Memoria GPU.** Con il campionamento temporale ogni nodo di partenza ha un sottografo suo, e su rel-f1 ogni layer in
  piu' fa arrivare quel sottografo a gran parte del database (misurato: baseline a 2 layer ~3,8 GB di picco; 3 layer >20 GB
  a batch 512). `rb_data.build_loaders` misura i nodi campionati per batch e, se superano quelli del baseline ufficiale,
  divide il batch in micro-batch con accumulo del gradiente (stesso batch effettivo e stesso numero di step).
  `RB_NODE_BUDGET_SCALE` (default 1.0) riduce il budget per TUTTE le condizioni, baseline compreso (es. 0.5 se la VRAM
  libera e' poca con Qwen caricato). `main.py` stampa `peak_gb` per ogni run e `gpu free=...` all'avvio.
  Misura nelle condizioni reali con `WITH_LLM=1 ./run.sh baseline`.
- **Validazione e test possono non concordare.** Misurato con `./run.sh sweep` (14 config x 5 semi): correlazione di rango
  val-test +0.16, IC95% [-0.41, +0.63] -> INCONCLUSIVA. Senza le 2 config con residual sale a +0.74 [+0.29, +0.92]: la
  validazione segue il test, tranne per le connessioni residuali (val -0.043, test +0.065, 3.7 SE). Le config che "addestrano di piu'"
  (epoche, batch piu' piccolo, canali 64) guadagnano ~+0.07 in validazione (~3 SE) ma solo +0.00..+0.03 sul test (<1.3 SE).
- **Ricetta `tuned`** (`RB_RECIPE=tuned`, default di `./run.sh relbench`): aggiunge la condizione `baseline_tuned` (stessa architettura
  ufficiale, batch 128) e blocca la ricetta, cosi' i miglioramenti di `proposed` sono attribuibili all'architettura. `RB_RECIPE=official` per l'originale.
- **Il baseline ufficiale e' sotto-addestrato:** 1353 esempi / batch 512 = 3 step per epoca, 30 aggiornamenti in tutto.
- **VRAM condivisa.** Misurato su moro43 (RTX 5090, 32 GB): Qwen con `LLAMA_CTX=65536` occupa 22,9 GB; un altro utente
  (llama-server di `perreon`) ne occupava 7,9 GB, quindi restavano ~1,7 GB, meno dei ~4,5 GB che servono a un esperimento.
  `LLAMA_CTX=65536 ./run.sh vram` mostra memoria usata e libera con la configurazione scelta. Con `ARC_MAX_TOKENS_MULT=3`
  (fino a 32k token generati) non scendere sotto ~64k di contesto; per liberare VRAM usa `--cache-type-k/-v q8_0` e `--n-cpu-moe N`.
- **Sweep architetturale (ricetta `tuned`, 14 config x 5 semi).** Due miglioramenti netti e coerenti tra validazione e test:
  `aggr=max` (val +0.103 = 6.2 SE; test +0.035 = 2.7 SE) e `TransformerConv` (val +0.088 = 6.0 SE; test +0.022 = 1.4 SE). Le
  connessioni residuali peggiorano la validazione (-0.067, -4.9 SE) senza peggiorare il test: e' il punto cieco della validazione.
  Prima di fidarsi dei vincitori, confermarli su semi nuovi (winner's curse):
  `RB_SWEEP_MODE=arch RB_SWEEP_ONLY="aggr=max,transformer" RB_SWEEP_SEEDS=10 RB_SWEEP_SEED_OFFSET=100 ./run.sh sweep`.

## KIT 0.3 — modalità a configurazioni e documentazione delle run
- `./run.sh relbench` ora cerca in **modalità a configurazioni**: l'LLM propone JSON con le impostazioni architetturali (`rb_task/task_spec/search_space.json`),
  un esecutore le scrive in `rb_config.PROPOSED_OVERRIDES`. Nessun file di codice può essere modificato; le iterazioni invalide (codice di uscita != 0, semi o condizioni mancanti) sono scartate;
  alla fine il modello è rivalutato su semi nuovi (`stage-13/confirmation.md`). `ARC_SEARCH_MODE=code` riattiva la riscrittura del codice (con protezioni).
- Cause del fallimento della prima run (rinomina in `main.py`, regola dei 3 semi, metriche parziali accettate): `docs/runs/RUN-001_pipeline_relbench_2026-10-04.md`.
- **Ogni run va documentata** in `docs/runs/` (vedi `docs/runs/README.md`). `./run.sh relbench|sweep|baseline|smoke` scrivono un manifest in `docs/runs/_manifests/`;
  dopo una pipeline: `./run.sh report artifacts/rc-XXXX RUN-003` genera il rapporto automatico (tempi, tabelle, controllo dei numeri del paper).
- Dopo aver estratto lo zip: `python3 rb_task/patches/apply_relbench_patches.py` (aggiunge le patch 0.3 a quelle già applicate), poi `./run.sh smoke`.

## KIT 0.4 — memoria tra passate, descrizione fedele del metodo, run lunghe
- La ricerca in modalità configurazioni ricorda tutte le valutazioni (anche delle passate precedenti) e riparte dalla migliore.
- Alla fine di stage 13 viene scritto `rb_task/task_spec/METHOD_GROUND_TRUTH.md` (impostazioni realmente valutate, numeri di conferma, differenze appaiate): è aggiunto ai prompt di analisi e paper, perché non descrivano metodi mai implementati.
- Run lunga (es. 24 h): in `config.arc.relbench.yaml` imposta `max_iterations: 150` e `max_refine_duration_sec: 86400`. Leggi prima `docs/runs/RUN-003_...md` §5: più valutazioni migliorano quasi certamente la validazione, non necessariamente il test.
- Diagnostica del divario sweep/pipeline: `RB_SWEEP_THREADS=1 RB_SWEEP_MODE=arch RB_SWEEP_ONLY="__none__" RB_SWEEP_SEEDS=10 ./run.sh sweep` (solo la configurazione di riferimento, 10 semi, 1 thread) da confrontare con `baseline_tuned` di `RB_RECIPE=tuned ./run.sh baseline`.

## KIT 0.5 — modalità codice con schede dai paper (default di `./run.sh relbench`)
- Stage 6 scarica da arXiv i PDF dei paper più utili, li legge sezione per sezione e scrive una scheda di implementazione per paper (K1…K4), collegata al codice ufficiale clonato.
- Le schede e le skill del progetto entrano nei prompt di ipotesi, piano e scrittura del codice; ogni tentativo deve citare la scheda in `PROPOSED_SOURCE` e cambiare davvero il modello di `proposed`.
- I baseline usano `rb_model_official.py` (congelato); l'LLM modifica `rb_model.py` e può creare nuovi file.
- Test breve: `ARC_DEADLINE_HOURS=3 ./run.sh relbench`. Run lunga: `ARC_DEADLINE_HOURS=24 ./run.sh relbench` (in tmux).
- Ricerca a configurazioni (RUN-003): `ARC_SEARCH_MODE=config ./run.sh relbench`.
- Dopo la run: `stage-06/impl_cards/` (schede), `stage-06/knowledge_meta.json` (paper letti), `stage-13/refinement_log.json` (`PROPOSED_SOURCE` e motivi di rifiuto per tentativo).

## KIT 0.5.2 — codice ufficiale dei paper
- Per ogni paper delle schede: link GitHub nel PDF, altrimenti ricerca GitHub tramite l'id arXiv; il repository viene clonato in `stage-06/paper_repos/`.
- I moduli del modello diventano file `vendor_<repo>_<modulo>.py` del progetto (sola lettura) e la scheda ne elenca classi e firme: l'LLM li importa.
- Richiede di ricostruire l'immagine una volta (`./run.sh build-relbench`: aggiunge `einops` e `h5py`, ultimo strato, pochi minuti).
- Controllo dopo una run: `stage-06/knowledge_meta.json` (campi `repo`, `vendored`, `not_vendored`).

## KIT 0.6.3 — correzioni dopo RUN-007 (stage 13 fallito con HTTP 400)
- I prompt di riparazione dello stage 13 non contengono piu' il codice vendorizzato (in RUN-007: 192k caratteri, oltre il contesto di 65k token).
- La riparazione automatica parte solo se la run e' davvero fallita (crash, nessuna metrica, NaN), non per i warning di torch_frame.
- Un errore dell'LLM salta il tentativo invece di far fallire lo stage; il corpo degli errori HTTP 400 finisce nel log.
- Vendoring: niente script da riga di comando (argparse) ne' copie di librerie installate (RelGNN: 8 moduli invece di 25).
- La storia mostrata a Qwen include sempre gli ultimi tentativi (prima: solo le prime 20 voci).
- GPU condivisa: `./run.sh relbench` si ferma subito se la GPU ha meno di `RB_PREFLIGHT_MIN_FREE_GB` (27,5) GB liberi
  (`RB_SKIP_GPU_CHECK=1` per saltare il controllo); durante la run `main.py` aspetta fino a `RB_GPU_WAIT_SEC` (600 s) che ci
  siano `RB_MIN_FREE_GB` (4,5) GB liberi, poi stampa `GPU_UNAVAILABLE` ed esce con codice 3 (nessuna "riparazione" del codice).
