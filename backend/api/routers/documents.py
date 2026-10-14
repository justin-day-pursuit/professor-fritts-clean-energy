"""
Document upload API — stores files under .data/uploads and parses bills CSV when possible.
"""

from __future__ import annotations

import csv
import io
import uuid
from pathlib import Path
from uuid import UUID

from django.conf import settings
from fastapi import APIRouter, File, HTTPException, UploadFile

from api import schemas
from core import services

router = APIRouter(prefix="/sessions", tags=["documents"])


def _parse_bills_csv(content: bytes) -> dict:
    """
    Read a simple month,kwh CSV and return totals for parsed_summary.

    Non-numeric rows are skipped; maintain the two-column format in sample fixtures.
    """
    text = content.decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    monthly = []
    total = 0.0
    for row in reader:
        key = row.get("kwh") or row.get("KWH") or row.get("kWh")
        if key is None:
            continue
        try:
            val = float(str(key).replace(",", ""))
        except ValueError:
            continue
        month = row.get("month") or row.get("Month") or ""
        monthly.append({"month": month, "kwh": val})
        total += val
    return {"type": "bills", "months": monthly, "total_kwh": total}


@router.post("/{session_id}/documents", response_model=schemas.DocumentResponse)
async def upload_document(session_id: UUID, file: UploadFile = File(...)):
    """Accept multipart upload; parse bills CSV, otherwise record as received only."""
    try:
        await services.get_session_async(session_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc

    data_dir = getattr(settings, "DATA_DIR", Path("backend/.data"))
    upload_dir = Path(data_dir) / "uploads" / str(session_id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    raw = await file.read()
    safe_name = file.filename or "upload.bin"
    stored = upload_dir / f"{uuid.uuid4().hex}_{safe_name}"
    stored.write_bytes(raw)

    parsed: dict = {"status": "received", "parsed": False}
    name_lower = safe_name.lower()
    if name_lower.endswith(".csv") and ("bill" in name_lower or "kwh" in name_lower or True):
        try:
            bill_summary = _parse_bills_csv(raw)
            if bill_summary["months"]:
                parsed = {"status": "parsed", "parsed": True, **bill_summary}
        except Exception:
            parsed = {"status": "received", "parsed": False, "note": "CSV could not be parsed"}

    doc = await services.add_document_async(
        session_id,
        filename=safe_name,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(raw),
        stored_path=str(stored.relative_to(data_dir)),
        parsed_summary=parsed,
    )
    return schemas.DocumentResponse(
        id=doc.id,
        session_id=session_id,
        filename=doc.filename,
        content_type=doc.content_type,
        size_bytes=doc.size_bytes,
        stored_path=doc.stored_path,
        parsed_summary=doc.parsed_summary,
        created_at=doc.created_at,
    )
