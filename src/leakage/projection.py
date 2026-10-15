"""Narrow the upstream train-OR-test criterion using saved symbolic evidence."""
import csv
from pathlib import Path

def read(directory, name):
    with (Path(directory) / name).open(newline="") as f:
        return list(csv.reader(f, delimiter="\t"))

def train_affecting(directory):
    flows = {(a, ac, b, bc) for a, ac, b, bc, _ in read(directory, "FlowFromExtended.csv")}
    overlap = {tuple(r) for r in read(directory, "DataOverlap.csv")}
    reductions = read(directory, "TaintStartsTarget.csv")
    projected = []
    for r in read(directory, "Telemetry_FinalPreProcessingLeak.csv"):
        _, train, _, _, trainctx, _, test, _, _, testctx, reduced, src = r
        if any(to == reduced and source == src and label == "rowset"
               and (train, trainctx, to, toctx) in flows
               and (test, testctx, source, sourcectx) in overlap
               for to, toctx, source, sourcectx, _, _, label in reductions):
            projected.append(r)
    return projected
