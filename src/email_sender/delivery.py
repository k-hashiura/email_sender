import email.utils
import sys
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from logging import getLogger
from pathlib import Path
from smtplib import SMTP
import os

import click
import pandas as pd
from blastengine.Client import Blastengine
from blastengine.Transaction import Transaction
from email_validator import validate_email
from pydantic import BaseModel, EmailStr, Field

from email_sender.settings import load_settings
from email_sender.template import load_template

settings = load_settings()
txt_template, html_template = load_template()

logger = getLogger(__name__)


class DeliveryItem(BaseModel):
    """送付ごとに固有な情報"""

    app_id: str
    email_address: str

    # @property
    # def pdf_path(self) -> str:
    #     return "docs/協力金振込対象実績について（お知らせ）.pdf"
    cc_list: list[str] = [
        # "matsuura.takeshi.yz@tohoku-epco.co.jp",
        # "tanaka.nagisa.nt@tohoku-epco.co.jp",
        "k-hashiura+cc@k-socket.co.jp"
    ]

    @property
    def to_addr(self) -> str:
        return self.email_address

    @property
    def text_part(self) -> str:
        return txt_template.render(self.model_dump())

    @property
    def html_part(self) -> str:
        return html_template.render(self.model_dump())


def extract_data_from_excel(src_file: Path, sheet_name: str | None) -> pd.DataFrame:
    # Excelの読み込み
    raw_df = pd.read_excel(
        io=src_file,
        sheet_name=(sheet_name or settings.send_list_sheetname),
        skiprows=3,
        # header=None,
        # names=['メールアドレス', 'is_check'],
        dtype=str,
    )

    # 数値をゼロ埋め & フォーマット

    # 不要な行を削除
    # raw_df = raw_df.dropna(subset=["番号"])
    # raw_df = pd.to_datetime(raw_df["メール日"]).dt.date
    # raw_df = raw_df[raw_df["メール日"] == '2024-05-29 00:00:00']
    # raw_df.to_csv('test.csv')

    rename_cols = {
        "通し番号": "app_id",
        "メールアドレス": "email_address",
    }

    # int_cols = [
    #     "sub_amount",
    #     "eq_count",
    #     "ac_count",
    #     "eq_lease",
    #     "ac_lease",
    #     "total_amount",
    #     "paid_amount",
    # ]

    result_df = raw_df.rename(columns=rename_cols)

    # for col in int_cols:
    #     result_df[col] = result_df[col].fillna(0).astype(int).apply(lambda x: f"{x:,}")

    result_df = result_df.fillna('')

    return result_df


def convert_data(excel_df: pd.DataFrame) -> list[DeliveryItem]:
    result: list[DeliveryItem] = []
    for _, row in excel_df.iterrows():
        try:
            item = DeliveryItem(**row.to_dict())
        except Exception:
            logger.exception("データの読み込みに失敗")
            sys.exit(1)
        result.append(item)
    return result


def get_deliveries(src_file: Path, sheet_name: str | None) -> list[DeliveryItem]:
    return convert_data(extract_data_from_excel(src_file, sheet_name))


def _construct_transaction(delivery: DeliveryItem) -> Transaction:
    transaction = Transaction()
    # 設定から
    transaction.subject(settings.email_subject)
    transaction.from_address(email=settings.from_address, name=settings.from_name)
    # 各送付ごと
    transaction.to(delivery.to_addr)
    for cc in delivery.cc_list:
        transaction.cc(cc)
    transaction.text_part(delivery.text_part)
    transaction.html_part(delivery.html_part)

    # if not os.path.isfile(delivery.pdf_path):
    #     raise FileNotFoundError(f"NOT FOUND: {delivery.pdf_path}")

    # transaction.attachments(delivery.pdf_path)

    return transaction


def send_emails(deliveries: list[DeliveryItem], dryrun: bool) -> None:
    # BlastEngineのクライアントを初期化
    Blastengine(settings.be_username, settings.be_api_key.get_secret_value())

    error_count = 0
    # 各メールを送信
    with click.progressbar(deliveries, show_pos=True) as itr:
        for delivery in itr:
            transaction = _construct_transaction(delivery)
            try:
                if dryrun:
                    delivery_id = 0
                    validate_email(delivery.email_address)
                else:
                    delivery_id = transaction.send()

                logger.debug(
                    {
                        "message": "Email Sent",
                        "delivery_id": delivery_id,
                        **delivery.model_dump(),
                        "txt": delivery.text_part,
                        "html": delivery.html_part,
                    }
                )
            except Exception:
                msg = {
                    "message": "メール送付処理に失敗しました。",
                    **delivery.model_dump(),
                }
                logger.exception(msg)
                error_count += 1
        if dryrun:
            logger.info("全メールの確認処理完了（DRYRUN）")
        else:
            logger.info("全メールの送付処理完了")
        logger.info(f"エラー数: {error_count}")


# def send_emails_in_smtp(deliveries: list[DeliveryItem], is_real: bool) -> None:
#     # SMTPクライアントを初期化
#     smtp_host = "smtp.engn.jp"
#     smtp_user = settings.be_username
#     smtp_pass = settings.be_password.get_secret_value()
#     client = SMTP(smtp_host, 587)
#     client.starttls()
#     client.login(smtp_user, smtp_pass)

#     # 各メールを送信
#     for delivery in deliveries:
#         # メールを作成
#         msg = MIMEMultipart()
#         msg["To"] = delivery.to_addr
#         msg["From"] = settings.from_address
#         msg["Subject"] = settings.email_subject
#         msg["Date"] = email.utils.formatdate()
#         msg["Message-ID"] = email.utils.make_msgid(domain="machiiko.com")
#         msg.attach(MIMEText(delivery.text_part))

#         try:
#             if is_real:
#                 res = client.send_message(msg)
#             else:
#                 res = None
#             logger.info(
#                 {
#                     "message": "Email Sent",
#                     "delivery_id": "SMTP",
#                     **delivery.model_dump(),
#                     "txt": delivery.text_part,
#                     # "html": delivery.html_part,
#                     "smtp_error": res,
#                 }
#             )
#         except Exception:
#             msg = {"message": "メール送付処理に失敗しました。", **delivery.model_dump()}
#             logger.exception(msg)
#     if is_real:
#         logger.info("全メールの送付処理完了")
#     else:
#         logger.info("全メールの確認処理完了（DRYRUN）")
