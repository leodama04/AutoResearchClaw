"""Literature -> implementation knowledge for the code-writing stages.

Stage 6 (KNOWLEDGE_EXTRACT) only summarises abstracts. This module adds, at the end of stage 6:
  1. choice of the K shortlisted papers most useful to IMPLEMENT model improvements (LLM, with fallback);
  2. download of their full text (arXiv PDF, using the arXiv id / arXiv DOI or an arXiv title search);
  3. section-by-section reading of each paper, one paper at a time (map: notes per section);
  4. an IMPLEMENTATION CARD per paper (reduce), linked to the official code cloned at stage 5;
  5. KNOWLEDGE.md = rules + cards + official code excerpts, written to ARC_KNOWLEDGE_FILE.
`knowledge_for(name)` returns that text (plus matching project skills for stage 13) for the prompts of the
stages that write code or hypotheses; it is injected by the PromptManager patch.

Env: ARC_KNOWLEDGE_FILE, ARC_IMPL_CARDS_K (4), ARC_IMPL_MAX_CHUNKS (4), ARC_KNOWLEDGE_MAX_CHARS (26000),
ARC_KNOWLEDGE_STAGES, ARC_RUN_STARTED_AT (epoch; older knowledge files are ignored), ARC_EXTRA_REPOS,
ARC_LIT_YEAR_MIN, ARC_LIT_QUERIES_FILE.
"""

from __future__ import annotations

import difflib
import json
import os
import re
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Callable
from urllib.parse import quote
from urllib.request import Request, urlopen

_UA = "Mozilla/5.0 (AutoResearchClaw knowledge builder; research use)"
_THINK = re.compile(r"<think>.*?</think>", re.DOTALL)
_ARXIV_ID = re.compile(r"(\d{4}\.\d{4,5})(v\d+)?", re.I)

DEFAULT_STAGES = (
    "synthesis,hypothesis_gen,hypothesis_synthesize,experiment_design,code_generation,"
    "iterative_improve,iterative_repair,code_repair,code_exec_fix"
)


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


# ============================================================================ literature search knobs
def adjust_queries(queries: list, year_min: int) -> tuple[list, int]:
    """Stage 4: ARC_LIT_YEAR_MIN overrides the year filter; ARC_LIT_QUERIES_FILE adds curated queries first."""
    try:
        if _env("ARC_LIT_YEAR_MIN"):
            year_min = int(_env("ARC_LIT_YEAR_MIN"))
    except ValueError:
        pass
    extra: list[str] = []
    path = _env("ARC_LIT_QUERIES_FILE")
    if path and Path(path).is_file():
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                extra.append(line)
    seen, out = set(), []
    for q in extra + [str(q) for q in (queries or [])]:
        key = q.lower().strip()
        if key and key not in seen:
            seen.add(key)
            out.append(q)
    return out, year_min


def rescue_plan(payload, text: str, topic: str) -> dict | None:
    """Stage 3: the LLM writes its search queries, but the pipeline only accepts them inside a YAML string
    ('search_plan_yaml'); when that string is missing or malformed it replaces them with pieces of the topic title.
    Recover the LLM's own queries from wherever they are in its answer (no human-written queries are added)."""
    import yaml as _yaml

    found: list[str] = []

    def add(q):
        if isinstance(q, str):
            q = " ".join(q.split())
            if 2 <= len(q.split()) <= 12 and q.lower() not in {x.lower() for x in found}:
                found.append(q)

    def walk(o):
        if isinstance(o, dict):
            spy = o.get("search_plan_yaml")
            if isinstance(spy, dict):
                walk(spy)
            for key, val in o.items():
                if key in ("queries", "query", "search_queries", "keywords", "search_terms", "search_strings"):
                    for q in (val if isinstance(val, list) else [val]):
                        add(q)
                else:
                    walk(val)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(payload if isinstance(payload, (dict, list)) else {})
    if len(found) < 3 and text:  # YAML anywhere in the raw answer
        for block in re.findall(r"```(?:yaml)?\s*\n(.*?)```", text, re.DOTALL):
            try:
                walk(_yaml.safe_load(block))
            except Exception:  # noqa: BLE001
                continue
    if len(found) < 3:
        return None
    try:
        year = int(_env("ARC_LIT_YEAR_MIN") or 2010)
    except ValueError:
        year = 2010
    return {
        "topic": topic,
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "search_strategies": [
            {"name": "llm_queries", "queries": found[:8], "sources": ["arxiv", "semantic_scholar", "openreview"],
             "max_results_per_query": 60},
            {"name": "llm_queries_more", "queries": found[8:14] or found[:3], "sources": ["semantic_scholar"], "depth": 1},
        ],
        "filters": {"min_year": year, "language": ["en"], "peer_review_preferred": True},
        "deduplication": {"method": "title_doi_hash", "fuzzy_threshold": 0.9},
        "recovered_from_llm_answer": True,
    }


# ============================================================================ helpers
def _slug(text: str, n: int = 40) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:n] or "paper"


