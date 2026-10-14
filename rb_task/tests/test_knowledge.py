#!/usr/bin/env python3
"""Offline tests of the literature -> implementation-knowledge module (_arc_knowledge.py).

Needs PyMuPDF (in the Docker image) to build a small PDF; ARC_ROOT (default /app) for the pipeline's PDF reader
and skill registry. No network: downloads are replaced by a fake fetcher.
"""
import json
import logging
import os
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("ARC_ROOT", "/app"))
sys.path[:0] = [str(ROOT), str(HERE.parent / "patches")]
import _arc_knowledge as K  # noqa: E402

tmp = Path(tempfile.mkdtemp())

# 1) query e anno minimo
qf = tmp / "q.txt"
qf.write_text("# commento\nrelational deep learning\nGraph Neural\n", encoding="utf-8")
os.environ.update({"ARC_LIT_YEAR_MIN": "2010", "ARC_LIT_QUERIES_FILE": str(qf)})
q, y = K.adjust_queries(["graph neural", "binary classification"], 2020)
assert y == 2010 and q == ["relational deep learning", "Graph Neural", "binary classification"], (q, y)
print("OK 1: year_min 2020 -> 2010, query curate in testa, duplicati rimossi")

# 2) identificativi arXiv
assert K.arxiv_id_of({"doi": "10.48550/arxiv.2502.06784"}) == "2502.06784"
assert K.arxiv_id_of({"url": "https://arxiv.org/abs/2211.12792v2"}) == "2211.12792"
assert K.arxiv_id_of({"arxiv_id": "2407.20060"}) == "2407.20060"
assert K.arxiv_id_of({"doi": "10.1109/tnnls.2020.2978386"}) is None
print("OK 2: arXiv id da arxiv_id, DOI arXiv, URL arxiv.org")

# 3) PDF finto: sezioni e scelta delle parti
paper_text = {
    "Abstract": "We propose RelToy, a relational message passing scheme.",
    "1 Introduction": "Relational databases are everywhere. " * 40,
    "2 Related Work": "Many GNNs exist. " * 40,
    "3 Method": "RelToy computes h_v = max_{u in N(v)} W h_u + b for every edge type. " * 30,
    "4 Experiments": "On RelBench driver-top3 RelToy reaches 0.85 ROC-AUC with hidden size 128 and lr 0.005. " * 20,
    "5 Conclusion": "We conclude. " * 20,
}
import fitz  # noqa: E402

doc = fitz.open()
y_ = 72
page = doc.new_page()
for head, body in paper_text.items():
    for line in [head] + [body[i:i + 95] for i in range(0, len(body), 95)]:
        if y_ > 780:
            page, y_ = doc.new_page(), 72
        page.insert_text((50, y_), line, fontsize=9)
        y_ += 12
pdf_bytes = doc.tobytes()
text = K.pdf_text(K.Path(tmp / "x.pdf")) if False else None
(tmp / "probe.pdf").write_bytes(pdf_bytes)
full = K.pdf_text(tmp / "probe.pdf")
secs = K.split_sections(full)
heads = [h for h, _ in secs]
assert any("Method" in h for h in heads) and any("Experiments" in h for h in heads), heads
chunks = K.choose_chunks(secs, max_chunks=2, size=6000)
joined = " ".join(h for h, _ in chunks)
assert "Method" in joined and "Related" not in joined and "Conclusion" not in joined, joined
print("OK 3: testo dal PDF, sezioni", heads[:6], "-> parti scelte:", [h for h, _ in chunks])

# 4) download (finto) e costruzione delle schede
fetched = []
def fake_fetch(url):
    fetched.append(url)
    return pdf_bytes
p, how = K.fetch_pdf({"doi": "10.48550/arxiv.2502.06784", "title": "RelToy"}, tmp / "papers", fake_fetch)
assert p and p.name == "2502.06784.pdf" and fetched == ["https://arxiv.org/pdf/2502.06784"], (p, fetched)
p2, how2 = K.fetch_pdf({"title": "x"}, tmp / "papers", lambda u: b"<html>")
assert p2 is None
print("OK 4: PDF scaricato dall'id arXiv (", how, "); risposta non-PDF scartata")

