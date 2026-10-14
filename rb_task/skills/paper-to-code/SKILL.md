---
name: paper-to-code
description: How to turn an implementation card (paper + official code) into a working change of the model. Use when a code change must implement a method from the literature.
metadata:
  category: experiment
  trigger-keywords: "paper,implementation,official code,port,card,method,literature,reproduce,gnn,relbench"
  applicable-stages: "8,9,10,13"
  priority: "1"
  version: "1.0"
  author: relbench-kit
  references: "KNOWLEDGE.md built at stage 6 of the run"
---
1. Pick ONE component from ONE card (K1, K2, ...): the smallest piece that changes how the model computes, e.g. the
   message-passing operator, the aggregation, the readout, the column encoder or the temporal encoding.
2. If the card lists vendored official code (`vendor_<repo>_<module>.py`, read-only), IMPORT it
   (`from vendor_<repo>_<module> import <Class>`) and write only the adapter to our batch. Otherwise, if the card
   shows official code, port it: copy the class/function, keep its names, adapt only the interfaces
   (our `x_dict` / `edge_index_dict`, channel sizes, `HeteroConv` per edge type). Do not re-derive from the equations
   what the code already implements.
3. Wire it behind a switch read from `cfg`, enable it in `PROPOSED_OVERRIDES`, and write the card id and the component
   in `PROPOSED_SOURCE`.
4. Keep the paper's hyperparameters unless they break the memory/time budget; say which ones you changed.
5. If the previous attempt failed (see REFINEMENT HISTORY), fix that error first instead of switching idea.
6. Never claim a component you did not implement; hypotheses and plans must cite the card they come from.
7. If the official code works on per-node token sequences instead of a graph batch, use
   `from rb_tokens import seed_token_sets`: `tok["tokens"]` ([B, K, C], seed first) is the input such code expects;
   use the output for the seed as its representation.
