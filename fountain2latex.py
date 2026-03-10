#!/usr/bin/env python3
"""
fountain2latex.py
====================
Fountain → LaTeX converter using screenplain as the parser.

Install dependency:
    pip install screenplain

Usage:
    python fountain2latex.py input.fountain
    python fountain2latex.py input.fountain -o output.tex
    python fountain2latex.py input.fountain --title "Too Nice to Die" --author "David Joyner"
    python fountain2latex.py input.fountain --scene-numbers
    python fountain2latex.py input.fountain --debug-ast

Compile output with:
    pdflatex -interaction=nonstopmode output.tex
    pdflatex -interaction=nonstopmode output.tex   # second pass fixes page numbers

TODO: Fix mid-dialog-block page cuts.

written March 2026 - claude (mostly) and wdj (for sneaky latex spacing)

"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

# ---------------------------------------------------------------------------
# screenplain imports — fail early with a helpful message
# ---------------------------------------------------------------------------
try:
    from screenplain.parsers.fountain import parse as sp_parse
    from screenplain.types import (
        Screenplay, Slug, Action, Dialog, DualDialog,
        Transition, Section, PageBreak,
    )
    from screenplain.richstring import RichString, Segment, Bold, Italic, Underline
except ImportError:
    print(
        "Error: screenplain is not installed.\n"
        "Install it with:  pip install screenplain",
        file=sys.stderr,
    )
    sys.exit(1)


# =============================================================================
# LATEX UTILITIES
# =============================================================================

_LATEX_SPECIAL = {
    '\\': r'\textbackslash{}',
    '{':  r'\{',
    '}':  r'\}',
    '$':  r'\$',
    '&':  r'\&',
    '%':  r'\%',
    '#':  r'\#',
    '_':  r'\_',
    '^':  r'\^{}',
    '~':  r'\textasciitilde{}',
    '<':  r'\textless{}',
    '>':  r'\textgreater{}',
}


def _escape(text: str) -> str:
    """Escape LaTeX-special characters in a plain string."""
    result = []
    for ch in text:
        result.append(_LATEX_SPECIAL.get(ch, ch))
    return ''.join(result)


def richstring_to_latex(rs: RichString) -> str:
    """
    Convert a screenplain RichString (with styled Segments) into LaTeX.
    screenplain already parsed bold/italic/underline for us.
    """
    parts = []
    for seg in rs.segments:
        text = _escape(seg.text)
        styles = seg.styles
        if Bold in styles and Italic in styles:
            text = r'\textbf{\textit{' + text + r'}}'
        elif Bold in styles:
            text = r'\textbf{' + text + r'}'
        elif Italic in styles:
            text = r'\textit{' + text + r'}'
        if Underline in styles:
            text = r'\underline{' + text + r'}'
        parts.append(text)
    return ''.join(parts)


def rich_lines_to_latex(lines) -> str:
    """Join a list of RichStrings with LaTeX line breaks."""
    return r'\\'.join(richstring_to_latex(ln) for ln in lines)


def plain_escape(text: str) -> str:
    """Escape a plain Python string (not a RichString) for LaTeX."""
    return _escape(text)


# =============================================================================
# LATEX PREAMBLE
# =============================================================================

_PREAMBLE = r"""\documentclass[12pt]{article}

%% ---- Packages ----
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{courier}
\usepackage[top=1in, bottom=1in, left=1.5in, right=0.5in]{geometry}
\usepackage{fancyhdr}
\usepackage{multicol}

%% ---- Page style ----
\pagestyle{fancy}
\fancyhf{}
\renewcommand{\headrulewidth}{0pt}
\fancyhead[R]{\footnotesize\thepage.}
\setlength{\headheight}{14pt}

%% ---- Font: Courier throughout ----
\renewcommand{\familydefault}{\ttdefault}

%% ---- Screenplay macros ----