def arxiv_id_of(paper: dict) -> str | None:
    """arXiv id from arxiv_id, an arXiv DOI (10.48550/arXiv.XXXX) or an arxiv.org URL."""
    for key in ("arxiv_id", "doi", "url", "pdf_url"):
        val = str(paper.get(key) or "")
        if not val:
            continue
        if key == "arxiv_id" or "arxiv" in val.lower():
            m = _ARXIV_ID.search(val)
            if m:
                return m.group(1)
    return None


def _http_get(url: str, timeout: int = 60, max_bytes: int = 40_000_000) -> bytes:
    try:
        from researchclaw.web._ssrf import check_url_ssrf  # reuse the pipeline's own guard

        err = check_url_ssrf(url)
        if err:
            raise ValueError(err)
    except ImportError:
        pass
    req = Request(url, headers={"User-Agent": _UA})
    with urlopen(req, timeout=timeout) as resp:  # noqa: S310
        data = resp.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ValueError("file too large")
    return data


def arxiv_search_title(title: str) -> str | None:
    """arXiv API title search; returns the id of a near-identical title."""
    q = quote(f'ti:"{title[:200]}"')
    url = f"http://export.arxiv.org/api/query?search_query={q}&max_results=5"
    try:
        xml = _http_get(url, timeout=30, max_bytes=2_000_000)
        root = ET.fromstring(xml)
    except Exception:  # noqa: BLE001
        return None
    ns = {"a": "http://www.w3.org/2005/Atom"}
    best, best_r = None, 0.0
    for entry in root.findall("a:entry", ns):
        t = " ".join((entry.findtext("a:title", default="", namespaces=ns) or "").split())
        r = difflib.SequenceMatcher(None, t.lower(), title.lower()).ratio()
        m = _ARXIV_ID.search(entry.findtext("a:id", default="", namespaces=ns) or "")
        if m and r > best_r:
            best, best_r = m.group(1), r
    return best if best_r >= 0.9 else None


def fetch_pdf(paper: dict, out_dir: Path, fetch: Callable[[str], bytes] | None = None) -> tuple[Path | None, str]:
    """Download the paper's PDF (arXiv). Returns (path or None, source description)."""
    fetch = fetch or _http_get
    out_dir.mkdir(parents=True, exist_ok=True)
    aid = arxiv_id_of(paper)
    how = "arXiv id from metadata"
    if not aid:
        aid = arxiv_search_title(str(paper.get("title", "")))
        how = "arXiv title search"
    if not aid:
        return None, "no arXiv version found"
    path = out_dir / f"{aid}.pdf"
    if path.is_file() and path.stat().st_size > 10_000:
        return path, f"{how} (cached)"
    try:
        data = fetch(f"https://arxiv.org/pdf/{aid}")
    except Exception as exc:  # noqa: BLE001
        return None, f"download failed: {exc}"
    if not data[:5] == b"%PDF-":
        return None, "download is not a PDF"
    path.write_bytes(data)
    time.sleep(1.0)  # be gentle with arXiv
    return path, how


_HEAD = re.compile(r"(?:^|\n)\s*((?:\d{1,2}|[A-H])(?:\.\d{1,2})?\.?\s+[A-Z][^\n]{2,70})\s*\n")
_KEEP = ("method", "model", "approach", "architecture", "framework", "propos", "message", "layer", "encod",
         "aggregat", "attention", "transformer", "algorithm", "design", "implementation", "detail",
         "hyperparam", "setup", "training", "experiment", "result", "ablation", "relbench", "complexity")
_SKIP = ("related", "conclusion", "acknowledg", "reference", "limitation", "broader", "impact", "ethic",
         "future", "checklist", "introduction", "background", "preliminar")


_GH = re.compile(r"github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)")
_INFRA = {"snap-stanford/relbench", "pyg-team/pytorch_geometric", "pytorch/pytorch", "kumo-ai/pytorch-frame",
          "huggingface/transformers"}


def github_links(text: str) -> list[str]:
    """Official-code links written in the paper (e.g. 'code at github.com/snap-stanford/relgt')."""
    out: list[str] = []
    for owner, repo in _GH.findall(text or ""):
        repo = repo.rstrip(".").removesuffix(".git")
        key = f"{owner}/{repo}".lower()
        if key in _INFRA or not repo:
            continue
        url = f"https://github.com/{owner}/{repo}"
        if url not in out:
            out.append(url)
    return out


def pdf_text(path: Path) -> str:
    try:
        from researchclaw.web.pdf_extractor import PDFExtractor  # the pipeline's own PDF reader

        content = PDFExtractor(extract_sections=False).extract(path)
        return getattr(content, "text", "") or ""
    except Exception:  # noqa: BLE001
        try:
            import fitz  # PyMuPDF

            with fitz.open(str(path)) as doc:
                return "\n".join(page.get_text() for page in doc)
        except Exception:  # noqa: BLE001
            return ""


def split_sections(text: str) -> list[tuple[str, str]]:
    """(heading, body) pairs; one pseudo-section if no numbered heading is found."""
    text = text.split("\nReferences\n")[0].split("\nREFERENCES\n")[0]
    marks = list(_HEAD.finditer(text))
    if len(marks) < 3:
        return [("full text", text)]
    out = [("preamble", text[: marks[0].start()])]
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        out.append((m.group(1).strip(), text[m.end():end]))
    return out


