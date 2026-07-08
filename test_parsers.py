import io
import traceback
from app.parsers import parse_file
from app.chunking import chunk_text

def make_minimal_pdf():
    # A standard 1-page PDF string with "Hello PDF World" text.
    # Uses Helvetica base font.
    pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [ 3 0 R ] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources 5 0 R /MediaBox [ 0 0 595.275 841.889 ] /Contents 4 0 R >>\nendobj\n"
        b"4 0 obj\n<< /Length 52 >>\nstream\n"
        b"BT\n/F1 12 Tf\n72 720 Td\n(Hello PDF World - Test Page) Tj\nET\n"
        b"endstream\nendobj\n"
        b"5 0 obj\n<< /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >>\nendobj\n"
        b"xref\n"
        b"0 6\n"
        b"0000000000 65535 f\n"
        b"0000000009 00000 n\n"
        b"0000000054 00000 n\n"
        b"0000000109 00000 n\n"
        b"0000000216 00000 n\n"
        b"0000000319 00000 n\n"
        b"trailer\n<< /Size 6 /Root 1 0 R >>\n"
        b"startxref\n"
        b"416\n"
        b"%%EOF\n"
    )
    return pdf_content

def make_minimal_docx():
    import docx
    doc = docx.Document()
    # Add 25 paragraphs to test grouping of 10 paragraphs.
    for i in range(1, 26):
        doc.add_paragraph(f"This is docx paragraph {i}. It contains standard paragraph text.")
    out = io.BytesIO()
    doc.save(out)
    return out.getvalue()

def make_minimal_pptx():
    from pptx import Presentation
    prs = Presentation()
    blank_layout = prs.slide_layouts[6]
    for i in range(1, 4):
        slide = prs.slides.add_slide(blank_layout)
        txBox = slide.shapes.add_textbox(0, 0, 100, 100)
        tf = txBox.text_frame
        tf.text = f"This is slide {i} text contents."
    out = io.BytesIO()
    prs.save(out)
    return out.getvalue()

def make_minimal_html():
    return (
        b"<html>\n"
        b"  <head><title>Test Page</title></head>\n"
        b"  <body>\n"
        b"    <h1>Main Heading</h1>\n"
        b"    <p>This is paragraph 1 of the HTML document.</p>\n"
        b"    <h2>Secondary Heading</h2>\n"
        b"    <p>This is paragraph 2. It is under the second heading.</p>\n"
        b"    <p>This is paragraph 3, also under the second heading.</p>\n"
        b"  </body>\n"
        b"</html>"
    )

def make_minimal_csv():
    # Generate 45 rows of data.
    lines = ["id,name,value"]
    for i in range(1, 46):
        lines.append(f"{i},Item_{i},Val_{1000 + i}")
    return "\n".join(lines).encode("utf-8")

def make_minimal_txt():
    # Word count: 1200 words.
    words = [f"word{i}" for i in range(1, 1201)]
    return " ".join(words).encode("utf-8")

def test_file_type(name: str, bytes_generator, filename: str):
    print("=" * 60)
    print(f"Testing File Type: {name} (filename: {filename})")
    print("=" * 60)
    try:
        file_bytes = bytes_generator()
        print(f"Generating bytes complete, size: {len(file_bytes)} bytes.")
        
        # Parse file
        parsed_blocks = parse_file(file_bytes, filename)
        print(f"Parsing complete. Extracted {len(parsed_blocks)} blocks.")
        for idx, block in enumerate(parsed_blocks):
            snippet = block['text'].replace('\n', '\\n')[:80] + '...' if len(block['text']) > 80 else block['text'].replace('\n', '\\n')
            print(f"  Block {idx}: location='{block['location']}', text='{snippet}'")
            
        # Chunk text (setting size to a small value e.g. 50 tokens to force splitting and test overlap/indexing)
        chunks = chunk_text(parsed_blocks, chunk_size_tokens=50, overlap_ratio=0.2)
        print(f"Chunking complete. Created {len(chunks)} chunks.")
        for idx, chunk in enumerate(chunks[:5]): # Show up to first 5 chunks
            snippet = chunk['text'].replace('\n', '\\n')[:80] + '...' if len(chunk['text']) > 80 else chunk['text'].replace('\n', '\\n')
            print(f"    Chunk {idx}: index={chunk['chunk_index']}, location='{chunk['location']}', text='{snippet}'")
        if len(chunks) > 5:
            print(f"    ... and {len(chunks) - 5} more chunks.")
            
        # If it's a CSV, check row-level splitting
        if filename.endswith(".csv"):
            print("\n  Validating CSV boundaries (rows should never split mid-row and columns must be present):")
            all_valid = True
            for i, chunk in enumerate(chunks):
                text_lines = chunk['text'].splitlines()
                if not text_lines:
                    continue
                header = text_lines[0]
                if header != "id,name,value":
                    print(f"    [FAIL] Chunk {i} header '{header}' does not match expected header 'id,name,value'")
                    all_valid = False
                for r in text_lines[1:]:
                    parts = r.split(',')
                    if len(parts) != 3:
                        print(f"    [FAIL] Chunk {i} contains split row: '{r}'")
                        all_valid = False
            if all_valid:
                print("    [PASS] All CSV chunks are correctly formatted at row boundaries!")
                
    except Exception as e:
        print(f"Error testing {name}: {e}")
        traceback.print_exc()
    print()

def main():
    test_file_type("TXT", make_minimal_txt, "sample.txt")
    test_file_type("CSV", make_minimal_csv, "sample.csv")
    test_file_type("HTML", make_minimal_html, "sample.html")
    test_file_type("DOCX", make_minimal_docx, "sample.docx")
    test_file_type("PPTX", make_minimal_pptx, "sample.pptx")
    test_file_type("PDF", make_minimal_pdf, "sample.pdf")
    
    # Test error handling
    print("=" * 60)
    print("Testing Unsupported File Type Error Handling")
    print("=" * 60)
    try:
        parse_file(b"some binary data", "unsupported.xlsx")
        print("[FAIL] Dispatcher did not raise error for unsupported extension.")
    except ValueError as ve:
        print(f"[PASS] Correctly raised ValueError: {ve}")
    except Exception as e:
        print(f"[FAIL] Raised unexpected exception: {e}")

if __name__ == "__main__":
    main()
