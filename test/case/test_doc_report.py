from pathlib import Path

from docx import Document

from address_planner import AddressSpace


def test_gen_doc_writes_a_readable_address_map(tmp_path: Path) -> None:
    top = AddressSpace("doc_top", 64, description="root")
    top.add(AddressSpace("child", 16, description="child"), 0)

    top.generate(str(tmp_path), gen_doc=True, report_viewer=False)

    report = tmp_path / "doc_top" / "html" / "doc.docx"
    assert report.is_file()
    assert not (report.parent / "data.json").exists()
    paragraphs = [paragraph.text for paragraph in Document(report).paragraphs]
    assert paragraphs == ["Address Map", "1 doc_top", "1.1 child"]
