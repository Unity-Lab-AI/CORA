#!/usr/bin/env python3
"""
Split a big Python module into a package of parts, keeping every name and the
original import path (the original file becomes a facade), with comments and
formatting preserved (libcst).

    python scripts/split_module.py voice/commands.py --package voice/cmd_parts --check
    python scripts/split_module.py voice/commands.py --package voice/cmd_parts

How parts are chosen
  * everything before the first top-level "# ====" banner is the header -> _base.py
    (imports, constants, module state, the registry / decorators / helpers)
  * each top-level banner starts a part named from the banner text
  * --plan name=def1,def2 ... overrides: those top-level definitions go to that part

Rules that keep behaviour identical
  * a function that rebinds a module global (a `global X` statement) stays with X:
    both live in _base.py, and every OTHER part reads X through `_base.X` (rewritten
    with libcst) so a rebind is seen everywhere; plain readers of never-rebound names
    import them normally
  * a part imports the header names it uses from _base and sibling names from the
    sibling part; a dependency cycle between two parts merges them
  * the facade re-exports every top-level name (public and private) of every part and
    keeps the `if __name__ == "__main__"` block
"""
import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

import libcst as cst

ROOT = Path(__file__).resolve().parent.parent
BANNER = re.compile(r'^#\s*(=+|-{4,})\s*(?P<title>[^=#-].*?)?\s*(=+|-{4,})?\s*$')


def banner_title(stmt) -> str | None:
    """Title of a section banner in the statement's leading comment lines, if any:
    either "# ==== Title ====" or a "# Title" line between two "# ====" lines."""
    comments = [ll.comment.value if ll.comment else '' for ll in getattr(stmt, 'leading_lines', [])]
    for i, c in enumerate(comments):
        m = BANNER.match(c)
        if m and (m.group('title') or '').strip():
            return m.group('title').strip(' =-')
        if m and i + 2 < len(comments) and BANNER.match(comments[i + 2]) and comments[i + 1].startswith('#') and not BANNER.match(comments[i + 1]):
            t = comments[i + 1].lstrip('#').strip()
            if t:
                return t
    return None


def slug(t: str) -> str:
    s = re.sub(r'[^a-z0-9]+', '_', t.lower()).strip('_')
    return s[:30].rstrip('_') or 'part'


def defined_names(stmt) -> list:
    if isinstance(stmt, (cst.FunctionDef, cst.ClassDef)):
        return [stmt.name.value]
    if isinstance(stmt, cst.SimpleStatementLine):
        names = []
        for s in stmt.body:
            if isinstance(s, (cst.Assign,)):
                for t in s.targets:
                    names += _target_names(t.target)
            elif isinstance(s, (cst.AnnAssign, cst.AugAssign)):
                names += _target_names(s.target)
            elif isinstance(s, (cst.Import, cst.ImportFrom)):
                names += _import_names(s)
        return names
    if isinstance(stmt, (cst.If, cst.Try, cst.With)):
        out = []
        for b in _blocks(stmt):
            for st in b.body:
                out += defined_names(st)
        return out
    return []


def _blocks(stmt):
    blocks = []
    if isinstance(stmt, cst.If):
        blocks.append(stmt.body)
        if stmt.orelse is not None and isinstance(stmt.orelse, (cst.Else, cst.If)):
            blocks += _blocks(stmt.orelse) if isinstance(stmt.orelse, cst.If) else [stmt.orelse.body]
    elif isinstance(stmt, cst.Try):
        blocks.append(stmt.body)
        for h in stmt.handlers:
            blocks.append(h.body)
        if stmt.orelse: blocks.append(stmt.orelse.body)
        if stmt.finalbody: blocks.append(stmt.finalbody.body)
    elif isinstance(stmt, cst.With):
        blocks.append(stmt.body)
    return blocks


def _target_names(t):
    if isinstance(t, cst.Name):
        return [t.value]
    if isinstance(t, (cst.Tuple, cst.List)):
        out = []
        for e in t.elements:
            out += _target_names(e.value)
        return out
    return []


def _import_names(s):
    out = []
    if isinstance(s, cst.Import):
        for a in s.names:
            out.append((a.asname.name.value if a.asname else a.name.value.split('.')[0]) if isinstance(a.name, cst.Name) else (a.asname.name.value if a.asname else _dotted_root(a.name)))
    elif isinstance(s, cst.ImportFrom) and not isinstance(s.names, cst.ImportStar):
        for a in s.names:
            out.append(a.asname.name.value if a.asname else a.name.value)
    return out


