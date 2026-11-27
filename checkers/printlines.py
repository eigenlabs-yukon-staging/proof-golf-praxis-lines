"""Printed lines of a result's statement and proof, as typeset in the Praxis paper (llncs, 10 pt New Computer
Modern, 6.5 in text width): a standard-library model of TeX's paragraph filling, from the fonts' own glyph
widths (widths.json). Markup costs nothing; what prints costs its width."""
import json, math, os, re

W = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "widths.json")))
W = {f: {int(k): v for k, v in t.items()} for f, t in W.items()}
PT = 10.0 / 1000                    # font units (per 1000 em) to points at 10 pt
TEXTWIDTH = 468.0                   # 6.5 in
PARINDENT = 15.0
SPACE, SHRINK = 3.33, 1.11
REL = {"=", "<", ">", "\\le", "\\leq", "\\ge", "\\geq", "\\ne", "\\neq", "\\in", "\\notin", "\\subseteq", "\\subset",
       "\\supseteq", "\\to", "\\mapsto", "\\equiv", "\\approx", "\\sim", "\\coloneqq", "\\defeq", ":=", "\\iff",
       "\\implies", "\\Rightarrow", "\\leftarrow", "\\gets", "\\mid", "\\perp", "\\cong", "\\simeq", "\\propto", "\\ll", "\\gg"}
BIN = {"+", "-", "\\cdot", "\\times", "\\oplus", "\\otimes", "\\cup", "\\cap", "\\pm", "\\setminus", "\\wedge", "\\vee", "\\circ", "\\star", "*"}
GREEK = "alpha beta gamma delta epsilon varepsilon zeta eta theta vartheta iota kappa lambda mu nu xi pi varpi rho varrho sigma varsigma tau upsilon phi varphi chi psi omega".split()
UGREEK = "Gamma Delta Theta Lambda Xi Pi Sigma Upsilon Phi Psi Omega".split()
ZERO = set("left right big Big bigg Bigg bigl bigr Bigl Bigr biggl biggr displaystyle textstyle scriptstyle limits nolimits label nonumber notag qedhere noindent par medskip smallskip bigskip allowbreak hfill centering phantom hphantom vphantom strut relax protect".split())
STYLE_TEXT = set("text textrm textup textnormal mathrm operatorname mathsf textsf mathtt texttt mbox hbox".split())
STYLE_IT = set("textit emph mathit".split())
STYLE_BF = set("textbf mathbf boldsymbol bm".split())
ACCENT = set("hat widehat bar overline tilde widetilde vec dot ddot underline check breve".split())
NAMED = {"log", "exp", "ln", "det", "dim", "deg", "gcd", "max", "min", "Pr", "ker", "rank", "lcm", "sup", "inf",
         "lim", "sin", "cos", "mod", "bmod", "arg", "tr", "Tr"}
WIDE = {"ldots": 1500, "cdots": 1500, "dots": 1500, "quad": 1000, "qquad": 2000, "sum": 1056, "prod": 944,
        "infty": 1000, "partial": 556, "forall": 556, "exists": 556, "emptyset": 500, "varnothing": 500,
        "langle": 389, "rangle": 389, "lfloor": 444, "rfloor": 444, "lceil": 444, "rceil": 444, "|": 500,
        "{": 500, "}": 500, "neg": 667, "top": 778, "bot": 778, "ell": 417, "nabla": 833, "prime": 275}


def gw(ch, font):
    t = W.get(font, W["rm"])
    return t.get(ord(ch), W["rm"].get(ord(ch), 500)) * PT


def textw(s, font="rm"):
    return sum(gw(c, font) for c in s)


def mathletter(c):
    if "a" <= c <= "z":
        return 0x210E if c == "h" else 0x1D44E + ord(c) - 97
    if "A" <= c <= "Z":
        return 0x1D434 + ord(c) - 65
    return ord(c)


def group(s, i):
    """The {...} group or single token at s[i]; returns (content, next index)."""
    while i < len(s) and s[i] == " ":
        i += 1
    if i < len(s) and s[i] == "{":
        d = 0
        for j in range(i, len(s)):
            d += (s[j] == "{") - (s[j] == "}")
            if d == 0:
                return s[i + 1:j], j + 1
        return s[i + 1:], len(s)
    if i < len(s) and s[i] == "\\":
        m = re.match(r"\\([A-Za-z]+|.)", s[i:], re.S)
        return (m.group(0), i + len(m.group(0))) if m else ("", len(s))
    return (s[i], i + 1) if i < len(s) else ("", i)


