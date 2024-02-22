from datetime import datetime
from logging import DEBUG, FileHandler, StreamHandler, getLogger
import sys

import click
from pythonjsonlogger import jsonlogger
from pathlib import Path

from email_sender.services.txt2html import convert_txt2html
from email_sender.settings import load_settings
from email_sender.template import load_template
from email_sender.delivery import get_deliveries, send_emails


logger = getLogger(__name__)
settings = load_settings()


CONFIG_FILENAME = "email_config.json"


def _setup_logger() -> None:
    now = datetime.now()
    log_dir = Path("./logs")
    log_dir.mkdir(exist_ok=True)
    log_filename = log_dir / f"{now.isoformat()}-log.jsonl"

    logger = getLogger("email_sender")
    json_fmt = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(message)s", json_ensure_ascii=False
    )

    # ファイルハンドラを定義
    fh = FileHandler(log_filename)
    fh.setFormatter(json_fmt)
    fh.setLevel(DEBUG)
    logger.addHandler(fh)

    # StreamHandlerを定義
    sh = StreamHandler()
    logger.addHandler(sh)
    logger.setLevel(DEBUG)


@click.group()
@click.version_option()
def cli() -> None:
    """BlastEngineでのメール送付"""


@cli.command("txt2html")
@click.argument(
    "txt_file",
    type=click.Path(path_type=Path),
)
def txt2html(txt_file: Path):
    """プレーンテキストをHTMLのテンプレートに変換"""
    logger.debug("invoking txt2html")
    convert_txt2html(txt_file)


@cli.command("tempalte")
def template():
    txt_template, html_template = load_template()
    click.echo(txt_template.render())


@cli.command("env")
def env():
    click.echo(load_settings())


@cli.command("check")
@click.argument(
    "src_file",
    type=click.Path(path_type=Path),
)
def check(src_file: Path):
    """メールの送付ファイルをチェック"""



@click.argument(
    "src_file",
    type=click.Path(path_type=Path),
)
@click.option(
    "--dryrun/--no-dryrun", "is_dryrun", help="実際に送付", default=True, is_flag=True
)
@cli.command("send")
def send(src_file: Path, is_dryrun: bool) -> None:
    _setup_logger()
    """本番のメールを送付"""
    # 設定値を出力
    logger.info({**{"message": "Settings"}, **settings.model_dump()})

    deliveries = get_deliveries(src_file)
    print(deliveries)
    logger.info(
        {
            "message": "今回の送付情報",
            "detail": {
                "count": len(deliveries),
                "first_email": deliveries[0].to_addr,
                "last_email": deliveries[-1].to_addr,
            },
        }
    )

    # DRY RUNかどうか
    if is_dryrun:
        logger.info(f"確認を実行しますか？")
    else:
        logger.info(f"本番の送付を実行しますか？")

    is_ok = click.confirm("Ok to Continue?")
    if not is_ok:
        logger.info("Aborted by user.")
        return

    send_emails(deliveries, is_dryrun)
    # send_emails_in_smtp(deliveries, real)


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
