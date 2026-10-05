# RUN-000 — Esperimenti preliminari su rel-f1 / driver-top3 (baseline e sweep)

| campo | valore |
|---|---|
| ID / data | RUN-000, 2026-10-03/04 (raccolta retroattiva; i manifest automatici non esistevano) |
| tipo | baseline ufficiale, seed project, sweep delle ricette, sweep architetturale |
| comandi | `./run.sh baseline`, `./run.sh sweep`, `RB_SWEEP_MODE=arch ./run.sh sweep` |
| versione del kit | 0.1–0.2 |
| dati | RelBench 1.1.0, `rel-f1` / `driver-top3`: tabelle ufficiali (1353 / 588 / 726 esempi train / val / test); `driver-position` 7453 / 499 / 760; `driver-dnf` ricalcolato in locale (hash non valido sul server) |

## 1. Obiettivo
Ottenere il numero da battere, tarare l'ambiente e capire se la validazione è una guida affidabile per ottimizzare il test.

## 2. Risultati (fatti)

### 2.1 GNN ufficiale (`examples/gnn_node.py`, un seme)
Miglior val AUROC 0,7283; test 0,8116 (tre esecuzioni: 0,8128 / 0,8113 / 0,8116). Con lo stesso seme i risultati si ripetono entro circa 0,002.

### 2.2 Seed project, ricetta ufficiale, 10 semi
| condizione | val AUROC | test AUROC |
|---|---|---|
| baseline_graphsage | 0,6966 ± 0,0525 | 0,7636 ± 0,0372 |
| proposed (2 layer, dropout 0,1, residual) | 0,6444 ± 0,0216 | 0,8243 ± 0,0512 |

Il baseline ufficiale è **sotto-addestrato**: 1353 esempi / batch 512 = 3 aggiornamenti per epoca, 30 in tutto; la validazione è bimodale tra i semi. Picco GPU 3,3–3,9 GB.
Un modello a 3 layer con la regola ufficiale di campionamento usa più di 20 GB (il sottografo temporale di ogni seme raggiunge gran parte del database); il seed ora limita la memoria con un budget di nodi e micro-batch.

### 2.3 Sweep delle ricette (ricetta ufficiale come riferimento, 5 semi per configurazione)
| configurazione | val | test |
|---|---|---|
| baseline (official) | 0,6936 ± 0,054 | 0,7574 ± 0,031 |
| epochs=30 | 0,7582 ± 0,023 | 0,7707 ± 0,021 |
| epochs=60 | 0,7652 ± 0,011 | 0,7906 ± 0,049 |
| batch=128 (4× più aggiornamenti) | 0,7676 ± 0,019 | 0,7760 ± 0,018 |
| lr=1e-3, epochs=30 | 0,7664 ± 0,003 | 0,7582 ± 0,023 |
| dropout=0,1 | 0,7068 ± 0,053 | 0,7691 ± 0,024 |
| residual | 0,6501 ± 0,011 | 0,8227 ± 0,024 |
| dropout=0,1 + residual | 0,6463 ± 0,013 | 0,7940 ± 0,070 |
| channels=64 | 0,7628 ± 0,015 | 0,7672 ± 0,005 |
| channels=256 | 0,6491 ± 0,039 | 0,7266 ± 0,022 |
| gatv2 | 0,6630 ± 0,044 | 0,7315 ± 0,072 |
| gin | 0,6919 ± 0,041 | 0,7332 ± 0,044 |
| transformer | 0,7462 ± 0,065 | 0,7757 ± 0,069 |
| resgated | 0,7230 ± 0,044 | 0,7758 ± 0,029 |

Correlazione di rango validazione–test: +0,16 (IC 95 % ≈ [−0,41, +0,63], 14 configurazioni) → inconcludente. Senza le due configurazioni con residual: +0,74 [+0,29, +0,92].
Le connessioni residuali peggiorano la validazione di 0,043 (1,8 SE) ma migliorano il test di 0,065 (3,7 SE).
Le configurazioni che "addestrano di più" guadagnano circa +0,07 in validazione (≈ 3 SE) ma solo +0,00…+0,03 sul test (< 1,3 SE).