run_dir = tmp / "run"
(run_dir / "stage-05").mkdir(parents=True)
repo = tmp / "repos" / "RelToy"
(repo / "examples").mkdir(parents=True)
(repo / "examples" / "reltoy_conv.py").write_text("class RelToyConv:\n    '''max over edge types'''\n    pass\n" * 5)
(repo / "setup.py").write_text("x = 1\n")
(repo / "README.md").write_text("# RelToy\nOfficial code of RelToy (arXiv 2502.06784).\n")
shortlist = [
    {"title": "A Comprehensive Survey on GNNs", "year": 2020, "abstract": "survey", "relevance_score": 0.9},
    {"title": "RelToy: Relational Max Passing", "year": 2025, "abstract": "We propose RelToy.", "doi": "10.48550/arxiv.2502.06784", "relevance_score": 0.8},
    {"title": "Other", "year": 2019, "abstract": "chemistry", "relevance_score": 0.5},
]
(run_dir / "stage-05" / "shortlist.jsonl").write_text("\n".join(json.dumps(r) for r in shortlist) + "\n")
(run_dir / "stage-05" / "code_repos.json").write_text(json.dumps({"repos": [
    {"paper_title": "RelToy: Relational Max Passing", "repo_url": "https://github.com/x/RelToy", "local_path": str(repo)}]}))
calls = []
def chat(llm, system, user, max_tokens=None, **kw):
    calls.append((system[:30], user))
    if "Pick up to" in user:
        return SimpleNamespace(content='<think>x</think>{"selected": [1], "reasons": {"1": "implementable"}}')
    if "Extract as bullet points" in user:
        return SimpleNamespace(content="- h_v = max_u W h_u (per edge type)\n- hidden 128, lr 0.005\n- driver-top3 ROC-AUC 0.85")
    return SimpleNamespace(content="#### What the method changes\nmax aggregation per edge type\n#### Components to implement\n1. RelToyConv\n"
                                   "#### Hyperparameters (paper values)\nhidden 128\n#### Reported results on RelBench\ndriver-top3 0.85\n"
                                   "#### How to port it to our project\nadd gnn_type 'reltoy'\n#### Risks\nnone")
know = tmp / "KNOWLEDGE.md"
os.environ.update({"ARC_KNOWLEDGE_FILE": str(know), "ARC_IMPL_CARDS_K": "1", "ARC_RUN_STARTED_AT": str(time.time() - 5), "ARC_REQUIRE_FULLTEXT": "0"})
stage6 = run_dir / "stage-06"
stage6.mkdir()
meta = K.build_knowledge(run_dir, stage6, SimpleNamespace(research=SimpleNamespace(topic="T")), object(), chat,
                         logging.getLogger("t"), fetch=fake_fetch)
kt = know.read_text()
assert meta["cards"][0]["title"].startswith("RelToy") and meta["cards"][0]["pdf"] and meta["cards"][0]["parts"], meta
assert "### [K1] RelToy" in kt and "arXiv 2502.06784" in kt and "code: https://github.com/x/RelToy" in kt
assert "reltoy_conv.py" in kt, "il codice ufficiale (examples/) deve essere nell'estratto"
assert "MUST be used" in kt and (stage6 / "impl_cards").is_dir() and (stage6 / "KNOWLEDGE.md").exists()
n_map = sum(1 for s, u in calls if "Extract as bullet points" in u)
assert n_map >= 1 and any("max u W h_u" in u or "h_v = max_u" in u for s, u in calls if "NOTES FROM THE FULL TEXT" in u)
assert (stage6 / "cards" / "K1_implementation_card.md").exists(), "la scheda deve arrivare anche alla sintesi (stage-06/cards)"
print(f"OK 5: scheda K1 dal testo completo ({n_map} parti lette) + codice ufficiale; il survey non e' stato scelto")