def choose_chunks(sections: list[tuple[str, str]], max_chunks: int = 4, size: int = 10_000) -> list[tuple[str, str]]:
    """Method / implementation / results sections first, merged into chunks of <= size chars."""
    def prio(h: str) -> int:
        hl = h.lower()
        if any(k in hl for k in _SKIP):
            return 9
        if any(k in hl for k in ("method", "model", "approach", "architecture", "framework", "propos", "message")):
            return 0
        if any(k in hl for k in _KEEP):
            return 1
        return 2 if hl not in ("preamble",) else 3

    if len(sections) == 1:
        body = sections[0][1]
        return [(f"part {i // size + 1}", body[i:i + size]) for i in range(0, min(len(body), size * max_chunks), size)]
    ranked = sorted(((prio(h), i, h, b) for i, (h, b) in enumerate(sections)), key=lambda x: (x[0], x[1]))
    picked = sorted([r for r in ranked if r[0] < 9][: max_chunks * 3], key=lambda x: x[1])
    chunks: list[tuple[str, str]] = []
    cur_h, cur_b = [], ""
    for _, _, h, b in picked:
        b = b.strip()
        if len(b) > size:
            b = b[:size]
        if cur_b and len(cur_b) + len(b) > size:
            chunks.append((" / ".join(cur_h), cur_b))
            cur_h, cur_b = [], ""
        cur_h.append(h)
        cur_b += f"\n\n## {h}\n{b}"
    if cur_b:
        chunks.append((" / ".join(cur_h), cur_b))
    return chunks[:max_chunks]


def _chat(chat, llm, system: str, user: str, max_tokens: int) -> str:
    try:
        resp = chat(llm, system, user, max_tokens=max_tokens)
    except TypeError:
        resp = chat(llm, system, user)
    return _THINK.sub("", getattr(resp, "content", "") or "").strip()


# ============================================================================ paper selection
def select_papers(shortlist: list[dict], repos: list[dict], k: int, llm, chat, topic: str) -> list[dict]:
    has_code = {str(r.get("paper_title", "")).lower() for r in repos}
    rows = []
    for i, p in enumerate(shortlist):
        code = str(p.get("title", "")).lower() in has_code
        full = bool(arxiv_id_of(p))
        rows.append(f"[{i}] ({p.get('year')}) {p.get('title')}{'  [official code available]' if code else ''}"
                    f"{'  [full text on arXiv]' if full else '  [abstract only]'}\n"
                    f"     {str(p.get('abstract') or '')[:500]}")
    chosen: list[int] = []
    if llm is not None and rows:
        system = "You select research papers for an engineer who must IMPLEMENT model improvements. Reply with JSON only."
        user = (f"Topic: {topic}\n\nThe engineer will modify a heterogeneous GNN (the official RelBench RDL model: "
                "PyTorch-Frame column encoders + relative-time encoding + GraphSAGE message passing over the database "
                "graph + MLP head) to improve ROC-AUC on RelBench rel-f1 / driver-top3.\n\nCandidate papers:\n"
                + "\n".join(rows)
                + f"\n\nPick up to {k} papers whose METHODS contain concrete, implementable components for that model "
                  "(concrete, implementable model components), preferring papers whose "
                  "full text is on arXiv and papers with official code, and papers that report results on RelBench. "
                  "Avoid surveys, data-augmentation/retrieval pipelines that need external models, and other domains.\n"
                  'Reply: {"selected": [indices], "reasons": {"index": "why"}}')
        text = _chat(chat, llm, system, user, 2000)
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                sel = json.loads(m.group(0)).get("selected", [])
                chosen = [int(i) for i in sel if str(i).lstrip("-").isdigit() and 0 <= int(i) < len(shortlist)]
            except (ValueError, TypeError):
                chosen = []
    if not chosen:  # fallback: official code first, then relevance; no surveys
        order = sorted(
            range(len(shortlist)),
            key=lambda i: (
                "survey" in str(shortlist[i].get("title", "")).lower(),
                str(shortlist[i].get("title", "")).lower() not in has_code,
                -float(shortlist[i].get("relevance_score") or 0),
            ),
        )
        chosen = order
    out, seen = [], set()
    for i in chosen:
        if i not in seen:
            seen.add(i)
            out.append(shortlist[i])
        if len(out) >= k:
            break
    return out


# ============================================================================ official code: find, vendor, map
_LISTY = ("arxiv", "daily", "paper", "awesome", "list", "survey", "reading", "collection", "digest")