### 2.4 Sweep architetturale (ricetta `tuned` = `batch_size` 128, 5 semi)
| configurazione | val | test | Δ val (SE) | Δ test (SE) |
|---|---|---|---|---|
| baseline (ricetta fissa) | 0,7487 ± 0,026 | 0,7796 ± 0,026 | | |
| **aggr=max** | **0,8516 ± 0,026** | **0,8146 ± 0,012** | +0,103 (6,2) | +0,035 (2,7) |
| **transformer** | **0,8365 ± 0,019** | **0,8017 ± 0,023** | +0,088 (6,0) | +0,022 (1,4) |
| layers=1 | 0,7794 ± 0,013 | 0,7564 ± 0,050 | +0,031 (2,3) | −0,023 (−0,9) |
| channels=64 | 0,7742 ± 0,014 | 0,7837 ± 0,016 | +0,026 (1,9) | +0,004 (0,3) |
| gin | 0,7691 ± 0,024 | 0,7652 ± 0,021 | +0,020 (1,3) | −0,014 (−1,0) |
| resgated | 0,7602 ± 0,020 | 0,7867 ± 0,028 | +0,012 (0,8) | +0,007 (0,4) |
| channels=256 | 0,7576 ± 0,013 | 0,7703 ± 0,021 | +0,009 (0,7) | −0,009 (−0,6) |
| aggr=mean | 0,7517 ± 0,012 | 0,7892 ± 0,034 | +0,003 (0,2) | +0,010 (0,5) |
| head norm=layer_norm | 0,7493 ± 0,019 | 0,7884 ± 0,027 | +0,001 (0,0) | +0,009 (0,5) |
| dropout=0,1 | 0,7404 ± 0,025 | 0,7862 ± 0,031 | −0,008 (−0,5) | +0,007 (0,4) |
| gatv2 | 0,7261 ± 0,025 | 0,7643 ± 0,059 | −0,023 (−1,4) | −0,015 (−0,5) |
| dropout=0,1 + residual | 0,6826 ± 0,019 | 0,7932 ± 0,036 | −0,066 (−4,6) | +0,014 (0,7) |
| residual | 0,6820 ± 0,014 | 0,7971 ± 0,026 | −0,067 (−4,9) | +0,018 (1,1) |

Correlazione di rango: +0,03 (IC 95 % [−0,51, +0,55], n = 14) → inconcludente. I due grandi miglioramenti (`aggr=max`, `transformer`) vanno nella stessa direzione su validazione e test;
l'unico punto cieco della validazione sono le connessioni residuali.

## 3. Interpretazione
- **Dimostrato (entro il rumore):** l'ambiente funziona; il baseline ufficiale è sotto-addestrato; con la ricetta `tuned` l'aggregazione `max` e l'operatore Transformer migliorano nettamente validazione e test (poi confermati in [RUN-002](RUN-002_conferma_sweep_2026-10-04.md)).
- **Ipotesi:** il disaccordo validazione–test sulle connessioni residuali potrebbe dipendere dal cambio di periodo (validazione 2005–2009, test dal 2010) o dalla dimensione della validazione (≈ 590 righe); non l'ho verificato.
- **Limiti:** 5 semi per configurazione; la scelta dei due "vincitori" è fatta guardando i risultati (rischio di sovrastima, poi controllato in RUN-002); un solo task e un solo dataset.

## 4. Errata
- Il verdetto "validazione = guida debole" stampato dalla prima versione dello strumento di sweep era troppo netto (con 14 configurazioni l'intervallo di confidenza è molto ampio): ora lo strumento riporta l'intervallo e dice "inconcludente".
- Nella prima descrizione della memoria avevo ipotizzato che crescesse con il prodotto dei vicini per layer; i dati hanno mostrato che dipende dal numero di nodi campionati (ogni layer in più satura il sottografo), da cui il budget di nodi con micro-batch.