# 5) iniezione nei prompt e file vecchi ignorati
os.environ["ARC_KNOWLEDGE_STAGES"] = "hypothesis_gen,iterative_improve"
assert "### [K1]" in K.knowledge_for("iterative_improve") and "### [K1]" in K.knowledge_for("hypothesis_gen")
assert K.knowledge_for("paper_draft") == ""
assert K.knowledge_ids() == ["K1"]
os.environ["ARC_RUN_STARTED_AT"] = str(time.time() + 3600)
assert K.knowledge_for("hypothesis_gen") == "" and K.knowledge_ids() == []
os.environ["ARC_RUN_STARTED_AT"] = str(time.time() - 5)
know.touch()
print("OK 6: conoscenza iniettata solo negli stage previsti; file di una run precedente ignorato")

# 6) riferimento alla scheda (modalita' codice)
good = {"rb_config.py": 'PROPOSED_OVERRIDES = {"gnn_type": "reltoy"}\nPROPOSED_SOURCE = "K1: RelToyConv"\n'}
assert K.knowledge_ref_ok(good) == (True, "")
assert not K.knowledge_ref_ok({"rb_config.py": 'PROPOSED_SOURCE = ""\n'})[0]
assert not K.knowledge_ref_ok({"rb_config.py": 'PROPOSED_SOURCE = "K7: x"\n'})[0]
assert K.proposed_source(good["rb_config.py"]) == "K1: RelToyConv"
assert K.knowledge_ref_ok({"rb_config.py": 'PROPOSED_SOURCE = "K1: GATv2 attention with LayerNorm"\n'})[0]   # default: codice generico ammesso
os.environ["ARC_REQUIRE_COMPONENT_MATCH"] = "1"
assert not K.knowledge_ref_ok({"rb_config.py": 'PROPOSED_SOURCE = "K1: GATv2 attention with LayerNorm"\n'})[0]   # modalita' severa
os.environ["ARC_REQUIRE_COMPONENT_MATCH"] = "0"
assert K.knowledge_ref_ok({"rb_config.py": 'PROPOSED_SOURCE = "K1: RelToyConv"\n'})[0]
assert K.github_links("see github.com/snap-stanford/relgt. and https://github.com/snap-stanford/relbench") == ["https://github.com/snap-stanford/relgt"]
print("OK 7: PROPOSED_SOURCE deve citare una scheda esistente e un componente descritto in quella scheda; link al codice dal PDF")
# 8) codice ufficiale importabile: vendoring di un repo finto con import interni e un modulo con dipendenza mancante
repo2 = tmp / "repos" / "toyrepo"
repo2.mkdir(parents=True)
(repo2 / "layers.py").write_text(
    "import torch\n"
    "class ToyLayer(torch.nn.Module):\n"
    "    \"\"\"A toy layer.\"\"\"\n"
    "    def __init__(self, dim):\n"
    "        super().__init__()\n"
    "        self.lin = torch.nn.Linear(dim, dim)\n"
    "    def forward(self, x):\n"
    "        return self.lin(x)\n")
(repo2 / "model.py").write_text(
    "from layers import ToyLayer\n"
    "import layers\n"
    "class ToyNet(ToyLayer):\n"
    "    def forward(self, x, edge_index):\n"
    "        return layers.ToyLayer.forward(self, x)\n")
