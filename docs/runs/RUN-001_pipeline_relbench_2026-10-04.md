# RUN-001 — Pipeline completa su RelBench rel-f1 / driver-top3 (modalità "riscrivi il codice")

| campo | valore |
|---|---|
| ID / data | RUN-001, 2026-10-04 (16:26–17:42 UTC) |
| tipo | pipeline completa (`./run.sh relbench`) fino al PDF |
| comando | `./run.sh relbench` con ricetta `tuned` (default), `ARC_MAX_TOKENS_MULT=3`, contesto 65536, thinking acceso |
| versione del kit | **0.2** (prima delle correzioni descritte in questo documento); il manifest automatico non esisteva ancora |
| run id | `rc-20261004-162625-9b9601` (cartella consegnata come `primo_esperimento_relbench_f1_driver_top3`) |
| durata | 1,16 h di stage (29 esecuzioni di stage su 29 completate, 0 fallite) |
| rapporto automatico | [RUN-001_auto.md](RUN-001_auto.md) |

## 1. Obiettivo
Verificare che AutoResearchClaw, partendo dal GNN ufficiale di RelBench (GraphSAGE eterogeneo) e da una specifica del task, riesca a
**migliorare iterativamente** l'AUROC su `driver-top3` modificando layer, forward, encoder delle colonne e tipo di GNN, e a produrre
un paper coerente con i risultati.

