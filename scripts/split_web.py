#!/usr/bin/env python3
"""
Split web/index.html into web/index.html (markup only) + web/css/cora.css +
web/js/NN-<section>.js, keeping the page's behaviour byte-for-byte:

  * the single <style> block becomes css/cora.css (one <link>)
  * the single <script> block is cut at its "// ====" section banners into
    classic scripts loaded IN ORDER (not ES modules: the page's inline
    onclick="..." handlers and the functions reference each other through the
    shared global scope, which ES modules would break)
  * the first file keeps everything before the first banner (the CORA_LOCAL
    constants and the opening helpers), so load order equals the old order

Run:  python scripts/split_web.py            (writes files, prints the plan)
      python scripts/split_web.py --check    (prints the plan only)
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / 'web'
INDEX = WEB / 'index.html'

BANNER = re.compile(r'^        // =+\s*$')      # exactly the script's own indent: banners nested in functions do not cut


def slug(title: str) -> str:
    t = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
    return t[:28].rstrip('-') or 'section'


def main(check: bool = False):
    html = INDEX.read_text(encoding='utf-8')
    m_style = re.search(r'\n([ \t]*)<style>\n(.*?)\n[ \t]*</style>\n', html, re.S)
    m_script = re.search(r'\n([ \t]*)<script>\n(.*?)\n[ \t]*</script>\n', html, re.S)
    assert m_style and m_script, "expected exactly one <style> and one <script> block"
    css = m_style.group(2)
    js = m_script.group(2)
    js_lines = js.split('\n')

    # cut points: a banner line followed by a "// Title" line followed by a banner
    cuts = []
    for i in range(len(js_lines) - 2):
        if BANNER.match(js_lines[i]) and js_lines[i + 1].startswith('        //') and not js_lines[i + 1].startswith('         ') and BANNER.match(js_lines[i + 2]):
            title = js_lines[i + 1].strip().lstrip('/').strip()
            cuts.append((i, title))
    assert cuts, "no section banners found"

    parts = []
    first_end = cuts[0][0]
    parts.append(('00-runtime', 'local runtime constants + opening helpers', js_lines[:first_end]))
    for n, (start, title) in enumerate(cuts):
        end = cuts[n + 1][0] if n + 1 < len(cuts) else len(js_lines)
        parts.append((f"{n + 1:02d}-{slug(title)}", title, js_lines[start:end]))

    # dedent by the script's own indentation (8 spaces) where present
    def dedent(lines):
        out = []
        for l in lines:
            out.append(l[8:] if l.startswith('        ') else l.lstrip() if l.strip() == '' else l)
        return '\n'.join(out).rstrip() + '\n'

    plan = [(name, title, len(lines)) for name, title, lines in parts]
    for name, title, n in plan:
        print(f"  js/{name}.js  {n:5d} lines   {title}")
    print(f"  css/cora.css  {len(css.splitlines()):5d} lines")
    if check:
        return

    (WEB / 'css').mkdir(exist_ok=True)
    (WEB / 'js').mkdir(exist_ok=True)
    (WEB / 'css' / 'cora.css').write_text(dedent(css.split('\n')), encoding='utf-8', newline='\n')
    for name, title, lines in parts:
        header = f"// C.O.R.A web - {title}\n// Classic script, loaded in order by index.html (shared global scope). Split from index.html on 2026-10-14.\n\n"
        (WEB / 'js' / f'{name}.js').write_text(header + dedent(lines), encoding='utf-8', newline='\n')

    indent_s = m_style.group(1)
    indent_j = m_script.group(1)
    link = f'\n{indent_s}<link rel="stylesheet" href="css/cora.css">\n'
    scripts = '\n' + ''.join(f'{indent_j}<script src="js/{name}.js"></script>\n' for name, _, _ in parts)
    new_html = html[:m_style.start()] + link + html[m_style.end():]
    m_script2 = re.search(r'\n([ \t]*)<script>\n(.*?)\n[ \t]*</script>\n', new_html, re.S)
    new_html = new_html[:m_script2.start()] + scripts + new_html[m_script2.end():]
    INDEX.write_text(new_html, encoding='utf-8', newline='\n')
    print(f"index.html: {len(new_html.splitlines())} lines (was {len(html.splitlines())})")


def depth_zero_lines(lines):
    """Line indexes at brace depth 0 (outside strings, template literals and comments)."""
    out, depth, in_block, in_str = [], 0, False, None
    for i, line in enumerate(lines):
        if depth == 0 and not in_block and in_str is None:
            out.append(i)
        j = 0
        while j < len(line):
            c = line[j]
            nxt = line[j + 1] if j + 1 < len(line) else ''
            if in_block:
                if c == '*' and nxt == '/':
                    in_block = False
                    j += 1
            elif in_str:
                if c == '\\':
                    j += 1
                elif c == in_str:
                    in_str = None
            else:
                if c == '/' and nxt == '/':
                    break
                if c == '/' and nxt == '*':
                    in_block = True
                    j += 1
                elif c in ('"', "'", '`'):
                    in_str = c
                elif c == '{':
                    depth += 1
                elif c == '}':
                    depth -= 1
            j += 1
    return out


def second_pass(max_lines: int = 800, target: int = 560):
    """Cut js files over max_lines at depth-0 declaration lines nearest multiples of `target`."""
    html = INDEX.read_text(encoding='utf-8')
    for js in sorted((WEB / 'js').glob('*.js')):
        lines = js.read_text(encoding='utf-8').split('\n')
        if len(lines) <= max_lines:
            continue
        starts = [i for i in depth_zero_lines(lines)
                  if re.match(r'^(async function |function |const |let |var |class )', lines[i]) and i > 0 and lines[i - 1].strip() == '']
        cuts, want = [], target
        for i in starts:
            if i >= want:
                cuts.append(i)
                want = i + target
        if not cuts or len(lines) - cuts[-1] < 80:
            cuts = cuts[:-1] if cuts and len(lines) - cuts[-1] < 80 else cuts
        if not cuts:
            print(f"  {js.name}: {len(lines)} lines, no safe cut (one block), left whole")
            continue
        pieces, prev = [], 0
        for c in cuts + [len(lines)]:
            pieces.append(lines[prev:c])
            prev = c
        stem = js.stem
        names = []
        for k, piece in enumerate(pieces):
            name = f"{stem}{chr(ord('a') + k)}"
            body = '\n'.join(piece).rstrip() + '\n'
            if k:
                body = f"// {stem} (part {k + 1}): continues the previous file, same global scope\n\n" + body
            (WEB / 'js' / f'{name}.js').write_text(body, encoding='utf-8', newline='\n')
            names.append(name)
        js.unlink()
        tag = f'<script src="js/{js.name}"></script>'
        indent = re.search(r'^([ \t]*)' + re.escape(tag), html, re.M)
        ind = indent.group(1) if indent else '    '
        html = html.replace(ind + tag, '\n'.join(f'{ind}<script src="js/{n}.js"></script>' for n in names))
        print(f"  {js.name}: {len(lines)} lines -> " + ', '.join(f"{n}.js ({len(pc)})" for n, pc in zip(names, pieces)))
    INDEX.write_text(html, encoding='utf-8', newline='\n')


if __name__ == '__main__':
    if '--pass2' in sys.argv:
        second_pass()
    else:
        main(check='--check' in sys.argv)
