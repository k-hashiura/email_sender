import pandas as pd


if __name__ == "__main__":
    id_list = extract_id_list(
        "data/2024-05-13-CP周知メール/logs/2024-05-13T17:18:48.607670-log.jsonl"
    )
    print(id_list)
