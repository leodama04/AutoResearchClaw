# RUN-003 — Pipeline completa in modalità "a configurazioni" (kit 0.3)

| campo | valore |
|---|---|
| ID / data | RUN-003, 2026-10-04 (19:00–20:33 UTC) |
| tipo | pipeline completa (`./run.sh relbench`) fino al PDF |
| comando | `./run.sh relbench` (default: ricetta `tuned`, `ARC_SEARCH_MODE=config`, margine 0,005, pazienza 5, conferma sui semi 100–109) |
| versione del kit | 0.3 / 0.3.1 (nessun manifest automatico disponibile per questa run) |
| run id | `rc-20261004-190007-9b9601` (cartella consegnata come `secondo_esperimento_relbench_f1_driver_top3`) |
| durata | 1,41 h di stage; 29/29 completati, 0 falliti |
| rapporto automatico | [RUN-003_auto.md](RUN-003_auto.md) |

## 1. Obiettivo
Ripetere RUN-001 dopo le correzioni (filtro di validità, file protetti, ricerca a configurazioni, conferma su semi nuovi) e verificare se la pipeline trova autonomamente un miglioramento reale del GNN.

## 2. Setup
Come RUN-001, con: l'LLM propone un JSON di impostazioni architetturali (14 chiavi, [search_space.json](../../rb_task/task_spec/search_space.json)); l'esecutore le scrive in `PROPOSED_OVERRIDES`; nessun codice può cambiare.
`max_iterations` 12 per passata; il numero di semi resta 10; i numeri di test sono nascosti all'LLM; la ricerca non aveva memoria tra le passate (aggiunta dopo, v. §6).
Riferimento di valutazione (stage 12, semi 0–9): `baseline_graphsage` val 0,722 ± 0,048 / test 0,765 ± 0,030; `baseline_tuned` 0,787 ± 0,010 / 0,789 ± 0,015; `proposed` (identico al tuned) 0,787 ± 0,011 / 0,792 ± 0,017.

## 3. Risultati (fatti)

### 3.1 La ricerca: 20 valutazioni in tre passate
La decisione di fine analisi è stata "refine" due volte, quindi stage 13 è stato eseguito tre volte (5 + 5 + 10 iterazioni), tutte valide (codice 0, 10 semi, tutte le condizioni): il filtro di validità e la protezione dei file hanno funzionato, nessuna iterazione corrotta.

| passata | iterazioni | risultato |
|---|---|---|
| 1 | 5 | nessuna configurazione migliora il riferimento (0,787) |
| 2 | 5 | nessuna migliora |
| 3 | 10 | **4 miglioramenti**: it. 5 `{aggr: max, dropout: 0,1}` → 0,8637; it. 7 `+ channels 256` → 0,8694; it. 8 `+ enc_layers 2` (proposta di ripiego) → 0,8786; it. 10 `+ head_layers 2` → **0,8854** |

Configurazione finale: `aggr=max, channels=256, dropout=0,1, enc_layers=2, head_layers=2` (le altre impostazioni sono le ufficiali).
Valutazioni distinte 19 su 20: `{channels: 256, residual: true}` è stata valutata nella passata 1 (0,6810) e nella 3 (0,6815): stessa configurazione, risultato quasi identico (la valutazione è riproducibile a parità di semi e di codice).
L'LLM ha proposto più volte combinazioni con `residual`, `jk=cat`, GATv2, GIN, ResGated (tutte peggiori in validazione); **non ha mai provato `transformer`**, che nello sweep era uno dei due vincitori. `aggr=max` è arrivato solo alla 14ª proposta.

### 3.2 Conferma su semi nuovi (100–109), passata finale
| condizione | val AUROC | test AUROC |
|---|---|---|
| baseline_graphsage (ufficiale) | 0,7327 ± 0,0540 | 0,7643 ± 0,0437 |
| baseline_tuned | 0,7878 ± 0,0128 | 0,8015 ± 0,0172 |
| **proposed (finale)** | **0,8884 ± 0,0071** | **0,8113 ± 0,0320** |

Confronti appaiati per seme (stessa esecuzione, 10 semi; test di permutazione con inversione dei segni):

