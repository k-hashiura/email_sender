from __future__ import annotations

import json
from logging import getLogger
from pathlib import Path
from typing import Iterable
import os

import click
import pandas as pd
import requests
from blastengine.Client import Blastengine
from requests import Response

from email_sender.settings import Settings, load_settings

logger = getLogger(__name__)

ENDPOINT = "https://app.engn.jp/api/v1/logs/mails/results"


def extract_id_list(src) -> pd.Series:
    df = pd.read_json(src, lines=True)
    df = df[df["message"] == "Email Sent"]
    return df["delivery_id"].astype(int)


def parse_log_jsonl(src) -> pd.DataFrame:
    df = pd.read_json(src, lines=True)
    df.to_excel("sample-log-parsed.xlsx")
    # 必要な行を抜き出し
    df = df[df["message"] == "Email Sent"]

    # 必要な列のみ抜き出し
    cols = [
        "asctime",
        "delivery_id",
        "email_address",
        "iss_num",
        "addressee",
        "paydate",
        "app_num",
        "pdf_filename",
    ]
    df = df[cols]
    return df


def get_detail(delivery_id: int, settings: Settings) -> Response:
    client = Blastengine(settings.be_username, settings.be_api_key.get_secret_value())
    url = ENDPOINT
    headers = {"Authorization": f"Bearer {client.token}"}
    params = {"delivery_id": delivery_id}
    res = requests.get(url=url, headers=headers, params=params)
    if res.status_code != 200:
        print(f"\nStatusCode: {res.status_code}")
        print(f"TEXT: {res.text}")
        raise RuntimeError
    return res


def get_detail_list(delivery_ids: Iterable[int]) -> list[Response]:
    result: list[Response] = []
    settings = load_settings()
    with click.progressbar(delivery_ids) as itr:
        for id in itr:
            result.append(get_detail(id, settings))
    return result


def get_header(d: dict) -> str:
    return ",".join(d.keys())


def get_log_txt(delivery_ids: Iterable[int]) -> str:
    responses = get_detail_list(delivery_ids)
    lines: list[str] = []

    for res in responses:
        lines.append(json.dumps(res.json()["data"][0]))

    return "\n".join(lines)


def parse_result_jsonl(filename: Path) -> pd.DataFrame:
    tz_aware_cols = [
        'delivery_time',
        'created_time',
        'updated_time',
        'open_time',
    ]
    df = pd.read_json(filename, lines=True)
    for c in tz_aware_cols:
        df[c] = df[c].dt.tz_localize(None)
    return df

def get_result_from_logfile(logfile: Path):
    ids = extract_id_list(logfile)

    result_dir = Path('result')
    result_dir.mkdir(exist_ok=True)
    result_jsonl_path = result_dir / logfile.name
    t = get_log_txt(ids)
    with open(result_jsonl_path, "w") as f:
        f.write(t)

    result_xlsx_path = result_jsonl_path.with_suffix('.xlsx')
    result_df = parse_result_jsonl(result_jsonl_path)
    result_df.to_excel(result_xlsx_path)

    log_df = parse_log_jsonl(logfile)

    log_with_result = pd.merge(
        left=log_df,
        right=result_df,
        left_on="delivery_id",
        right_on="delivery_id",
        how="left",
    )
    os.makedirs('sample', exist_ok=True)
    log_with_result.to_excel('sample/LOG-RESULT.xlsx')


if __name__ == "__main__":
    get_result_from_logfile(
        Path(
            "../../data/2024-05-27-NWインボイス定例/logs/2024-05-27T13:51:52.375889-log.jsonl"
        )
    )
