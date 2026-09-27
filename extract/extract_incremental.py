import json
import os
from datetime import date
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.dialects.postgresql import insert as pg_insert

load_dotenv()

RAW_SOURCE_DIR = Path("raw_source")
LANDING_DIR = Path("landing")
WATERMARK_FILE = Path("extract/state/watermark.json")


class ValidationError(Exception):
    pass


REQUIRED_COLUMNS = {"order_id", "customer_id",
                    "order_status", "order_purchase_timestamp"}


def validate(df: pd.DataFrame) -> None:
    if df.empty:
        raise ValidationError(
            "Empty data，but pending_dates is not null，possible damage on raw_source")

    missing_cols = REQUIRED_COLUMNS - set(df.columns)
    if missing_cols:
        raise ValidationError(f"Missing required: {missing_cols}")

    null_keys = df[df["order_id"].isna() | df["customer_id"].isna()]
    if not null_keys.empty:
        raise ValidationError(
            f"Found {len(null_keys)} records of order_id or customer_id is empty")

    dup_ids = df["order_id"][df["order_id"].duplicated()]
    if not dup_ids.empty:
        raise ValidationError(
            f"Found {len(dup_ids)} duplicated order_id: {dup_ids.unique()[:5].tolist()}")

    print(
        f"Validation successed：{len(df)} records，{df['order_id'].nunique()} unique order_id")


def read_watermark() -> date | None:
    if not WATERMARK_FILE.exists():
        return None
    data = json.loads(WATERMARK_FILE.read_text())
    return date.fromisoformat(data["last_extracted_date"])


def write_watermark(new_date: date) -> None:
    WATERMARK_FILE.parent.mkdir(parents=True, exist_ok=True)
    WATERMARK_FILE.write_text(json.dumps(
        {"last_extracted_date": new_date.isoformat()}))


def list_pending_dates(watermark: date | None) -> list[date]:
    all_dates = sorted(date.fromisoformat(p.stem)
                       for p in RAW_SOURCE_DIR.glob("*.csv"))
    if watermark is None:
        return all_dates
    return [d for d in all_dates if d > watermark]


def extract(pending_dates: list[date]) -> pd.DataFrame:
    frames = [pd.read_csv(RAW_SOURCE_DIR / f"{d}.csv") for d in pending_dates]
    return pd.concat(frames, ignore_index=True)


def load(df: pd.DataFrame, pending_dates: list[date]) -> Path:
    LANDING_DIR.mkdir(exist_ok=True)
    out_path = LANDING_DIR / \
        f"batch_{pending_dates[0]}_to_{pending_dates[-1]}.csv"
    df.to_csv(out_path, index=False)
    return out_path


def get_engine():
    url = (
        f"postgresql+psycopg2://{os.environ['DB_USER']}:{os.environ['DB_PASSWORD']}"
        f"@{os.environ['DB_HOST']}:{os.environ['DB_PORT']}/{os.environ['DB_NAME']}"
    )
    return create_engine(url)


def load_to_db(df: pd.DataFrame) -> int:
    engine = get_engine()
    metadata = MetaData(schema="raw")
    table = Table("raw_orders_incremental", metadata, autoload_with=engine)

    records = df.to_dict(orient="records")
    with engine.begin() as conn:
        stmt = pg_insert(table).values(records)
        stmt = stmt.on_conflict_do_nothing(index_elements=["order_id"])
        result = conn.execute(stmt)
    return result.rowcount


def main():
    watermark = read_watermark()
    print(f"Current watermark: {watermark}")

    pending_dates = list_pending_dates(watermark)
    if not pending_dates:
        print("No data updated, skip this extract.")
        return

    print(
        f"Found {len(pending_dates)} days to be extracted: {pending_dates[0]} ~ {pending_dates[-1]}")

    df = extract(pending_dates)
    print(f"Extracted {len(df)} records")

    try:
        validate(df)
    except ValidationError as e:
        print(
            f"Validateion fail，extraction terminated，watermark will not be updated：{e}")
        return

    out_path = load(df, pending_dates)
    print(f"Wrote into landing file: {out_path}")

    inserted = load_to_db(df)
    print(f"Inserted {inserted} new records into raw.raw_orders_incremental")

    write_watermark(pending_dates[-1])
    print(f"watermark updated: {pending_dates[-1]}")


if __name__ == "__main__":
    main()