def find_repo_by_arxiv(aid: str) -> str | None:
    """GitHub search for repositories whose README mentions the arXiv id (official repos usually do)."""
    if not aid:
        return None
    url = f"https://api.github.com/search/repositories?q=%22{aid}%22+in:readme&sort=stars&order=desc&per_page=10"
    headers = {"User-Agent": _UA, "Accept": "application/vnd.github+json"}
    if _env("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {_env('GITHUB_TOKEN')}"
    try:
        with urlopen(Request(url, headers=headers), timeout=30) as resp:  # noqa: S310
            items = json.loads(resp.read().decode("utf-8")).get("items", [])
    except Exception:  # noqa: BLE001
        return None
    for it in items:
        name = str(it.get("full_name", ""))
        if not name or any(k in name.lower() for k in _LISTY) or it.get("fork"):
            continue
        return f"https://github.com/{name}"
    return None


_ENTRY = re.compile(r"^(main|train|run|setup|test|eval|demo|example|benchmark|preprocess|download)|_ddp|_test", re.I)


def _imports_ok(src: str, local: set[str]) -> tuple[bool, list[str]]:
    import ast
    import importlib.util

    try:
        tree = ast.parse(src)
    except SyntaxError:
        return False, ["syntax error"]
    missing = []
    for node in tree.body:
        mods = []
        if isinstance(node, ast.Import):
            mods = [a.name.split(".")[0] for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            mods = [node.module.split(".")[0]]
        for m in mods:
            if m in local:
                continue
            try:
                if importlib.util.find_spec(m) is None:
                    missing.append(m)
            except (ImportError, ValueError):
                missing.append(m)
    return not missing, missing


def _is_script(src: str) -> bool:
    """True for a command-line script: argparse parser built or parse_args() called at module level
    (e.g. RelGNN's examples/gnn_node.py). Importing such a file would parse argv and start training."""
    import ast

    try:
        tree = ast.parse(src)
    except SyntaxError:
        return False
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom)):
            continue
        if isinstance(node, ast.If) and "__main__" in ast.dump(node.test):
            continue
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call):
                fn = sub.func
                name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
                if name in ("ArgumentParser", "parse_args", "parse_known_args"):
                    return True
    return False


def _installed_copy(path: Path, repo_dir: Path, installed: Callable[[str], bool] | None = None) -> str:
    """Name of an installed package of which `path` is a copy (a directory of the repo with __init__.py named like an
    importable package, e.g. the `relbench/` fork shipped inside the RelGNN repo); '' otherwise."""
    import importlib.util

    if installed is None:
        def installed(name: str) -> bool:
            try:
                return importlib.util.find_spec(name) is not None
            except (ImportError, ValueError):
                return False
    rel = Path(path).relative_to(repo_dir).parts[:-1]
    cur = Path(repo_dir)
    for part in rel:
        cur = cur / part
        if (cur / "__init__.py").is_file() and part.isidentifier() and installed(part):
            return part
        break  # only top-level package directories of the repo
    return ""


def visible_files(files: dict) -> dict:
    """Project files shown in stage-13 prompts (improve AND repair): hidden files (vendored official code, frozen
    baseline model, loaders) are left out - they are read-only and their API is in the knowledge block."""
    return {k: v for k, v in (files or {}).items() if not hidden_file(k)}


def vendor_repo(repo_dir: Path, tag: str, out_dir: Path, repo_url: str = "", max_total: int | None = None,
                installed: Callable[[str], bool] | None = None) -> dict:
    """Copy the model modules of an official repository as importable flat files vendor_<tag>_<module>.py.

    Training/entry scripts and modules whose imports are not installed are skipped; intra-repo imports are
    rewritten. The LLM can then IMPORT the official classes instead of re-implementing them."""
    if max_total is None:
        try:
            max_total = int(_env("ARC_VENDOR_MAX_CHARS", "100000"))
        except ValueError:
            max_total = 100_000
    out_dir.mkdir(parents=True, exist_ok=True)
    cands = [p for p in sorted(Path(repo_dir).rglob("*.py"))
             if ".git" not in p.parts and "tests" not in p.parts and not _ENTRY.search(p.stem)
             and p.stem != "__init__" and p.stat().st_size < 60_000]
    skipped: dict = {}
    keep = []
    for p in cands:  # copies of installed libraries and command-line scripts are not model code
        pkg = _installed_copy(p, Path(repo_dir), installed)
        if pkg:
            skipped[str(p.relative_to(repo_dir))] = f"copy of the installed package '{pkg}'"
            continue
        if _is_script(p.read_text(encoding="utf-8", errors="replace")):
            skipped[str(p.relative_to(repo_dir))] = "command-line script (argparse at module level)"
            continue
        keep.append(p)
    cands = keep
    local = {p.stem for p in cands}
    vendored, total = {}, 0
    for p in cands:
        src = p.read_text(encoding="utf-8", errors="replace")
        ok, missing = _imports_ok(src, local)
        if not ok:
            skipped[p.name] = f"needs {missing}"
            continue
        try:
            from researchclaw.experiment.validator import validate_code

            if not validate_code(src).ok:
                skipped[p.name] = "rejected by the pipeline's code validator"
                continue
        except ImportError:
            pass
        if total + len(src) > max_total:
            skipped[p.name] = "size budget"
            continue
        vendored[p.stem] = src
        total += len(src)
    files = {}
    for stem, src in vendored.items():
        for other in vendored:
            new = f"vendor_{tag}_{other}"
            src = re.sub(rf"^(\s*)from {re.escape(other)} import ", rf"\1from {new} import ", src, flags=re.M)
            src = re.sub(rf"^(\s*)import {re.escape(other)}\s*$", rf"\1import {new} as {other}", src, flags=re.M)
        name = f"vendor_{tag}_{stem}.py"
        header = f"# Vendored (read-only) from {repo_url or repo_dir} - official code of the paper. Do not edit.\n"
        (out_dir / name).write_text(header + src, encoding="utf-8")
        files[name] = header + src
    return {"files": files, "skipped": skipped}


