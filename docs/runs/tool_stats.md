# Statistiche dei tool per run (lette dai file delle run)

| | rc-20261001-182455-1c7204 | rc-20261001-184010-1c7204 | rc-20261001-190640-1c7204 | rc-20261001-193911-1c7204 | rc-20261002-170404-1c7204 | rc-20261002-182940-4496ae | rc-20261004-162625-9b9601 | rc-20261004-190007-9b9601 | rc-20261005-183409-9b9601 | rc-20261006-144130-9b9601 | rc-20261007-085443-9b9601 | rc-20261010-133700-9b9601 | rc-20261013-131020-9b9601 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| durata (h) | 0.08 | 0.14 | 0.13 | 0.14 | 0.65 | 1.97 | 1.16 | 1.41 | 2.03 | 1.98 | 2.21 | 0.58 | 15.16 |
| stato | failed | failed | failed | failed | failed | done | done | done | done | done | done | failed | done |
| query (scritte dall'LLM) | 5 (False) | 15 (True) | 15 (True) | 15 (True) | 9 (True) | 12 (True) | 7 (False) | 16 (True) | 7 (False) | 12 (True) | 7 (False) | 9 (True) | 12 (True) |
| candidati trovati | 217 | 406 | 419 | 384 | 319 | 429 | 248 | 523 | 586 | 752 | 587 | 414 | 500 |
| shortlist | 15 | 15 | 15 | 15 | 15 | 15 | 15 | 15 | 15 | 15 | 15 | 15 | 15 |
| schede dal testo completo | - | - | - | - | - | - | - | - | 3 | 2 | 2 | 3 | 3 |
| paper scartati (senza testo completo) | - | - | - | - | - | - | - | - | 0 | 0 | 0 | 3 | 3 |
| schede | - | - | - | - | - | - | - | - | K1: Improving Relational Deep Learning via Language Model-based Graph Augm; K2: Relational Graph Transformer; K3: From Schema to Signal: Retrieval-Augmented Modeling for Relational Dat; K4: QUARTET: Quad-branch cross-Attention and Random-walk Traces for Enhanc | K1: QUARTET: Quad-branch cross-Attention and Random-walk Traces for Enhanc; K2: Relational Graph Transformer | K1: Relational Graph Transformer; K2: QUARTET: Quad-branch cross-Attention and Random-walk Traces for Enhanc | K1: QUARTET: Quad-branch cross-Attention and Random-walk Traces for Enhanc; K2: RelGNN: Composite Message Passing for Relational Deep Learning; K3: Boosting Relational Deep Learning with Pretrained Tabular Models | K1: QUARTET: Quad-branch cross-Attention and Random-walk Traces for Enhanc; K2: RelGNN: Composite Message Passing for Relational Deep Learning; K3: Boosting Relational Deep Learning with Pretrained Tabular Models |
| repository dei paper delle schede | - | - | - | - | - | - | - | - | - | https://github.com/zjunlp/Relphormer.git | https://github.com/snap-stanford/relgt | https://github.com/snap-stanford/RelGNN.git; https://github.com/AntonioLonga/LightRDL.git | https://github.com/snap-stanford/RelGNN; https://github.com/AntonioLonga/LightRDL |
| repository clonati allo stage 5 | 2 | 2 | 2 | 2 | 2 | 1 | 1 | 1 | 0 | 1 | 1 | 2 | 2 |
| file vendorizzati (caratteri) | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 5 (64020) | 5 (60737) | 28 (190249) | 11 (74809) |
| passate dello stage 13 | 0 | 0 | 0 | 0 | 0 | 3 | 3 | 3 | 3 | 3 | 3 | 0 | 3 |
| tentativi | - | - | - | - | - | 7 | 17 | 20 | 29 | 30 | 30 | - | 366 |
| valutati | - | - | - | - | - | 7 | 9 | 20 | 12 | 11 | 4 | - | 190 |
| crash alla prima esecuzione | - | - | - | - | - | 4 | 12 | 0 | 16 | 12 | 15 | - | 141 |
| riparati | - | - | - | - | - | 0 | 14 | 0 | 17 | 11 | 13 | - | 127 |
| identici, non eseguiti | - | - | - | - | - | 0 | 0 | 0 | 0 | 0 | 0 | - | 70 |
| respinti dai controlli | - | - | - | - | - | 0 | 0 | 0 | 1 | 8 | 16 | - | 12 |
| errori dell'LLM | - | - | - | - | - | 0 | 0 | 0 | 0 | 0 | 0 | - | 0 |
| miglioramenti accettati | - | - | - | - | - | 1 | 4 | 4 | 1 | 2 | 0 | - | 2 |
| tentativi con codice ufficiale importato | - | - | - | - | - | 0 | 0 | 0 | 0 | 0 | 0 | - | 86 |
| moduli ufficiali importati | - | - | - | - | - | - | - | - | - | - | - | - | vendor_relgnn_relgnn_model: 77, vendor_relgnn_atomic_routes: 73, vendor_relgnn_relgnn_nn: 10, vendor_relgnn_model: 2, vendor_lightrdl_model: 1 |
| schede citate (tentativi) | - | - | - | - | - | - | - | - | K2: 26, K3: 1 | K1: 6, K2: 14 | K1: 16, K2: 2 | - | K1: 230, K2: 85, K3: 32 |
| tipi di architettura distinti | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 5 | 2 | 9 | 0 | 65 |
| più provati | - | - | - | - | - | - | - | gatv2: 3, gin: 2, resgated: 1 | gatv2: 19, relgt: 6, relational_graph_transformer: 1, ram: 1, sage: 1 | relphormer: 13, k1_sketch: 1 | gatv2: 8, relgt_local: 2, relgt: 2, sage_attn: 1, sage: 1 | - | attention: 109, relgnn: 79, gatv2_stable: 53, gatv2: 11, gatv2_res: 9 |
| righe cambiate in rb_model.py per tentativo (mediana) | - | - | - | - | - | - | 23 | 0.0 | 45 | 52.5 | 25.0 | - | 119.0 |
| correlazione val-test sui tentativi | - | - | - | - | - | - | -0.486 | 0.289 | 0.615 | 0.627 | -0.2 | - | 0.053 |
| modello finale: file cambiati | - | - | - | - | - | config.py: +9/-28, data.py: +20/-78, main.py: +49/-39, model.py: +14/-27, train.py: +23/-41 | main.py: +120/-18, rb_config.py: +10/-12, rb_model.py: +35/-8 | rb_config.py: +1/-1 | rb_config.py: +2/-2, rb_model.py: +3/-0 | rb_config.py: +2/-2, rb_model.py: +6/-1 | - | - | rb_config.py: +2/-2, rb_model.py: +90/-29 |
| modello finale: righe +/- | - | - | - | - | - | +115/-213 | +165/-38 | +1/-1 | +5/-2 | +8/-3 | +0/-0 | - | +92/-31 |
| modello finale: nuovi file | - | - | - | - | - | - | - | - | - | - | - | - | - |
| modello finale: usa codice ufficiale | - | - | - | - | - | - | - | - | - | - | - | - | - |
| modello finale: fonte dichiarata | - | - | - | - | - | - | - | - | 'K2: GATv2 attention-based aggregation with LayerNorm and dropout' | 'K2: Local Attention Module' | "" | - | 'K1: GATv2 attention aggregation with GraphNorm & residual connections' |
| conferma: test baseline_tuned / proposed | - / - | - / - | - / - | - / - | - / - | - / - | - / - | 0.8015 / 0.8113 | 0.7974 / 0.8290 | 0.7936 / 0.8017 | 0.7717 / 0.7717 | - / - | 0.7897 / 0.7773 |
| conferma: Δ val (p) | - (-) | - (-) | - (-) | - (-) | - (-) | - (-) | - (-) | - (-) | +0.0490 (0.0039) | +0.0155 (0.0645) | +0.0024 (0.1816) | - (-) | +0.1095 (0.0020) |
| conferma: Δ test (p) | - (-) | - (-) | - (-) | - (-) | - (-) | - (-) | - (-) | - (-) | +0.0316 (0.0039) | +0.0081 (0.4902) | +0.0000 (0.9863) | - (-) | -0.0123 (0.4336) |
| qualità del paper (revisione automatica) | - | - | - | - | - | 7.0 | 5.0 | 6.0 | 8.0 | 2.0 | 2.0 | - | 5 |
