import csv
import io
import json
import sqlite3
from typing import Any

from fastapi import HTTPException, UploadFile

from app.models.database import get_connection, init_db
from app.schemas.sample import SOURCE_TYPES, SampleImportResponse, SampleItem, SampleListResponse


MAX_CSV_BYTES = 1_000_000
MAX_CSV_ROWS = 1000
REQUIRED_FIELDS = (
    "title",
    "content",
    "tags",
    "category",
    "likes",
    "collects",
    "comments",
    "cover_text",
    "source_note",
    "source_type",
)
OPTIONAL_FIELDS = ("publish_time",)
ALL_FIELDS = REQUIRED_FIELDS + OPTIONAL_FIELDS


def _parse_tags(value: str) -> list[str]:
    return [tag.strip().lstrip("#") for tag in value.replace("，", ",").split(",") if tag.strip()]


def _parse_int(value: str, field: str, row_number: int) -> int:
    try:
        parsed = int(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(f"第 {row_number} 行字段 {field} 必须是非负整数。") from exc
    if parsed < 0:
        raise ValueError(f"第 {row_number} 行字段 {field} 必须是非负整数。")
    return parsed


def _validate_row(row: dict[str, Any], row_number: int) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for field in REQUIRED_FIELDS:
        value = str(row.get(field, "")).strip()
        if not value:
            if field == "source_type":
                raise ValueError(f"第 {row_number} 行缺少 source_type，必须说明样本来源类型。")
            raise ValueError(f"第 {row_number} 行缺少必填字段 {field}。")
        cleaned[field] = value

    source_type = cleaned["source_type"]
    if source_type not in SOURCE_TYPES:
        allowed = ", ".join(SOURCE_TYPES)
        raise ValueError(f"第 {row_number} 行 source_type 无效：{source_type}。允许值：{allowed}。")

    tags = _parse_tags(cleaned["tags"])
    if not tags:
        raise ValueError(f"第 {row_number} 行 tags 至少需要 1 个标签。")

    cleaned["tags"] = tags
    cleaned["likes"] = _parse_int(cleaned["likes"], "likes", row_number)
    cleaned["collects"] = _parse_int(cleaned["collects"], "collects", row_number)
    cleaned["comments"] = _parse_int(cleaned["comments"], "comments", row_number)
    cleaned["publish_time"] = str(row.get("publish_time", "")).strip() or None
    return cleaned


def row_to_sample(row: Any) -> SampleItem:
    return SampleItem(
        id=row["id"],
        title=row["title"],
        content=row["content"],
        tags=json.loads(row["tags"]),
        category=row["category"],
        likes=row["likes"],
        collects=row["collects"],
        comments=row["comments"],
        cover_text=row["cover_text"],
        publish_time=row["publish_time"],
        source_note=row["source_note"],
        source_type=row["source_type"],
        created_at=row["created_at"],
    )


async def import_samples_csv(file: UploadFile) -> SampleImportResponse:
    init_db()
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="请上传 CSV 文件。")

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="CSV 文件为空。")
    if len(raw) > MAX_CSV_BYTES:
        raise HTTPException(status_code=400, detail=f"CSV 文件过大，当前限制为 {MAX_CSV_BYTES // 1000}KB。")

    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="CSV 文件必须使用 UTF-8 编码。") from exc

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV 缺少表头。")

    missing = [field for field in REQUIRED_FIELDS if field not in reader.fieldnames]
    if missing:
        raise HTTPException(status_code=400, detail=f"CSV 缺少必填字段：{', '.join(missing)}。")

    unknown_fields = [field for field in reader.fieldnames if field not in ALL_FIELDS]
    if unknown_fields:
        raise HTTPException(status_code=400, detail=f"CSV 包含不支持字段：{', '.join(unknown_fields)}。")

    rows: list[dict[str, Any]] = []
    try:
        for index, row in enumerate(reader, start=2):
            if len(rows) >= MAX_CSV_ROWS:
                raise ValueError(f"CSV 数据行超过上限 {MAX_CSV_ROWS} 行，请拆分后再导入。")
            rows.append(_validate_row(row, index))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not rows:
        raise HTTPException(status_code=400, detail="CSV 没有可导入的数据行。")

    inserted_ids: list[int] = []
    try:
        with get_connection() as connection:
            for row in rows:
                cursor = connection.execute(
                    """
                    INSERT INTO samples (
                        title, content, tags, category, likes, collects, comments,
                        cover_text, publish_time, source_note, source_type
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["title"],
                        row["content"],
                        json.dumps(row["tags"], ensure_ascii=False),
                        row["category"],
                        row["likes"],
                        row["collects"],
                        row["comments"],
                        row["cover_text"],
                        row["publish_time"],
                        row["source_note"],
                        row["source_type"],
                    ),
                )
                inserted_ids.append(cursor.lastrowid)
    except sqlite3.Error as exc:
        raise HTTPException(status_code=500, detail="样本写入数据库失败，请检查本地数据库文件权限或稍后重试。") from exc

    imported = [get_sample(sample_id) for sample_id in inserted_ids]
    return SampleImportResponse(imported_count=len(imported), samples=imported)


def list_samples(category: str | None = None, source_type: str | None = None) -> SampleListResponse:
    init_db()
    if source_type and source_type not in SOURCE_TYPES:
        allowed = ", ".join(SOURCE_TYPES)
        raise HTTPException(status_code=400, detail=f"source_type 无效。允许值：{allowed}。")

    clauses: list[str] = []
    params: list[str] = []
    if category:
        clauses.append("category = ?")
        params.append(category)
    if source_type:
        clauses.append("source_type = ?")
        params.append(source_type)

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    try:
        with get_connection() as connection:
            rows = connection.execute(f"SELECT * FROM samples {where_sql} ORDER BY id DESC", params).fetchall()
    except sqlite3.Error as exc:
        raise HTTPException(status_code=500, detail="读取样本列表失败，请检查数据库状态。") from exc
    items = [row_to_sample(row) for row in rows]
    return SampleListResponse(items=items, total=len(items))


def get_sample(sample_id: int) -> SampleItem:
    init_db()
    try:
        with get_connection() as connection:
            row = connection.execute("SELECT * FROM samples WHERE id = ?", (sample_id,)).fetchone()
    except sqlite3.Error as exc:
        raise HTTPException(status_code=500, detail="读取样本详情失败，请检查数据库状态。") from exc
    if not row:
        raise HTTPException(status_code=404, detail="样本不存在。")
    return row_to_sample(row)


def delete_sample(sample_id: int) -> dict[str, bool]:
    init_db()
    try:
        with get_connection() as connection:
            cursor = connection.execute("DELETE FROM samples WHERE id = ?", (sample_id,))
    except sqlite3.Error as exc:
        raise HTTPException(status_code=500, detail="删除样本失败，请检查数据库状态。") from exc
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="样本不存在。")
    return {"deleted": True}