def code_map(files: dict) -> str:
    """Classes / functions with their signatures and first docstring line, and how to import them."""
    import ast

    out = []
    for name, src in sorted(files.items()):
        mod = name[:-3]
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        items = []
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                sigs = []
                for fn in node.body:
                    if isinstance(fn, ast.FunctionDef) and fn.name in ("__init__", "forward"):
                        args = [a.arg for a in fn.args.args if a.arg != "self"]
                        sigs.append(f"{fn.name}({', '.join(args)})")
                doc = (ast.get_docstring(node) or "").strip().splitlines()[:1]
                items.append(f"  - class `{node.name}`: {'; '.join(sigs)}{' - ' + doc[0][:100] if doc else ''}")
            elif isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                args = [a.arg for a in node.args.args]
                items.append(f"  - def `{node.name}({', '.join(args)})`")
        if items:
            out.append(f"- `{name}` -> `from {mod} import ...`\n" + "\n".join(items[:12]))
    return "\n".join(out)


def hidden_file(name: str) -> bool:
    """Files kept out of the stage-13 prompt (frozen official model, loaders, vendored official code)."""
    names = [x.strip() for x in _env("ARC_PROMPT_HIDE_FILES").split(",") if x.strip()]
    prefixes = [x.strip() for x in _env("ARC_PROMPT_HIDE_PREFIXES", "vendor_").split(",") if x.strip()]
    return name in names or any(name.startswith(p) for p in prefixes)


# ============================================================================ cards
_MAP_SYS = ("You read one part of a machine-learning paper and extract ONLY what an engineer needs to implement the "
            "method. Be precise and concise. Never invent numbers.")
_RED_SYS = ("You write implementation cards that let an engineer re-implement a paper's method inside an existing "
            "PyTorch Geometric code base. Never invent numbers or components that are not in the notes or the code.")


def map_chunk(chat, llm, title: str, heading: str, body: str) -> str:
    user = (f"Paper: {title}\nPart: {heading}\n\n{body}\n\n"
            "Extract as bullet points: model components and how they are computed (equations in LaTeX or plain text, "
            "inputs/outputs, tensor shapes), algorithm steps, hyperparameters with their values, training details, "
            "results on RelBench tasks (task, metric, value) and on rel-f1 if present, and implementation caveats. "
            "If this part has nothing implementable, reply NONE.")
    return _chat(chat, llm, _MAP_SYS, user, 3000)


def reduce_card(chat, llm, paper: dict, notes: list[str], code: str, card_id: str) -> str:
    user = (f"Card id: {card_id}\nPaper: {paper.get('title')} ({paper.get('year')})\n"
            f"Abstract: {str(paper.get('abstract') or '')[:1200]}\n\nNOTES FROM THE FULL TEXT (section by section):\n"
            + ("\n\n".join(n for n in notes if n and n.strip().upper() != "NONE") or "(full text not available)")
            + (f"\n\nOFFICIAL CODE (excerpt):\n{code}" if code else "")
            + "\n\nWrite the implementation card in markdown with exactly these headings:\n"
              "#### What the method changes\n#### Components to implement\n(numbered; for each: purpose, inputs/outputs, "
              "equations, where it plugs into our model: column encoder, temporal encoding, message passing, readout, "
              "loss/training)\n#### Hyperparameters (paper values)\n#### Reported results on RelBench\n(only numbers "
              "present in the notes; otherwise 'not reported')\n#### How to port it to our project\n(our model: "
              "rb_model.py with HeteroConv over edge types, x_dict / edge_index_dict, build_model(data, col_stats_dict, "
              "cfg, out_channels); a new option is activated through rb_config.PROPOSED_OVERRIDES, e.g. "
              "{\"gnn_type\": \"<new name>\"}; refer to the functions of the official code when given)\n"
              "#### Risks\n(memory, run time, compatibility)\nAt most 3500 characters.")
    return _chat(chat, llm, _RED_SYS, user, 6000)


def _clone(url: str, dest: Path) -> Path | None:
    if dest.is_dir():
        return dest
    try:
        subprocess.run(["git", "clone", "--depth", "1", url, str(dest)], check=True,
                       capture_output=True, timeout=180)
        return dest
    except Exception:  # noqa: BLE001
        return None


