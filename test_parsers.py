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
    import os
    path = "data/people_strategy_summary_slides.pptx"
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    raise FileNotFoundError(f"Mock PPTX file not found at {path}")

def make_minimal_xlsx():
    import zipfile
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w') as z:
        z.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Types xmlns="http://schemas.openxmlformats.org/markup-compatibility/2006">\n'
            '  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
            '  <Default Extension="xml" ContentType="application/xml"/>\n'
            '  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>\n'
            '  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>\n'
            '</Types>'
        )
        z.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">\n'
            '  <sheets>\n'
            '    <sheet name="TestSheet" sheetId="1" r:id="rId1"/>\n'
            '  </sheets>\n'
            '</workbook>'
        )
        z.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
            '  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>\n'
            '</Relationships>'
        )
        z.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
            '  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>\n'
            '</Relationships>'
        )
        z.writestr(
            "xl/worksheets/sheet1.xml",
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">\n'
            '  <sheetData>\n'
            '    <row r="1">\n'
            '      <c r="A1" t="inlineStr"><is><t>Header1</t></is></c>\n'
            '      <c r="B1" t="inlineStr"><is><t>Header2</t></is></c>\n'
            '    </row>\n'
            '    <row r="2">\n'
            '      <c r="A2" t="inlineStr"><is><t>Row1Val1</t></is></c>\n'
            '      <c r="B2" t="inlineStr"><is><t>Row1Val2</t></is></c>\n'
            '    </row>\n'
            '  </sheetData>\n'
            '</worksheet>'
        )
    return out.getvalue()

def make_minimal_png():
    # 1x1 pixel transparent PNG
    return b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'

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
        parsed_blocks, _ = parse_file(file_bytes, filename)
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
    test_file_type("XLSX", make_minimal_xlsx, "sample.xlsx")
    test_file_type("PNG", make_minimal_png, "sample.png")
    
    # Test error handling
    print("=" * 60)
    print("Testing Unsupported File Type Error Handling")
    print("=" * 60)
    try:
        parse_file(b"some binary data", "unsupported.xyz")
        print("[FAIL] Dispatcher did not raise error for unsupported extension.")
    except ValueError as ve:
        print(f"[PASS] Correctly raised ValueError: {ve}")
    except Exception as e:
        print(f"[FAIL] Raised unexpected exception: {e}")

if __name__ == "__main__":
    main()
