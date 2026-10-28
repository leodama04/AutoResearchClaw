# Registro delle modifiche al kit RelBench / pipeline

Ogni run cita la versione del kit usata (`rb_task/VERSION`). Le patch al codice della pipeline si applicano con `python3 rb_task/patches/apply_relbench_patches.py` (idempotente, crea `.bak`).

## 0.6.11 — 2026-10-23 (perché i baseline cambiano tra una run e l'altra)
Nuovo strumento, nessuna modifica alla pipeline né ai file protetti del progetto.
- **Osservazione** (dai `confirmation.json` e dai `results.json` per seme di RUN-003–RUN-006, tre conferme per run, semi 100–109):
  dentro una run le conferme danno quasi lo stesso risultato seme per seme (`baseline_graphsage`: in media 0,002 di differenza per
  seme; `baseline_tuned`: medie entro 0,006), tra run diverse no (`baseline_graphsage`: 0,035 per seme; `baseline_tuned` da 0,772 a
  0,802), anche quando tutti i file eseguiti per i baseline sono identici byte per byte (RUN-005 contro RUN-006). C'è qualcosa che
  resta fisso dentro una run e cambia tra le run; la causa non è identificata.
- `./run.sh repro-check` (`rb_task/tools/repro_check.py`, senza LLM, ~15 min): tre container come tre run, con il progetto
  ufficiale del kit e gli stessi semi. A e B partono da una cache dei dati vuota (tipi delle colonne, tabelle materializzate,
  embedding del testo: `RB_CACHE_DIR`, che nella pipeline sta in `/tmp` del container e si ricostruisce a ogni run) ed eseguono
  `main.py` due volte; C riusa la cache di A. Salva per ogni container i risultati per seme, l'impronta della cache, le versioni
  delle librerie e la GPU; `run.sh` salva dall'host id e strati dell'immagine Docker. Il confronto (`summary.md`) riporta le
  differenze per seme dentro lo stesso container e tra container, e confronta le cache file per file (tipi delle colonne,
  statistiche come le liste delle categorie, tensori, embedding compresi).
- `./run.sh repro-stypes` (`repro_check.py stypes`), aggiunto dopo la prima prova (RUN-014: container diversi danno gli stessi
  risultati e le cache sono identiche, ma le run salvate cadono in pochi gruppi con risultati per seme quasi uguali). I tipi delle
  colonne vengono decisi una volta per run da `get_stype_proposal` di RelBench su un campione casuale di 1000 righe per tabella
  (`DataFrame.sample` senza seme). Lo strumento estrae il campione 50 volte (semi numpy 0–49), conta le varianti di `stypes.json`
  e le colonne che cambiano, allena i baseline con ciascuna variante (fino a 4) e confronta i risultati per seme con quelli delle
  run salvate (RUN-003, 004, 005, 006, 008 e la prova del 23/10).
- Test: `test_repro_check.py` (progetto finto: dati preparati diversi tra container -> A ≠ B, C = A; il caso in cui anche C ≠ A; varianti dei tipi delle colonne valutate una per una).

## 0.6.10 — 2026-10-15 (rapporto automatico, dopo RUN-011)
- `rb_task/tools/run_report.py`: il topic nella panoramica è quello usato dalla run (passato da `run.sh`, per esempio quello di
  `RB_TASK=driver-dnf`, letto da `stage-08/novelty_report.json`), non quello di default scritto in `config.yaml` (che diceva
  driver-top3 anche per RUN-011); il percorso del PDF del paper è relativo alla run. Nessuna modifica alla pipeline.

## 0.6.9 — 2026-10-15 (RelGNN con la configurazione degli autori)
Nuovo strumento, nessuna modifica alla pipeline ne' ai file protetti del progetto.
- `./run.sh relgnn-train` (`rb_task/tools/relgnn_train.py`): domanda dopo RUN-008/RUN-009, cioe' se il divario tra RelGNN
  allenato da Qwen (test 0,733 su driver-top3) e il checkpoint degli autori (0,8585 con il nostro codice) dipende dalla
  configurazione o dall'addestramento, e se allenare piu' a lungo serve (domanda del correlatore sui training step).
  Per ogni task, numero di epoche (`--epochs`, default 10,30) e seme (default 100-109) allena:
  `baseline_graphsage`, `baseline_tuned` (modello RDL congelato, nostro loader), `relgnn_authors` (`RelGNN_Model` del
  repository ufficiale con modello E loader degli autori da `get_configs`: strati, canali, teste, `simplified_MP`, batch,
  fanout, salti, `subgraph_type`) e `relgnn_run008` (stesso modello con 2 strati e 4 teste come Qwen in RUN-008, nostro
  loader con batch 128). Tutte con `rb_train.run_one` della pipeline: Adam, lr della ricetta (0,005), epoca migliore
  scelta sulla validazione, test valutato una volta. Riporta gli aggiornamenti dei pesi per condizione e le differenze
  appaiate contro `baseline_tuned`; riferimenti: paper e checkpoint (RUN-009).