def repo_matches_paper(repo_dir: Path, aid: str | None, title: str, pdf_links: list[str], url: str) -> bool:
    """A repository found by a search is accepted only if the paper links it, or its README cites the
    paper's arXiv id or exact title (stage 5 once matched RelGT to Relphormer, a different paper)."""
    if any(url.rstrip("/").removesuffix(".git").lower() == l.lower() for l in pdf_links):
        return True
    text = ""
    for name in ("README.md", "README.rst", "README.txt", "README"):
        p = Path(repo_dir) / name
        if p.is_file():
            text = p.read_text(encoding="utf-8", errors="replace").lower()
            break
    if aid and aid in text:
        return True
    # a short title is a prefix of other titles ("Relational Graph Transformer" vs "Relphormer: Relational Graph
    # Transformer for Knowledge Graph ..."): the title alone is accepted only when it is long and specific
    t = re.sub(r"\s+", " ", (title or "").lower()).strip()
    return bool(t) and len(t.split()) >= 6 and t in re.sub(r"\s+", " ", text)


def code_for(paper: dict, repos: list[dict], run_dir: Path) -> tuple[str, str]:
    """(repo url, code excerpt) of the paper's official repository, if cloned at stage 5."""
    title = str(paper.get("title", "")).lower()
    for r in repos:
        if str(r.get("paper_title", "")).lower() == title:
            local = Path(str(r.get("local_path", "")))
            if not local.is_absolute():
                local = Path.cwd() / local
            try:
                from researchclaw.pipeline.stage_impls._repo_context import repo_source_excerpts

                ex = repo_source_excerpts(local, max_files=3, max_chars_per_file=3500, max_total_chars=7000)
            except Exception:  # noqa: BLE001
                ex = ""
            return str(r.get("repo_url", "")), ex
    return "", ""


