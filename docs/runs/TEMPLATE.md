# RUN-NNN — <titolo breve>

| campo | valore |
|---|---|
| ID / data | RUN-NNN, AAAA-MM-GG |
| tipo | pipeline completa / sweep / conferma / baseline / altro |
| comando | `./run.sh ...` (copiato dal manifest) |
| manifest | `docs/runs/_manifests/<file>.txt` |
| versione del kit | (da `rb_task/VERSION`) + commit |
| run id (pipeline) | `rc-...` e percorso della cartella |
| durata | |

## 1. Obiettivo
Che domanda deve rispondere questa run? Che cosa ci si aspettava e perché.

## 2. Setup
- Dataset / task / ricetta di addestramento / semi / modello LLM
- Impostazioni rilevanti (variabili `ARC_*`, `RB_*`, `LLAMA_*`, parametri del config)
- Patch o modifiche rispetto alla run precedente

## 3. Risultati (fatti)
Tabelle copiate dal rapporto automatico o dall'output. Per ogni confronto: media ± deviazione standard, numero di semi, differenza in errori standard.

## 4. Interpretazione
- **Dimostrato:**
- **Ipotesi non verificate:**
- **Cosa è andato storto:**
- **Limiti** (rumore, dimensione di validazione/test, scelte fatte guardando i risultati, ecc.)

## 5. Decisioni e prossimi passi

## 6. Errata (correzioni a analisi precedenti)

## 7. File di riferimento
Percorsi di log, JSON, PDF, zip.
