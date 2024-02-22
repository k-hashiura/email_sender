from datetime import datetime
from logging import DEBUG, FileHandler, StreamHandler, getLogger
import sys

import click
from pythonjsonlogger import jsonlogger
from pathlib import Path

from typing import Callable

from email_sender.services.txt2html import hi


logger = getLogger(__name__)


CONFIG_FILENAME = "email_config.json"


def _check_config_exists() -> bool:
    return (Path(".") / CONFIG_FILENAME).is_file()


def check_config_exists(f: Callable) -> Callable:
    def wrapper(*args, **kwargs):
        if not _check_config_exists():
            click.echo(f"{CONFIG_FILENAME} isn't exists...")
            sys.exit(1)
        click.echo("hi")
        return f(*args, **kwargs)

    return wrapper


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
def txt2html():
    """プレーンテキストをHTMLのテンプレートに変換"""
    logger.debug("invoking txt2html")


@cli.command("init")
@click.argument(
    "dirname",
    type=click.Path(path_type=Path),
)
def init_email_dir(dirname: Path) -> None:
    if dirname.exists():
        click.secho()


@cli.command("check")
@check_config_exists
def check():
    """メールの送付ファイルをチェック"""


@cli.command("send")
@check_config_exists
def send() -> None:
    """本番のメールを送付"""


def main() -> None:
    _setup_logger()
    cli()


if __name__ == "__main__":
    main()
