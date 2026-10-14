# RelBench study (summary)
Improve the official RelBench GNN (RDL with heterogeneous GraphSAGE) on rel-f1 / driver-top3 (ROC-AUC, temporal
splits; selection on validation only, test reported). Conditions: baseline_graphsage (official), baseline_tuned (official
model, batch 128), proposed (baseline_tuned + changes implemented from the implementation cards K1..Kn of the
knowledge file). Hypotheses and plans must be grounded in those cards (cite the card id); do not invent components
that no card describes. 10 seeds; final model re-evaluated on fresh seeds.