def build_knowledge(run_dir, stage_dir, config, llm, chat, logger, fetch=None) -> dict:
    """Entry point called at the end of stage 6."""
    out_file = _env("ARC_KNOWLEDGE_FILE")
    run_dir, stage_dir = Path(run_dir), Path(stage_dir)
    meta: dict[str, Any] = {"cards": [], "started": time.strftime("%Y-%m-%dT%H:%M:%S")}
    if not out_file or llm is None:
        return meta
    k = int(_env("ARC_IMPL_CARDS_K", "4") or 4)
    max_chunks = int(_env("ARC_IMPL_MAX_CHUNKS", "4") or 4)
    budget = int(_env("ARC_KNOWLEDGE_MAX_CHARS", "26000") or 26000)
    topic = getattr(getattr(config, "research", None), "topic", "")
    shortlist = []
    sl = run_dir / "stage-05" / "shortlist.jsonl"
    if sl.is_file():
        shortlist = [json.loads(l) for l in sl.read_text(encoding="utf-8").splitlines() if l.strip()]
    repos = []
    cr = run_dir / "stage-05" / "code_repos.json"
    if cr.is_file():
        try:
            repos = json.loads(cr.read_text(encoding="utf-8")).get("repos", [])
        except ValueError:
            repos = []
    for url in [u.strip() for u in _env("ARC_EXTRA_REPOS").split(",") if u.strip()]:
        dest = _clone(url, stage_dir / "extra_repos" / _slug(url.rstrip("/").split("/")[-1]))
        if dest:
            repos.append({"paper_title": "", "repo_url": url, "local_path": str(dest), "extra": True})
    if _env("ARC_REQUIRE_FULLTEXT", "1") == "1":  # arXiv has the full text: abstract-only papers are discarded
        full_text = []
        for p in shortlist:
            aid = arxiv_id_of(p) or arxiv_search_title(str(p.get("title", "")))
            if aid:
                p = dict(p)
                p.setdefault("arxiv_id", aid)
                full_text.append(p)
            else:
                meta.setdefault("discarded_no_fulltext", []).append(p.get("title"))
        shortlist = full_text
    selected = select_papers(shortlist, repos, k, llm, chat, topic)
    cards_dir = stage_dir / "impl_cards"
    cards_dir.mkdir(parents=True, exist_ok=True)
    blocks: list[str] = []
    per_card = max(2500, (budget - 2500) // max(1, len(selected) + len([r for r in repos if r.get("extra")])))
    for i, paper in enumerate(selected, 1):
        cid = f"K{i}"
        t0 = time.time()
        pdf, how = fetch_pdf(paper, stage_dir / "papers", fetch)
        full = pdf_text(pdf) if pdf else ""
        sections = split_sections(full) if full else []
        chunks = choose_chunks(sections, max_chunks=max_chunks) if sections else []
        notes = [map_chunk(chat, llm, str(paper.get("title")), h, b) for h, b in chunks]
        repo_url, code = code_for(paper, repos, run_dir)
        repo_dir = None
        pdf_links = github_links(full)
        if repo_url:
            repo_dir = next((Path(str(r.get("local_path"))) for r in repos if r.get("repo_url") == repo_url), None)
            local = repo_dir if (repo_dir is None or repo_dir.is_absolute()) else Path.cwd() / repo_dir
            if not repo_matches_paper(local, arxiv_id_of(paper), str(paper.get("title", "")), pdf_links, repo_url):
                logger.warning("Stage 6: repository %s does not belong to '%s' - discarded", repo_url, paper.get("title"))
                meta.setdefault("discarded_repos", []).append({"paper": paper.get("title"), "repo": repo_url})
                repo_url, code, repo_dir = "", "", None
        if not repo_url:  # official code linked in the paper, else a GitHub search on the arXiv id
            links = pdf_links[:2]
            if not links and _env("ARC_REPO_SEARCH", "1") == "1":
                found = find_repo_by_arxiv(arxiv_id_of(paper) or "")
                links = [found] if found else []
            for url in links:
                dest = _clone(url, stage_dir / "paper_repos" / _slug(url.rstrip("/").split("/")[-1]))
                if dest is not None:
                    repo_url, repo_dir = url, dest
                    break
        vend: dict = {"files": {}, "skipped": {}}
        if repo_dir is not None and Path(repo_dir).is_dir() and _env("ARC_VENDOR_CODE", "1") == "1":
            tag = _slug(repo_url.rstrip("/").split("/")[-1].replace(".git", ""), 16).replace("-", "")
            vend = vendor_repo(Path(repo_dir), tag, stage_dir / "vendor", repo_url)
        if repo_dir is not None and not code:
            try:
                from researchclaw.pipeline.stage_impls._repo_context import repo_source_excerpts

                code = repo_source_excerpts(Path(repo_dir), max_files=2, max_chars_per_file=3000, max_total_chars=5000)
            except Exception:  # noqa: BLE001
                code = ""
        cmap = code_map(vend["files"])
        card = reduce_card(chat, llm, paper, notes, code, cid)
        card_md = (f"# [{cid}] {paper.get('title')}\n\nsource: {how}; pdf: {pdf.name if pdf else 'none'}; "
                   f"sections read: {[h.replace(chr(10), ' ') for h, _ in chunks]}; code: {repo_url or 'none'}\n\n{card}\n")
        (cards_dir / f"{cid}_{_slug(str(paper.get('title')))}.md").write_text(card_md, encoding="utf-8")
        (stage_dir / "cards").mkdir(exist_ok=True)  # stage 7 (synthesis) reads stage-06/cards/*.md
        (stage_dir / "cards" / f"{cid}_implementation_card.md").write_text(card_md, encoding="utf-8")
        head = (f"### [{cid}] {paper.get('title')} ({paper.get('year')})"
                f"{' - arXiv ' + arxiv_id_of(paper) if arxiv_id_of(paper) else ''}"
                f"{' - code: ' + repo_url if repo_url else ''}\n"
                f"_read from: {'full text, ' + str(len(chunks)) + ' parts' if chunks else 'abstract only'}_\n")
        code_part = ""
        if cmap:
            code_part += ("\n**Official code available in the project (read-only, IMPORT it instead of re-implementing):**\n"
                          + cmap + "\n")
        if vend["skipped"]:
            code_part += f"_not vendored: {vend['skipped']}_\n"
        if code:
            code_part += f"\n**Official code (excerpt):**\n{code}\n"
        room = per_card - len(head) - min(len(code_part), per_card // 2)
        blocks.append(head + card[:max(800, room)] + code_part[: max(per_card // 2, 4000)])
        meta["cards"].append({"id": cid, "title": paper.get("title"), "pdf": bool(pdf), "how": how,
                              "parts": [h for h, _ in chunks], "repo": repo_url,
                              "vendored": sorted(vend["files"]), "not_vendored": vend["skipped"],
                              "seconds": round(time.time() - t0)})
        logger.warning("Stage 6: implementation card %s ready (%s, %d parts)", cid, how, len(chunks))
    for r in [r for r in repos if r.get("extra")]:
        try:
            from researchclaw.pipeline.stage_impls._repo_context import repo_source_excerpts

            ex = repo_source_excerpts(Path(r["local_path"]), max_files=3, max_chars_per_file=3500, max_total_chars=6000)
        except Exception:  # noqa: BLE001
            ex = ""
        if ex:
            blocks.append(f"### [code] {r['repo_url']}\n{ex[: per_card]}\n")
    ids = [c["id"] for c in meta["cards"]]
    header = (
        "## KNOWLEDGE FROM THE LITERATURE AND OFFICIAL CODE (built at stage 6 of this run from the full text of the papers;"
        " authoritative, MUST be used)\n"
        f"Implementation cards: {', '.join(ids) if ids else 'none'}.\n"
        "- Hypotheses and experiment plans must each be grounded in one of these cards (cite its id).\n"
        "- OFFICIAL CODE FIRST: when a card lists official code available in the project (vendor_*.py files), IMPORT those"
        " classes and write only the glue to our batch; do NOT re-implement them from scratch (re-implementations produced"
        " most of the crashes so far). If the official code works on per-node token sequences instead of a graph batch,"
        " `rb_tokens.seed_token_sets(batch, x_dict, entity_table, k)` converts our batch into per-seed token sets"
        " ([B, K, C], seed first, with node type, hop and relative time). Without official code, port the excerpt shown."
        " vendor_*.py files are read-only. Activate the new component for `proposed` through rb_config.PROPOSED_OVERRIDES and declare"
        " the card in rb_config.PROPOSED_SOURCE (e.g. \"K1: <component>\").\n"
        "- Attempts without a valid card id in PROPOSED_SOURCE, or that leave `proposed` functionally identical to"
        " `baseline_tuned`, are rejected automatically. Generic code (e.g. a standard PyG operator) is acceptable when it"
        " is related to the cited card.\n"
    )
    text = header + "\n" + "\n".join(blocks)
    text = text[:budget]
    (stage_dir / "KNOWLEDGE.md").write_text(text, encoding="utf-8")
    Path(out_file).parent.mkdir(parents=True, exist_ok=True)
    Path(out_file).write_text(text, encoding="utf-8")
    meta["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    (stage_dir / "knowledge_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


# ============================================================================ prompt injection
def _valid_file() -> str:
    path = _env("ARC_KNOWLEDGE_FILE")
    if not path or not Path(path).is_file():
        return ""
    started = _env("ARC_RUN_STARTED_AT")
    try:
        if started and Path(path).stat().st_mtime < float(started):
            return ""  # left over from an earlier run
    except ValueError:
        pass
    text = Path(path).read_text(encoding="utf-8")
    return text if "KNOWLEDGE FROM THE LITERATURE" in text else ""


def knowledge_ids() -> list[str]:
    return re.findall(r"### \[(K\d+)\]", _valid_file())


def _skills_text(stage_num: int) -> str:
    try:
        from researchclaw.pipeline._helpers import _get_skill_registry

        reg = _get_skill_registry(None)
        ctx = "relbench graph neural network gnn pytorch geometric heterogeneous message passing paper implementation code"
        matched = [s for s in reg.match(ctx, stage_num)
                   if any(k and k in ctx for k in getattr(s, "trigger_keywords", []))]  # drop fallback matches
        return reg.export_for_prompt(matched, max_chars=4000) if matched else ""
    except Exception:  # noqa: BLE001
        return ""


def knowledge_for(name: str) -> str:
    """Text appended to the prompt of stage / sub-prompt `name` ('' if not applicable)."""
    stages = [s.strip() for s in _env("ARC_KNOWLEDGE_STAGES", DEFAULT_STAGES).split(",") if s.strip()]
    if name not in stages:
        return ""
    text = _valid_file()
    if name in ("iterative_improve", "iterative_repair", "code_repair", "code_exec_fix"):
        skills = _skills_text(13)  # stage 13 does not receive the pipeline's skill overlay: add it here
        if skills:
            text = (text + "\n\n" if text else "") + "## Matched Domain Skills\n" + skills
    return text


# ============================================================================ gate helpers (code mode)
def proposed_source(config_text: str) -> str:
    m = re.search(r'^PROPOSED_SOURCE\s*=\s*([\'"])(.*?)\1\s*$', config_text or "", re.MULTILINE)
    return m.group(2) if m else ""


def knowledge_ref_ok(candidate_files: dict, config_file: str = "rb_config.py") -> tuple[bool, str]:
    ids = knowledge_ids()
    if not ids:
        return True, ""  # no knowledge was built: nothing to enforce
    src = proposed_source(candidate_files.get(config_file, ""))
    cited = re.findall(r"\bK\d+\b", src)
    if not cited:
        return False, (f"PROPOSED_SOURCE does not cite an implementation card; set it to one of {ids}, "
                       "e.g. \"K1: <component you implemented>\"")
    if not any(c in ids for c in cited):
        return False, f"PROPOSED_SOURCE cites {cited}, which are not cards of this run ({ids})"
    if _env("ARC_REQUIRE_COMPONENT_MATCH", "0") == "1":
        ok, why = component_in_card(src, cited)
        if not ok:
            return False, why
    return True, ""


_STOP = {"with", "and", "the", "for", "from", "into", "based", "using", "via", "our", "new", "layer", "layers",
         "model", "module", "component", "implementation", "implemented", "adapted", "adapt", "plus", "improved"}


def card_text(card_id: str) -> str:
    text = _valid_file()
    m = re.search(rf"### \[{re.escape(card_id)}\](.*?)(?=\n### \[|\Z)", text, re.DOTALL)
    return m.group(1) if m else ""


def component_in_card(src: str, cited: list[str]) -> tuple[bool, str]:
    """The component named after 'K<n>:' must come from that card: >= 60% of its content words appear in the card."""
    name = src.split(":", 1)[1] if ":" in src else ""
    words = [w for w in re.findall(r"[a-z0-9]+", name.lower()) if len(w) >= 4 and w not in _STOP]
    if not words:
        return False, ("PROPOSED_SOURCE must name the component, e.g. \"K2: Transformer with Local/Global Attention\" "
                       "(use the component names listed in the card)")
    best = 0.0
    for cid in cited:
        body = card_text(cid).lower()
        if body:
            best = max(best, sum(1 for w in words if w in body) / len(words))
    if best < 0.6:
        return False, (f"the component in PROPOSED_SOURCE ('{name.strip()[:80]}') is not described in card {cited[0]}: "
                       "implement a component listed in the card and use its name")
    return True, ""
