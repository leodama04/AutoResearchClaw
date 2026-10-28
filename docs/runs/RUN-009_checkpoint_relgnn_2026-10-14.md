# RUN-009 — checkpoint ufficiali di RelGNN valutati con il nostro codice

| campo | valore |
|---|---|
| ID / data | RUN-009, 2026-10-14 |
| tipo | valutazione (nessun addestramento), richiesta dal correlatore |
| comando | `./run.sh relgnn-ckpt` (kit 0.6.5) e `./run.sh relgnn-ckpt --tasks driver-position` (kit 0.6.6) |
| manifest | `docs/runs/_manifests/20261014-134107_relgnn-ckpt.txt`, `20261014-134755_relgnn-ckpt.txt` |
| risultati | `artifacts/relgnn_checkpoint_eval_20261014-134108.md` / `.json` (top3, dnf), `..._20261014-134756.*` (position) |
| durata | pochi secondi per task (checkpoint già scaricati) |

## 1. Obiettivo
Prima di confrontare i risultati della pipeline con i paper, verificare che i numeri pubblicati si riproducano nel nostro ambiente:
stesso codice dei dati della pipeline (`rb_data.prepare_data`), modello e pesi degli autori.

## 2. Setup
- Modello: `RelGNN_Model` dal repository ufficiale (clonato dalla pipeline in RUN-008), configurazione degli autori per task
  (`get_configs`) e loro loader (fanout 128/64, `subgraph_type` del task, batch del task).
- Pesi: `tianlangchen/RelGNN` su Hugging Face, caricati con controllo delle chiavi. Le uniche chiavi assenti sono 7 buffer
  `fill_values` (uno per encoder delle colonne data/ora delle tabelle drivers, constructor_results, qualifying, results,
  constructor_standings, standings, races): torch_frame 0.3 li salva, la 0.2.3 usata dagli autori li calcolava a ogni passo dalle
  statistiche delle colonne; sono ricalcolati con lo stesso calcolo.
- Metrica: `task.evaluate` di relbench su validazione e test, 3 semi di campionamento (0, 1, 2).

## 3. Risultati

| task | metrica | val (nostro) | test (nostro) | test RelGNN (paper) | test RDL (paper) | test RDL (nostro) |
|---|---|---|---|---|---|---|
| driver-top3 | ROC-AUC | 0,7119 | **0,8585** | 0,8569 | 0,7554 | 0,755 ± 0,021 (RUN-008, semi 100–109) |
| driver-dnf | ROC-AUC | 0,7953 | **0,7489** | 0,7529 | 0,7262 | da misurare |
| driver-position | MAE (più basso è meglio) | 2,8471 | **3,7479** | 3,798 | 4,022 | da misurare |

Deviazione standard tra i semi di campionamento < 0,0001 (con fanout 128/64 il campionamento copre quasi tutti i vicini).
Al primo tentativo driver-position si era fermato con `TypeError: got an unexpected keyword argument 'squared'` (relbench 1.1.0
calcola `rmse` con un argomento rimosso da scikit-learn 1.6; corretto nel kit 0.6.6, vale anche per baseline e pipeline su quel
task); rifatto con il kit 0.6.6.

## 4. Interpretazione
- **Dimostrato:**
  - Il nostro codice dei dati e di valutazione riproduce i numeri pubblicati su tutti e tre i task: driver-top3 0,8585 contro
    0,8569 (+0,002), driver-dnf 0,7489 contro 0,7529 (−0,004), driver-position MAE 3,748 contro 3,798 (un po' meglio; il paper
    riporta la media di 5 addestramenti, qui c'è un solo checkpoint). Insieme al baseline RDL (0,755 contro 0,7554) il riferimento
    è solido.
  - Quindi il 0,733 di test di RelGNN in RUN-008 non dipende dai dati né dalla valutazione, ma da come la pipeline lo ha allenato:
    2 layer e 4 teste invece di 1 layer, 2 teste e `simplified_MP`, e la nostra ricetta (10 epoche, batch 128).
  - **Il modello pubblicato ha validazione 0,712 su driver-top3**: meno del nostro `baseline_tuned` (~0,77) e molto meno del vincitore
    di RUN-008 (0,886), che sul test fa 0,777. Il modello migliore sul test sarebbe tra i peggiori secondo il criterio con cui la pipeline
    sceglie. È la conferma più netta che su driver-top3 la validazione non indica il test (correlazione 0,05 in RUN-008).
- **Ipotesi non verificate:** come gli autori abbiano scelto configurazione ed epoche (il paper non lo dice); se RelGNN allenato da noi
  con la loro configurazione arrivi a ~0,85.
- **Limiti:** un solo checkpoint per task (gli autori riportano la media di 5 semi di addestramento).

## 5. Decisioni e prossimi passi
- Allenare RelGNN con la configurazione degli autori nel nostro ciclo di addestramento, con la ricetta della pipeline e con più epoche:
  dice quanto del divario 0,73 → 0,86 viene da configurazione e durata dell'addestramento (la domanda del correlatore sui training step).
- Portare ai relatori il dato sulla validazione prima di altre run lunghe: con questo criterio la pipeline non può scegliere modelli come RelGNN.

## 6. Errata
Nessuna. Aggiornamento 2026-10-15: RelGNN allenato da noi con la configurazione degli autori (RUN-012) **non** arriva a ~0,85
su driver-top3 (0,790 a 10 epoche, 0,802 a 30) ed è sotto il baseline su driver-dnf e driver-position; il paper non pubblica
learning rate, epoche né criterio di scelta dei checkpoint.

## 7. File di riferimento
`artifacts/relgnn_checkpoint_eval_20261014-134108.md/.json`, `artifacts/relgnn_checkpoints/*.pth`, `rb_task/tools/relgnn_checkpoint_eval.py`.
