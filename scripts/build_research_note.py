"""Render the project's compact Markdown research note with existing ReportLab."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import quote
from xml.sax.saxutils import escape

import reportlab
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_COMMIT = "21bf13e4888c24f2f05f1ff21708a175bcb155c5"
BASE = f"https://github.com/Siquan-Wang/alpha-research-rl/blob/{EVIDENCE_COMMIT}/"
BLUE = colors.HexColor("#245873")
INK = colors.HexColor("#25323d")
MUTED = colors.HexColor("#586773")
WIDTH = letter[0] - 92


def normalize(text):
    # Use ordinary hyphens in text for portable extraction and line breaking.
    return text.translate(str.maketrans({"\u2010": "-", "\u2011": "-", "\u2012": "-",
                                        "\u2013": "-", "\u2014": "-", "\u2212": "-"}))


def register_fonts():
    folder = Path(reportlab.__file__).parent / "fonts"
    for name, file in (("Note", "Vera.ttf"), ("Note-Bold", "VeraBd.ttf"),
                       ("Note-Italic", "VeraIt.ttf"), ("Note-BoldItalic", "VeraBI.ttf")):
        pdfmetrics.registerFont(TTFont(name, str(folder / file)))
    pdfmetrics.registerFontFamily("Note", normal="Note", bold="Note-Bold", italic="Note-Italic",
                                  boldItalic="Note-BoldItalic")


def link_target(raw, source):
    if raw.startswith(("https://", "http://")):
        return raw
    path, _, fragment = raw.partition("#")
    target = (source.parent / path).resolve() if path else source.resolve()
    relative = target.relative_to(ROOT)
    if not target.is_file():
        raise ValueError(f"Missing manuscript reference: {relative}")
    return BASE + quote(relative.as_posix(), safe="/") + ("#" + quote(fragment) if fragment else "")


def inline(text, source):
    pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)|\*\*(.+?)\*\*|`([^`]+)`|(?<!\*)\*([^*]+)\*(?!\*)")
    parts, cursor = [], 0
    for match in pattern.finditer(text):
        parts.append(escape(normalize(text[cursor:match.start()])))
        label, url, bold, code, italic = match.groups()
        if label is not None:
            target = escape(link_target(url, source), {'"': '&quot;'})
            parts.append(f'<a href="{target}" color="#245873">{inline(label, source)}</a>')
        elif bold is not None:
            parts.append(f"<b>{inline(bold, source)}</b>")
        elif code is not None:
            parts.append(f'<font name="Courier" size="9">{escape(normalize(code))}</font>')
        else:
            parts.append(f"<i>{inline(italic, source)}</i>")
        cursor = match.end()
    parts.append(escape(normalize(text[cursor:])))
    return "".join(parts)


def styles():
    body = ParagraphStyle("Body", fontName="Note", fontSize=10.1, leading=14.1,
                          textColor=INK, spaceAfter=8.5, allowWidows=0, allowOrphans=0)
    return {
        "body": body,
        "title": ParagraphStyle("Title", parent=body, fontName="Note-Bold", fontSize=24,
                                leading=29, spaceAfter=16, keepWithNext=True),
        "h2": ParagraphStyle("H2", parent=body, fontName="Note-Bold", fontSize=13,
                             leading=17, spaceBefore=13, spaceAfter=7, keepWithNext=True, textColor=BLUE),
        "h3": ParagraphStyle("H3", parent=body, fontName="Note-Bold", fontSize=10.8,
                             leading=14.5, spaceBefore=8, spaceAfter=5, keepWithNext=True),
        "caption": ParagraphStyle("Caption", parent=body, fontSize=8.4, leading=11.5,
                                  textColor=MUTED, spaceAfter=12),
        "cell": ParagraphStyle("Cell", parent=body, fontSize=8.1, leading=11,
                               spaceAfter=0, allowWidows=1, allowOrphans=1),
        "headcell": ParagraphStyle("HeadCell", parent=body, fontName="Note-Bold", fontSize=8.1,
                                   leading=11, textColor=colors.white, spaceAfter=0),
        "bullet": ParagraphStyle("Bullet", parent=body, leftIndent=11, firstLineIndent=-8,
                                  spaceAfter=5),
        "code": ParagraphStyle("Equation", fontName="Courier", fontSize=8.6, leading=12.3,
                                leftIndent=9, spaceBefore=4, spaceAfter=10, textColor=INK),
    }


def page_frame(canvas, doc):
    canvas.saveState()
    canvas.setFont("Note-Bold", 8)
    canvas.setFillColor(BLUE)
    canvas.drawString(46, letter[1] - 31, "ALPHARESEARCH-RL  /  RESEARCH NOTE")
    canvas.setStrokeColor(colors.HexColor("#d7e0e5"))
    canvas.line(46, letter[1] - 39, letter[0] - 46, letter[1] - 39)
    canvas.setFillColor(MUTED)
    canvas.setFont("Note", 7.4)
    canvas.drawString(46, 28, "October 2026  |  Development evidence; no profitability claim")
    canvas.drawRightString(letter[0] - 46, 28, str(doc.page))
    canvas.restoreState()


def table_flow(lines, source, style):
    rows = [[cell.strip() for cell in line.strip().strip("|").split("|")] for line in lines]
    if len(rows) < 3 or not all(re.fullmatch(r":?-+:?", cell) for cell in rows[1]):
        raise ValueError("Expected a Markdown table header separator")
    rows.pop(1)
    count = len(rows[0])
    if not all(len(row) == count for row in rows):
        raise ValueError("Unequal manuscript table widths")
    weights = [max(len(re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", row[i])) for row in rows)
               for i in range(count)]
    weights = [max(16, min(75, weight)) ** .55 for weight in weights]
    widths = [WIDTH * weight / sum(weights) for weight in weights]
    cells = [[Paragraph(inline(cell, source), style["headcell" if i == 0 else "cell"])
              for cell in row] for i, row in enumerate(rows)]
    table = Table(cells, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f0f4f6"), colors.white]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LINEBELOW", (0, 0), (-1, 0), .5, colors.white),
    ]))
    return [table, Spacer(1, 11)]


def build_story(source, style):
    lines = source.read_text(encoding="utf-8").splitlines()
    story, i, title = [], 0, None
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith("# "):
            if title is not None:
                raise ValueError("Only one manuscript title is supported")
            title = line[2:]
            story.append(Paragraph(inline(title, source), style["title"]))
            i += 1
        elif line.startswith(("## ", "### ")):
            heading, key = (line[4:], "h3") if line.startswith("### ") else (line[3:], "h2")
            if key == "h2" and heading.startswith(("5. ", "6. ", "7. ")):
                story.append(PageBreak())
            story.append(Paragraph(inline(heading, source), style[key]))
            i += 1
        elif line.startswith("```"):
            block, i = [], i + 1
            while i < len(lines) and not lines[i].startswith("```"):
                if len(lines[i]) > 92:
                    raise ValueError("Shorten a manuscript equation line to fit the page")
                block.append(normalize(lines[i]))
                i += 1
            if i == len(lines):
                raise ValueError("Unclosed equation block")
            story.append(Preformatted("\n".join(block), style["code"]))
            i += 1
        elif line.startswith("|"):
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append(lines[i])
                i += 1
            story.extend(table_flow(block, source, style))
        elif line.startswith("!["):
            match = re.fullmatch(r"!\[([^]]*)\]\(([^)]+)\)", line)
            if not match:
                raise ValueError("Unsupported figure syntax")
            caption, relative = match.groups()
            # Keep the authored numbered caption with its figure, not a second alt-text caption.
            following = i + 1
            while following < len(lines) and not lines[following].strip():
                following += 1
            if following < len(lines) and re.match(r"\*Figure \d+\.", lines[following].strip()):
                caption = lines[following].strip()
                i = following
            image_path = (source.parent / relative).resolve()
            image_path.relative_to(ROOT)
            figure = Image(str(image_path))
            height = WIDTH * figure.imageHeight / figure.imageWidth
            if height > 450:
                raise ValueError("Figure exceeds the note's page layout")
            figure.drawWidth, figure.drawHeight = WIDTH, height
            story.append(KeepTogether([Spacer(1, 5), figure, Spacer(1, 6),
                                        Paragraph(inline(caption, source), style["caption"])]))
            i += 1
        elif re.match(r"(?:- |\d+\. )", line):
            prefix, value = re.match(r"(- |\d+\. )(.*)", line).groups()
            i += 1
            while i < len(lines) and lines[i].startswith("  "):
                value += " " + lines[i].strip()
                i += 1
            label = "- " if prefix == "- " else prefix
            story.append(Paragraph(escape(label) + inline(value, source), style["bullet"]))
        elif line == "---":
            story.extend([HRFlowable(width="100%", color=colors.HexColor("#d7e0e5")), Spacer(1, 8)])
            i += 1
        else:
            paragraph = [line]
            i += 1
            while i < len(lines) and lines[i].strip():
                if re.match(r"^(#|\||```|!\[|- |\d+\. )", lines[i]):
                    break
                paragraph.append(lines[i].strip())
                i += 1
            story.append(Paragraph(inline(" ".join(paragraph), source), style["body"]))
    if title is None:
        raise ValueError("The manuscript needs a title")
    return story, normalize(title)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "docs/research-note-v1.md")
    parser.add_argument("--output", type=Path, default=ROOT / "output/pdf/alpha-research-note-v1.pdf")
    args = parser.parse_args()
    register_fonts()
    story, title = build_story(args.source.resolve(), styles())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(args.output), pagesize=letter, leftMargin=46, rightMargin=46,
                            topMargin=54, bottomMargin=46, title=title, author="AlphaResearch-RL project",
                            subject="Bounded empirical evidence on language-model factor research",
                            pageCompression=1, invariant=1)
    doc.build(story, onFirstPage=page_frame, onLaterPages=page_frame)
    print(json.dumps({"output": str(args.output), "pages": doc.page,
                      "manuscript_sha256": hashlib.sha256(args.source.read_bytes()).hexdigest(),
                      "pdf_sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
                      "reportlab_version": reportlab.Version}))


if __name__ == "__main__":
    main()