| confronto | differenza media | IC 95 % (bootstrap) | semi migliori | p |
|---|---|---|---|---|
| validazione: proposed − tuned | **+0,1006** (SE 0,0042) | [+0,0925, +0,1078] | 10/10 | 0,002 |
| **test: proposed − tuned** | **+0,0097** (SE 0,0081) | **[−0,0062, +0,0238]** | **6/10** | **0,23** |
| test: proposed − ufficiale | +0,0470 (SE 0,0169) | [+0,0162, +0,0792] | 8/10 | 0,023 |
| test: tuned − ufficiale | +0,0373 (SE 0,0134) | [+0,0140, +0,0639] | 9/10 | 0,012 |

### 3.3 Validazione e test lungo la ricerca
Su 20 valutazioni la correlazione di rango tra Δvalidazione e Δtest (rispetto al `baseline_tuned` della stessa esecuzione) è +0,30. Le 5 valutazioni con Δvalidazione > +0,02 (tutte con `aggr=max`) hanno Δvalidazione medio +0,088 ma Δtest medio solo **+0,013** (valori: +0,021, −0,004, −0,003, +0,020, +0,028).
Dall'iterazione 5 alla 10 la validazione sale da 0,8637 a 0,8854 (+0,022), mentre sui semi di conferma il guadagno del test sul tuned resta +0,010.

### 3.4 Il paper (stage 17–23)
- Rapporto di qualità 6/10 ("Borderline / Accept with revisions"), `fabrication_suspected=False`, 409 valori verificati, 5/5 citazioni verificate, PDF compilato. I 12 numeri del paper trovano tutti riscontro nei risultati aggregati; i semi dichiarati (10) sono giusti.
- **Il metodo descritto non esiste.** Il paper "introduce Relation-Conditioned Feature Projection (RCFP)", "una matrice di proiezione appresa che comprime i metadati relazionali prima del message passing" (22 menzioni). Nel codice non c'è nessuna proiezione: la modifica reale è la sostituzione della somma con il massimo nell'aggregazione, 256 canali, dropout 0,1, encoder a 2 layer e testa a 2 layer. Il paper non nomina mai `max`, `channels`, `dropout`.
  Causa: l'ipotesi dello stage 8 (scritta prima di qualunque esperimento) inventa RCFP, e gli stage di analisi e di scrittura non ricevono la configurazione realmente valutata.
- Nei risultati il paper è onesto: riporta il risultato "iniziale" (test 0,8255 ± 0,020, +2,83 % sul tuned) e quello confermativo (0,8113 ± 0,032, +0,97 %), e conclude che il metodo "non fornisce miglioramenti consistenti".
  Dichiara di non aver eseguito test appaiati "per mancanza dei log per seme" (esistevano in `results.json`; il kit non li passava allo stage 14).

## 4. Interpretazione
- **Dimostrato:**
  1. La pipeline, in modalità a configurazioni, funziona dall'inizio alla fine senza iterazioni corrotte; ha trovato da sola una configurazione che migliora di circa +0,10 la validazione, confermata su semi nuovi con 10 semi su 10 (p = 0,002).
  2. Il miglioramento della **validazione** non è un artefatto dei semi: si riproduce quasi identico nella conferma (il valore atteso dalla selezione era +0,099, osservato +0,101).
  3. Il miglioramento sul **test** rispetto al baseline equo (`baseline_tuned`) è piccolo e non statisticamente supportato (+0,010, IC95 % da −0,006 a +0,024; 6 semi su 10). Il guadagno sul baseline ufficiale (+0,047) è per l'80 % dovuto alla ricetta di addestramento (+0,037), non all'architettura.