def mathw(s, scale=1.0):
    """Width of a math formula; returns a list of (width, breakable_after) chunks at the top level."""
    chunks, cur, i = [], 0.0, 0
    def put(w):
        nonlocal cur
        cur += w * scale
    def addabs(w):
        nonlocal cur
        cur += w
    def brk(w):
        nonlocal cur
        cur += w * scale
        chunks.append(cur)
        cur = 0.0
    while i < len(s):
        c = s[i]
        if c in " \n\t&":
            i += 1
            continue
        if c in "^_":
            arg, i = group(s, i + 1)
            addabs(sum(mathw(arg, scale * 0.7)))
            continue
        if c in "{}":
            i += 1
            continue
        if c == "\\":
            m = re.match(r"\\([A-Za-z]+|.)", s[i:], re.S)
            if not m:
                i += 1; continue
            name = m.group(1); i += len(m.group(0))
            if name in ZERO:
                if name == "label":
                    _, i = group(s, i)
                continue
            if name in (",", ";", ":", "!", " "):
                put({",": 1.67, ";": 2.78, ":": 2.22, "!": -1.67, " ": 3.33}[name]); continue
            if name in ("frac", "dfrac", "tfrac", "binom"):
                a, i = group(s, i); b, i = group(s, i)
                addabs(max(sum(mathw(a, scale * 0.7)), sum(mathw(b, scale * 0.7))) + 2.4 * scale); continue
            if name == "sqrt":
                if i < len(s) and s[i] == "[":
                    j = s.index("]", i); i = j + 1
                a, i = group(s, i); addabs(sum(mathw(a, scale)) + 8.3 * scale); continue
            if name in STYLE_TEXT or name in STYLE_BF or name in STYLE_IT:
                a, i = group(s, i)
                f = "bf" if name in STYLE_BF else ("it" if name in STYLE_IT else "rm")
                if name in ("mathbf", "boldsymbol", "bm") or name in STYLE_IT or name in ("mathrm", "mathsf", "mathtt", "operatorname"):
                    put(textw(re.sub(r"\\[A-Za-z]+|[{}]", "", a), f) * (1.0 if name != "mathsf" else 0.95) + (1.67 if name == "operatorname" else 0))
                else:
                    put(sum(w for w, _ in textline(a, f)))
                continue
            if name in ("mathbb", "mathcal", "mathfrak", "mathscr"):
                a, i = group(s, i); put(7.3 * max(1, len(re.sub(r"\\[A-Za-z]+|[{}\s]", "", a)))); continue
            if name in ACCENT:
                a, i = group(s, i); addabs(sum(mathw(a, scale))); continue
            if name in ("cref", "Cref", "ref", "eqref"):
                _, i = group(s, i); put(textw("Lemma B.12")); continue
            if name in GREEK:
                put(gw(chr(0x1D6FC + GREEK.index(name) % 25), "math") if False else 5.8); continue
            if name in UGREEK:
                put(7.2); continue
            if name in NAMED:
                put(textw(name) + 1.67); continue
            if name in WIDE:
                put(WIDE[name] * PT); continue
            if "\\" + name in REL:
                brk(7.78 + 5.56); continue
            if "\\" + name in BIN:
                brk(7.78 + 4.44); continue
            put(7.0)                                   # any other symbol or user macro: one glyph
            continue
        if c in "=<>":
            i += 1; brk(7.78 + 5.56); continue
        if c in "+-*":
            i += 1; brk(7.78 + 4.44); continue
        if c == ",":
            i += 1; brk(2.78 + 1.67); continue
        i += 1
        if c.isdigit() or c in "()[]|/.;:!'":
            put(gw(c, "rm"))
        else:
            put(W["math"].get(mathletter(c), 500) * PT)
    chunks.append(cur)
    return chunks


