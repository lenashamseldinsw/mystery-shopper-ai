from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
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
    # Logo
    # -------------------------------------------------
    def add_logo_header(self, doc, logo_path):
        if logo_path and os.path.exists(logo_path):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.add_run().add_picture(logo_path, width=Inches(2.5))

    # -------------------------------------------------
    # Titles & headers (NOT lists)
    # -------------------------------------------------
    def add_title_section(self, doc, text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
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

    # -------------------------------------------------
    # Footer
    # -------------------------------------------------
    def add_footer(self, doc, text):
        footer = doc.sections[0].footer
        p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.right_to_left = True

        run = p.add_run(text)
        run.font.name = self.font
        run.font.size = Pt(9)

    # -------------------------------------------------
    # LISTS — Word-native ONLY (this is the fix)
    # -------------------------------------------------

    # ✅ This is the SAME bullet behavior from the point where bullets worked
    def _add_bullet_item(self, doc, text):
        p = doc.add_paragraph(style="List Bullet")
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p.paragraph_format.right_to_left = True

        run = p.add_run(text)
        run.font.name = self.font
        run.font.size = Pt(12)

    # ✅ Fixed numbering: Word-native, RTL, no heading abuse
    def _add_numbered_item(self, doc, text):
        p = doc.add_paragraph(style="List Number")
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p.paragraph_format.right_to_left = True

        run = p.add_run(text)
        run.font.name = self.font
        run.font.size = Pt(12)

    # -------------------------------------------------
    # Dispatcher
    # -------------------------------------------------
    def add_formatted_paragraph(self, doc, content):
        for line in content.split("\n"):
            line = line.strip()
            if not line:
                doc.add_paragraph("")
                continue

            # Remove markdown bold/italic
            line = re.sub(r"\*\*(.*?)\*\*", r"\1", line)
            line = re.sub(r"\*(.*?)\*", r"\1", line)

            # Section headers (###)
            if line.startswith("###"):
                self.add_section_header(
                    doc,
                    line.replace("###", "").strip()
                )

            # Numbered list: 1. text
            elif re.match(r"^\d+\.\s+", line):
                self._add_numbered_item(
                    doc,
                    re.sub(r"^\d+\.\s+", "", line)
                )

            # Bullet list: • text / * text / - text (remove bullet, keep as plain statement)
            elif re.match(r"^[•*\-●]\s+", line):
                # Remove bullet character completely and create plain paragraph
                bullet_text = re.sub(r"^[•*\-●]\s+", "", line).strip()
                if bullet_text:  # Only process if there's text after removing bullet
                    # Create normal paragraph without any bullet or dash
                    p = doc.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                    p.paragraph_format.right_to_left = True
                    
                    # Replace periods with Arabic periods
                    text_with_arabic_periods = bullet_text.replace(".", "۔")
                    
                    run = p.add_run(text_with_arabic_periods)
                    run.font.name = self.font
                    run.font.size = Pt(12)

            # Normal paragraph
            else:
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                p.paragraph_format.right_to_left = True

                run = p.add_run(line)
                run.font.name = self.font
                run.font.size = Pt(12)

    # -------------------------------------------------
    # Save
    # -------------------------------------------------
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
