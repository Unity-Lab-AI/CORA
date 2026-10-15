#!/usr/bin/env python3
"""
Move a module's `if __name__ == "__main__":` block into `main(_m)` in another
module. The module stays the owner of every global: in the moved code every name
the module defines is read and assigned through `_m` (the live module), nested
defs included, and `global X` lines become `_m.X = ...`. A one-line guard stays.

    python scripts/move_main.py src/boot_sequence.py src/boot_runtime.py
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
    mod_path, out_path = ROOT / sys.argv[1], ROOT / sys.argv[2]
    src = mod_path.read_text(encoding='utf-8')
    tree = cst.parse_module(src)
    mod_import = '.'.join(mod_path.relative_to(ROOT).with_suffix('').parts)
    out_import = '.'.join(out_path.relative_to(ROOT).with_suffix('').parts)

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

    midx = next(i for i, st in enumerate(tree.body)
                if isinstance(st, cst.If) and isinstance(st.test, cst.Comparison) and isinstance(st.test.left, cst.Name) and st.test.left.value == '__name__')
    block = tree.body[midx]
    rw = PhaseRewriter(module_names, set())
    rw.depth = 1
    body = [x for x in (s.visit(rw) for s in block.body.body) if not isinstance(x, cst.RemovalSentinel)]
    main_fn = cst.FunctionDef(name=cst.Name('main'), params=cst.Parameters(params=[cst.Param(cst.Name('_m'))]),
                              body=cst.IndentedBlock(body=body))
    header = (f'#!/usr/bin/env python3\n"""The runtime of {mod_import}: what ran under `if __name__ == "__main__"` there, moved\n'
              f'out on 2026-10-14. `_m` is the live {mod_import} module (its names are read and assigned\n'
              'through it), so the module stays the owner of every global."""\n'
              'from __future__ import annotations\nimport json\nimport os\nimport re\nimport sys\nimport time\n')
    code = header + cst.Module(body=import_stmts).code + '\n\n' + cst.Module(body=[main_fn]).code
    out_path.write_text(code, encoding='utf-8', newline='\n')

    guard = cst.parse_module(
        f'if __name__ == "__main__":\n'
        f'    # the runtime moved to {out_import} on 2026-10-14 (this module stays the owner of its globals)\n'
        f'    import importlib\n'
        f'    importlib.import_module("{out_import}").main(sys.modules[__name__])\n').body
    new_body = list(tree.body[:midx]) + list(guard) + list(tree.body[midx + 1:])
    out = tree.with_changes(body=new_body).code
    if not re.search(r'^import sys\b', out, flags=re.M):
        out = out.replace('import os\n', 'import os\nimport sys\n', 1)
    mod_path.write_text(out, encoding='utf-8', newline='\n')
    print(f"moved __main__ block ({len(block.body.body)} statements) to {sys.argv[2]}; guard left in {sys.argv[1]}")


if __name__ == '__main__':
    main()
