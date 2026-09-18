import os
import uuid
from sqlalchemy.orm import Session
from fastapi import UploadFile
from app.models.attachment import Attachment
from app.config import UPLOAD_DIR, MAX_UPLOAD_SIZE_MB

MAX_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
ALLOWED_TYPES = {"image/png", "image/jpeg", "application/pdf", "text/plain"}
 


def validate_file(file: UploadFile, size_bytes: int):
    if file.content_type not in ALLOWED_TYPES:
        raise ValueError(
            f"File type '{file.content_type}' not allowed. Allowed: png, jpeg, pdf, txt"
        )
    if size_bytes > MAX_SIZE_BYTES:
        raise ValueError("File too large. Maximum allowed size is 5 MB")


def save_attachment(db: Session, ticket_id: int, file: UploadFile, contents: bytes) -> Attachment:
    validate_file(file, len(contents))

    # Unique naam banate hain taake 2 alag files same naam se overwrite na hon
    unique_name = f"{uuid.uuid4()}_{file.filename}"
    filepath = os.path.join(UPLOAD_DIR, unique_name)

    with open(filepath, "wb") as f:
        f.write(contents)

    record = Attachment(
        ticket_id=ticket_id,
        filename=file.filename,
        filepath=filepath,
        content_type=file.content_type,
        size_bytes=len(contents),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_attachments_by_ticket(db: Session, ticket_id: int):
    return db.query(Attachment).filter(Attachment.ticket_id == ticket_id).all()


def get_attachment_by_id(db: Session, attachment_id: int):
    return db.query(Attachment).filter(Attachment.id == attachment_id).first()