from __future__ import annotations

from pathlib import Path

from task_reminder.app.financial_agent.sources import PdfFinancialDataSource


PDF_BYTES = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length 115 >>
stream
BT
/F1 12 Tf
72 720 Td
(Statement 2026-06-20) Tj
0 -18 Td
(2026-06-19 Coffee Shop -45.90 ILS) Tj
0 -18 Td
(2026-06-20 Supermarket -122.10 ILS) Tj
ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000010 00000 n 
0000000061 00000 n 
0000000118 00000 n 
0000000245 00000 n 
0000000417 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
484
%%EOF
"""


def test_pdf_source_extracts_statement_text(tmp_path):
    pdf_path = tmp_path / "credit-card-statement.pdf"
    pdf_path.write_bytes(PDF_BYTES)

    bundle = PdfFinancialDataSource(pdf_path).load()

    assert bundle.metadata["source_file"].endswith("credit-card-statement.pdf")
    assert "Statement 2026-06-20" in bundle.metadata["extracted_text"]
    assert bundle.metadata["page_count"] == 1
    assert bundle.transactions == []