def _dotted_root(attr):
    while isinstance(attr, cst.Attribute):
        attr = attr.value
    return attr.value if isinstance(attr, cst.Name) else ''


class NameCollector(cst.CSTVisitor):
    def __init__(self):
        self.names = set()
        self.globals = set()

    def visit_Name(self, node):
        self.names.add(node.value)

    def visit_Global(self, node):
        for n in node.names:
            self.globals.add(n.name.value)


def used_names(stmt):
    v = NameCollector()
    stmt.visit(v)
    return v.names, v.globals


class _ModuleLevelNames(cst.CSTVisitor):
    """Names a statement needs when it is EXECUTED at import time: class bases and
    decorators, default values, module-level expressions; function bodies are skipped
    (those can import lazily)."""

    def __init__(self):
        self.names = set()
        self._depth = 0

    def visit_FunctionDef(self, node):
        for d in node.decorators:
            d.visit(_NameGrab(self.names))
        node.params.visit(_NameGrab(self.names))
        if node.returns is not None:
            node.returns.visit(_NameGrab(self.names))
        return False      # do not descend into the body

    def visit_Name(self, node):
        self.names.add(node.value)


class _NameGrab(cst.CSTVisitor):
    def __init__(self, acc):
        self.acc = acc

    def visit_Name(self, node):
        self.acc.add(node.value)


def module_level_names(stmt):
    v = _ModuleLevelNames()
    stmt.visit(v)
    return v.names


class SiblingLazyImporter(cst.CSTTransformer):
    """Function bodies (including methods) that name something defined in a sibling
    part import it lazily at the top of the body, so parts never import each other at
    module level (no cycles, no load-order traps)."""

    def __init__(self, owner_of, pkg_import, skip_names):
        self.owner_of = owner_of
        self.pkg_import = pkg_import
        self.skip_names = skip_names

    def leave_FunctionDef(self, original, updated):
        # names used in the BODY only
        v = NameCollector()
        original.body.visit(v)
        needed = defaultdict(list)
        for n in sorted(v.names):
            if n in self.owner_of and n not in self.skip_names:
                needed[self.owner_of[n]].append(n)
        if not needed:
            return updated
        stmts = [cst.parse_statement(f"from {self.pkg_import}.{q} import {', '.join(ns)}") for q, ns in needed.items()]
        body = updated.body
        if isinstance(body, cst.IndentedBlock):
            return updated.with_changes(body=body.with_changes(body=list(stmts) + list(body.body)))
        return updated


class OneLevelDeeper(cst.CSTTransformer):
    """_base.py lives one folder deeper than the original module, so every path built
    from __file__ needs one more step up: Path(__file__).parent -> .parent.parent,
    os.path.dirname(os.path.abspath(__file__)) -> wrapped in one more dirname."""

    def leave_Attribute(self, original, updated):
        # the OUTERMOST .parent of a chain rooted at Path(__file__)
        if updated.attr.value == 'parent' and self._rooted_in_file(updated.value) and not self._parent_of_parent_marker:
            return cst.Attribute(value=updated, attr=cst.Name('parent'))
        return updated

    _parent_of_parent_marker = False

    def visit_Attribute(self, node):
        # mark inner .parent nodes so only the outermost gets the extra step
        if node.attr.value == 'parent' and isinstance(node.value, cst.Attribute) and node.value.attr.value == 'parent':
            pass
        return True

    @staticmethod
    def _rooted_in_file(node):
        while isinstance(node, cst.Attribute):
            node = node.value
        return (isinstance(node, cst.Call) and isinstance(node.func, cst.Name) and node.func.value == 'Path'
                and node.args and isinstance(node.args[0].value, cst.Name) and node.args[0].value.value == '__file__')

    def leave_Call(self, original, updated):
        # os.path.dirname(<something containing __file__>) chains: wrap the OUTERMOST in one more dirname
        f = updated.func
        if (isinstance(f, cst.Attribute) and f.attr.value == 'dirname' and isinstance(f.value, cst.Attribute)
                and f.value.attr.value == 'path' and isinstance(f.value.value, cst.Name) and f.value.value.value == 'os'):
            grab = set()
            updated.visit(_NameGrab(grab))
            if '__file__' in grab and not getattr(updated, '_wrapped', False):
                return cst.Call(func=cst.parse_expression('os.path.dirname'), args=[cst.Arg(value=updated)])
        return updated