- **Probabile ma non dimostrato:** la ricerca ha sovra-adattato la validazione. Indizi: le modifiche successive a `aggr=max` (it. 7–10) aggiungono +0,022 in validazione senza guadagno visibile sul test; l'errore standard dell'AUROC dovuto alla sola dimensione dei campioni è circa 0,023 sulla validazione (119 positivi su 588, stima di Hanley–McNeil) e 0,022 sul test (151 positivi su 726) — più grande dei guadagni cercati e condiviso da tutte le configurazioni (stessi 588 esempi), quindi non si cancella con più semi.
- **Non spiegato:** il sweep e `main.py` danno numeri diversi per la stessa configurazione e gli stessi semi: `baseline_tuned` val 0,749–0,757 / test 0,762–0,780 nello sweep contro val 0,785–0,788 / test 0,789–0,802 nella pipeline (e il baseline ufficiale val 0,694–0,697 contro 0,715–0,722). L'unica differenza di codice che ho trovato è `torch.set_num_threads(1)` in `main.py`. Conseguenza: i Δtest di RUN-002 (+0,051 e +0,056) erano calcolati contro un baseline basso e sono probabilmente sovrastimati (vedi Errata).
- **Cosa è andato storto:** (1) il paper descrive un metodo inventato; (2) l'LLM ha esplorato male (nessun `transformer`, molte combinazioni con `residual`/`jk`); (3) nessuna memoria tra le passate: la passata 3 ha ripetuto una configurazione già valutata e le prime due passate (10 valutazioni) sono state in pratica sprecate;
  (4) il paper non aveva i log per seme; (5) con 12 iterazioni per passata la ricerca si è fermata mentre migliorava ancora (4 miglioramenti su 10 iterazioni, stop per numero massimo di iterazioni e non per saturazione).
- **Limiti:** una sola run; una sola suddivisione validazione/test (singolo periodo, ~590 e ~730 righe); la scelta del "migliore" fatta sulla stessa validazione usata per riportare i risultati di selezione.

## 5. Domanda: ha senso far girare la pipeline più a lungo (fino a 24 h)?
- **Costo:** una valutazione completa (3 condizioni × 10 semi) richiede 116–150 s, ~150 s per iterazione con l'LLM → ~570 iterazioni in 24 h. Lo spazio ha ~2,5 milioni di combinazioni: una ricerca di qualche centinaio di valutazioni è possibile, ma il collo di bottiglia non è il tempo.
- **Validazione:** quasi certamente salirà ancora (la curva stava salendo). Più valutazioni sulla stessa validazione di 588 righe aumentano però il rischio di sovra-adattamento: l'evidenza di questa run è che +0,10 in validazione si traduce in circa +0,01 sul test.
- **Test:** non c'è alcuna prova che altre ore migliorino il test; l'ipotesi più ragionevole è un guadagno piccolo (frazioni di punto fino a pochi punti) e incerto. Prima di allungare conviene cambiare il segnale di selezione (v. §6).
- Cosa farei prima di una run da 24 h: memoria tra passate e partenza dal migliore (fatto, kit 0.4), descrizione fedele del metodo nel paper (fatto, kit 0.4), una validazione più ampia o a più finestre temporali (da decidere), selezione dei migliori k candidati con semi nuovi, margine di accettazione che cresce col numero di valutazioni.

## 5b. Confronto con la leaderboard di RelBench (driver-top3, test, AUROC)
Fonte: tabella "Classification" della leaderboard `relbench/leaderboard` (Hugging Face Space), incollata dall'utente il 2026-10-04 (data di aggiornamento non indicata). Metrica: AUROC sullo split di test ufficiale; "task-specific" = addestrato/affinato
sulle etichette del task, "zero-shot" = modello in-context senza addestramento sul task. Le colonne sono 12 attività; `driver-top3` è l'ottava. Valori confermati da fonti indipendenti: RDL 75,5 (articolo RelBench 75,54 ± 0,63), LightGBM 73,9 (73,92), RelGNN 85,7 (85,69).

