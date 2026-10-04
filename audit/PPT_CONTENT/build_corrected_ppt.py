"""Build the corrected mid-review PPTX from the uploaded template.

Preserves the template's design/structure and replaces only the data-bearing
cells and status text with values traced to audit/FINAL_RESEARCH_REPORT/.
"""
import copy
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

SRC = "audit/PPT_CONTENT/Causal_Provenance_Mid_Review.pptx.pptx"
DST = "audit/PPT_CONTENT/Causal_Provenance_Mid_Review_CORRECTED.pptx"
p = Presentation(SRC)


def walk(shapes):
    for sh in shapes:
        if sh.shape_type == MSO_SHAPE_TYPE.GROUP:
            yield from walk(sh.shapes)
        else:
            yield sh


def set_text(shape, text):
    tf = shape.text_frame
    first = tf.paragraphs[0]
    if first.runs:
        first.runs[0].text = text
        for extra in first.runs[1:]:
            extra.text = ""
    else:
        first.add_run().text = text
    for extra in tf.paragraphs[1:]:
        for r in extra.runs:
            r.text = ""


def set_lines(shape, lines):
    tf = shape.text_frame
    base = copy.deepcopy(tf.paragraphs[0]._p)
    for para in list(tf.paragraphs):
        para._p.getparent().remove(para._p)
    for ln in lines:
        tf._txBody.append(copy.deepcopy(base))
        para = tf.paragraphs[-1]
        for r in list(para.runs):
            r._r.getparent().remove(r._r)
        para.add_run().text = ln


def cell(c, text):
    tf = c.text_frame
    first = tf.paragraphs[0]
    if first.runs:
        first.runs[0].text = text
        for e in first.runs[1:]:
            e.text = ""
    else:
        first.add_run().text = text
    for para in tf.paragraphs[1:]:
        for r in para.runs:
            r.text = ""


# ---- Slide 7: methodology table corrections ----
for sh in walk(p.slides[6].shapes):
    if sh.has_table:
        t = sh.table
        cell(t.cell(1, 1), "Synthetic provenance graphs (80 nodes / 179 edges, seeded) + real DARPA TC Engagement 3 traces: Theia '3' and Theia '5m', parsed by the repo's own CDM parser and truncated to the FIRST 50,000 edges. Scenarios 1r and 6r were unavailable and are NOT reported.")
        cell(t.cell(5, 1), "GraphSAGE: 30 epochs, lr 0.01, hidden 64, weighted BCE, seed 42 (ORIGINAL, leaky). CORRECTED protocol: disjoint 60/20/20 train/val/test edges, message passing restricted to train+val, threshold chosen on validation only.")
        cell(t.cell(8, 1), "pytest -q: 98 passed / 5 failed. The 5 failures are tests/test_graph_loader.py and are caused only by the absence of gitignored data/parsed/*.csv (environmental, not a code defect).")

# ---- Slide 10: result table + note textboxes ----
for sh in walk(p.slides[9].shapes):
    if sh.has_table:
        t = sh.table
        cell(t.cell(1, 2), "0.8125"); cell(t.cell(1, 3), "0.6500"); cell(t.cell(1, 4), "0.7222")
        cell(t.cell(2, 1), "GraphSAGE (ORIGINAL, leaky, tau*=0.70)")
        cell(t.cell(2, 2), "0.7000"); cell(t.cell(2, 3), "0.4667"); cell(t.cell(2, 4), "0.5600")
        cell(t.cell(3, 1), "Rule Engine (CORRECTED, 10 seeds)")
        cell(t.cell(3, 2), "0.7146+-0.0948"); cell(t.cell(3, 3), "0.9329+-0.0629"); cell(t.cell(3, 4), "0.8048+-0.0627")
        cell(t.cell(4, 0), "Synthetic")
        cell(t.cell(4, 1), "GraphSAGE (CORRECTED, leakage-free)")
        cell(t.cell(4, 2), "0.3416+-0.3093"); cell(t.cell(4, 3), "0.5017+-0.3637"); cell(t.cell(4, 4), "0.3224+-0.1942")
        cell(t.cell(5, 0), "DARPA Theia-3 (50k cap, synthetic post-collection poison)")
        cell(t.cell(5, 1), "Rule Engine"); cell(t.cell(5, 2), "0.9195+-0.0070"); cell(t.cell(5, 3), "0.7667+-0.0720"); cell(t.cell(5, 4), "0.8347+-0.0459")
        cell(t.cell(6, 0), "DARPA Theia-5m (50k cap, synthetic post-collection poison)")
        cell(t.cell(6, 1), "Rule Engine"); cell(t.cell(6, 2), "-"); cell(t.cell(6, 3), "-"); cell(t.cell(6, 4), "0.8504+-0.0599")
        cell(t.cell(7, 0), "Heavy mimicry (CORRECTED, label-free)")
        cell(t.cell(7, 1), "Rule Engine"); cell(t.cell(7, 2), "0.7146"); cell(t.cell(7, 3), "0.9329"); cell(t.cell(7, 4), "0.8048")
    elif sh.has_text_frame and "ROC-AUC stays" in sh.text_frame.text:
        set_text(sh, "Rule Engine ROC-AUC is a genuine continuous violation-score AUC = 0.9528 +/- 0.0312 (CORRECTED). The previously reported 1.0000 is retracted (hard-coded fallback). 1M edges: Rule Engine inference 34.48 s, peak ~971 MB, end-to-end 187.17 s (~29,007 edges/s).")
    elif sh.has_text_frame and "Both detectors degrade" in sh.text_frame.text:
        set_text(sh, "Paired RuleEngine - GraphSAGE F1 difference = +0.4824 (95% CI 0.3285-0.6363; Wilcoxon p = 0.001953; Cohen's dz = 2.24) on identical test instances. ROC-AUC difference +0.1239 is NOT significant (p = 0.1055).")

# ---- Slide 11: status/timeline ----
for sh in walk(p.slides[10].shapes):
    if sh.has_text_frame and "Current Status" in sh.text_frame.text:
        set_lines(sh, [
            "Completed",
            "- Provenance pipeline end-to-end: schema, CDM parser, synthetic + DARPA TC E3 loader",
            "- 15-rule causal/semantic rule engine + GraphSAGE (PyTorch Geometric) baseline implemented and evaluated",
            "- Full evaluation suite: synthetic benchmark, DARPA cross-dataset, rule ablation, adversarial-mimicry robustness, scalability to 1,000,000 edges",
            "- Rigorous audit: leakage-free GraphSAGE protocol, 10-seed statistics, poisoning & DARPA ground-truth audit",
            "- pytest: 98 passed / 5 failed (failures only due to absent gitignored DARPA CSVs)",
            "Planned before submission",
            "- Obtain full 4-scenario DARPA TC E3 data (1r and 6r currently unavailable)",
            "- Hybrid detector combining GraphSAGE embeddings with rule-violation scores",
            "- Post-quantum signing + Merkle anchoring for the provenance-integrity module",
        ])

p.save(DST)
print("saved", DST)