class RebindRewriter(cst.CSTTransformer):
    """X -> _base.X for reads of rebound module globals (only bare Name loads that are
    not attribute targets, not keyword names, not local definitions)."""

    def __init__(self, names):
        self.names = names
        self.skip = set()

    def visit_Attribute(self, node):
        # don't rewrite the attr part of a.b
        self.skip.add(id(node.attr))

    def visit_Arg(self, node):
        if node.keyword is not None:
            self.skip.add(id(node.keyword))

    def visit_Param(self, node):
        self.skip.add(id(node.name))

    def visit_FunctionDef(self, node):
        self.skip.add(id(node.name))

    def visit_ClassDef(self, node):
        self.skip.add(id(node.name))

    def leave_Name(self, original, updated):
        if original.value in self.names and id(original) not in self.skip:
            return cst.Attribute(value=cst.Name('_base'), attr=cst.Name(original.value))
        return updated


def _deepen(stmt):
    """Apply OneLevelDeeper to the outermost Path(__file__)...parent chain / dirname chain only."""
    class Outer(cst.CSTTransformer):
        def __init__(self):
            self.done_parents = set()

        def leave_Attribute(self, original, updated):
            if updated.attr.value == 'parent' and OneLevelDeeper._rooted_in_file(updated.value):
                # outermost = no enclosing Attribute(.parent) around this one; we detect by returning
                # a marker-free node and letting the parent (if any) see a Call/Attribute value
                return updated
            return updated
    # simpler and exact: textual regex on this statement's code for the two idioms
    code = cst.Module(body=[stmt]).code
    new = re.sub(r'Path\(__file__\)((?:\.resolve\(\))?(?:\.parent)+)', lambda m: f"Path(__file__){m.group(1)}.parent", code)
    new = re.sub(r'((?:os\.path\.dirname\()+os\.path\.abspath\(__file__\)\)+)', lambda m: f"os.path.dirname({m.group(1)})", new)
    new = re.sub(r'((?:os\.path\.dirname\()+__file__\)+)', lambda m: f"os.path.dirname({m.group(1)})", new)
    if new != code:
        return cst.parse_module(new).body[0]
    return stmt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('module')
    ap.add_argument('--package', required=True, help='package dir for the parts, e.g. voice/cmd_parts')
    ap.add_argument('--plan', nargs='*', default=[], help='name=def1,def2 overrides')
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()

    mod_path = ROOT / a.module
    pkg_dir = ROOT / a.package
    pkg_import = a.package.replace('/', '.').replace('\\', '.')
    src = mod_path.read_text(encoding='utf-8')
    tree = cst.parse_module(src)

    # ---- group top-level statements
    header, parts, order = [], defaultdict(list), []
    current = None
    main_block = []
    for stmt in tree.body:
        if isinstance(stmt, cst.If) and 'cst.Name' and src and getattr(stmt.test, 'left', None) is not None and isinstance(stmt.test.left, cst.Name) and stmt.test.left.value == '__name__':
            main_block.append(stmt)
            continue
        t = banner_title(stmt)
        if t:
            current = slug(t)
            if current not in order:
                order.append(current)
        if current is None:
            header.append(stmt)
        else:
            parts[current].append(stmt)

    overrides = {}
    for item in a.plan:
        name, defs = item.split('=', 1)
        for d in defs.split(','):
            overrides[d.strip()] = slug(name)
    if overrides:
        moved = defaultdict(list)
        for pname in list(parts):
            keep = []
            for stmt in parts[pname]:
                dn = defined_names(stmt)
                target = next((overrides[n] for n in dn if n in overrides), None)
                (moved[target] if target else keep).append(stmt)
            parts[pname] = keep
        keep = []
        for stmt in header:
            dn = defined_names(stmt)
            target = next((overrides[n] for n in dn if n in overrides), None)
            (moved[target] if target else keep).append(stmt)
        header = keep
        for pname, stmts in moved.items():
            if pname not in order:
                order.append(pname)
            parts[pname] = parts.get(pname, []) + stmts
    parts = {p: parts[p] for p in order if parts.get(p)}

    # ---- names
    def names_of(stmts):
        out = []
        for s in stmts:
            out += defined_names(s)
        return out

    header_names = set(names_of(header))
    part_names = {p: set(names_of(s)) for p, s in parts.items()}
    all_defined = header_names | set().union(*part_names.values()) if part_names else header_names

    # rebound globals: `global X` anywhere -> X and the rebinding statements live in _base
    rebound = set()
    for p, stmts in list(parts.items()):
        keep = []
        for s in stmts:
            _, g = used_names(s)
            if g:
                rebound |= g
                header.append(s)          # the rebinding function moves to _base
                header_names |= set(defined_names(s))
            else:
                keep.append(s)
        parts[p] = keep
    for s in header:
        _, g = used_names(s)
        rebound |= g
    # the DEFINITION of every rebound global moves to _base too (a rebinding function in
    # _base and the variable in a part would be two different variables)
    for p, stmts in list(parts.items()):
        keep = []
        for s in stmts:
            if set(defined_names(s)) & rebound and not isinstance(s, (cst.FunctionDef, cst.ClassDef)):
                header.append(s)
                header_names |= set(defined_names(s))
            else:
                keep.append(s)
        parts[p] = keep
    # module-level statements in _base must find every name they use at import time:
    # pull the (non-def) defining statements of such names out of the parts, transitively
    changed = True
    while changed:
        changed = False
        need = set()
        for s in header:
            if not isinstance(s, (cst.FunctionDef, cst.ClassDef)):
                need |= module_level_names(s)
        for p, stmts in list(parts.items()):
            keep = []
            for s in stmts:
                if not isinstance(s, (cst.FunctionDef, cst.ClassDef)) and set(defined_names(s)) & need:
                    header.append(s)
                    header_names |= set(defined_names(s))
                    changed = True
                else:
                    keep.append(s)
            parts[p] = keep
    rebound &= header_names
    # _base keeps the ORIGINAL source order (a moved constant must follow what it is built from)
    _pos = {id(st): i for i, st in enumerate(tree.body)}
    header.sort(key=lambda st: _pos.get(id(st), 10**9))
    part_names = {p: set(names_of(s)) for p, s in parts.items()}

    # ---- dependencies: module-level sibling needs import at the top (cycles there merge the
    # parts); function-level sibling needs import lazily inside the function
    def compute_deps():
        d = {}
        for p, stmts in parts.items():
            used, top = set(), set()
            for s in stmts:
                u, _ = used_names(s)
                used |= u
                top |= module_level_names(s)
            d[p] = {'base': sorted((used & header_names) - rebound - part_names[p]),
                    'rebound': sorted(used & rebound),
                    'sib': {q: sorted(top & part_names[q]) for q in parts if q != p and top & part_names[q]},
                    'sib_lazy': {q: sorted((used - top) & part_names[q]) for q in parts if q != p and (used - top) & part_names[q]}}
        return d
    deps = compute_deps()
    changed = True
    while changed:
        changed = False
        for p in list(parts):
            for q in list(deps[p]['sib']):
                if p in deps.get(q, {}).get('sib', {}):
                    parts[p] += parts.pop(q)          # a module-level cycle: merge q into p
                    part_names[p] |= part_names.pop(q)
                    changed = True
                    break
            if changed:
                break
        if changed:
            deps = compute_deps()

    print(f"module {a.module} -> package {pkg_import}")
    print(f"  _base: {len(header)} statements, names: {len(header_names)}; rebound globals: {sorted(rebound)}")
    for p, stmts in parts.items():
        lines = sum(len(tree.code_for_node(s).splitlines()) for s in stmts)
        print(f"  {p}: {len(stmts)} statements, ~{lines} lines, imports from _base: {len(deps[p]['base'])}, rebound reads: {deps[p]['rebound']}, siblings top: {list(deps[p]['sib'])}, lazy: {list(deps[p]['sib_lazy'])}")
    if a.check:
        return

    # ---- write
    pkg_dir.mkdir(parents=True, exist_ok=True)
    class LazyImporter(cst.CSTTransformer):
        """Inside a _base function that names something defined in a part, import it
        there (lazily), so _base never imports a part at module level."""
        def __init__(self, part_of):
            self.part_of = part_of

        def leave_FunctionDef(self, original, updated):
            used, _ = used_names(original)
            needed = defaultdict(list)
            for n in sorted(used):
                if n in self.part_of:
                    needed[self.part_of[n]].append(n)
            if not needed:
                return updated
            stmts = [cst.parse_statement(f"from {pkg_import}.{q} import {', '.join(ns)}") for q, ns in needed.items()]
            body = updated.body
            if isinstance(body, cst.IndentedBlock):
                return updated.with_changes(body=body.with_changes(body=list(stmts) + list(body.body)))
            return updated

    part_of = {n: p for p, ns in part_names.items() for n in ns}
    header = [h.visit(LazyImporter(part_of)) if isinstance(h, cst.FunctionDef) else h for h in header]
    header = [_deepen(h) for h in header]
    base_mod = tree.with_changes(body=header)
    base_code = ('#!/usr/bin/env python3\n"""Shared base of the %s package (split from %s on 2026-10-14): imports, module\nstate, the helpers and every function that rebinds a module global."""\nfrom __future__ import annotations\n' % (pkg_import, a.module)) + base_mod.code
    (pkg_dir / '_base.py').write_text(base_code, encoding='utf-8', newline='\n')

    init_lines = ['#!/usr/bin/env python3', f'"""{pkg_import}: parts of {a.module}; importing the package loads every part."""',
                  f'from {pkg_import} import _base  # noqa: F401']
    facade_imports = [f'from {pkg_import}._base import {", ".join(sorted(header_names))}  # noqa: F401']
    for p, stmts in parts.items():
        body = [_deepen(st) for st in stmts]     # parts sit one folder deeper too
        if deps[p]['rebound']:
            rw = RebindRewriter(set(deps[p]['rebound']))
            body = [s.visit(rw) for s in body]
        owner_of = {n: q for q, ns in part_names.items() if q != p for n in ns}
        if deps[p]['sib_lazy']:
            body = [s.visit(SiblingLazyImporter(owner_of, pkg_import, set().union(*deps[p]['sib'].values()) if deps[p]['sib'] else set())) for s in body]
        imports = [f'from {pkg_import} import _base  # noqa: F401']
        if deps[p]['base']:
            imports.append(f'from {pkg_import}._base import {", ".join(deps[p]["base"])}  # noqa: F401')
        for q, names in deps[p]['sib'].items():
            imports.append(f'from {pkg_import}.{q} import {", ".join(names)}  # noqa: F401')
        # the header's own imports (stdlib etc.) are needed by name too: re-import everything the header imports
        hdr_imports = [s for s in header if isinstance(s, cst.SimpleStatementLine) and any(isinstance(x, (cst.Import, cst.ImportFrom)) for x in s.body)]
        pre = cst.Module(body=hdr_imports).code if hdr_imports else ''
        code = ('#!/usr/bin/env python3\n"""%s: %s (split from %s on 2026-10-14)."""\nfrom __future__ import annotations\n' % (pkg_import, p, a.module)) + pre + '\n'.join(imports) + '\n\n\n' + cst.Module(body=body).code
        (pkg_dir / f'{p}.py').write_text(code, encoding='utf-8', newline='\n')
        init_lines.append(f'from {pkg_import} import {p} as _{p}  # noqa: F401')
        if part_names[p]:
            facade_imports.append(f'from {pkg_import}.{p} import {", ".join(sorted(part_names[p]))}  # noqa: F401')
    (pkg_dir / '__init__.py').write_text('\n'.join(init_lines) + '\n', encoding='utf-8', newline='\n')

    # facade: the module docstring, then re-exports, then the __main__ block
    doc = ''
    if tree.body and isinstance(tree.body[0], cst.SimpleStatementLine) and isinstance(tree.body[0].body[0], cst.Expr) and isinstance(tree.body[0].body[0].value, cst.SimpleString):
        doc = tree.code_for_node(tree.body[0]) + '\n'
    facade = (doc + f'# Split into the {pkg_import} package on 2026-10-14; this module keeps every name it always had.\n'
              + f'from {pkg_import} import _base  # noqa: F401\n' + '\n'.join(facade_imports) + '\n')
    if main_block:
        facade += '\n\n' + cst.Module(body=main_block).code
    mod_path.write_text(facade, encoding='utf-8', newline='\n')
    print(f"written: {pkg_dir} ({len(parts) + 2} files) and facade {a.module}")


if __name__ == '__main__':
    main()
