# RUN-012 — RelGNN con la configurazione degli autori, allenato con il nostro codice

| campo | valore |
|---|---|
| ID / data | RUN-012, 2026-10-15 |
| tipo | addestramento e valutazione senza LLM (`./run.sh relgnn-train`) |
| comando | `./run.sh relgnn-train` (default: driver-top3, driver-dnf, driver-position; 10 e 30 epoche; semi 100–109) |
| versione del kit | 0.6.9 |
| risultati | `artifacts/relgnn_train_<data>/summary.md` / `summary.json` / `results.json` |
| codice di RelGNN | repository ufficiale clonato in RUN-008 (`artifacts/rc-20261013-131020-9b9601/stage-06/paper_repos/relgnn`) |

## 1. Obiettivo
In RUN-008 RelGNN usato da Qwen arrivava a 0,733 di test su driver-top3, mentre il checkpoint degli autori, valutato con il nostro
codice, arriva a 0,8585 (RUN-009). Il divario dipende dalla **configurazione** (Qwen: 2 strati, 4 teste, batch 128) o
dall'**addestramento**? E allenare più a lungo serve? (domanda del correlatore sui training step)

## 2. Setup
- Quattro condizioni per task, sugli stessi 10 semi (100–109):
  - `baseline_graphsage` e `baseline_tuned`: il modello RDL congelato, come nella pipeline;
  - `relgnn_authors`: `RelGNN_Model` del repository ufficiale con la configurazione degli autori per modello e loader
    (`examples/utils.py`, `get_configs`);
  - `relgnn_run008`: lo stesso modello con 2 strati e 4 teste come Qwen in RUN-008, con il nostro loader (batch 128).
- Tutte con il ciclo di addestramento della pipeline (`rb_train.run_one`): Adam, lr 0,005, epoca migliore scelta sulla
  validazione, test valutato una volta. 10 e 30 epoche.
- Cosa non sappiamo: il repository di RelGNN non contiene il codice di addestramento (lo script "per riprodurre i risultati"
  valuta i checkpoint). Il paper (arXiv 2502.06784 v2) dice di mantenere "identical settings" a RelBench e di mediare su 5 semi, ma
  non riporta learning rate, epoche, né come sono scelti i modelli.

## 3. Risultati (test; tra parentesi la differenza da `baseline_tuned` con p e semi in cui la condizione è meglio)

### driver-top3 (AUROC; checkpoint degli autori 0,8585, paper 0,8569)

| condizione | aggiornamenti, 10 ep. | test, 10 epoche | aggiornamenti, 30 ep. | test, 30 epoche |
|---|---|---|---|---|
| baseline_graphsage (batch 512) | 30 | 0,752 | 90 | **0,789** |
| baseline_tuned (batch 128) | 110 | 0,768 | 330 | 0,780 |
| **RelGNN, configurazione degli autori** (1 strato, 2 teste, batch 256) | 60 | **0,790** (+0,022, p = 0,076, 7/10) | 180 | **0,802** (+0,022, p = 0,119, 7/10) |
| RelGNN, configurazione di Qwen (2 strati, 4 teste, batch 128) | 110 | 0,716 (−0,052, p = 0,010, 2/10) | 330 | 0,722 (−0,059, p = 0,025, 2/10) |

Validazione: graphsage 0,722 / 0,764; tuned 0,763 / 0,768; RelGNN autori 0,769 / 0,853; RelGNN config. di Qwen 0,739 / 0,869
(10 / 30 epoche). Il checkpoint degli autori ha validazione 0,712.

### driver-dnf (AUROC; checkpoint 0,7489, paper 0,7529)

| condizione | aggiornamenti, 10 ep. | test, 10 epoche | aggiornamenti, 30 ep. | test, 30 epoche |
|---|---|---|---|---|
| baseline_graphsage | 230 | **0,730** (+0,004, p = 0,61) | 690 | 0,703 |
| baseline_tuned | 900 | 0,725 | 2.700 | 0,682 |
| RelGNN, configurazione degli autori (2 strati, 1 testa, batch 256) | 450 | 0,688 (−0,037, p = 0,076, 3/10) | 1.350 | 0,686 (+0,004, p = 0,72) |
| RelGNN, configurazione di Qwen | 900 | 0,683 (−0,043, p = 0,051) | 2.700 | 0,699 (+0,017, p = 0,17) |

Validazione: graphsage 0,715 / 0,781; tuned 0,767 / 0,796; RelGNN autori 0,796 / 0,807; config. di Qwen 0,798 / 0,802. Il checkpoint
ha validazione 0,795. Dai batch per epoca, driver-dnf ha circa 11.400 righe di training (90 batch da 128), contro le 1.353 di driver-top3.

