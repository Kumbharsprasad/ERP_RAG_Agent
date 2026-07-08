import io
import os
import shutil
import pdfplumber
import docx
from pptx import Presentation
from bs4 import BeautifulSoup, NavigableString
import pandas as pd
import pytesseract
import logfire

# Configure Tesseract path for Windows fallback if not on PATH
if not shutil.which("tesseract"):
    default_win_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    if os.path.exists(default_win_path):
        pytesseract.pytesseract.tesseract_cmd = default_win_path

def parse_pdf(file_bytes: bytes, filename: str) -> list[dict]:
    """
    Parses a PDF file from bytes.
    Extracts text per page, with location formatted as 'Page {n}' (1-indexed).
    Falls back to Tesseract OCR if pdfplumber cannot extract text from a page.
    """
    blocks = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for idx, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            
            # If extracted text is empty, attempt OCR fallback
            if not text.strip():
                logfire.warn("Page {page_num} of {filename} has no digital text. Running Tesseract OCR...", page_num=idx + 1, filename=filename)
                try:
                    # Convert page to a PIL Image
                    page_image = page.to_image(resolution=150)
                    pil_img = page_image.original
                    ocr_text = pytesseract.image_to_string(pil_img)
                    if ocr_text and ocr_text.strip():
                        text = ocr_text
                        logfire.info("OCR successfully extracted text for Page {page_num}", page_num=idx + 1)
                except Exception as ocr_err:
                    logfire.error("OCR fallback failed for {filename} Page {page_num}", filename=filename, page_num=idx + 1, error=str(ocr_err))
                    print(f"Warning: OCR fallback failed for {filename} Page {idx + 1}: {ocr_err}")
            
            blocks.append({
                "text": text,
                "source_file": filename,
                "location": f"Page {idx + 1}"
            })
    return blocks

def parse_docx(file_bytes: bytes, filename: str) -> list[dict]:
    """
    Parses a DOCX file from bytes.
    Extracts paragraphs and groups them into blocks of ~10 paragraphs.
    Location is formatted as 'Paragraphs {start}-{end}'.
    """
    doc = docx.Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    
    blocks = []
    chunk_size = 10
    for i in range(0, len(paragraphs), chunk_size):
        group = paragraphs[i:i + chunk_size]
        text = "\n".join(group)
        blocks.append({
            "text": text,
            "source_file": filename,
            "location": f"Paragraphs {i + 1}-{i + len(group)}"
        })
    return blocks

def parse_pptx(file_bytes: bytes, filename: str) -> list[dict]:
    """
    Parses a PPTX file from bytes.
    Extracts text per slide, with location formatted as 'Slide {n}' (1-indexed).
    """
    prs = Presentation(io.BytesIO(file_bytes))
    blocks = []
    for idx, slide in enumerate(prs.slides):
        slide_text_parts = []
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                slide_text_parts.append(shape.text)
        text = "\n".join(slide_text_parts)
        blocks.append({
            "text": text,
            "source_file": filename,
            "location": f"Slide {idx + 1}"
        })
    return blocks

