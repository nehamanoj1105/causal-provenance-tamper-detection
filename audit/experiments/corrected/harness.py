"""
Corrected evaluation harness.

Provides:
  * a genuine continuous Rule-Engine anomaly score (violation-severity weighted)
    so that ROC-AUC / PR-AUC are *computed*, never fabricated;
  * a leakage-free GraphSAGE protocol with disjoint train/validation/test edges,
    validation-only threshold selection, and message passing restricted to
    train+val edges (test edges neither seen nor used for node features).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from src.detection.rule_engine import default_rule_engine
from src.graph_construction.schema import EdgeType, NodeType, ProvenanceGraph
from audit.experiments.corrected.metrics import Metrics, compute_metrics

SEVERITY_WEIGHT = {"HIGH": 3.0, "MEDIUM": 2.0, "LOW": 1.0}
NODE_TYPE_MAP = {NodeType.PROCESS: 0, NodeType.FILE: 1, NodeType.USER: 2, NodeType.NETWORK: 3}
EDGE_TYPE_MAP = {EdgeType.READ: 0, EdgeType.WRITE: 1, EdgeType.EXECUTE: 2,
                 EdgeType.CONNECT: 3, EdgeType.SPAWN: 4, EdgeType.DELETE: 5}


# --------------------------------------------------------------------------
# Rule Engine: continuous score
# --------------------------------------------------------------------------
@dataclass
class RuleEngineOutput:
    per_rule_counts: dict[str, int]
    edge_score: dict[str, float]      # continuous, >= 0
    flagged: set[str]                 # score > 0
    results: list


def run_rule_engine(graph: ProvenanceGraph, threshold: float = 0.0) -> RuleEngineOutput:
    """
    Runs all rules. Builds a per-edge continuous anomaly score as the
    severity-weighted count of violations attributed to the edge (directly
    by edge_id, or via a node_id -> incident edges).

    The score is a genuine ranking signal: it distinguishes edges with no
    violation (0.0) from multiple/severe violations (higher).
    """
    engine = default_rule_engine()
    results = engine.run(graph)

    per_rule_counts: dict[str, int] = {}
    edge_score: dict[str, float] = {}

    incident: dict[str, list[str]] = {}
    for e in graph.edges:
        incident.setdefault(e.source_id, []).append(e.edge_id)
        incident.setdefault(e.target_id, []).append(e.edge_id)

    for r in results:
        per_rule_counts[r.rule] = len(r.violations)
        for v in r.violations:
            w = SEVERITY_WEIGHT.get(getattr(v, "severity", "LOW"), 1.0)
            targets: list[str] = []
            if getattr(v, "edge_id", None):
                targets.append(str(v.edge_id))
            elif getattr(v, "node_id", None):
                targets.extend(incident.get(str(v.node_id), []))
            for t in targets:
                edge_score[t] = edge_score.get(t, 0.0) + w

    flagged = {eid for eid, s in edge_score.items() if s > threshold}
    return RuleEngineOutput(per_rule_counts, edge_score, flagged, results)


def rule_engine_metrics(graph, gt_ids: set[str], threshold: float = 0.0):
    out = run_rule_engine(graph, threshold=threshold)
    all_ids = [e.edge_id for e in graph.edges]
    y_true = [1 if eid in gt_ids else 0 for eid in all_ids]
    y_score = [out.edge_score.get(eid, 0.0) for eid in all_ids]
    y_pred = [1 if eid in out.flagged else 0 for eid in all_ids]
    m = compute_metrics(y_true, y_pred, y_score=y_score)
    return m, out, y_true, y_score, all_ids


# --------------------------------------------------------------------------
# GraphSAGE: leakage-free protocol
# --------------------------------------------------------------------------
def _edge_split(num_edges: int, seed: int, train=0.6, val=0.2):
    rng = np.random.RandomState(seed)
    idx = rng.permutation(num_edges)
    n_tr = int(num_edges * train)
    n_va = int(num_edges * val)
    return idx[:n_tr], idx[n_tr:n_tr + n_va], idx[n_tr + n_va:]


def graphsage_eval(
    poisoned_graph: ProvenanceGraph,
    gt_ids: set[str],
    seed: int = 42,
    epochs: int = 100,
    lr: float = 0.01,
    hidden_channels: int = 64,
    train_ratio: float = 0.6,
    val_ratio: float = 0.2,
    device: str = "cpu",
):
    """
    Leakage-free GraphSAGE edge classification.

    Protocol:
      * edges partitioned into disjoint train / val / test by edge index.
      * message passing uses ONLY train+val edges (test edges are unseen).
      * node features (degree) computed from train+val edges only.
      * model selected & threshold chosen on the VALIDATION split only.
      * metrics reported on the TEST split; continuous scores -> real AUCs.
    """
    import torch
    import torch.nn as nn
    from src.ml.graphsage import GraphSAGEForTamperDetection
    from src.ml.utils import set_seed

    set_seed(seed)
    torch.manual_seed(seed)

    edges = list(poisoned_graph.edges)
    node_ids = list(poisoned_graph.nodes.keys())
    node_to_idx = {nid: i for i, nid in enumerate(node_ids)}
    N = len(node_ids)

    tr_idx, va_idx, te_idx = _edge_split(len(edges), seed, train_ratio, val_ratio)
    mp_idx = np.concatenate([tr_idx, va_idx])  # message-passing edges

    def build_edge_index(idxs):
        src = [node_to_idx[edges[i].source_id] for i in idxs]
        tgt = [node_to_idx[edges[i].target_id] for i in idxs]
        return torch.tensor([src, tgt], dtype=torch.long)

    # Message passing sees ONLY train+val edges. Test edges are never added to
    # the graph; they are scored as query edges on the fixed node embeddings.
    edge_index_mp = build_edge_index(mp_idx)
    edge_index_tr = build_edge_index(tr_idx)
    edge_index_va = build_edge_index(va_idx)
    edge_index_te = build_edge_index(te_idx)

    # node features from message-passing edges only (no test structure leak)
    in_deg = np.zeros(N); out_deg = np.zeros(N)
    for i in mp_idx:
        e = edges[i]
        out_deg[node_to_idx[e.source_id]] += 1
        in_deg[node_to_idx[e.target_id]] += 1
    feats = []
    for nid in node_ids:
        nt = node_to_idx[nid]
        oh = [0.0] * 4
        oh[NODE_TYPE_MAP.get(poisoned_graph.nodes[nid].node_type, 0)] = 1.0
        i = node_to_idx[nid]
        feats.append(oh + [out_deg[i], in_deg[i], out_deg[i] + in_deg[i]])
    x = torch.tensor(feats, dtype=torch.float)

    y = np.array([1.0 if edges[i].edge_id in gt_ids else 0.0 for i in range(len(edges))])
    y_all = torch.tensor(y, dtype=torch.float)

    dev = torch.device(device)
    x = x.to(dev)
    edge_index_mp = edge_index_mp.to(dev)

    # Training targets: only the train edges among the message-passing edges.
    tr_in_mp = np.isin(mp_idx, tr_idx)
    y_mp_train = torch.tensor(y[mp_idx][tr_in_mp], dtype=torch.float, device=dev)

    model = GraphSAGEForTamperDetection(in_channels=x.size(1), hidden_channels=hidden_channels).to(dev)
    n_pos = float(y[tr_idx].sum()); n_neg = float(len(tr_idx) - n_pos)
    pos_w = torch.tensor([n_neg / max(1.0, n_pos)], device=dev)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_w)
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)

    def score_edges(edge_index_q):
        """Scores arbitrary query edges using node embeddings from the
        train+val message-passing graph."""
        model.eval()
        with torch.no_grad():
            node_emb, _, _ = model(x, edge_index_mp)
            logits_q = model.edge_predictor(node_emb, edge_index_q)
            return torch.sigmoid(logits_q).cpu().numpy()

    best = {"f1": -1.0, "thr": 0.5, "epoch": 0, "state": None}
    patience, bad = 15, 0
    for ep in range(1, epochs + 1):
        model.train(); opt.zero_grad()
        node_emb, logits, _ = model(x, edge_index_mp)  # train-time message passing: train+val
        logits_tr = logits[torch.tensor(tr_in_mp, device=dev)]
        loss = criterion(logits_tr, y_mp_train)
        loss.backward(); opt.step()

        if ep % 5 == 0 or ep == epochs:
            sv = score_edges(edge_index_va.to(dev))
            va_y = y[va_idx]
            thr_grid = np.arange(0.05, 1.0, 0.05)
            best_f1, best_thr = -1.0, 0.5
            for t in thr_grid:
                pred = (sv >= t).astype(int)
                tp = int(((va_y == 1) & (pred == 1)).sum())
                fp = int(((va_y == 0) & (pred == 1)).sum())
                fn = int(((va_y == 1) & (pred == 0)).sum())
                pr = tp / (tp + fp) if (tp + fp) else 0.0
                rc = tp / (tp + fn) if (tp + fn) else 0.0
                f1 = 2 * pr * rc / (pr + rc) if (pr + rc) else 0.0
                if f1 > best_f1:
                    best_f1, best_thr = f1, t
            if best_f1 > best["f1"]:
                best = {"f1": best_f1, "thr": float(best_thr), "epoch": ep,
                        "state": {k: v.clone() for k, v in model.state_dict().items()}}
                bad = 0
            else:
                bad += 1
                if bad >= patience:
                    break

    if best["state"] is not None:
        model.load_state_dict(best["state"])
    s = score_edges(edge_index_te.to(dev))
    te_y = y[te_idx]
    te_pred = (s >= best["thr"]).astype(int)
    m = compute_metrics(te_y, te_pred, y_score=s)
    info = {"best_threshold": best["thr"], "best_val_f1": best["f1"],
            "best_epoch": best["epoch"], "n_train": len(tr_idx),
            "n_val": len(va_idx), "n_test": len(te_idx),
            "test_scores": s.tolist(), "test_labels": te_y.tolist()}
    return m, info
