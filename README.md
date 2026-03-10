# fountain2latex
This python program uses screenplain (www.screenplain.com, also on gitbub) to help parse a fountain screenplay into latex, which then can be edited or directly compiled to a pdf. It's a Python command-line tool that converts [Fountain](https://fountain.io) screenplay files to LaTeX (`.tex`), producing Hollywood-standard screenplay formatting when compiled with `pdflatex`.

It uses [screenplain](https://github.com/vilcans/screenplain) as its Fountain parser, so it inherits screenplain's battle-tested handling of the Fountain spec. The LaTeX renderer is custom, giving you a fully editable `.tex` file you can diff, version-control, and customize.

---

## Requirements

- Python 3.8+
- [screenplain](https://github.com/vilcans/screenplain)
- A LaTeX distribution with `pdflatex` (e.g. [TeX Live](https://www.tug.org/texlive/) or [MiKTeX](https://miktex.org/))

Install screenplain:

```bash
pip install screenplain
```

---

## Usage

```bash
python fountain2latex_v2.py input.fountain
```

This produces `input.tex` in the same directory. Then compile:

```bash
pdflatex -interaction=nonstopmode input.tex
pdflatex -interaction=nonstopmode input.tex   # run twice to fix page numbers
```

---

## Options

| Flag | Description |
|------|-------------|
| `input` | Path to the `.fountain` source file (required) |
| `-o`, `--output` | Output `.tex` path (default: same stem as input) |
| `--title "..."` | Override the screenplay title |
| `--author "..."` | Override the author name |
| `--draft-date "..."` | Override the draft date |
| `--no-title-page` | Suppress title page generation |
| `--scene-numbers` | Print scene numbers in scene headings |
| `--debug-ast` | Dump the parsed element list to stdout and exit (useful for diagnosing parse issues) |

---

## Fountain syntax supported

fountain2latex supports the core Fountain specification via screenplain. The examples below are drawn from Anton Chekhov's *The Proposal* (1888, public domain).

### Title page

```
Title: THE PROPOSAL
Author: Anton Chekhov
Draft date: 1888
Contact: Public Domain
Notes: A Jest in One Act. Translated from the Russian.
```

### Scene headings

```
INT. CHUBUKOV'S COUNTRY HOUSE - DAY
```

Force a scene heading with a leading `.`:

```
.FLASHBACK - THE MEADOWS - 1850
```

### Action

```
A well-appointed drawing room. STEPAN STEPANOVITCH CHUBUKOV,
a landowner, stands near a window. His neighbor, IVAN
VASSILEVITCH LOMOV, enters wearing a dress coat and white gloves.
He is nervous, excitable, and prone to palpitations.
```

### Character and dialogue

```
LOMOV
Thank you. And how are you, Stepan Stepanovitch?

CHUBUKOV
Oh, bearing up, bearing up, my angel, thanks to your
prayers and all the rest of it. Do sit down...
```

### Parentheticals

```
CHUBUKOV
(going to meet him, beaming)
Ivan Vassilevitch! What a surprise! My dear fellow!
```

### CONT'D

Write it directly as part of the character name — screenplain passes it through automatically:

```
LOMOV (CONT'D)
I am thirty-five years old. I need a quiet, settled life.
My heart is weak — I have palpitations all the time.
```

### Transitions

```
FADE IN:

FADE OUT.
```

Force a transition with `>`:

```
> SMASH CUT TO:
```

### Centered text

```
> THE END <
```

### Dual dialogue

```
CHUBUKOV ^
Ours!

LOMOV
Mine!
```

### Inline emphasis

```
The boundary is _clearly marked_ on the survey.

He speaks *very* quietly now.

She holds the document marked **DISPUTED**.
```

### Page breaks

```
===
```

### Notes and boneyard (stripped from output)

```
[[Reminder: Lomov's palpitations should escalate through the scene]]

/* This entire block is commented out
   and will not appear in output */
```

### Sections (stripped from output)

Section headings (lines starting with `#`) are structural annotations used in writing tools. They are silently removed from the LaTeX output and do not appear in the compiled PDF.

```
# Act One
## The Proposal
```

---

## Formatting defaults

The generated LaTeX uses Hollywood-standard screenplay margins and Courier font throughout:

| Element | Formatting |
|---------|-----------|
| Page margins | 1.5in left, 0.5in right, 1in top/bottom |
| Font | Courier 12pt |
| Scene headings | Bold, full text width |
| Action | Full text width, ragged right |
| Character cues | ~2.5in from left margin, not bolded |
| Dialogue | Indented 1in from left margin |
| Parentheticals | Indented 1.75in from left margin |
| Transitions | Flush right |
| Page numbers | Upper right |

---

## Customizing formatting

All formatting is controlled by LaTeX macros defined in the preamble of the generated `.tex` file — or equivalently in the `_PREAMBLE` string in `fountain2latex_v2.py`. You can edit them directly without touching any Python logic.

Key macros:

```latex
\newcommand{\Scene}[1]{...}       % Scene headings
\newcommand{\Action}[1]{...}      % Action paragraphs
\newcommand{\Character}[1]{...}   % Character cues
\newcommand{\Dialogue}[1]{...}    % Dialogue lines
\newcommand{\Paren}[1]{...}       % Parentheticals
\newcommand{\Trans}[1]{...}       % Transitions
\newcommand{\Centered}[1]{...}    % Centered text
```

All spacing is controlled by explicit `\vspace` values within these macros — there is no `parskip` magic. To adjust spacing, change the relevant `\vspace` value directly. For example, to increase space before each character block, change `\vspace{8pt}` in `\Character`. To adjust the dialogue column width, change the `\hspace` indent and the `\parbox` width in `\Dialogue` together — they must be consistent to keep the right edge aligned.

---

## Example end-to-end

Given `the_proposal.fountain`:

```
Title: THE PROPOSAL
Author: Anton Chekhov
Draft date: 1888

FADE IN:

INT. CHUBUKOV'S COUNTRY HOUSE - DAY

A well-appointed drawing room. CHUBUKOV stands near a window.
LOMOV enters wearing a dress coat and white gloves.

CHUBUKOV
(going to meet him, beaming)
Ivan Vassilevitch! What a surprise! My dear fellow!

LOMOV
Thank you. And how are you, Stepan Stepanovitch?

CHUBUKOV
Oh, bearing up, bearing up, my angel, thanks to your
prayers and all the rest of it. Do sit down...

FADE OUT.
```

Run:

```bash
python fountain2latex_v2.py the_proposal.fountain
pdflatex -interaction=nonstopmode the_proposal.tex
pdflatex -interaction=nonstopmode the_proposal.tex
```

---

## Debugging

If elements are being misclassified (e.g. a character name parsed as action, or a transition missed), use `--debug-ast` to inspect what screenplain produced:

```bash
python fountain2latex_v2.py the_proposal.fountain --debug-ast
```

Output looks like:

```
=== TITLE PAGE ===
  Title: ['THE PROPOSAL']
  Author: ['Anton Chekhov']
  Draft date: ['1888']

=== ELEMENTS (12) ===
  [000] Slug: INT. CHUBUKOV'S COUNTRY HOUSE - DAY
  [001] Action: A well-appointed drawing room. CHUBUKOV stands...
  [002] Dialog: char=CHUBUKOV, blocks=2
  [003] Dialog: char=LOMOV, blocks=1
  ...
```

If a character name is not being recognized (e.g. it contains lowercase letters), prefix it with `@` in your Fountain source to force character classification:

```
@Natalia
(in a whisper)
He came to propose.
```

---

## Credits

- Fountain parsing by [screenplain](https://github.com/vilcans/screenplain) (Martin Vilcans), MIT license (also at screenplain.com)
- LaTeX renderer by David Joyner
- [Fountain format](https://fountain.io) by Stu Maschwitz and John August
- Example script: *The Proposal* by Anton Chekhov (1888, public domain)
