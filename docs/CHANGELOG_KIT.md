# Registro delle modifiche al kit RelBench / pipeline

Ogni run cita la versione del kit usata (`rb_task/VERSION`). Le patch al codice della pipeline si applicano con `python3 rb_task/patches/apply_relbench_patches.py` (idempotente, crea `.bak`).

## 0.3.1 — 2026-10-04
- **Correzione:** il manifest automatico faceva uscire `run.sh` in silenzio (codice 1, senza lanciare Docker) quando nell'ambiente non c'era nessuna variabile `ARC_*`/`RB_*`/`LLAMA_*`
  (`grep` senza corrispondenze + `set -e` + `pipefail`). Il manifest ora gira in una subshell e non può interrompere il comando. Verificato con un Docker finto su tutti i sottocomandi in ambiente pulito.
  Il difetto non era emerso nei miei test perché avevo impostato una variabile `RB_`.
- Lo smoke test ora dice chiaramente di applicare le patch se mancano.

## 0.3 — 2026-10-04 (dopo RUN-001)
Motivazione: le cause del fallimento di RUN-001 (vedi il suo §4).
- **Correzione della corruzione di `main.py`:** `pipeline/_helpers._extract_multi_file_blocks` rinominava il primo file della risposta in `main.py` se la risposta non conteneva `main.py`.
  `ARC_PRESERVE_FILENAMES=1` disattiva la rinomina.
- **Filtro di validità delle iterazioni** (stage 13): conta solo un'esecuzione con codice di uscita 0, senza timeout, con `proposed` e tutte le condizioni di riferimento e lo stesso numero di semi atteso (letto dallo stage 12).
  Prima venivano accettate metriche parziali di esecuzioni in errore.
- **Protezione dei file** (`ARC_PROTECTED_FILES`, `ARC_SEARCH_SPACE_FILE`): `main.py`, `rb_data.py`, `rb_loader.py`, `rb_text.py`, `rb_train.py` non possono cambiare; in `rb_config.py` solo `PROPOSED_OVERRIDES`, validato contro lo spazio di ricerca.
- **Modalità a configurazioni** (`ARC_SEARCH_MODE=config`, default di `./run.sh relbench`): l'LLM propone un oggetto JSON con le impostazioni architetturali (spazio in `rb_task/task_spec/search_space.json`: 14 chiavi);
  un esecutore le scrive in `rb_config.PROPOSED_OVERRIDES`; se la proposta è invalida o ripetuta, ricerca deterministica sui vicini del migliore. Nessuna riparazione del codice in questa modalità.
  `ARC_SEARCH_MODE=code` ripristina la riscrittura del codice (con le protezioni).
- **Margine di rumore** (`ARC_MIN_IMPROVEMENT`, default 0,005 in `./run.sh relbench`) e pazienza 5.
- **Conferma finale su semi nuovi** (`ARC_CONFIRM_SEED_OFFSET`, default 100): il progetto finale è rivalutato su semi mai usati; i numeri vengono esposti allo stage 14 come metriche `confirm_*` e salvati in `confirmation.json/md`.
- **Regola dei tre semi** (`BUG-183`) neutralizzata nel prompt di raffinamento (`ARC_KEEP_SEEDS=1`).
- **Seed project:** nuove opzioni architetturali (`jk`, `enc_layers`, `enc_width`, `enc_dropout`, `time_encoding`, `head_layers`); interfaccia `PROPOSED_OVERRIDES`; `SEED_OFFSET`/`N_SEEDS`. Il baseline resta identico all'ufficiale (stessi 1.340.033 parametri).
- **Documentazione:** `docs/runs/`, manifest automatico per ogni run, `./run.sh report`.

## 0.2 — 2026-10-03/04
- `rb_loader.py` (caricamento offline-first; recupero se l'hash di un file di RelBench non coincide: osservato per `driver-dnf`); `pandas<3`, `sentence-transformers<6` + `transformers<5`.
- Budget di nodi con micro-batch e accumulo del gradiente; ricetta `tuned` (`baseline_tuned`); strumenti `sweep`, `vram`; test su dati finti.
- Nascondere i numeri di test all'LLM nel raffinamento; cronologia dei tentativi nel prompt; pazienza configurabile.

## 0.1 — 2026-10-02/03
- Seed project (GNN ufficiale in file piccoli), specifica del task, Dockerfile/immagine `arc-relbench`, `run.sh` con `smoke` e `baseline`.
- Patch precedenti al lavoro su RelBench: estratti di codice dalle repo di riferimento nel prompt dello stage 10, `ARC_MAX_TOKENS_MULT`, riparazione automatica dello stage 12, correzione del parsing del blueprint YAML, interruttore del thinking di Qwen.