def textline(s, font):
    """Words of running text: list of (width, is_word_end) boxes; math is split at its break points."""
    boxes, i, word = [], 0, 0.0
    def end():
        nonlocal word
        if word:
            boxes.append((word, True)); word = 0.0
    while i < len(s):
        c = s[i]
        if c.isspace() or c == "~":
            if c == "~":
                word += SPACE; i += 1; continue
            end(); i += 1; continue
        if c == "$" or s.startswith("\\(", i):
            if s.startswith("\\(", i):
                j = s.find("\\)", i + 2); body = s[i + 2:j if j >= 0 else len(s)]; i = (j + 2) if j >= 0 else len(s)
            else:
                j = s.find("$", i + 1); body = s[i + 1:j if j >= 0 else len(s)]; i = (j + 1) if j >= 0 else len(s)
            ch = mathw(body)
            for k, w in enumerate(ch):
                word += w
                if k < len(ch) - 1:
                    boxes.append((word, True)); word = 0.0
            continue
        if c == "\\":
            m = re.match(r"\\([A-Za-z]+|.)", s[i:], re.S)
            if not m:
                i += 1; continue
            name = m.group(1); i += len(m.group(0))
            if name in ZERO:
                if name == "label":
                    _, i = group(s, i)
                continue
            if name in ("cref", "Cref", "ref", "eqref"):
                _, i = group(s, i); word += textw("Lemma B.12", font); continue
            if name in ("cite", "citep", "citet"):
                if i < len(s) and s[i] == "[":
                    j = s.index("]", i); word += textw(s[i + 1:j], font) + SPACE; i = j + 1
                _, i = group(s, i); word += textw("[AB12]", font); continue
            if name in STYLE_TEXT or name in STYLE_IT or name in STYLE_BF:
                a, i = group(s, i)
                f = "bf" if name in STYLE_BF else ("it" if name in STYLE_IT and font != "it" else font)
                for w, e in textline(a, f):
                    word += w
                    if e:
                        boxes.append((word, True)); word = 0.0
                continue
            if name in (",", " "):
                word += 1.67 if name == "," else SPACE; continue
            if name in ("ldots", "dots"):
                word += 15.0; continue
            if len(name) == 1:
                word += gw(name, font); continue
            word += 7.0
            continue
        if c in "{}":
            i += 1; continue
        word += gw(c, font); i += 1
    end()
    return boxes


def fill(boxes, first_indent=PARINDENT):
    """Greedy TeX-like filling (spaces may shrink); a too-long box hyphenates across lines."""
    if not boxes:
        return 0
    lines, cur, n = 1, first_indent, 0
    for w, _ in boxes:
        need = cur + (SPACE if n else 0) + w
        if need - SHRINK * n <= TEXTWIDTH or n == 0 and cur + w <= TEXTWIDTH:
            cur = need; n += 1
        else:
            rest = w
            # hyphenation: a long word starts on this line when at least a third fits
            if w > 40 and TEXTWIDTH - cur - SPACE > w / 3:
                rest = w - (TEXTWIDTH - cur - SPACE)
            lines += 1; cur, n = rest, 1
            while cur > TEXTWIDTH:
                lines += 1; cur -= TEXTWIDTH
    return lines


DISPLAY = re.compile(r"\\\[(.*?)\\\]|\$\$(.*?)\$\$|\\begin\{(equation\*?|align\*?|gather\*?|multline\*?|alignat\*?)\}(.*?)\\end\{\3\}", re.S)


def block_lines(text, font, head=None):
    """Lines of one statement or proof: paragraphs, list items, and display formulas."""
    text = text or ""
    total, pieces, last = 0.0, [], 0
    for m in DISPLAY.finditer(text):
        pieces.append(("t", text[last:m.start()]))
        body = m.group(1) or m.group(2) or m.group(4) or ""
        pieces.append(("d", body)); last = m.end()
    pieces.append(("t", text[last:]))
    first = True
    for kind, p in pieces:
        if kind == "d":
            rows = [r for r in re.split(r"\\\\", p) if r.strip()]
            for r in rows:
                w = sum(mathw(r))
                total += max(1, math.ceil(w / TEXTWIDTH)) + (1 if re.search(r"\\[dt]?frac", r) else 0)
            continue
        paras = re.split(r"\n\s*\n|\\item\b|\\begin\{(?:enumerate|itemize|description)\}(?:\[[^\]]*\])?|\\end\{(?:enumerate|itemize|description)\}", p)
        for k, para in enumerate(paras):
            if not para.strip():
                continue
            boxes = textline(para, font)
            if first and head:
                boxes = textline(head, "bf") + boxes
            total += fill(boxes, 0 if first else PARINDENT)
            first = False
    if first and head:
        total += 1
    return total


RESULTS = ("lemma", "proposition", "theorem", "corollary")


def node_lines(n, label=None):
    """Printed lines of a result: its header and statement (italic, as llncs sets lemmas) and its proof."""
    if n.get("kind") not in RESULTS:
        return 0.0
    head = (label or "Lemma B.12") + " (" + (n.get("name") or "") + ")."
    return block_lines(n.get("statement"), "it", head) + block_lines(n.get("proof"), "rm", "Proof.")
