# RUN-017 — I modelli finali con le varianti 1–3 dei tipi delle colonne (e l'aggregazione `max` da sola)

| campo | valore |
|---|---|
| ID / data | RUN-017, 2026-10-30 (primo tentativo il 2026-10-29: §2.3) |
| tipo | rivalutazione senza LLM, `./run.sh repro-stypes --project` |
| comando | `RB_TASK=<task> ./run.sh repro-stypes --max-worlds 3 --project <progetto> --out artifacts/ch5_c2_<nome>` (da `ch5_runs_2.sh`, con `RB_GPU_WAIT_SEC=43200`) |
| manifest | `docs/runs/_manifests/20261030-113638_repro-stypes.txt` (RUN-011 su top3), `20261030-083219_...` (RUN-011 su top3, interrotto), `20261030-083237_...` (aggr=max), `20261030-083757_...` (RUN-004), `20261030-084914_...` (RUN-008), `20261030-085525_...` (RUN-011 su dnf); 29/10: `20261029-163357`, `-170057`, `-170129`, `-173841`, `-180822` |
| versione del kit | relbench-kit 0.6.11, commit `25844e5` |
| durata | circa 2 minuti per variante su driver-top3, circa 9 minuti su driver-dnf; GPU libera (40 MiB occupati all'avvio) |

## 1. Obiettivo
[RUN-015](RUN-015_repro-stypes_2026-10-23.md) ha dimostrato che i tipi di cinque colonne di `rel-f1` vengono decisi all'inizio di ogni
run da un campione casuale e spostano i valori assoluti dei baseline. Restava da verificare se cambino anche le **differenze appaiate**
su cui si basano le conclusioni (RUN-015 §5): il guadagno di RUN-004, l'assenza di guadagno di RUN-008, la perdita di RUN-011 su
driver-dnf e il guadagno del modello di RUN-011 su driver-top3 (RUN-013). Si aggiunge l'aggregazione `max` da sola, per sapere quanto di
quest'ultimo guadagno spieghi (RUN-013 §5).

## 2. Setup
### 2.1 Modelli
- `stage-13/experiment_final` di RUN-004 (`rc-20261005-183409-9b9601`), RUN-008 (`rc-20261013-131020-9b9601`) e RUN-011
  (`rc-20261014-152719-4d33ce`), eseguiti con i loro file (anche `main.py`, `rb_train.py`, ... della versione del kit della run);
- `artifacts/ch5_aggr_max_only`: copia del progetto di partenza del kit 0.6.11 con `PROPOSED_OVERRIDES = {"aggr": "max"}`
  (modello ufficiale con aggregazione `max`, ricetta `tuned`).

### 2.2 Varianti, semi e statistiche
Lo strumento estrae il campione 50 volte (semi numpy 0–49) e valuta le 3 varianti più frequenti, con `stypes.json` fissato nella cache
iniziale. Le varianti sono le stesse di RUN-015 (37/50, 5/50 e 3/50 campioni; file identici byte per byte nelle cinque esecuzioni).
Condizioni `baseline_graphsage`, `baseline_tuned`, `proposed`; semi 100–109; differenze appaiate calcolate da `worlds/v*/results.json`
(IC 95% bootstrap con 10.000 ricampionamenti, test esatto con inversione dei segni).

### 2.3 Primo tentativo (2026-10-29, `ch5_runs.sh`)
Un altro utente occupava 26–29 GB della GPU. Su 15 valutazioni ne sono riuscite 3 (RUN-008 su top3 con la variante 1, RUN-011 su top3 e
su dnf con la variante 2); le altre sono terminate con codice 3 (`GPU_UNAVAILABLE` di `main.py` dopo 10 minuti di attesa) o 1 (crash; i
log non sono stati conservati). Le 3 valutazioni riuscite sono riportate sotto come ripetizioni.

### 2.4 Secondo tentativo (2026-10-30, `ch5_runs_2.sh`)
12 valutazioni su 15 riuscite. RUN-011 su driver-top3 si è interrotto dopo 18 secondi, durante la variante 1 (il log della
valutazione si ferma alla quarta epoca di `proposed`, senza errori, e lo strumento non ha scritto il riassunto): causa non nota.
Rifatto lo stesso giorno alle 11:36 UTC con lo stesso comando (`--out artifacts/ch5_c3_run011_top3`): completo.

## 3. Risultati (fatti)

| modello e task | variante | `baseline_graphsage` test | `baseline_tuned` test | `proposed` test | Δ test [IC 95%], p, semi meglio | Δ val, p |
|---|---|---|---|---|---|---|
| RUN-004 su driver-top3 | 1 | 0,7502 | 0,7850 | 0,8232 | +0,038 [+0,017, +0,062], p = 0,010, 9/10 | +0,065, p = 0,002 |
| RUN-004 su driver-top3 | 2 | 0,7682 | 0,8012 | 0,8270 | +0,026 [+0,017, +0,034], p = 0,004, 9/10 | +0,063, p = 0,002 |
| RUN-004 su driver-top3 | 3 | 0,7600 | 0,7959 | 0,8274 | +0,032 [+0,018, +0,046], p = 0,002, 10/10 | +0,056, p = 0,004 |
| RUN-008 su driver-top3 | 1 | 0,7492 | 0,7834 | 0,7634 | −0,020 [−0,040, +0,003], p = 0,119, 2/10 | +0,122, p = 0,002 |
| RUN-008 su driver-top3 | 2 | 0,7680 | 0,8057 | 0,7719 | −0,034 [−0,058, −0,013], p = 0,014, 1/10 | +0,102, p = 0,002 |
| RUN-008 su driver-top3 | 3 | 0,7601 | 0,7906 | 0,7881 | −0,002 [−0,024, +0,017], p = 0,834, 5/10 | +0,116, p = 0,002 |
| RUN-008 su driver-top3 (29/10) | 1 | 0,7503 | 0,7741 | 0,7737 | −0,000 [−0,038, +0,032], p = 0,988, 5/10 | +0,125, p = 0,002 |
| aggr=max da solo su driver-top3 | 1 | 0,7505 | 0,7794 | 0,8158 | +0,036 [+0,020, +0,054], p = 0,004, 9/10 | +0,091, p = 0,002 |
| aggr=max da solo su driver-top3 | 2 | 0,7678 | 0,8042 | 0,7986 | −0,006 [−0,014, +0,004], p = 0,275, 3/10 | +0,091, p = 0,002 |
| aggr=max da solo su driver-top3 | 3 | 0,7607 | 0,7911 | 0,8082 | +0,017 [+0,002, +0,034], p = 0,062, 7/10 | +0,090, p = 0,002 |
| RUN-011 su driver-top3 | 1 | 0,7497 | 0,7779 | 0,8107 | +0,033 [+0,014, +0,050], p = 0,012, 9/10 | +0,108, p = 0,002 |
| RUN-011 su driver-top3 | 2 | 0,7677 | 0,8021 | 0,8100 | +0,008 [−0,013, +0,022], p = 0,457, 8/10 | +0,099, p = 0,002 |
| RUN-011 su driver-top3 | 3 | 0,7600 | 0,7965 | 0,8001 | +0,004 [−0,010, +0,016], p = 0,598, 7/10 | +0,102, p = 0,002 |
| RUN-011 su driver-top3 (29/10) | 2 | 0,7686 | 0,8066 | 0,8166 | +0,010 [+0,000, +0,019], p = 0,086, 8/10 | +0,092, p = 0,002 |
| RUN-011 su driver-dnf | 1 | 0,7319 | 0,7315 | 0,7109 | −0,021 [−0,029, −0,013], p = 0,002, 0/10 | +0,037, p = 0,002 |
| RUN-011 su driver-dnf | 2 | 0,7288 | 0,7107 | 0,7062 | −0,004 [−0,033, +0,028], p = 0,805, 4/10 | +0,042, p = 0,002 |
| RUN-011 su driver-dnf | 3 | 0,7311 | 0,7321 | 0,6943 | −0,038 [−0,057, −0,017], p = 0,014, 2/10 | +0,052, p = 0,002 |
| RUN-011 su driver-dnf (29/10) | 2 | 0,7241 | 0,7133 | 0,7148 | +0,002 [−0,021, +0,022], p = 0,902, 5/10 | +0,047, p = 0,002 |

Verifiche:
- su driver-top3 le varianti si riconoscono dai baseline: tra due esecuzioni con la stessa variante `baseline_graphsage` differisce di
  0,0006–0,0022 per seme; la conferma finale di RUN-008 dista 0,007 dalla variante 3 e almeno 0,033 dalle altre (come in RUN-015);
- su driver-dnf no: le tre varianti distano tra loro 0,012–0,018 per seme su `baseline_graphsage`, quanto due valutazioni della stessa
  variante (0,011; `baseline_tuned` 0,030). La variante usata da RUN-011 non si può quindi stabilire;
- dai loro risultati per seme su driver-top3, **RUN-010, RUN-012 e RUN-013 hanno usato la variante 1**: `baseline_graphsage` dista
  0,005–0,008 per seme dalla variante 1 e almeno 0,040 dalle varianti 2 e 3 (`artifacts/transfer_20261014-141446`,
  `transfer_20261015-185414`, `relgnn_train_20261015-172509`).

## 4. Interpretazione
- **Dimostrato:**
  - Il guadagno sulla validazione di ogni modello c'è con tutte le varianti (p ≤ 0,004).
  - **Le differenze appaiate sul test possono dipendere dalla variante**, non solo i valori assoluti: l'aggregazione `max` da sola
    guadagna +0,036 (p = 0,004) con la variante 1, −0,006 (p = 0,28) con la 2 e +0,017 (p = 0,062) con la 3.
  - Il guadagno di RUN-004 regge con tutte le varianti (da +0,026 a +0,038, p ≤ 0,010), come nell'ablazione di
    [RUN-016](RUN-016_ablazione_run004_2026-10-30.md).
  - Il modello di RUN-008 non migliora il test con nessuna variante (da −0,034 a −0,000); con la variante 2 è peggiore (p = 0,014).
  - Il modello di RUN-011 su driver-dnf è peggiore del baseline con le varianti 1 e 3 (−0,021, p = 0,002; −0,038, p = 0,014) e uguale
    con la variante 2 (−0,004 e +0,002 in due valutazioni).
  - **Il modello di RUN-011 migliora driver-top3 solo con la variante 1**: +0,033 (p = 0,012, 9 semi su 10), come in RUN-013 (+0,032,
    p = 0,006), che usava la stessa variante; con le varianti 2 e 3 +0,008 (p = 0,46) e +0,004 (p = 0,60).
  - Con la variante 1 l'aggregazione `max` da sola guadagna quanto il modello di RUN-011 (+0,036 contro +0,033); con le varianti 2 e 3
    nessuno dei due ha un guadagno significativo. Le altre modifiche di RUN-011 non aggiungono niente di misurabile.
- **Ipotesi non verificate:**
  - Una ripetizione con la stessa variante può cambiare la differenza appaiata di circa 0,02 per i modelli con molta varianza tra i semi
    (RUN-008 con la variante 1: −0,000 il 29/10, −0,020 il 30/10).
- **Cosa è andato storto:** primo tentativo (§2.3); la prima valutazione di RUN-011 su driver-top3 interrotta (§2.4).
- **Limiti:** 10 semi; una o due valutazioni per variante; le varianti 4–7 (5 campioni su 50) non valutate.

## 5. Decisioni e prossimi passi
- Tesi: le conclusioni che si basano su una sola run vanno riportate con la dipendenza dalla variante. Il guadagno di RUN-004 e
  l'assenza di guadagno di RUN-008 valgono con tutte le varianti, la perdita di RUN-011 su driver-dnf con due su tre, il guadagno
  del modello di RUN-011 su driver-top3 (RUN-013) con una su tre, e con quella variante lo dà anche l'aggregazione `max` da sola.
- Per le run future resta la correzione proposta in RUN-015 (tipi delle colonne fissati); non applicata.

## 6. Errata
Nessuna in questo documento. Da aggiungere come aggiornamenti: [RUN-011](RUN-011_pipeline_code-mode_24h_driver-dnf_2026-10-14.md)
(perdita su driver-dnf con 2 varianti su 3), [RUN-013](RUN-013_transfer_run011_2026-10-15.md) (il guadagno su driver-top3 vale con la variante 1 e lo dà anche `aggr=max` da solo),
[RUN-015 §5](RUN-015_repro-stypes_2026-10-23.md) (rivalutazione fatta qui).

## 7. File di riferimento
`artifacts/ch5_c2_{run004,run008,aggrmax}_top3/`, `artifacts/ch5_c2_run011_dnf/`, `artifacts/ch5_c3_run011_top3/`
(`artifacts/ch5_c2_run011_top3/` è il tentativo interrotto):
`summary_stypes.md`, `stypes_info.json`, `worlds/v*/results.json`, `worlds/v*/log.txt`; 29/10: `artifacts/ch5_c_*`;
`artifacts/ch5_aggr_max_only/rb_config.py`; `artifacts/ch5_runs.log`, `artifacts/ch5_runs_2.log`.
