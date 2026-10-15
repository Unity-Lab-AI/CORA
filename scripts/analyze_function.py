#!/usr/bin/env python3
"""
Report what a phase-split of one giant function would have to carry:
the "# PHASE" blocks at the function's top level, the locals each block assigns
and reads, which locals cross block boundaries, early returns, nested defs,
and try/with blocks that span phases.

    python scripts/analyze_function.py src/boot_sequence.py run_boot_sequence
"""
import ast
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PHASE = re.compile(r'^\s*# =+\s*$|^\s*# PHASE\b')


def main():
    mod, fname = sys.argv[1], sys.argv[2]
    src = (ROOT / mod).read_text(encoding='utf-8')
    lines = src.split('\n')
    tree = ast.parse(src)
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == fname)
    params = {a.arg for a in fn.args.args + fn.args.kwonlyargs}
    # module-level names
    mod_names = set()
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
            mod_names.add(n.name)
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    mod_names.add(t.id)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names:
                mod_names.add((a.asname or a.name).split('.')[0])

    # blocks: consecutive top-level statements of the function, cut where a statement's
    # preceding comment lines contain a "# PHASE" banner
    blocks, cur, cur_title = [], [], 'prologue'
    for st in fn.body:
        start = st.lineno
        # look back over comment/blank lines
        k = start - 2
        title = None
        while k >= 0 and (lines[k].strip() == '' or lines[k].strip().startswith('#')):
            m = re.match(r'^\s*# (PHASE[^#]*)$', lines[k])
            if m:
                title = m.group(1).strip()
            k -= 1
        if title and cur:
            blocks.append((cur_title, cur))
            cur, cur_title = [], title
        elif title:
            cur_title = title
        cur.append(st)
    if cur:
        blocks.append((cur_title, cur))

    def assigned(nodes):
        out = set()
        for n in nodes:
            for x in ast.walk(n):
                if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Store):
                    out.add(x.id)
                elif isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    out.add(x.name)
                elif isinstance(x, ast.ExceptHandler) and x.name:
                    out.add(x.name)
                elif isinstance(x, (ast.Import, ast.ImportFrom)):
                    for a in x.names:
                        out.add((a.asname or a.name).split('.')[0])
        return out

    def loaded(nodes):
        out = set()
        for n in nodes:
            for x in ast.walk(n):
                if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Load):
                    out.add(x.id)
        return out

    info = []
    all_assigned = defaultdict(set)
    for i, (title, nodes) in enumerate(blocks):
        a, l = assigned(nodes), loaded(nodes)
        rets = [x for n in nodes for x in ast.walk(n) if isinstance(x, ast.Return)]
        defs = [x.name for n in nodes for x in ast.walk(n) if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef))]
        glob = {g for n in nodes for x in ast.walk(n) if isinstance(x, ast.Global) for g in x.names}
        span = (nodes[0].lineno, nodes[-1].end_lineno)
        info.append((title, span, a, l, rets, defs, glob))
        for name in a:
            all_assigned[name].add(i)

    locals_all = set().union(*[i[2] for i in info]) | params
    print(f"{fname}: {len(fn.body)} top-level statements, lines {fn.lineno}-{fn.end_lineno}, params {sorted(params)}")
    print(f"blocks: {len(blocks)}")
    cross = defaultdict(set)
    for i, (title, span, a, l, rets, defs, glob) in enumerate(info):
        reads_from_others = {n for n in l if n in locals_all and n not in mod_names and i not in all_assigned.get(n, set()) and n not in params}
        for n in reads_from_others:
            cross[n].add(i)
        print(f"  [{i:2d}] {title[:48]:48s} L{span[0]}-{span[1]} ({span[1]-span[0]+1:4d}) assigns {len(a):3d} | reads-other-blocks {sorted(reads_from_others)[:8]} | returns {len(rets)} | nested defs {defs} | global {sorted(glob)}")
    shared = {n for n, blks in all_assigned.items() if len(blks) > 1 or (n in cross)}
    print("\ncross-phase locals (assigned in one block, read in another):", sorted(shared | set(cross)))
    print("params read by blocks:", sorted(p for p in params if any(p in i[3] for i in info)))


if __name__ == '__main__':
    main()