% Scene heading
\newcommand{\Scene}[1]{%
  \vspace{12pt}%
  \noindent\textbf{#1}\par%
  \vspace{4pt}%
}

% Action paragraph
\newcommand{\Action}[1]{%
  \vspace{4pt}%
  \noindent\parbox{\textwidth}{#1}\par%
}

% Centered action
\newcommand{\Centered}[1]{%
  \vspace{4pt}%
  \begin{center}#1\end{center}%
}

% Character/Paren/Dialogue use explicit vspace only — no parskip package.
\newcommand{\Character}[1]{%
  \vspace{8pt}%
  \noindent\hspace{2.5in}#1\par%
  \vspace{2pt}%
}

\newcommand{\Dialogue}[1]{%
  \noindent\hspace{1in}\parbox{\dimexpr\textwidth - 2in}{#1}\par%
  \vspace{6pt}%
}

\newcommand{\Paren}[1]{%
  \vspace{-2pt}%
  \noindent\hspace{1.75in}(#1)\par%
  \vspace{2pt}%
}

% Transition (flush right)
\newcommand{\Trans}[1]{%
  \vspace{6pt}%
  \noindent\hfill #1\par%
  \vspace{6pt}%
}
"""


# =============================================================================
# TITLE PAGE RENDERER
# =============================================================================

def _render_title_page(
    screenplay: Screenplay,
    cli_title: Optional[str],
    cli_author: Optional[str],
    cli_draft_date: Optional[str],
) -> str:
    """Build a LaTeX title page from screenplain's title_page dict."""

    def get(key: str) -> str:
        """Pull a title-page value as plain escaped text."""
        vals = screenplay.title_page.get(key, [])
        return plain_escape(' '.join(str(v) for v in vals))

    def get_rich(key: str) -> str:
        rs_list = screenplay.get_rich_attribute(key)
        return r'\\'.join(richstring_to_latex(rs) for rs in rs_list)

    title = cli_title or get('Title') or get('title')
    author = cli_author or get('Author') or get('author') or get('Authors')
    draft_date = cli_draft_date or get('Draft date') or get('Draft Date')
    contact = get('Contact') or get('contact')

    lines = [
        r'\begin{titlepage}',
        r'\centering',
        r'\vspace*{2in}',
    ]
    if title:
        lines.append(r'{\Huge\textbf{' + title + r'}}\\[18pt]')
    if author:
        lines.append(r'{\large Written by}\\[6pt]')
        lines.append(r'{\large ' + author + r'}\\[12pt]')
    if draft_date:
        lines.append(r'{\normalsize ' + draft_date + r'}\\[6pt]')
    if contact:
        lines.append(r'\vfill')
        lines.append(r'\raggedright\small ' + contact)
    lines += [
        r'\end{titlepage}',
        r'\setcounter{page}{1}',
    ]
    return '\n'.join(lines)


# =============================================================================
# ELEMENT RENDERERS
# =============================================================================

def _render_slug(el: Slug, scene_numbers: bool) -> str:
    text = richstring_to_latex(el.line)
    if scene_numbers and el.scene_number:
        num = richstring_to_latex(el.scene_number)
        text = text + r'\hfill\textbf{' + num + r'}'
    return r'\Scene{' + text + r'}'


def _render_action(el: Action) -> str:
    text = rich_lines_to_latex(el.lines)
    if el.centered:
        return r'\Centered{' + text + r'}'
    return r'\Action{' + text + r'}'


def _render_dialog(el: Dialog) -> str:
    """Render a Dialog block: character name + blocks of dialogue/parens."""
    parts = [r'\Character{' + richstring_to_latex(el.character) + r'}']
    for is_paren, line in el.blocks:
        text = richstring_to_latex(line)
        if is_paren:
            # strip surrounding parens screenplain leaves in the text
            inner = text.lstrip('(').rstrip(')')
            parts.append(r'\Paren{' + inner + r'}')
        else:
            parts.append(r'\Dialogue{' + text + r'}')
    return '\n'.join(parts)


def _render_dual_dialog(el: DualDialog) -> str:
    left = _render_dialog(el.left)
    right = _render_dialog(el.right)
    return (
        r'\begin{multicols}{2}' + '\n'
        + left + '\n'
        + r'\columnbreak' + '\n'
        + right + '\n'
        + r'\end{multicols}'
    )


def _render_transition(el: Transition) -> str:
    return r'\Trans{' + richstring_to_latex(el.line) + r'}'


def _render_section(el: Section) -> str:
    # Section headings (lines starting with #) are structural annotations
    # in Fountain — suppress them from printed output entirely.
    return ''


def _render_page_break(_el: PageBreak) -> str:
    return r'\clearpage'


def _render_element(el, scene_numbers: bool) -> str:
    if isinstance(el, Slug):
        return _render_slug(el, scene_numbers)
    if isinstance(el, Action):
        return _render_action(el)
    if isinstance(el, Dialog):
        return _render_dialog(el)
    if isinstance(el, DualDialog):
        return _render_dual_dialog(el)
    if isinstance(el, Transition):
        return _render_transition(el)
    if isinstance(el, Section):
        return _render_section(el)
    if isinstance(el, PageBreak):
        return _render_page_break(el)
    # Fallback — shouldn't happen, but emit a comment so it's visible
    return '% [unhandled element: %s]' % type(el).__name__


# =============================================================================
# TOP-LEVEL RENDERER
# =============================================================================

def render_latex(
    screenplay: Screenplay,
    cli_title: Optional[str] = None,
    cli_author: Optional[str] = None,
    cli_draft_date: Optional[str] = None,
    include_title_page: bool = True,
    scene_numbers: bool = False,
) -> str:
    parts: List[str] = [_PREAMBLE, r'\begin{document}', '']

    has_title_info = (
        cli_title or cli_author
        or screenplay.title_page.get('Title')
        or screenplay.title_page.get('title')
        or screenplay.title_page.get('Author')
        or screenplay.title_page.get('author')
    )
    if include_title_page and has_title_info:
        parts.append(_render_title_page(screenplay, cli_title, cli_author, cli_draft_date))
        parts.append('')

    for el in screenplay:
        parts.append(_render_element(el, scene_numbers))

    parts += ['', r'\end{document}']
    return '\n'.join(parts)


# =============================================================================
# DEBUG AST DUMP
# =============================================================================

def _dump_ast(screenplay: Screenplay) -> None:
    print("=== TITLE PAGE ===")
    for k, v in screenplay.title_page.items():
        print(f"  {k}: {v}")
    print(f"\n=== ELEMENTS ({len(screenplay.paragraphs)}) ===")
    for i, el in enumerate(screenplay):
        t = type(el).__name__
        if isinstance(el, Slug):
            print(f"  [{i:03d}] {t}: {el.line}")
        elif isinstance(el, Action):
            preview = str(el.lines[0])[:60] if el.lines else ''
            print(f"  [{i:03d}] {t}{'(centered)' if el.centered else ''}: {preview}")
        elif isinstance(el, Dialog):
            print(f"  [{i:03d}] {t}: char={el.character}, blocks={len(el.blocks)}")
        elif isinstance(el, DualDialog):
            print(f"  [{i:03d}] {t}: left={el.left.character} | right={el.right.character}")
        elif isinstance(el, Transition):
            print(f"  [{i:03d}] {t}: {el.line}")
        elif isinstance(el, Section):
            print(f"  [{i:03d}] {t}(level={el.level}): {el.text}")
        elif isinstance(el, PageBreak):
            print(f"  [{i:03d}] {t}")
        else:
            print(f"  [{i:03d}] {t}")


# =============================================================================
# CLI
# =============================================================================

def main() -> int:
    ap = argparse.ArgumentParser(
        prog='fountain2latex',
        description='Convert a Fountain screenplay to LaTeX (uses screenplain parser).',
    )
    ap.add_argument('input', help='Input .fountain file')
    ap.add_argument('-o', '--output', help='Output .tex file (default: same stem)')
    ap.add_argument('--title', help='Override title')
    ap.add_argument('--author', help='Override author')
    ap.add_argument('--draft-date', dest='draft_date', help='Override draft date')
    ap.add_argument(
        '--no-title-page', dest='include_title_page',
        action='store_false', default=True,
        help='Suppress title page',
    )
    ap.add_argument(
        '--scene-numbers', dest='scene_numbers',
        action='store_true', default=False,
        help='Print scene numbers in headings',
    )
    ap.add_argument(
        '--debug-ast', dest='debug_ast',
        action='store_true', default=False,
        help='Dump parsed AST and exit',
    )
    args = ap.parse_args()

    src = Path(args.input)
    if not src.exists():
        print(f'Error: file not found: {src}', file=sys.stderr)
        return 1

    try:
        with src.open(encoding='utf-8') as fh:
            screenplay = sp_parse(fh)
    except Exception as e:
        print(f'Parse error: {e}', file=sys.stderr)
        return 2

    if args.debug_ast:
        _dump_ast(screenplay)
        return 0

    try:
        tex = render_latex(
            screenplay,
            cli_title=args.title,
            cli_author=args.author,
            cli_draft_date=args.draft_date,
            include_title_page=args.include_title_page,
            scene_numbers=args.scene_numbers,
        )
    except Exception as e:
        print(f'Render error: {e}', file=sys.stderr)
        return 3

    dst = Path(args.output) if args.output else src.with_suffix('.tex')
    try:
        dst.write_text(tex, encoding='utf-8')
    except OSError as e:
        print(f'Error writing {dst}: {e}', file=sys.stderr)
        return 1

    print(f'Written: {dst}')
    print(f'Compile: pdflatex -interaction=nonstopmode "{dst}"')
    return 0


if __name__ == '__main__':
    sys.exit(main())
