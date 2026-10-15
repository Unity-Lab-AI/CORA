#!/usr/bin/env python3
"""
Move one top-level function out of a module into its own module, keeping the
module as the owner of every global: inside the moved function (and its nested
defs) every name the module defines is read and assigned through `_m`, the live
module, and `global X` lines become `_m.X = ...`. The original module keeps a
stub with the same name and signature that calls the moved body.

    python scripts/move_function.py src/boot_sequence.py full_boot src/boot_runtime.py
"""
import re
import sys
from pathlib import Path

import libcst as cst

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
from split_module import defined_names  # noqa: E402
from split_function import PhaseRewriter  # noqa: E402


def main():
    mod_path, fname, out_path = ROOT / sys.argv[1], sys.argv[2], ROOT / sys.argv[3]
    src = mod_path.read_text(encoding='utf-8')
    tree = cst.parse_module(src)
    mod_import = '.'.join(mod_path.relative_to(ROOT).with_suffix('').parts)
    out_import = '.'.join(out_path.relative_to(ROOT).with_suffix('').parts)

    import_stmts, module_names, import_names = [], set(), set()
    for st in tree.body:
        if isinstance(st, cst.SimpleStatementLine) and any(isinstance(x, (cst.Import, cst.ImportFrom)) for x in st.body):
            import_stmts.append(st)
            import_names |= set(defined_names(st))
        else:
            module_names |= set(defined_names(st))
    module_names -= import_names
    module_names.discard(fname)

    fidx = next(i for i, st in enumerate(tree.body) if isinstance(st, cst.FunctionDef) and st.name.value == fname)
    fn = tree.body[fidx]
    rw = PhaseRewriter(module_names, set())
    rw.depth = 1                      # the function's own returns stay plain returns
    moved = fn.visit(rw)
    # parameters: _m first, then the original ones
    params = moved.params.with_changes(params=[cst.Param(cst.Name('_m'))] + list(moved.params.params))
    moved = moved.with_changes(params=params, name=cst.Name(fname), leading_lines=[])

    body_code = cst.Module(body=[moved]).code
    header = (f'#!/usr/bin/env python3\n"""{fname} of {mod_import}, moved out on 2026-10-14. `_m` is the live {mod_import} module:\n'
              f'its names are read and assigned through it, so it stays the owner of every global."""\n'
              'from __future__ import annotations\nimport json\nimport os\nimport re\nimport sys\nimport time\n')
    out_path.write_text(header + cst.Module(body=import_stmts).code + '\n\n' + body_code, encoding='utf-8', newline='\n')

    # stub in the original module
    sig_params = fn.params
    call_args = ', '.join([p.name.value for p in sig_params.params] + [f"{p.name.value}={p.name.value}" for p in sig_params.kwonly_params])
    stub_src = cst.Module(body=[fn.with_changes(body=cst.parse_module(
        f'    """Moved to {out_import} on 2026-10-14; this stub keeps the name and signature."""\n'
        f'    import importlib\n'
        f'    return importlib.import_module("{out_import}").{fname}(sys.modules[__name__]{", " + call_args if call_args else ""})\n').body if False else
        cst.IndentedBlock(body=cst.parse_module(
            f'"""Moved to {out_import} on 2026-10-14; this stub keeps the name and signature."""\n'
            f'import importlib\n'
            f'return importlib.import_module("{out_import}").{fname}(sys.modules[__name__]{", " + call_args if call_args else ""})\n').body))]).code
    new_body = list(tree.body[:fidx]) + list(cst.parse_module(stub_src).body) + list(tree.body[fidx + 1:])
    out = tree.with_changes(body=new_body).code
    if not re.search(r'^import sys\b', out, flags=re.M):
        out = out.replace('import os\n', 'import os\nimport sys\n', 1)
    mod_path.write_text(out, encoding='utf-8', newline='\n')
    print(f"moved {fname}: {out_path.relative_to(ROOT)} ({len(body_code.splitlines())} lines); stub left in {sys.argv[1]}")


if __name__ == '__main__':
    main()
