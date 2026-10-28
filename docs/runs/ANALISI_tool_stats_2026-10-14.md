# Statistiche dei tool di tutte le run — lettura (2026-10-14)

Tabella completa generata da `./run.sh tool-stats` in [tool_stats.md](tool_stats.md) (13 cartelle in `artifacts/`).
Richiesta del correlatore (call del 13/10): quanti paper trovati, quanti usati davvero, quante modifiche al codice.

## Quali cartelle sono quali run

| cartella | run documentata | note |
|---|---|---|
| rc-20261001-182455, -184010, -190640, -193911, rc-20261002-170404 | — | tentativi del 1–2 ottobre, prima del kit; tutti falliti in meno di 40 minuti |
| rc-20261002-182940-4496ae | — | prima del kit: completata (2 h), progetto scritto da zero dall'LLM (`config.py`, `data.py`, `model.py`, `train.py`) |
| rc-20261004-162625 | RUN-001 | kit 0.2, modalità codice |
| rc-20261004-190007 | RUN-003 | kit 0.3, modalità configurazioni |
| rc-20261005-183409 | RUN-004 | kit 0.5, modalità codice con schede, 3 h |
| rc-20261006-144130 | RUN-005 | kit 0.5.2, 3 h |
| rc-20261007-085443 | RUN-006 | kit 0.5.3, "24 h" (2,2 h effettive) |
| rc-20261010-133700 | RUN-007 | kit 0.6.2, fallita allo stage 13 |
| rc-20261013-131020 | RUN-008 | kit 0.6.3, 24 h (15,2 h effettive) |

## Le run documentate in una tabella

| | RUN-001 | RUN-003 | RUN-004 | RUN-005 | RUN-006 | RUN-008 |
|---|---|---|---|---|---|---|
| query scritte da Qwen | no (7, pezzi del titolo) | sì (16) | no (7) | sì (12) | no (7) | sì (12) |
| candidati trovati | 248 | 523 | 586 | 752 | 587 | 500 |
| schede dal testo completo | — | — | 3 | 2 | 2 | 3 |
| repository dei paper delle schede | — | — | — | Relphormer (paper sbagliato) | RelGT | RelGNN, LightRDL |
| tentativi | 17 | 20 | 29 | 30 | 30 | 366 |
| valutati | 9 | 20 | 12 | 11 | 4 | 190 |
| crash alla prima esecuzione | 12 | 0 | 16 | 12 | 15 | 141 |
| miglioramenti accettati | 4 | 4 | 1 | 2 | 0 | 2 |
| righe cambiate nel modello finale | +165/−38 | +1/−1 | +5/−2 | +8/−3 | +0/−0 | +92/−31 |
| il modello finale usa codice dei paper | no | no | no | no | no | no |
| conferma, test: baseline_tuned → proposed | — | 0,8015 → 0,8113 | 0,7974 → 0,8290 | 0,7936 → 0,8017 | 0,7717 → 0,7717 | 0,7897 → 0,7773 |
| conferma, Δ test (p) | — | +0,010 (0,23) | **+0,032 (0,004)** | +0,008 (0,49) | 0,000 (0,99) | −0,012 (0,43) |
| conferma, Δ val (p) | — | +0,101 (0,002) | +0,049 (0,004) | +0,016 (0,06) | +0,002 (0,18) | +0,110 (0,002) |
| voto del paper (revisione automatica) | 5 | 6 | 8 | 2 | 2 | 5 |

RUN-007 è fallita prima del raffinamento (nessun tentativo). Per RUN-003 le differenze appaiate (e i p) vengono dal suo
documento: il kit 0.3 non le salvava nel file letto dallo script. In RUN-004 la conferma è stata ripetuta in tre passate sullo stesso
modello: +0,038, +0,039, +0,032 (la tabella riporta l'ultima).

## Cosa dicono
1. **Paper trovati e usati.** Ogni run trova 250–750 candidati, ne tiene 15, e dal kit 0.5 ne legge 2–3 a testo completo. Il codice
   ufficiale è stato importato in tre run: in RUN-005 era di un altro paper (Relphormer, usato una volta, crash), in RUN-006 quello
   di RelGT è stato importato 5 volte senza mai funzionare, in RUN-008 quello di RelGNN ha funzionato (86 tentativi) ma è rimasto
   sotto il baseline. **Nessun modello finale usa codice dei paper**: i vincitori sono modifiche scritte da Qwen con operatori
   standard di PyG (GATv2, TransformerConv, LayerNorm/GraphNorm, residual) o, in RUN-003, solo iperparametri; le citazioni delle
   schede sono nominali.
2. **Query.** In RUN-001, RUN-004 e RUN-006 le query di Qwen erano state scartate e sostituite con pezzi del titolo (difetto del
   codice originale, corretto nel kit 0.6.1); dalla 0.6.1 sono sempre le sue.
3. **Modifiche al codice.** Poche righe nei modelli finali (da +1/−1 a +92/−31); in RUN-008 la mediana per tentativo è 119 righe
   di `rb_model.py`. RUN-001 modificava anche `main.py` (prima che i file fissi fossero protetti).
4. **Affidabilità.** In modalità codice la parte dei tentativi che arriva a un risultato valido va dal 13% (RUN-006, 4 su 30) al
   53% (RUN-001, 9 su 17); RUN-008 52%. In modalità configurazioni (RUN-003) tutti e 20. Il resto sono crash non recuperati,
   tentativi identici non eseguiti (70 in RUN-008) e tentativi respinti dai controlli; in RUN-008 i crash più frequenti sono
   argomenti inesistenti passati agli operatori di PyG (40) e `rb_model.py` riscritto senza `build_model` (39).
5. **Risultati.** La validazione migliora nettamente in RUN-003, RUN-004 e RUN-008 (+0,05…+0,11, p ≤ 0,004); il test migliora in
   modo significativo solo in RUN-004 (+0,032, p = 0,004), il cui vincitore però cambia anche il learning rate. Nelle run
   successive, con la ricetta bloccata, nessun guadagno sul test; e il vincitore di RUN-008 non migliora neanche sugli altri task
   (RUN-010).

## Avvertenze sui numeri
- I campi introdotti nei kit più recenti valgono 0 nelle run vecchie perché allora non esistevano: tentativi identici non eseguiti
  (dal kit 0.6), errori dell'LLM (dal 0.6.3).
- "Tentativi con codice ufficiale importato": la tabella allegata li legge da un campo che esiste solo dal kit 0.6, quindi per
  RUN-005 e RUN-006 mostra 0 (i documenti delle run ne contano 1 e 5). Dal kit 0.6.8 lo script li ricava dal codice di ogni
  tentativo: rigenerare con `./run.sh tool-stats`.
- Le righe cambiate sono contate dallo script con un diff riga per riga; possono differire di poco dai documenti delle run (RUN-005:
  +8/−3 qui, "14 righe" nel documento).
- La correlazione validazione-test sui tentativi è calcolata su pochi modelli nelle run brevi (n = 4–20); l'unico valore affidabile
  è quello di RUN-008: 0,05 su 190 modelli.
