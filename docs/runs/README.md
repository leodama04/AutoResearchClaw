# Documentazione delle run

Ogni esecuzione che produce risultati (pipeline completa, sweep, conferma, baseline) ha **un documento** in questa cartella.
Serve a rispondere, anche dopo mesi, a tre domande: *che cosa è stato fatto*, *con quale configurazione e versione del codice*,
*quali risultati sono affidabili e quali no*.

## Regole
1. Un file per run: `RUN-NNN_<slug>_<AAAA-MM-GG>.md` (numerazione progressiva, mai riusata).
2. Si parte da `TEMPLATE.md`. Le sezioni "Setup" e "Risultati" si riempiono con i **fatti letti dai file**, non a memoria:
   - pipeline completa: `./run.sh report artifacts/rc-XXXX RUN-NNN` genera `RUN-NNN_auto.md` (tempi, tabelle, controlli);
   - sweep / baseline: incolla l'output del terminale in un blocco di codice e salva `sweep_results.json`.
3. Ogni run lanciata con `./run.sh` scrive un **manifest** in `_manifests/` (data, comando, versione del kit, commit, variabili d'ambiente, GPU).
   Cita il manifest nel documento.
4. La sezione **Interpretazione** distingue ciò che è dimostrato da ciò che è ipotesi. I numeri di test non si usano per scegliere nulla;
   i confronti si fanno su medie con più semi e con l'errore standard.
5. Se una analisi successiva corregge una precedente, la correzione va scritta nel documento della run corretta (sezione "Errata"), non nascosta.
6. Le modifiche al codice della pipeline/kit si registrano in `../CHANGELOG_KIT.md`; ogni run cita la versione del kit usata.

## Indice

| ID | Data | Tipo | Esito | Documento |
|---|---|---|---|---|
| RUN-000 | 2026-10-03/04 | esperimenti preliminari (baseline, sweep) | strumenti tarati; validazione e test non sempre concordi | [RUN-000_preliminari_2026-10-04.md](RUN-000_preliminari_2026-10-04.md) |
| RUN-001 | 2026-10-04 | pipeline completa `relbench` (modalità codice, kit 0.2) | pipeline completata, **nessun miglioramento dimostrabile** | [RUN-001_pipeline_relbench_2026-10-04.md](RUN-001_pipeline_relbench_2026-10-04.md) (+ [rapporto automatico](RUN-001_auto.md)) |
| RUN-002 | 2026-10-04 | conferma dei vincitori dello sweep, semi 100–109 | **confermati** `aggr=max` e `transformer` | [RUN-002_conferma_sweep_2026-10-04.md](RUN-002_conferma_sweep_2026-10-04.md) |
| RUN-003 | 2026-10-04 | pipeline completa `relbench` (modalità configurazioni, kit 0.3) | pipeline corretta; **validazione +0,10 confermata, test +0,01 non significativo**; il paper descrive un metodo inventato | [RUN-003_pipeline_config-mode_2026-10-04.md](RUN-003_pipeline_config-mode_2026-10-04.md) (+ [rapporto automatico](RUN-003_auto.md)) |
| RUN-004 | 2026-10-05 | pipeline 3 h, modalità codice con schede dai paper (kit 0.5) | **test +0,038 sul baseline equo (p = 0,004)**; schede fedeli; ma vincitore = GATv2 + lr 1e-3, citazione solo nominale; errori invisibili all'LLM | [RUN-004_pipeline_code-mode_3h_2026-10-05.md](RUN-004_pipeline_code-mode_3h_2026-10-05.md) (+ [rapporto automatico](RUN-004_auto.md)) |
| RUN-005 | 2026-10-06 | pipeline 3 h, modalità codice (kit 0.5.2) | **nessun miglioramento sul test** (+0,008, p = 0,49); 'miglioramenti' dovuti al rumore; repository sbagliato (Relphormer); riparazione che sovrascrive main.py | [RUN-005_pipeline_code-mode_3h_2026-10-06.md](RUN-005_pipeline_code-mode_3h_2026-10-06.md) (+ [rapporto automatico](RUN-005_auto.md)) |
| RUN-006 | 2026-10-07 | pipeline "24 h" in modalità codice (kit 0.5.3) | **durata 2,2 h**: tetto di 10 iterazioni per passata nel codice originale; 30 tentativi, nessun miglioramento; codice ufficiale di RelGT trovato e importato 5 volte ma mai funzionante | [RUN-006_pipeline_code-mode_24h_2026-10-07.md](RUN-006_pipeline_code-mode_24h_2026-10-07.md) (+ [rapporto automatico](RUN-006_auto.md)) |
| RUN-007 | 2026-10-10 | pipeline in modalità codice "non guidata" (kit 0.6.2) | **fallita allo stage 13 (HTTP 400)**: prompt di riparazione con 192k caratteri di codice vendorizzato, oltre il contesto; baseline mai addestrato (GPU piena). Qwen aveva scelto da solo RelGNN con il codice ufficiale. Corretto nel kit 0.6.3 | [RUN-007_pipeline_code-mode_fallita-stage13_2026-10-10.md](RUN-007_pipeline_code-mode_fallita-stage13_2026-10-10.md) (+ [rapporto automatico](RUN-007_auto.md)) |
| RUN-008 | 2026-10-13/14 | pipeline "24 h" in modalità codice, non guidata (kit 0.6.3) | **15,2 h, 366 tentativi**: codice ufficiale di RelGNN importato e funzionante (86 tentativi) ma sotto il baseline; vincitore GATv2 + GraphNorm + residual (non dai paper): **validazione +0,11, test −0,012 (p = 0,43)**; validazione e test non correlati (0,05) | [RUN-008_pipeline_code-mode_24h_2026-10-13.md](RUN-008_pipeline_code-mode_24h_2026-10-13.md) (+ [rapporto automatico](RUN-008_auto.md)) |