| metodo | regime | AUROC test `driver-top3` |
|---|---|---|
| KumoRFM (fine-tuned) | task-specific | 99,6 |
| Kapso (Leeroo) | task-specific | 93,6 |
| RT (pretrained + fine-tuned) | task-specific | 92,1 |
| KumoRFM-2 (in-context) | zero-shot | 92,2 |
| PluRel (pretrained + fine-tuned) | task-specific | 89,3 |
| RGP | task-specific | 87,9 |
| RelGNN | task-specific | 85,7 |
| RelAgent (GPT-5.2 agent) | task-specific | 85,2 |
| GelGT / RelGT | task-specific | 84,1 / 83,5 |
| RT (from scratch) / Rel-LLM | task-specific | 82,7 / 82,2 |
| **nostro modello finale (RUN-003, 10 semi)** | task-specific | **81,1 ± 3,2** |
| **nostro `baseline_tuned`** | task-specific | **80,2 ± 1,7** |
| RDL (GraphSAGE) = il modello ufficiale da cui partiamo | task-specific | 75,5 |
| LightGBM (feature grezze del pilota, senza grafo) | task-specific | 73,9 |
| GIN / HGT / GAT | task-specific | 73,6 / 70,8 / 60,0 |

Posizione sulla colonna `driver-top3`: 17 righe su 28 stanno sopra 81,1 (tra i 20 metodi task-specific: 11 sopra e 9 sotto), quindi il nostro modello sarebbe circa 18° su 29 in assoluto e 12° su 21 tra i task-specific. La posizione è approssimativa:
il nostro valore ha deviazione standard 3,2 su 10 semi e un errore di campionamento del test di circa 2 punti. Il massimo della colonna è 99,6; il valore 91,4 citato da una pagina aggregatrice **non compare** in nessuna riga.

Lettura:
- Il nostro baseline ufficiale (76,4 ± 4,4 su semi 100–109) riproduce il valore pubblicato (75,5).
- Il guadagno rispetto a RDL (+5,6 punti) viene per circa +3,7 dalla ricetta di addestramento e per +1,0 (non significativo) dalle modifiche architetturali (§3.2).
- Il nostro metodo ricade nella famiglia "GNN ben tarata". I risultati sopra 85 vengono da modelli diversi: pre-addestrati su molti database (RT, PluRel, KumoRFM), con message passing strutturalmente diverso (RelGNN, RGP, RelGT, GelGT) o costruiti da un agente (RelAgent, Kapso: dalla sola tabella non so come funzionino).
- Il confronto più vicino alla nostra pipeline è RelAgent (agente GPT-5.2, 85,2); da leggere per capire che cosa cambia rispetto al nostro approccio.
- Avvertenza: la colonna "Mean" della leaderboard è la media su 12 attività; noi abbiamo valutato una sola attività, quindi non è confrontabile.

## 6. Decisioni e prossimi passi (kit 0.4)
- Memoria tra passate: lo storico di tutte le valutazioni è nel prompt, le duplicate sono rifiutate, ogni passata riparte dalla migliore (record riportato come iterazione 0).
- `ARC_METHOD_FILE`: stage 13 scrive una descrizione autorevole di ciò che è stato valutato (impostazioni cambiate, numero di valutazioni, numeri di conferma, differenze appaiate con IC e p) e la aggiunge ai prompt di analisi, decisione e scrittura. Regole: nessun componente inventato, riportare la conferma, dire quali differenze sono supportate.
- `confirmation.json` contiene ora le statistiche appaiate; `RB_SWEEP_THREADS=1` per il test A/B sul divario sweep/pipeline.
- Da fare con te: decidere il nuovo segnale di selezione e lanciare il test A/B.

## 7. Errata
- **RUN-002:** i Δtest (+0,051 per `aggr=max`, +0,056 per `transformer`) usavano come baseline `baseline_tuned` misurato dallo sweep (test 0,762), 0,04 più basso dello stesso baseline misurato dalla pipeline sugli stessi semi (0,80). I valori assoluti del test di `aggr=max` (0,812) e `transformer` (0,818) restano plausibili, ma il vantaggio sul baseline è probabilmente più vicino a +0,01…+0,02. Il Δvalidazione (+0,100 per `max`) si è invece riprodotto nella pipeline.
- **RUN-001, §2.1 di RUN-000:** nessuna modifica.

## 8. File di riferimento
`stage-13*/refinement_log.json`, `stage-13*/confirmation.json`, `stage-13/confirm_sandbox/_project_1/results.json` (log per seme), `stage-14/experiment_summary.json`, `stage-20/quality_report.json`, `stage-22/paper.pdf`, `stage-23/paper_final_verified.md`.
