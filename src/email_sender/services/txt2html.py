import html
from pathlib import Path

from email_sender.exceptions import EmailSenderError


def convert_txt2html(src_file: Path) -> None:
    if not src_file.is_file():
        t = ""
        raise EmailSenderError(t)

    if not src_file.name.endswith(".txt.j2"):
        t = '拡張子が "txt.j2" のファイルを指定してください。'
        raise EmailSenderError(t)

    tgt_file = Path(str(src_file).replace(".txt.j2", ".html.j2"))

    if tgt_file.exists():
        t = "変換先のファイルが存在します。"
        raise EmailSenderError(t)

    with open(src_file, "r") as f:
        html_content = html.escape(f.read()).replace("\n", "<br>\n")
        with open(tgt_file, "w") as g:
            g.write(html_content)
