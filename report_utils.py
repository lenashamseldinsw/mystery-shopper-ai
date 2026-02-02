from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import io
import re
import os


class DOCXBuilder:
    def __init__(self):
        self.font = "Arial"

    # -------------------------------------------------
    # Base document
    # -------------------------------------------------
    def create_document(self):
        doc = Document()
        section = doc.sections[0]
        section.right_margin = Inches(1)
        section.left_margin = Inches(1)
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        return doc

    # -------------------------------------------------
    # Logo (safe)
    # -------------------------------------------------
    def add_logo_header(self, doc, logo_path):
        if logo_path and os.path.exists(logo_path):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.add_run().add_picture(logo_path, width=Inches(2.5))

    # -------------------------------------------------
    # Titles
    # -------------------------------------------------
    def add_title_section(self, doc, text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p.paragraph_format.right_to_left = True
        run = p.add_run(text)
        run.bold = True
        run.font.size = Pt(18)
        run.font.name = self.font

    def add_section_header(self, doc, text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p.paragraph_format.right_to_left = True
        run = p.add_run(text)
        run.bold = True
        run.font.size = Pt(14)
        run.font.name = self.font

    def add_footer(self, doc, text):
        f = doc.sections[0].footer.paragraphs[0]
        f.alignment = WD_ALIGN_PARAGRAPH.CENTER
        f.paragraph_format.right_to_left = True
        f.add_run(text).font.size = Pt(9)

    # -------------------------------------------------
    # Word-native Arabic numbering + bullets
    # -------------------------------------------------
    def _ensure_numbering(self, doc):
        numbering = doc.part.numbering_part.numbering_definitions._numbering
        if numbering.findall(qn("w:num")):
            return

        def _lvl(ilvl, fmt, txt):
            lvl = OxmlElement("w:lvl")
            lvl.set(qn("w:ilvl"), str(ilvl))

            start = OxmlElement("w:start")
            start.set(qn("w:val"), "1")

            numFmt = OxmlElement("w:numFmt")
            numFmt.set(qn("w:val"), fmt)

            lvlText = OxmlElement("w:lvlText")
            lvlText.set(qn("w:val"), txt)

            jc = OxmlElement("w:lvlJc")
            jc.set(qn("w:val"), "right")

            pPr = OxmlElement("w:pPr")
            bidi = OxmlElement("w:bidi")
            bidi.set(qn("w:val"), "1")

            ind = OxmlElement("w:ind")
            ind.set(qn("w:right"), "720")
            ind.set(qn("w:hanging"), "360")

            pPr.extend([bidi, ind])
            lvl.extend([start, numFmt, lvlText, jc, pPr])
            return lvl

        abstract = OxmlElement("w:abstractNum")
        abstract.set(qn("w:abstractNumId"), "0")
        abstract.append(_lvl(0, "decimal", "%1."))
        numbering.append(abstract)

        num = OxmlElement("w:num")
        num.set(qn("w:numId"), "1")
        aid = OxmlElement("w:abstractNumId")
        aid.set(qn("w:val"), "0")
        num.append(aid)
        numbering.append(num)

        # bullets
        abstract_b = OxmlElement("w:abstractNum")
        abstract_b.set(qn("w:abstractNumId"), "1")
        abstract_b.append(_lvl(0, "bullet", "•"))
        numbering.append(abstract_b)

        num_b = OxmlElement("w:num")
        num_b.set(qn("w:numId"), "2")
        aid_b = OxmlElement("w:abstractNumId")
        aid_b.set(qn("w:val"), "1")
        num_b.append(aid_b)
        numbering.append(num_b)

    def _numbered(self, doc, text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p.paragraph_format.right_to_left = True

        pPr = p._p.get_or_add_pPr()
        numPr = OxmlElement("w:numPr")
        ilvl = OxmlElement("w:ilvl")
        ilvl.set(qn("w:val"), "0")
        numId = OxmlElement("w:numId")
        numId.set(qn("w:val"), "1")
        numPr.extend([ilvl, numId])
        pPr.append(numPr)

        run = p.add_run(text)
        run.font.name = self.font
        run.font.size = Pt(12)

    def _bullet(self, doc, text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p.paragraph_format.right_to_left = True

        pPr = p._p.get_or_add_pPr()
        numPr = OxmlElement("w:numPr")
        ilvl = OxmlElement("w:ilvl")
        ilvl.set(qn("w:val"), "0")
        numId = OxmlElement("w:numId")
        numId.set(qn("w:val"), "2")
        numPr.extend([ilvl, numId])
        pPr.append(numPr)

        run = p.add_run(text)
        run.font.name = self.font
        run.font.size = Pt(12)

    # -------------------------------------------------
    # Dispatcher
    # -------------------------------------------------
    def add_formatted_paragraph(self, doc, content):
        self._ensure_numbering(doc)

        for line in content.split("\n"):
            line = line.strip()
            if not line:
                doc.add_paragraph("")
                continue

            if re.match(r"^\d+\.\s+", line):
                self._numbered(doc, re.sub(r"^\d+\.\s+", "", line))
            elif line.startswith("•"):
                self._bullet(doc, line[1:].strip())
            else:
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                p.paragraph_format.right_to_left = True
                run = p.add_run(line)
                run.font.name = self.font
                run.font.size = Pt(12)

    def save_to_buffer(self, doc):
        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        return buf


class ContentProcessor:
    @staticmethod
    def parse_sections_from_text(text):
        sections = {}
        current = None
        buff = []

        for line in text.split("\n"):
            if line.startswith("==="):
                if current:
                    sections[current] = "\n".join(buff).strip()
                current = line.replace("=", "").strip()
                buff = []
            else:
                buff.append(line)

        if current:
            sections[current] = "\n".join(buff).strip()
        return sections