- Il repository di RelGNN non contiene il codice di addestramento (lo script "per riprodurre i risultati" valuta i
  checkpoint): learning rate ed epoche degli autori non sono noti, quindi si usano quelli della nostra ricetta.
- Test: `test_relgnn_train.py` (FakeDataset: classe ufficiale, configurazioni, baseline congelati, semi, epoche,
  aggiornamenti per epoca, differenze appaiate, riepilogo).

## 0.6.8 — 2026-10-14 (correzioni di `tool-stats` dopo la prima tabella)
- Tentativi con codice ufficiale importato: letti dagli `import vendor_*` del codice di ogni tentativo invece che dal campo
  `arc_official_code`, che esiste solo dal kit 0.6. Nella prima tabella RUN-005 e RUN-006 risultavano 0 (i loro documenti ne
  contano 1 e 5); su RUN-008 il conteggio resta 86.
- Correlazione validazione-test con il numero di tentativi usati (`0.053 (n=190)`).
- Modello finale senza codice ufficiale: scritto "no" invece di "-" (che si confondeva con "dato assente").
- Conferma dei kit senza statistiche appaiate (RUN-003): Δ come differenza delle medie, senza p.
- Test: `test_tool_stats.py` (run di prova: import nel codice senza il campo, file vendor esclusi, `gnn_type` letto da
  `PROPOSED_OVERRIDES`, "no" per il modello finale).

