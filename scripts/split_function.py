#!/usr/bin/env python3
"""
Extract the "# PHASE ..." blocks of one giant function into one module per phase,
keeping behaviour: the function becomes the prologue + a call per phase.

    python scripts/split_function.py src/boot_sequence.py run_boot_sequence --package src/boot_phases --check
    python scripts/split_function.py src/boot_sequence.py run_boot_sequence --package src/boot_phases

Each phase module has  def run(_m, L):  with the block's statements, where
  * `_m` is the live original module: every name the module defines (its functions,
    classes, globals) is read and assigned through `_m.name`; `global X` lines go away
  * `L` is a SimpleNamespace holding the locals that cross phase boundaries (the
    function's parameters and any local assigned in one block and read in another);
    those are read and assigned as `L.name`; everything else stays a plain local
  * a `return v` at the phase's own level becomes `return ('return', v)` and the
    caller returns v; returns inside nested defs are untouched
  * the module's import lines are copied so the names they bind resolve the same way
Comments and formatting are kept (libcst).
"""
import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

import libcst as cst
import libcst.matchers as m

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from split_module import NameCollector, defined_names, slug  # noqa: E402

PHASE_RE = re.compile(r'^# (PHASE[^#]*)$')


class _Assigned(cst.CSTVisitor):
    """Names bound anywhere in a statement (stores, defs, except-as, imports, for/with targets)."""

    def __init__(self):
        self.names = set()
        self.except_names = set()      # names that can never be rewritten as L.x (except-as, comprehension vars)

    def visit_AssignTarget(self, node):
        node.target.visit(_Grab(self.names))

    def visit_AugAssign(self, node):
        node.target.visit(_Grab(self.names))

    def visit_AnnAssign(self, node):
        node.target.visit(_Grab(self.names))

    def visit_For(self, node):
        node.target.visit(_Grab(self.names))

    def visit_WithItem(self, node):
        if node.asname is not None:
            node.asname.name.visit(_Grab(self.names))

    def visit_ExceptHandler(self, node):
        if node.name is not None:
            node.name.name.visit(_Grab(self.names))
            node.name.name.visit(_Grab(self.except_names))

    def visit_CompFor(self, node):
        node.target.visit(_Grab(self.names))         # comprehension-local, bound here
        node.target.visit(_Grab(self.except_names))  # and never a crossing local

    def visit_FunctionDef(self, node):
        self.names.add(node.name.value)

    def visit_ClassDef(self, node):
        self.names.add(node.name.value)

    def visit_ImportAlias(self, node):
        n = node.asname.name.value if node.asname else (node.name.value if isinstance(node.name, cst.Name) else None)
        if n:
            self.names.add(n)


class _Grab(cst.CSTVisitor):
    def __init__(self, acc):
        self.acc = acc

    def visit_Name(self, node):
        self.acc.add(node.value)


def assigned_names(stmts):
    v = _Assigned()
    for s in stmts:
        s.visit(v)
    return v.names


def never_crossing(stmts):
    v = _Assigned()
    for s in stmts:
        s.visit(v)
    return v.except_names


def loaded_names(stmts):
    v = NameCollector()
    for s in stmts:
        s.visit(v)
    return v.names, v.globals


