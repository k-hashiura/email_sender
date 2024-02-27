"""プレーンテキストのメール本文をHTMLメール用にエスケープ & <br>タグを追加"""


import html
import sys
from pathlib import Path
from glob import glob


def convert_txt2html(src_filename: str) ->None:
    src_file = Path(src_filename)

    if not src_file.is_file():
        print("")
        sys.exit(1)

    if not src_file.name.endswith(".txt.j2"):
        print("")
        sys.exit(1)

    tgt_file = Path(src_filename.replace(".txt.j2", ".html.j2"))

    if tgt_file.exists():
        print("already exists")
        sys.exit(1)

    with open(src_file, "r") as f:
        html_content = html.escape(f.read()).replace("\n", "<br>\n")
        with open(tgt_file, "w") as g:
            g.write(html_content)


def main():
    args = sys.argv

    if len(args) != 2:
        print("引数はファイル名のみで")
        sys.exit(1)

    src_name = args[1]
    src = Path(src_name)
    if src.is_file():
        convert_txt2html(src_name)
    elif src.is_dir():
        print(f"{src}/*.txt.j2")
        files = glob(f"{src}/*.txt.j2")
        if len(files) == 0:
            print(f"{src}内にテンプレートテキストファイルがありません")
        for file in files:
            print(f"converting: {file}")
            convert_txt2html(file)


if __name__ == "__main__":
    main()
