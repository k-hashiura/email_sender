import click


@click.group()
@click.version_option()
def cli() -> None:
    """BlastEngineでのメール送付"""


@cli.command("txt2html")
def txt2html():
    """プレーンテキストをHTMLのテンプレートに変換"""


@cli.command("check")
def check():
    """メールの送付ファイルをチェック"""


@cli.command("send")
def send() -> None:
    """本番のメールを送付"""

def main() -> None:
    cli()


if __name__ == "__main__":
    main()
