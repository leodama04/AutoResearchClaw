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