## 0.6.7 — 2026-10-14 (strumenti per le richieste del correlatore)
- `./run.sh transfer --projects <run> --tasks ...` (`rb_task/tools/transfer_eval.py`): il modello finale di una run
  (`stage-13/experiment_final`: `rb_model.py`, `PROPOSED_OVERRIDES`, nuovi file e codice vendorizzato) allenato su altri task
  accanto a `baseline_graphsage` e `baseline_tuned`, 10 semi (100–109, mai usati per scegliere), stessa ricetta; tabella con
  medie e differenze appaiate (IC 95%, p, semi migliori; "meglio" = piu' basso per la MAE). `--epochs N` usa le stesse epoche
  per TUTTE le condizioni. I file protetti (main.py, rb_train.py, ...) vengono dal kit attuale (`--infra run` per usare quelli
  della run): il modello resta quello della run, le correzioni del kit (es. rmse 0.6.6) valgono anche per le run vecchie.
- `./run.sh tool-stats [run...]` (`rb_task/tools/tool_stats.py`, senza Docker): per ogni run query, candidati, shortlist,
  schede, repository, file vendorizzati, tentativi (valutati, crash, riparati, identici, respinti, errori dell'LLM),
  tentativi con codice ufficiale importato e moduli, schede citate, architetture provate, righe cambiate per tentativo,
  righe e file cambiati nel modello finale, uso del codice ufficiale nel modello finale, conferma (Δ val/test, p), correlazione
  val-test, voto del paper. Scrive `docs/runs/tool_stats.md` / `.json`.
- `DOCKER_GPUS=device=1 ./run.sh ...`: sceglie la GPU del nodo (default tutte).
- Test: `test_transfer_eval.py` (progetto di prova: semi, epoche, differenze appaiate anche per la MAE, file protetti dal kit).

## 0.6.6 — 2026-10-14 (task di regressione)
- `./run.sh relgnn-ckpt` su driver-position: `TypeError: got an unexpected keyword argument 'squared'`. relbench 1.1.0 calcola
  `rmse` con `mean_squared_error(..., squared=False)`, argomento rimosso da scikit-learn 1.6; `task.evaluate` calcola tutte le
  metriche del task, quindi OGNI valutazione di un task di regressione si fermava, anche nel seed project (baseline e pipeline
  su driver-position). Ora `rb_train.evaluate_task` usa le metriche di relbench sostituendo solo `rmse` con un calcolo
  equivalente (radice dell'errore quadratico medio); lo strumento dei checkpoint usa la stessa funzione.
  Nessun effetto sui task di classificazione (driver-top3, driver-dnf): stesse metriche di prima.
- Test: `test_regression_eval.py` (metriche r2/mae/rmse e addestramento completo su un task di regressione).

## 0.6.5 — 2026-10-14 (strumento dei checkpoint di RelGNN)
- Primo uso di `./run.sh relgnn-ckpt` sul cluster: "7 missing, 0 unexpected keys" su tutti e tre i task. Causa: da torch_frame 0.3
  i valori di riempimento dei NaN delle colonne (`fill_values`, calcolati dalle statistiche delle colonne quando si costruisce il
  modello) sono salvati come buffer; i checkpoint degli autori sono stati salvati con torch_frame 0.2.3, che li calcolava a ogni
  passo e non li salvava. Le 7 chiavi sono gli encoder delle colonne data/ora delle 7 tabelle di rel-f1 che le hanno.
  Ora queste chiavi vengono lasciate come calcolate dalle nostre statistiche (stesso calcolo della 0.2.3) e il report lo dice;
  qualsiasi altra chiave mancante o in piu' resta un errore, con i nomi delle chiavi.
- Test: caso "checkpoint salvato senza `fill_values`" in `test_relgnn_checkpoint_eval.py` (stesse predizioni).

## 0.6.4 — 2026-10-14 (dopo RUN-008)
Due modifiche al comportamento, decise dopo RUN-008; nient'altro cambia in cio' che Qwen vede o sceglie.
- **Ripartenza tra le passate solo da versioni accettate.** Prima la passata successiva partiva dal tentativo con la metrica
  piu' alta, anche se non aveva superato il margine e il ricontrollo: in RUN-008 la passata 2 e' partita dal tentativo 31
  (una sola esecuzione, test 0,742) e la sua conferma e' stata la peggiore (test 0,720). Ora conta solo `improved=True`;
  sui dati di RUN-008 la passata 2 sarebbe partita dal tentativo 19 (0,8787), la versione accettata.
  `ARC_WARM_START_ANY=1` ripristina il comportamento precedente.
- **Task configurabile con `RB_TASK`** (`driver-top3`, `driver-dnf`, `driver-position`). Prima "driver-top3", "ROC-AUC" e la
  descrizione del task erano scritti a mano nelle specifiche, nel topic, nel prompt di scelta dei paper, nella proposta in
  modalita' configurazioni e nel file del metodo. Ora le specifiche (`rb_task/task_spec/*.md`) sono modelli (`{{TASK}}`,
  `{{METRIC}}`, ...) riempiti dal registro dei task (fatti di relbench 1.1.0) quando vengono letti; i fatti misurati solo su
  driver-top3 compaiono solo per driver-top3. Per `driver-top3` il testo resta quello di prima, tranne la frase che
  descrive il task e gli split (verificato con un diff). Per una metrica d'errore (MAE di driver-position) tabelle di conferma, statistiche appaiate
  ("meglio" = piu' basso) e file del metodo usano la metrica giusta; `primary_metric` resta "piu' alto e' meglio" (= -MAE).
- **Nuovo strumento `./run.sh relgnn-ckpt`** (`rb_task/tools/relgnn_checkpoint_eval.py`): valuta i checkpoint ufficiali di
  RelGNN (Hugging Face `tianlangchen/RelGNN`) sui task di rel-f1 con il nostro codice dei dati, la configurazione degli autori
  per task e il loro loader, senza addestramento; confronta con i valori del paper. Richiesto dal correlatore.
- `run.sh` e `docker-entrypoint.sh` di nuovo eseguibili nello zip (nello zip 0.6.3 erano salvati senza permesso di esecuzione).
- Test: `test_fixes_064.py`, `test_relgnn_checkpoint_eval.py`; aggiornati i casi di ripartenza in `test_refine_modes.py`.

## 0.6.3 — 2026-10-11 (correzioni dopo RUN-007: stage 13 fallito con HTTP 400)
Solo correzioni di difetti: nulla cambia in cio' che viene detto a Qwen su paper e architetture.
- **Causa del fallimento:** i prompt di riparazione dello stage 13 (`iterative_repair`) contenevano TUTTI i file del progetto, codice
  vendorizzato compreso (filtro presente solo nel prompt di miglioramento). In RUN-007 il vendor era 192.182 caratteri (RelGNN 25 file +
  LightRDL 3): prompt stimato ~65.200 token + stderr, oltre il contesto di 65.536 di llama-server, quindi HTTP 400 e stage 13 FAILED.
  Ora i prompt di riparazione mostrano gli stessi file del prompt di miglioramento (`visible_files`).
- **Riparazione solo per veri fallimenti:** il codice originale chiamava la riparazione per qualsiasi riga con "Warning" su stderr
  (torch_frame stampa `UserWarning: Could not infer format` quando prepara le tabelle; in RUN-007 c'erano), quindi anche una run
  riuscita poteva essere seguita da una riparazione e da una seconda run, e il codice valutato diventava quello riparato.
  In RUN-004/005/006 i tentativi passati da una riparazione sono 17/29, 11/31 e 13/30; dai rapporti salvati non si puo' dire quanti
  fossero run gia' riuscite. Ora la riparazione parte solo per crash, assenza della metrica primaria o NaN/Inf.
  `ARC_REPAIR_ON_WARNINGS=1` ripristina il comportamento originale.
- **Errori dell'LLM:** un errore (HTTP 400, server giu') salta il tentativo e conta come tentativo senza metriche, invece di far fallire
  lo stage; una riparazione fallita lascia il risultato originale. Il client registra nel log il corpo delle risposte HTTP 400.
- **Vendoring:** esclusi gli script da riga di comando (argparse a livello di modulo) e le copie di librerie installate (la cartella
  `relbench/` dentro il repo di RelGNN, identica a relbench 1.1.0). RelGNN: 8 moduli e ~37.500 caratteri invece di 25 file e 153.657 (verificato sul repo clonato in RUN-007).
  Budget `ARC_VENDOR_MAX_CHARS` (default 100.000).
- **Storia nel prompt:** il codice originale passava `run_summaries[:20]`, cioe' le PRIME 20 voci: dopo ~19 tentativi Qwen non vedeva
  piu' l'esito degli ultimi. Non era successo prima (passate da al massimo 10 tentativi), ma dalla 0.6 il tetto non c'e' piu' e una
  run di 24 ore ne fa molti di piu'. Ora: riassunti dello stage 12, una riga per i tentativi vecchi, gli ultimi
  `ARC_HISTORY_LAST` (12) per intero, entro `ARC_HISTORY_MAX_CHARS` (40.000).
- **GPU condivisa:** in RUN-007 la GPU era piena (CUDA out of memory anche solo per creare il contesto) e la riparazione dello stage 12
  aveva modificato il codice (try/except, embedder del testo su CPU) per un problema dell'ambiente. Ora `./run.sh relbench` controlla
  prima la memoria libera (`RB_PREFLIGHT_MIN_FREE_GB`, 27,5; `RB_SKIP_GPU_CHECK=1` per saltare); `main.py` aspetta fino a
  `RB_GPU_WAIT_SEC` (600 s) che ci siano `RB_MIN_FREE_GB` (4,5) GB liberi, altrimenti stampa `GPU_UNAVAILABLE` ed esce con codice 3;
  stage 12 e 13 non chiedono all'LLM di "riparare" quel caso e la storia dice a Qwen che il tentativo non e' stato valutato.
- **Metrica diagnostica:** `proposed_identical_to_baseline` ora viene riportata dopo l'addestramento: riportata all'inizio, faceva
  sembrare "con metriche" una run poi crollata, e aggirava il controllo del codice originale che blocca lo stage 12 senza dati reali.
- Rapporto automatico: tentativi saltati per errore dell'LLM e GPU occupata indicati nella tabella.
- Test: `test_stage13_robustness.py` (riproduce RUN-007: con il kit 0.6.2 fallisce con lo stesso `HTTP Error 400`, con 0.6.3 passa) e
  `test_fixes_063.py`.

## 0.6.2 — 2026-10-08 (modello di partenza senza scorciatoie)
- In modalità codice `proposed` parte da `rb_model_minimal.py` (copiato come `rb_model.py`): solo il modello ufficiale RelBench (encoder PyTorch Frame, encoding temporale, GraphSAGE eterogeneo, testa MLP), senza le opzioni GATv2/GIN/Transformer/ResGated/jumping knowledge aggiunte per gli sweep. Ogni architettura alternativa deve venire dai paper scelti da Qwen.
  Verificato: stesse uscite e stessi 1.340.033 parametri del modello ufficiale dei baseline.
- La modalità a configurazioni e gli sweep continuano a usare il modello con le opzioni.
- Meccanismo: `ARC_SEED_FILE_MAP="rb_model.py=rb_model_minimal.py"` (impostato da `./run.sh relbench` in modalità codice); `rb_model_minimal.py` non viene mai copiato nel progetto.
- Correzione nel patcher: un nome di variabile duplicato impediva l'inserimento della nuova patch; aggiunto un controllo che verifica che tutti i 25 gruppi di patch siano applicati.

## 0.6.1 — 2026-10-08 (le scelte le fa Qwen)
Principio: nessuna indicazione su quali paper o architetture usare; Qwen sceglie in base alle proprie ricerche.
- Rimossi i nomi di metodi (RelGT, RelGNN, QUARTET, "graph transformer") da specifica, skill, docstring di `rb_tokens.py`, testo della conoscenza e prompt di selezione dei paper; gli esempi usano segnaposto.
- Query di letteratura scritte da noi disattivate per default (`ARC_LIT_QUERIES_FILE` vuoto; il file resta disponibile come opzione).
- Stage 3: le query scritte dall'LLM venivano scartate quando il suo piano YAML era malformato (il codice originale le sostituiva con pezzi del titolo); ora vengono recuperate dalla sua risposta (`rescue_plan`). Restano solo i filtri decisi dal professore (anno minimo 2010, testo completo).
- `rb_tokens.py` presentato come strumento generico per codice che lavora su sequenze di token, senza indicare alcun metodo.

## 0.6 — 2026-10-08 (dopo RUN-006 e le indicazioni del professore)
- Tetto di 10 iterazioni per passata del codice originale rimovibile (`ARC_MAX_REFINE_ITERS`, 1000 in `./run.sh relbench`): la RUN-006 "da 24 ore" era durata 2,2 h.
- `rb_task/seed_project/rb_tokens.py` (sola lettura): insiemi di token per seme dal batch eterogeneo, il formato dei graph transformer (RelGT); verificato con il `RelGTLayer` ufficiale.
- Codice ufficiale per primo: istruzioni, specifica e skill `paper-to-code` con esempio; moduli ufficiali importati registrati per tentativo (`arc_official_code`) e mostrati all'LLM, insieme alle modifiche scartate dalla guardia.
- Tentativi identici alla versione migliore non eseguiti (senza riparazione automatica).
- Codice generico ammesso se pertinente (`ARC_REQUIRE_COMPONENT_MATCH` ora 0 per default); citazione della scheda sempre obbligatoria.
- Schede solo da paper con testo completo su arXiv (`ARC_REQUIRE_FULLTEXT=1`; ricerca per titolo se manca l'id).
- Pazienza 60 e tolleranza di 30 tentativi senza metriche in modalità codice.

## 0.5.3 — 2026-10-07 (dopo RUN-005)
- Repository dei paper verificati: precedenza al link nel PDF; un repository trovato dalla ricerca (stage 5) vale solo se il README cita l'id arXiv o un titolo lungo e specifico (in RUN-005 a RelGT era stato associato Relphormer, un altro paper).
- Riparazione automatica: un blocco di codice senza nome va nel file a cui appartiene invece che in `main.py`; i file protetti modificati da una riparazione vengono spostati o ripristinati; il controllo dei file protetti vale anche dopo la riparazione.
- Tentativi identici alla versione migliore rifiutati; nessuna differenza "cosmetica" nella riscrittura di `rb_config.py`.
- Ricontrollo prima di accettare un miglioramento: seconda valutazione su 10 semi diversi (`ARC_RECHECK`, `ARC_RECHECK_SEED_OFFSET`=200) e media delle due.
- File del metodo con le righe di codice cambiate e la regola sui nomi degli operatori; specifica: nomi delle opzioni descrittivi.
- Rapporto automatico: riconoscimento della modalità corretto, ricontrolli mostrati.

## 0.5.2 — 2026-10-06 (repository dei paper)
- **Perché in RUN-004 nessun repository:** lo stage 5 cerca il codice solo per i primi 5 paper della shortlist (in RUN-004 erano lavori del 2026 senza codice trovabile;
  RelGT era 8°) e lo cerca con DuckDuckGo (`"<titolo>" github`) e con la ricerca GitHub sul titolo, entrambe fragili.
- **Ricerca del codice per i paper delle schede:** link GitHub nel testo del PDF, poi ricerca GitHub dei repository il cui README cita l'id arXiv (scarta liste e raccolte).
  Verificato dal vivo: per RelGT (2505.10960) trova `snap-stanford/relgt`.
- **Codice ufficiale importabile:** i moduli del modello vengono copiati nel progetto come `vendor_<repo>_<modulo>.py` (sola lettura; script di training, moduli con dipendenze mancanti o che il validatore rifiuta sono esclusi; import interni riscritti).
  Le schede elencano classi e firme ("mappa del codice"); l'LLM li importa e scrive solo l'adattatore. I file `vendor_*` sono protetti e nascosti dal prompt.
  Verificato sul codice di RelGT: `encoders.py`, `local_module.py`, `codebook.py` importabili; `model.py` richiede `einops` (aggiunto all'immagine, con `h5py`).
- Il token `GITHUB_TOKEN`, se presente, viene passato al container (limiti più alti per la ricerca).

## 0.5.1 — 2026-10-06 (dopo RUN-004)
- Errori visibili all'LLM: lo stderr salvato è la coda (traceback) e non i primi 2000 caratteri; salvato anche dopo la riparazione; avviso di torch_frame silenziato; nella storia solo l'estratto dell'errore.
- `PROPOSED_SOURCE` deve nominare un componente descritto nella scheda citata (`ARC_REQUIRE_COMPONENT_MATCH`).
- Ricetta bloccata in modalità codice (`locked_keys` in `search_space.json`, `ARC_LOCK_RECIPE`).
- Ripartenza dalla versione migliore e memoria tra le passate anche in modalità codice.
- Schede iniettate anche in `synthesis` e `hypothesis_synthesize` e copiate in `stage-06/cards/`; codice ufficiale dai link GitHub nel testo dei PDF.
- Selezione dei paper: preferisce testo completo su arXiv e risultati su RelBench, evita pipeline che richiedono modelli esterni.
- File del metodo: in modalità codice descrive anche le modifiche al codice (classi nuove, file nuovi, scheda dichiarata).
- Sweep: configurazioni personalizzate (`RB_SWEEP_CONFIGS_JSON`); ablazione di RUN-004 in `rb_task/task_spec/ablation_run004.json`.

## 0.5 — 2026-10-05 (indicazioni del professore dopo RUN-001/RUN-003)
Obiettivo: tornare alla modalità in cui Qwen scrive codice liberamente, ma ispirandosi DAVVERO ai paper e al loro codice, per run lunghe (24 h).
- **Perché in RUN-001 i paper non sono stati usati (cause trovate):** (1) lo stage 6 legge solo titolo e abstract dei 15 paper, in una sola chiamata; (2) le schede non arrivano allo stage 13, che scrive il codice;
  (3) gli estratti dei repository entrano solo nello stage 10, saltato quando si parte dal codice ufficiale, e l'helper escludeva `examples/`; (4) le ipotesi (stage 8) inventano metodi; (5) nessuna regola obbligava a usare la letteratura.
- **Letteratura:** `ARC_LIT_YEAR_MIN` (default 2010 invece di 2020, fisso nel codice degli stage 3–4) e query curate in testa (`rb_task/task_spec/literature_queries.txt`), oltre a quelle dell'LLM (in RUN-001 erano pezzi del titolo).
- **Schede di implementazione (fine dello stage 6, `_arc_knowledge.py`):** l'LLM sceglie i K=4 paper più implementabili; il PDF viene scaricato da arXiv (id, DOI arXiv o ricerca per titolo) e letto **sezione per sezione, un paper alla volta**
  (metodo, esperimenti, dettagli di implementazione); una scheda per paper con componenti, equazioni, iperparametri, risultati su RelBench e come portarlo nel nostro codice, collegata al codice ufficiale clonato allo stage 5.
  Usa il lettore PDF e il controllo degli URL già presenti nella pipeline. Output: `stage-06/papers/*.pdf`, `stage-06/impl_cards/K*.md`, `stage-06/KNOWLEDGE.md`, `knowledge_meta.json`.
- **La conoscenza è iniettata nei prompt** di `hypothesis_gen`, `experiment_design`, `code_generation`, `iterative_improve`, `iterative_repair`, `code_repair`, `code_exec_fix` (file di una run precedente ignorato).
- **Skill del progetto** (`rb_task/skills/` → `.claude/skills/`, caricate dal SkillRegistry della pipeline): `relbench-gnn-code`, `paper-to-code`, `relational-dl-literature`. Lo stage 13 non riceveva le skill: ora le riceve.
- **Uso obbligatorio della conoscenza (modalità codice):** ogni tentativo deve dichiarare in `rb_config.PROPOSED_SOURCE` la scheda usata (K1…); senza, è rifiutato anche se migliora la metrica (`ARC_REQUIRE_KNOWLEDGE_REF=1`).
- **Modifica davvero attivata:** `main.py` confronta `proposed` e `baseline_tuned` sullo stesso batch all'inizializzazione; se calcolano la stessa funzione il tentativo è rifiutato (in RUN-001 le 5 valutazioni complete erano identiche al baseline).
- **Baseline congelati:** `rb_model_official.py` (protetto) per i baseline, `rb_model.py` (modificabile) solo per `proposed`.
- **Run lunghe:** scadenza globale (`ARC_DEADLINE_HOURS`, default 24; lo stage 13 si ferma 75 min prima), tolleranza ai fallimenti consecutivi (`ARC_MAX_NO_METRICS` 12), pazienza 40; `config.arc.relbench.code.yaml`.
- **Contesto dell'LLM:** file protetti non necessari nascosti dal prompt dello stage 13 (`ARC_PROMPT_HIDE_FILES`), schede limitate a 20.000 caratteri.
- **Correzione:** la ripartenza dalla migliore configurazione (kit 0.4) stava nello stesso gruppo di patch del kit 0.3 e non veniva applicata su repo già patchati con lo 0.3; ora è un gruppo separato.
- Nuovi test: `test_knowledge.py`, `test_stage13_code_mode.py` (stage 13 completo con LLM finto che prova a barare).

## 0.4.1 — 2026-10-05
- **Correzione (errore mio):** `_repo_context.py` saltava la cartella `examples/` dei repository clonati; in RUN-001 il codice di RelGNN (`examples/relgnn_conv.py`, `relgnn_model.py`) non è mai entrato nel prompt e al suo posto sono stati presi 3 file di utilità. Ora premia i file con il nome del repository e `conv`, ed è copiato dal patcher.

## 0.4 — 2026-10-04 (dopo RUN-003)
Motivazione: i difetti emersi in RUN-003 (§4).
- **Memoria tra le passate** (modalità configurazioni): le valutazioni di tutte le passate sono nel prompt e nel controllo dei duplicati; ogni passata riparte dalla migliore (record riportato come iterazione 0, `arc_carried_from`).
  Il pipeline originale recupera la metrica migliore delle passate precedenti ma non i loro file (BUG-58).
- **Descrizione fedele del metodo** (`ARC_METHOD_FILE`, default `rb_task/task_spec/METHOD_GROUND_TRUTH.md` in `./run.sh relbench`): generata a fine stage 13 (impostazioni cambiate, dimensione della ricerca, conferma su semi nuovi,
  differenze appaiate con IC e p), aggiunta ai prompt di `result_analysis`, `research_decision`, `paper_outline`, `paper_draft`, `paper_revision`, `peer_review`. Azzerata all'inizio di ogni run.
- **Statistiche appaiate** nella conferma: `confirmation.json` → `paired`; i log per seme della conferma sono usati per IC bootstrap e test di permutazione.
- Sweep: `RB_SWEEP_THREADS` (test A/B del divario sweep/pipeline). Config: nota per run lunghe. Nuovi test: `test_refine_modes` (casi 9–10), `test_stage13_config_mode` (due passate, file del metodo).

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