def parse_html(file_bytes: bytes, filename: str) -> list[dict]:
    """
    Parses an HTML file from bytes.
    Extracts visible text, splitting content into sections based on heading tags (h1-h6).
    Location is formatted as 'Section {n}' (1-indexed).
    """
    html_content = file_bytes.decode("utf-8", errors="ignore")
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Remove scripts, styles, and other metadata tags to clean the HTML
    for tag in soup(["script", "style", "meta", "noscript", "header", "footer"]):
        tag.decompose()
        
    blocks = []
    current_section_text = []
    section_idx = 1
    
    def traverse(node):
        nonlocal section_idx, current_section_text
        # If node is one of the heading tags
        if node.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            # Save the text gathered so far into a block
            text_so_far = "".join(current_section_text).strip()
            if text_so_far:
                blocks.append({
                    "text": text_so_far,
                    "source_file": filename,
                    "location": f"Section {section_idx}"
                })
                section_idx += 1
                current_section_text = []
            
            # Start the new section with the heading text itself
            heading_text = node.get_text().strip()
            if heading_text:
                current_section_text.append(heading_text + "\n")
            return
            
        # If node is a text node (NavigableString), collect it
        if isinstance(node, NavigableString):
            val = str(node).strip()
            if val:
                current_section_text.append(val + " ")
            return
            
        # Recursively traverse child nodes
        if hasattr(node, "children"):
            for child in node.children:
                traverse(child)

    # Begin traversal on body (or root soup if body is missing)
    start_node = soup.body if soup.body else soup
    traverse(start_node)
    
    # Grab any trailing text
    final_text = "".join(current_section_text).strip()
    if final_text:
        blocks.append({
            "text": final_text,
            "source_file": filename,
            "location": f"Section {section_idx}"
        })
        
    return blocks

def parse_csv(file_bytes: bytes, filename: str) -> list[dict]:
    """
    Parses a CSV file from bytes.
    Groups rows into blocks of 20 rows each, including headers in every block.
    Location is formatted as 'Rows {start}-{end}'.
    """
    df = pd.read_csv(io.BytesIO(file_bytes))
    blocks = []
    chunk_size = 20
    num_rows = len(df)
    
    if num_rows == 0:
        blocks.append({
            "text": ",".join(df.columns),
            "source_file": filename,
            "location": "Rows 0-0"
        })
        return blocks
        
    for i in range(0, num_rows, chunk_size):
        sub_df = df.iloc[i:i + chunk_size]
        text = sub_df.to_csv(index=False)
        start_row = i + 1
        end_row = min(i + len(sub_df), num_rows)
        blocks.append({
            "text": text.strip(),
            "source_file": filename,
            "location": f"Rows {start_row}-{end_row}"
        })
        
    return blocks

def parse_txt(file_bytes: bytes, filename: str) -> list[dict]:
    """
    Parses a TXT file from bytes.
    Splits the decoded text into blocks of ~500 words.
    Location is formatted as 'Block {n}'.
    """
    text = file_bytes.decode("utf-8", errors="ignore")
    words = text.split()
    blocks = []
    chunk_size = 500
    num_words = len(words)
    
    if num_words == 0:
        blocks.append({
            "text": "",
            "source_file": filename,
            "location": "Block 1"
        })
        return blocks
        
    for i in range(0, num_words, chunk_size):
        group = words[i:i + chunk_size]
        blocks.append({
            "text": " ".join(group),
            "source_file": filename,
            "location": f"Block {i // chunk_size + 1}"
        })
        
    return blocks

def parse_file(file_bytes: bytes, filename: str) -> list[dict]:
    """
    Dispatcher function that picks the right parser based on file extension.
    Raises ValueError for unsupported types.
    """
    ext = os.path.splitext(filename)[1].lower()
    with logfire.span("Parsing file {filename} ({ext})", filename=filename, ext=ext):
        if ext == ".pdf":
            blocks = parse_pdf(file_bytes, filename)
        elif ext == ".docx":
            blocks = parse_docx(file_bytes, filename)
        elif ext == ".pptx":
            blocks = parse_pptx(file_bytes, filename)
        elif ext in [".html", ".htm"]:
            blocks = parse_html(file_bytes, filename)
        elif ext == ".csv":
            blocks = parse_csv(file_bytes, filename)
        elif ext == ".txt":
            blocks = parse_txt(file_bytes, filename)
        else:
            logfire.error("Unsupported extension {ext} for {filename}", ext=ext, filename=filename)
            raise ValueError(f"Unsupported file type: '{ext}' in file '{filename}'")
            
        logfire.info("Successfully parsed {filename}. Extracted {num_blocks} blocks.", filename=filename, num_blocks=len(blocks))
        return blocks