class PhaseRewriter(cst.CSTTransformer):
    """module names -> _m.name ; crossing locals -> L.name ; drop `global`; top-level returns."""

    def __init__(self, module_names, crossing):
        self.module_names = module_names
        self.crossing = crossing
        self.skip = set()
        self.depth = 0          # nested function depth (0 = the phase's own level)

    def visit_Attribute(self, node):
        self.skip.add(id(node.attr))

    def visit_Arg(self, node):
        if node.keyword is not None:
            self.skip.add(id(node.keyword))

    def visit_Param(self, node):
        self.skip.add(id(node.name))

    def visit_FunctionDef(self, node):
        self.skip.add(id(node.name))
        self.depth += 1

    def leave_FunctionDef(self, original, updated):
        self.depth -= 1
        return updated

    def visit_ClassDef(self, node):
        self.skip.add(id(node.name))

    def visit_ImportAlias(self, node):
        node.visit(_Grab(self.skip_names)) if hasattr(self, 'skip_names') else None
        return False

    def leave_Global(self, original, updated):
        return cst.RemoveFromParent()

    def leave_SimpleStatementLine(self, original, updated):
        if not updated.body:
            return cst.RemoveFromParent()
        return updated

    def leave_Name(self, original, updated):
        if id(original) in self.skip:
            return updated
        if original.value in self.crossing:
            return cst.Attribute(value=cst.Name('L'), attr=cst.Name(original.value))
        if original.value in self.module_names:
            return cst.Attribute(value=cst.Name('_m'), attr=cst.Name(original.value))
        return updated

    def leave_Return(self, original, updated):
        if self.depth == 0:
            val = updated.value if updated.value is not None else cst.Name('None')
            return updated.with_changes(value=cst.Tuple(elements=[cst.Element(cst.SimpleString("'return'")), cst.Element(val)]))
        return updated


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('module')
    ap.add_argument('function')
    ap.add_argument('--package', required=True)
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()

    mod_path = ROOT / a.module
    pkg_dir = ROOT / a.package
    pkg_import = a.package.replace('/', '.').replace('\\', '.')
    src = mod_path.read_text(encoding='utf-8')
    tree = cst.parse_module(src)

    # module names (defined, not imported) and import statements
    import_stmts, module_names, import_names = [], set(), set()
    for st in tree.body:
        if isinstance(st, cst.SimpleStatementLine) and any(isinstance(x, (cst.Import, cst.ImportFrom)) for x in st.body):
            import_stmts.append(st)
            import_names |= set(defined_names(st))
        elif isinstance(st, cst.If) and isinstance(st.test, cst.Comparison) and isinstance(st.test.left, cst.Name) and st.test.left.value == '__name__':
            pass        # names bound under `if __name__ == "__main__"` are that block's locals, not module globals
        else:
            module_names |= set(defined_names(st))
    module_names -= import_names

    fidx = next(i for i, st in enumerate(tree.body) if isinstance(st, cst.FunctionDef) and st.name.value == a.function)
    fn = tree.body[fidx]
    params = [p.name.value for p in fn.params.params + fn.params.kwonly_params]
    body = list(fn.body.body)

    # blocks by "# PHASE" banners in leading comments
    blocks, cur, title = [], [], 'prologue'
    for st in body:
        t = None
        for ll in getattr(st, 'leading_lines', []):
            if ll.comment:
                mm = PHASE_RE.match(ll.comment.value.strip())
                if mm:
                    t = mm.group(1).strip()
        if t and cur:
            blocks.append((title, cur))
            cur, title = [], t
        elif t:
            title = t
        cur.append(st)
    if cur:
        blocks.append((title, cur))
    assert blocks[0][0] == 'prologue', "the function must start with statements before the first PHASE banner"
    prologue = blocks[0][1]
    phases = blocks[1:]

    # crossing locals: params + names assigned in block i and loaded in block j != i (module names excluded)
    assigned = [assigned_names(b) - module_names for _, b in blocks]
    loaded = [loaded_names(b)[0] for _, b in blocks]
    # names bound by import statements INSIDE blocks (e.g. `from PIL import Image` in one phase,
    # used in a later one): those imports are copied into the phases that need them
    class _ImportGrab(cst.CSTVisitor):
        def __init__(self):
            self.by_name = {}

        def visit_Import(self, node):
            for al in node.names:
                n = al.asname.name.value if al.asname else (al.name.value if isinstance(al.name, cst.Name) else None)
                if n:
                    self.by_name[n] = cst.Module(body=[cst.SimpleStatementLine(body=[node])]).code.strip()

        def visit_ImportFrom(self, node):
            if isinstance(node.names, cst.ImportStar):
                return
            for al in node.names:
                n = al.asname.name.value if al.asname else al.name.value
                self.by_name[n] = cst.Module(body=[cst.SimpleStatementLine(body=[node])]).code.strip()
    ig = _ImportGrab()
    for _, b in blocks:
        for st in b:
            st.visit(ig)
    block_imports = ig.by_name

    crossing = set(params)
    banned = set().union(*[never_crossing(b) for _, b in blocks])
    needed_imports = defaultdict(set)      # phase number (1-based) -> import lines to add
    for j, l_j in enumerate(loaded):
        reads_unbound = (l_j - assigned[j]) - module_names - import_names
        for n in reads_unbound:
            if n in block_imports:
                needed_imports[j].add(block_imports[n])
            elif n not in banned and any(n in assigned[i] for i in range(len(blocks)) if i != j):
                crossing.add(n)
    print(f"{a.function}: {len(phases)} phases; crossing locals: {sorted(crossing)}")
    for j in sorted(needed_imports):
        if j > 0:
            print(f"  block {j} needs imports: {sorted(needed_imports[j])}")
    for t, b in phases:
        _, g = loaded_names(b)
        print(f"  {slug(t)[:40]:40s} {len(b):3d} stmts  globals {sorted(g)}")
    if a.check:
        return

    pkg_dir.mkdir(parents=True, exist_ok=True)
    mod_import = '.'.join(mod_path.relative_to(ROOT).with_suffix('').parts)
    imports_code = cst.Module(body=import_stmts).code
    names = []
    for n, (t, b) in enumerate(phases, 1):
        name = f"phase_{n:02d}_{slug(t)[:36]}"
        names.append((name, t))
        rw = PhaseRewriter(module_names, crossing)
        new_body = [x for x in (s.visit(rw) for s in b) if not isinstance(x, cst.RemovalSentinel)]
        extra = ''.join(f"try:\n    {line}\nexcept Exception:\n    pass\n" for line in sorted(needed_imports.get(n, set())))
        run_fn = cst.FunctionDef(name=cst.Name('run'), params=cst.Parameters(params=[cst.Param(cst.Name('_m')), cst.Param(cst.Name('L'))]),
                                 body=cst.IndentedBlock(body=new_body))
        code = (f'#!/usr/bin/env python3\n"""{t}\n\nOne phase of {mod_import}.{a.function}, split out on 2026-10-14. `_m` is the live\n'
                f'{mod_import} module (its names are read and assigned through it); `L` holds the locals\nshared across phases."""\n'
                'from __future__ import annotations\nimport json\nimport os\nimport re\nimport sys\nimport time\n' + imports_code + extra + '\n\n' + cst.Module(body=[run_fn]).code)
        (pkg_dir / f'{name}.py').write_text(code, encoding='utf-8', newline='\n')
    (pkg_dir / '__init__.py').write_text(f'#!/usr/bin/env python3\n"""{pkg_import}: the phases of {mod_import}.{a.function}, one module each, run in order."""\n'
                                         + ''.join(f'from {pkg_import} import {n}  # noqa: F401\n' for n, _ in names)
                                         + 'PHASES = [' + ', '.join(n for n, _ in names) + ']\n', encoding='utf-8', newline='\n')

    # the new function: prologue + L + the phase calls
    cross_init = ', '.join(f"{n}={n}" if n in params or n in assigned[0] else f"{n}=None" for n in sorted(crossing))
    tail = cst.parse_module(
        f"L = _types.SimpleNamespace({cross_init})\n"
        f"_m = sys.modules[__name__]\n"
        f"for _phase in {pkg_import}.PHASES:   # one module per boot phase (src/boot_phases/)\n"
        f"    _r = _phase.run(_m, L)\n"
        f"    if isinstance(_r, tuple) and _r and _r[0] == 'return':\n"
        f"        return _r[1]\n").body
    new_fn = fn.with_changes(body=fn.body.with_changes(body=prologue + list(tail)))
    header_imports = cst.parse_module(f"import types as _types\nimport {pkg_import}\n").body
    new_body = list(tree.body[:fidx]) + list(header_imports) + [new_fn] + list(tree.body[fidx + 1:])
    out = tree.with_changes(body=new_body).code
    if not re.search(r'^import sys\b', out, flags=re.M):
        out = out.replace('import os\n', 'import os\nimport sys\n', 1)
    mod_path.write_text(out, encoding='utf-8', newline='\n')
    print(f"written: {pkg_dir} ({len(names)} phases) and {a.module}")


if __name__ == '__main__':
    main()