### driver-position (MAE, più basso è meglio; checkpoint 3,748, paper 3,798)

| condizione | aggiornamenti, 10 ep. | test, 10 epoche | aggiornamenti, 30 ep. | test, 30 epoche |
|---|---|---|---|---|
| baseline_graphsage | 150 | **4,051** (−0,201, p = 0,049) | 450 | 4,219 |
| baseline_tuned | 590 | 4,251 | 1.770 | 4,409 |
| RelGNN, configurazione degli autori (1 strato, 4 teste, batch 512, bidirezionale) | 150 | 4,350 (+0,098, p = 0,36) | 450 | 4,368 (−0,041, p = 0,67) |
| RelGNN, configurazione di Qwen | 590 | 4,437 (+0,185, p = 0,11) | 1.770 | 4,590 (+0,181, p = 0,14) |

Validazione: graphsage 3,195 / 3,092; tuned 3,121 / 3,023; RelGNN autori 3,065 / 2,961; config. di Qwen 2,975 / 2,879. Il checkpoint
ha validazione 2,847.

## 4. Interpretazione
- **Dimostrato:**
  - **Su driver-top3 la configurazione spiega gran parte del risultato di RUN-008.** Stesso codice e stesso addestramento: con la
    configurazione degli autori RelGNN fa 0,790–0,802, con quella di Qwen 0,716–0,722 (vicino allo 0,733 di RUN-008).
  - Con la configurazione degli autori RelGNN supera `baseline_tuned` su driver-top3 di +0,022 a 10 e a 30 epoche (7 semi su 10), ma
    la differenza non è significativa (p = 0,076 e 0,119).
  - **Allenato da noi non arriva al checkpoint**: 0,79–0,80 contro 0,8585 su driver-top3; su driver-dnf (0,69 contro 0,75) e
    driver-position (MAE 4,35 contro 3,75) è peggiore anche del baseline RDL. Con quello che è pubblicato (impostazioni di RelBench,
    configurazione del repository) i numeri del paper si riproducono con i pesi degli autori, ma non riallenando il modello.
  - **Più epoche non sono una soluzione generale.** Su driver-top3 aiutano tutti i modelli (il baseline con la ricetta ufficiale passa
    da 0,752 a 0,789 con 90 aggiornamenti invece di 30: lì la ricetta ufficiale è sotto-allenata). Su driver-dnf e driver-position
    peggiorano il test dei baseline (dnf 0,725 → 0,682; position 4,25 → 4,41) mentre la validazione migliora.
  - La validazione non distingue i modelli buoni sul test anche qui: su driver-dnf il nostro RelGNN ha la stessa validazione del
    checkpoint (0,796 contro 0,795) e test 0,688 contro 0,749; su driver-top3 il checkpoint ha validazione più bassa dei nostri
    (0,712 contro 0,769–0,853) e test molto più alto.
- **Ipotesi non verificate:**
  - Il divario rimanente sta nell'addestramento degli autori (learning rate, epoche, arresto anticipato, criterio di scelta del
    modello), che non è pubblicato. Su driver-top3 il loro checkpoint non è quello con la validazione più alta tra i modelli che
    otteniamo noi: non sappiamo con che criterio sia stato scelto, né se la loro validazione coincida con la nostra (versioni diverse
    dei dati o delle librerie).
  - Su driver-top3 la tendenza con più epoche è positiva (+0,012 da 10 a 30 per RelGNN): non sappiamo se continui fino a ~0,85.
- **Limiti:** 10 semi; learning rate fisso a 0,005; due sole durate; addestramento su GPU non deterministico (lo stesso
  `baseline_tuned` a 10 epoche sui semi 100–109 dà 0,768 qui, 0,778 in RUN-010 e 0,790 nella conferma di RUN-008).

## 5. Decisioni e prossimi passi
- Su driver-top3, provare durate più lunghe solo per RelGNN con la configurazione degli autori e i baseline:
  `./run.sh relgnn-train --tasks driver-top3 --epochs 60,100 --variants authors`; eventualmente un learning rate diverso (`--lr 0.001`).
- Proporre al correlatore di chiedere agli autori (issue sul repository) learning rate, epoche e criterio di scelta dei checkpoint.
- Per la tesi: anche "usare il codice ufficiale con la configurazione ufficiale" non basta a riprodurre il paper senza il loro
  addestramento; l'errore di Qwen in RUN-008 (configurazione) spiega però gran parte del suo risultato.

## 6. Errata
Nessuna.

## 7. File di riferimento
`artifacts/relgnn_train_<data>/summary.md`, `summary.json`, `results.json`; `rb_task/tools/relgnn_train.py`.
