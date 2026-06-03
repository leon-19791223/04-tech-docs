# -*- coding: utf-8 -*-
"""Verify final question bank"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hccde_quiz as h

ids = []
for q in h.ALL_QUESTIONS:
    if q["id"] in ids:
        print(f"DUPLICATE: {q['id']}")
    ids.append(q["id"])

tj = sum(len(h.QUESTION_BANK[c]["judge"]) for c in range(1,7))
ts = sum(len(h.QUESTION_BANK[c]["single"]) for c in range(1,7))
tm = sum(len(h.QUESTION_BANK[c]["multi"]) for c in range(1,7))

print(f"Total: {len(h.ALL_QUESTIONS)} | Unique IDs: {len(set(ids))}")
print(f"  Judge: {tj} | Single: {ts} | Multi: {tm}")
for cid in range(1,7):
    nj = len(h.QUESTION_BANK[cid]["judge"])
    ns = len(h.QUESTION_BANK[cid]["single"])
    nm = len(h.QUESTION_BANK[cid]["multi"])
    print(f"  Ch{cid}: {nj}J + {ns}S + {nm}M = {nj+ns+nm}")
print(f"  Orig: 147 -> Added: {tj+ts+tm-147} -> Total: {tj+ts+tm}")
