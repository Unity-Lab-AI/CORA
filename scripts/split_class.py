#!/usr/bin/env python3
"""
Split one big class into mixins, keeping the class, its name, its module and its
behaviour exactly: method groups move to `class <Group>Mixin` in
<module_dir>/<module_stem>_parts/<group>.py and the original class inherits them.

    python scripts/split_class.py ui/code_editor.py CodeEditorModal --check
    python scripts/split_class.py ui/code_editor.py CodeEditorModal
    python scripts/split_class.py ui/boot_display.py BootDisplay --plan logging=log,log_speech,... stats=...

Groups come from "# ==== Title ====" banner comments inside the class body (the
methods after a banner belong to it) or from --plan group=method,method. Methods
without a group, __init__, dunder methods and the class's own attributes stay in
the original class.

Behaviour is kept by one rule: inside a moved method, every name that the ORIGINAL
module defines (its functions, classes, globals) is read through the live module,
`_m.<name>`, with `_m` imported lazily at the top of the method; plain imports
(tk, time, json ...) are copied to the part file. So globals the module rebinds
later are seen, and nothing is imported at module level in a cycle.
"""
import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

import libcst as cst

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from split_module import BANNER, NameCollector, defined_names, _NameGrab, slug  # noqa: E402


class ModuleNameRewriter(cst.CSTTransformer):
    """name -> _m.name for bare reads of names the original module defines."""

    def __init__(self, names):
        self.names = names
        self.skip = set()
        self.used = set()

    def visit_Attribute(self, node):
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

    def visit_ImportAlias(self, node):
        node.visit(_NameGrab(self.skip_names) if hasattr(self, 'skip_names') else _NameGrab(set()))

    def leave_Global(self, original, updated):
        # `global X` in a moved method: X is now rebound as `_m.X = ...` (an attribute store
        # on the live module), so the declaration goes away
        if all(n.name.value in self.names for n in original.names):
            self.used.update(n.name.value for n in original.names)
            return cst.RemoveFromParent()
        return updated

    def leave_SimpleStatementLine(self, original, updated):
        if not updated.body:
            return cst.RemoveFromParent()
        return updated

    def leave_Name(self, original, updated):
        if original.value in self.names and id(original) not in self.skip:
            self.used.add(original.value)
            return cst.Attribute(value=cst.Name('_m'), attr=cst.Name(original.value))
        return updated


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('module')
    ap.add_argument('klass')
    ap.add_argument('--plan', nargs='*', default=[])
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()

    mod_path = ROOT / a.module
    pkg_dir = mod_path.parent / f"{mod_path.stem}_parts"
    pkg_import = '.'.join(mod_path.relative_to(ROOT).with_suffix('').parts[:-1] + (f"{mod_path.stem}_parts",))
    mod_import = '.'.join(mod_path.relative_to(ROOT).with_suffix('').parts)
    src = mod_path.read_text(encoding='utf-8')
    tree = cst.parse_module(src)

    # module-level names (what the original defines) and its import statements
    module_names = set()
    import_stmts = []
    for st in tree.body:
        module_names |= set(defined_names(st))
        if isinstance(st, cst.SimpleStatementLine) and any(isinstance(x, (cst.Import, cst.ImportFrom)) for x in st.body):
            import_stmts.append(st)
    import_names = set()
    for st in import_stmts:
        import_names |= set(defined_names(st))
    module_names -= import_names                      # imports are copied, not routed through _m
    module_names.discard(a.klass)

    cls_idx = next(i for i, st in enumerate(tree.body) if isinstance(st, cst.ClassDef) and st.name.value == a.klass)
    cls = tree.body[cls_idx]
    body = list(cls.body.body)

    # groups: by in-class banners, then --plan overrides
    plan = {}
    for item in a.plan:
        g, ms = item.split('=', 1)
        for m in ms.split(','):
            plan[m.strip()] = slug(g)
    groups = defaultdict(list)
    keep = []
    current = None
    for st in body:
        comments = [ll.comment.value if ll.comment else '' for ll in getattr(st, 'leading_lines', [])]
        for c in comments:
            m = BANNER.match(c)
            if m and (m.group('title') or '').strip():
                current = slug(m.group('title').strip(' =-'))
        if isinstance(st, cst.FunctionDef):
            name = st.name.value
            g = plan.get(name, current)
            if name.startswith('__') or g is None:
                keep.append(st)
            else:
                groups[g].append(st)
        else:
            keep.append(st)                            # class attributes, docstring, nested classes stay

    print(f"class {a.klass} in {a.module}: {len(body)} members -> keep {len(keep)}, groups:")
    for g, ms in groups.items():
        lines = sum(len(tree.code_for_node(m).splitlines()) for m in ms)
        print(f"  {g}: {len(ms)} methods, ~{lines} lines: {', '.join(m.name.value for m in ms)[:120]}")
    if a.check or not groups:
        return

    pkg_dir.mkdir(exist_ok=True)
    init_lines = ['#!/usr/bin/env python3', f'"""{pkg_import}: mixins of {a.klass} (split from {a.module} on 2026-10-14)."""']
    mixin_names = []
    for g, ms in groups.items():
        mixin = ''.join(w.capitalize() for w in g.split('_')) + 'Mixin'
        mixin_names.append((g, mixin))
        rewritten = []
        for m in ms:
            rw = ModuleNameRewriter(module_names)
            new_m = m.visit(rw)
            if rw.used:
                imp = cst.parse_statement(f"from {mod_import.rsplit('.', 1)[0]} import {mod_import.rsplit('.', 1)[1]} as _m" if '.' in mod_import else f"import {mod_import} as _m")
                nb = new_m.body
                if isinstance(nb, cst.IndentedBlock):
                    new_m = new_m.with_changes(body=nb.with_changes(body=[imp] + list(nb.body)))
            rewritten.append(new_m)
        class_code = cst.Module(body=[cst.ClassDef(name=cst.Name(mixin), body=cst.IndentedBlock(body=rewritten),
                                                   leading_lines=[])]).code
        header = (f'#!/usr/bin/env python3\n"""{mixin}: the {g} methods of {a.klass} (split from {a.module} on 2026-10-14).\n'
                  f'Module names of {mod_import} are read through `_m` (imported lazily per method), so rebinding there is seen here."""\n'
                  'from __future__ import annotations\n')
        imports_code = cst.Module(body=import_stmts).code if import_stmts else ''
        (pkg_dir / f'{g}.py').write_text(header + imports_code + '\n\n' + class_code, encoding='utf-8', newline='\n')
        init_lines.append(f'from {pkg_import}.{g} import {mixin}  # noqa: F401')
    (pkg_dir / '__init__.py').write_text('\n'.join(init_lines) + '\n', encoding='utf-8', newline='\n')

    # original: import the mixins right before the class, inherit them, drop the moved methods
    new_bases = [cst.Arg(value=cst.Name(mx)) for _, mx in mixin_names] + list(cls.bases)
    new_cls = cls.with_changes(bases=new_bases, body=cls.body.with_changes(body=keep))
    import_line = cst.parse_statement(f"from {pkg_import} import {', '.join(mx for _, mx in mixin_names)}  # the class's method groups, split on 2026-10-14")
    new_body = list(tree.body[:cls_idx]) + [import_line, new_cls] + list(tree.body[cls_idx + 1:])
    mod_path.write_text(tree.with_changes(body=new_body).code, encoding='utf-8', newline='\n')
    print(f"written: {pkg_dir} ({len(groups)} mixins) and {a.module}")


if __name__ == '__main__':
    main()