(repo2 / "needs_missing.py").write_text("import surely_not_installed_pkg\n")
(repo2 / "train.py").write_text("print('entry point')\n")
vout = tmp / "vendor"
v = K.vendor_repo(repo2, "toy", vout, "https://github.com/x/toyrepo")
assert sorted(v["files"]) == ["vendor_toy_layers.py", "vendor_toy_model.py"], sorted(v["files"])
assert "needs_missing.py" in v["skipped"] and "train.py" not in v["files"]
src = v["files"]["vendor_toy_model.py"]
assert "from vendor_toy_layers import ToyLayer" in src and "import vendor_toy_layers as layers" in src
import importlib
sys.path.insert(0, str(vout))
net = importlib.import_module("vendor_toy_model").ToyNet(4)
assert tuple(net(__import__("torch").zeros(2, 4), None).shape) == (2, 4)
cm = K.code_map(v["files"])
assert "class `ToyLayer`: __init__(dim); forward(x) - A toy layer." in cm and "from vendor_toy_model import" in cm, cm
os.environ["ARC_PROMPT_HIDE_FILES"] = "rb_model_official.py"
assert K.hidden_file("vendor_toy_model.py") and K.hidden_file("rb_model_official.py") and not K.hidden_file("rb_model.py")
print("OK 8: codice ufficiale importabile (import interni riscritti, dipendenze mancanti e script esclusi), mappa del codice, file nascosti al prompt")
# 9) un repository trovato da una ricerca vale solo se appartiene al paper
rp = tmp / "repos" / "Relphormer"; rp.mkdir(parents=True)
(rp / "README.md").write_text("# Relphormer\nCode for the paper Relphormer: Relational Graph Transformer for Knowledge Graph Representations (arXiv 2205.10852)\n")
assert not K.repo_matches_paper(rp, "2505.10960", "Relational Graph Transformer", ["https://github.com/snap-stanford/relgt"], "https://github.com/zjunlp/Relphormer.git")
rg = tmp / "repos" / "relgt"; rg.mkdir(parents=True)
(rg / "README.md").write_text("# RelGT\nOfficial code of Relational Graph Transformer, https://arxiv.org/abs/2505.10960\n")
assert K.repo_matches_paper(rg, "2505.10960", "Relational Graph Transformer", [], "https://github.com/snap-stanford/relgt")
assert K.repo_matches_paper(rp, None, "x", ["https://github.com/zjunlp/Relphormer"], "https://github.com/zjunlp/Relphormer.git")
print("OK 9: repository di un altro paper scartato (caso RelGT -> Relphormer); accettato se il README cita l'id arXiv o se il PDF lo linka")
# 10) solo paper con testo completo: quelli senza versione arXiv vengono scartati prima della scelta
os.environ["ARC_REQUIRE_FULLTEXT"] = "1"
K.arxiv_search_title = lambda title: "2501.00001" if "Found" in title else None
seen = {}
def chat_sel(llm, system, user, max_tokens=None, **kw):
    if "Pick up to" in user:
        seen["prompt"] = user
        return SimpleNamespace(content='{"selected": [0]}')
    return SimpleNamespace(content="#### What the method changes\nx")
run2 = tmp / "run2"; (run2 / "stage-05").mkdir(parents=True)
(run2 / "stage-05" / "shortlist.jsonl").write_text("\n".join(json.dumps(r) for r in [
    {"title": "Abstract Only Paper", "year": 2026, "abstract": "a", "doi": "10.1109/x"},
    {"title": "Found On arXiv By Title", "year": 2025, "abstract": "b"}]) + "\n")
st6 = run2 / "stage-06"; st6.mkdir()
m2 = K.build_knowledge(run2, st6, SimpleNamespace(research=SimpleNamespace(topic="T")), object(), chat_sel,
                       logging.getLogger("t"), fetch=lambda u: b"<html>")
assert m2["discarded_no_fulltext"] == ["Abstract Only Paper"] and "Abstract Only Paper" not in seen["prompt"]
assert m2["cards"][0]["title"] == "Found On arXiv By Title"
print("OK 10: paper con il solo abstract scartati; quelli trovati su arXiv per titolo tenuti")
print("KNOWLEDGE TESTS PASSED")

# 11) stage 3: le query scritte dall'LLM vengono recuperate (nessuna query umana)
payload = {"sources": [{"id": "s1", "query": "RelBench graph neural networks"},
                       {"id": "s2", "query": "tabular feature encoding GNNs"},
                       {"id": "s3", "query": "temporal message passing relational data"}],
           "search_plan_yaml": "this is : not : valid : yaml : ["}
plan = K.rescue_plan(payload, "", "T")
qs = plan["search_strategies"][0]["queries"]
assert qs == ["RelBench graph neural networks", "tabular feature encoding GNNs", "temporal message passing relational data"], qs
assert plan["filters"]["min_year"] == 2010 and plan["recovered_from_llm_answer"]
plan2 = K.rescue_plan({"search_plan_yaml": {"search_strategies": [{"queries": ["a b", "c d", "e f g"]}]}}, "", "T")
assert plan2["search_strategies"][0]["queries"] == ["a b", "c d", "e f g"]
assert K.rescue_plan({"sources": []}, "nothing here", "T") is None
print("OK 11: query dell'LLM recuperate dalla risposta dello stage 3 (nessuna query scritta da noi)")
print("KNOWLEDGE TESTS PASSED")