## 2. Setup
- Dataset `rel-f1`, task `driver-top3` (binario, metrica ROC-AUC), tabelle ufficiali scaricate (1353 / 588 / 726 esempi train / val / test).
- Condizioni: `baseline_graphsage` (ricetta ufficiale), `baseline_tuned` (stessa architettura, `batch_size=128`), `proposed` (parte identica a `baseline_tuned`).
- Metrica di selezione `primary_metric` = AUROC di **validazione** media di `proposed` su 10 semi. Il test è solo riportato.
- Stage 10 con il seed (nessuna chiamata all'LLM), stage 12 con riparazione automatica, stage 13 con **riscrittura di codice da parte dell'LLM**
  (max 8 iterazioni per passata, pazienza 3, numeri di test nascosti all'LLM, cronologia dei tentativi nel prompt).
- LLM: Qwen3.6-35B-A3B locale (llama.cpp), thinking acceso.
- **Non attivi** (introdotti dopo): filtro di validità delle iterazioni, protezione dei file, modalità a configurazioni, correzione della rinomina in `main.py`.

## 3. Risultati (fatti)

### 3.1 Valutazione di riferimento (stage 12, 10 semi, 102 s)
| condizione | val AUROC | test AUROC |
|---|---|---|
| baseline_graphsage (ricetta ufficiale) | 0,715 ± 0,061 | 0,769 ± 0,033 |
| baseline_tuned | 0,778 ± 0,021 | 0,796 ± 0,019 |
| proposed (identica a baseline_tuned) | 0,777 ± 0,022 | 0,793 ± 0,023 |

`proposed` e `baseline_tuned` coincidono entro il rumore, come previsto: è un controllo di coerenza riuscito.
Picco di memoria GPU 3,83 GB.

### 3.2 Raffinamento (stage 13): tre passate
La pipeline ha ripetuto lo stage 13 tre volte (decisione "refine" dello stage 15, due volte).

| passata | iterazioni | miglior metrica registrata | motivo di arresto |
|---|---|---|---|
| 1 (`stage-13_v1`) | 6 | 0,77704 (baseline 0,77689) | 3 iterazioni consecutive senza metriche |
| 2 (`stage-13_v2`) | 3 | nessuna metrica | idem |
| 3 (`stage-13`) | 8 | **0,7862** (iter. 5) | iterazioni massime |

Valutazioni **complete e valide** del candidato (10 semi, esecuzione terminata senza errore):

| passata / iter. | proposed val | proposed test | baseline_tuned val / test |
|---|---|---|---|
| 3 / 1 | 0,7737 | 0,7893 | 0,7783 / 0,7938 |
| 3 / 2 | 0,7772 | 0,7902 | 0,7755 / 0,7925 |
| 3 / 3 | 0,7751 | 0,7940 | 0,7784 / 0,7936 |
| 1 / 2 | 0,7770 | 0,7869 | 0,7758 / 0,7966 |
| 1 / 3 | 0,7758 | 0,7964 | 0,7738 / 0,7876 |

In nessuna di queste la validazione supera `baseline_tuned` oltre il rumore (errore standard di circa 0,007 con 10 semi); sul test il candidato è
tra −0,010 e +0,009 rispetto a `baseline_tuned`. **Non c'è alcun miglioramento dimostrabile.**

### 3.3 Il "miglioramento" 0,7862 è un artefatto
Le iterazioni 4, 5 e 8 della passata 3 sono durate circa 10 s con codice di uscita 1 e nelle loro metriche compaiono **solo** `baseline_graphsage` e `baseline_tuned`,
mai `proposed`. L'LLM aveva cambiato il formato di stampa per seme in `condition=X seed=S primary_metric: V`; il parser ha letto il valore di `baseline_tuned`
(seme 0) come `primary_metric` (0,7815 e 0,7862) e la pipeline lo ha accettato come nuovo massimo. `experiment_final` (v5) è il codice di una di queste esecuzioni
in errore. Non conosco la causa dell'errore di quelle esecuzioni (lo stderr dopo la riparazione non è stato salvato).

### 3.4 L'unica altra valutazione completa del codice finale
Iterazione 7 (3 semi, perché l'LLM aveva riscritto `SEEDS = [0, 1, 2]`): **due esecuzioni dello stesso codice** hanno dato risultati molto diversi.

| esecuzione | proposed val | proposed test | baseline_tuned val / test | vanilla val |
|---|---|---|---|---|
| prima (`sandbox`) | 0,7893 | 0,7612 | 0,7610 / 0,7876 | 0,7214 |
| dopo la riparazione runtime (`sandbox_after_fix`) | 0,7858 | 0,7285 | 0,7623 / 0,7946 | 0,7220 |

La differenza sul test (0,033) a parità di configurazione mostra quanto siano rumorose le valutazioni a 3 semi (e/o che la riparazione abbia cambiato il codice: non l'ho verificato).
In entrambe la validazione è sopra `baseline_tuned` (+0,028 e +0,024) e il **test è sotto** (−0,026 e −0,066).

### 3.5 Qualità del paper (stage 17–23)
- Rapporto di qualità: 5/10, "Major revision"; `fabrication_suspected = false`; 29/29 citazioni verificate; PDF compilato.
- Il paper presenta "RELI" (GATv2 con LayerNorm e residual): val 0,789 vs 0,721 del baseline ufficiale, test 0,761 < tuned 0,788. La conclusione ("guadagno in validazione senza superiorità sul test") è onesta.
- **Incoerenze:** dichiara 3 semi mentre il sommario ne ha 10; la tabella degli iperparametri (hidden 64/128/256, lr 1e-3, 500 epoche, early stopping) non corrisponde alla configurazione reale;
  6 numeri (estremi di intervalli di confidenza) non corrispondono ad alcuna metrica della run; molte celle valgono `---`; un intervallo di confidenza non contiene la propria media.
- Le ipotesi dello stage 8 parlano di componenti inventati (HATG, AFP, obiettivo Macro-F1) che il codice non implementa.

## 4. Interpretazione
- **Dimostrato:** la pipeline funziona dal punto di vista operativo (29/29 stage, nessun OOM, PDF). Il suo ciclo di raffinamento in modalità "riscrittura del codice" **non ha trovato nessun miglioramento reale**
  e ha dichiarato un miglioramento falso (§3.3).
- **Cause individuate (a posteriori):**
  1. **Rinomina in `main.py`.** L'helper `_extract_multi_file_blocks` rinomina il *primo* file della risposta in `main.py` se la risposta non contiene `main.py`
     (regola pensata per progetti a file singolo). Quando l'LLM restituiva solo `rb_config.py`, il suo contenuto sovrascriveva `main.py`: è la corruzione osservata (`main.py` che inizia con il testo di `rb_config.py`,
     `NameError: experiment_harness`, versione v6 con file vuoti). Ogni iterazione richiedeva poi una seconda chiamata di riparazione.
  2. **Regola dei tre semi** (`BUG-183`) nel prompt di raffinamento: ha vinto sulla mia specifica, portando le valutazioni da 10 a 3 semi.
  3. **Metriche parziali accettate:** un'esecuzione in errore con una metrica stampata prima del crash veniva trattata come valida.
  4. **Rumore:** con 3 semi l'errore standard è circa 0,013, più grande dei miglioramenti cercati (circa 0,009).
- **Ipotesi non verificate:** perché le iterazioni 4, 5, 8 siano terminate con errore; se la riparazione runtime abbia cambiato qualcosa nel codice dell'iterazione 7.
- **Limiti:** una sola run; l'LLM ha esplorato pochissimo (le iterazioni valide sono 5); la validazione di `driver-top3` è piccola (588 righe) e non sempre concorde col test (vedi RUN-000).

## 5. Decisioni e prossimi passi
- Kit **0.3**: filtro di validità delle iterazioni (codice 0, tutte le condizioni, numero di semi atteso), protezione di `main.py`/`rb_data.py`/…, interfaccia `PROPOSED_OVERRIDES` in `rb_config.py`,
  correzione della rinomina (`ARC_PRESERVE_FILENAMES=1`), regola dei semi neutralizzata (`ARC_KEEP_SEEDS=1`), margine minimo di miglioramento, conferma finale su semi nuovi.
- Nuova **modalità a configurazioni** (`ARC_SEARCH_MODE=config`): l'LLM propone solo valori in uno spazio definito, un esecutore li valuta. Dettagli in `CHANGELOG_KIT.md`.
- Prima di rilanciare la pipeline: confermare su semi nuovi i vincitori dello sweep → fatto, vedi [RUN-002](RUN-002_conferma_sweep_2026-10-04.md).

## 6. Errata (correzioni a analisi precedenti)
- Nella prima analisi di questa run avevo scritto che le tabelle del paper (val 0,789 / test 0,761) "non coincidono con nessuna run del sommario". Il rapporto automatico ha mostrato che **coincidono con la prima esecuzione
  dell'iterazione 7** (§3.4): sono numeri reali di un'esecuzione a 3 semi, non inventati. L'incoerenza è che il sommario dello stage 14 usa altre esecuzioni (10 semi, stage 12) e che il paper mescola numeri di esecuzioni diverse.
  Ho corretto anche il giudizio sul controllo "numeri senza riscontro": ora conta solo le metriche aggregate, non i valori per epoca.

## 7. File di riferimento
- Cartella della run: `artifacts/rc-20261004-162625-9b9601/` (zip: `primo_esperimento_relbench_f1_driver_top3.zip`)
- `stage-12/runs/run-1.json`, `stage-13*/refinement_log.json`, `stage-14/experiment_summary.json`, `stage-20/quality_report.json`, `stage-22/paper.pdf`, `stage-23/paper_final_verified.md`
