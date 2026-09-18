from sqlalchemy.orm import Session
from app.models.comment import Comment
from app.schemas.comment import CommentCreate


def create_comment(db: Session, ticket_id: int, comment_data: CommentCreate) -> Comment:
    new_comment = Comment(
        ticket_id=ticket_id,
        author=comment_data.author,
        text=comment_data.text,
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment


def get_comments_by_ticket(db: Session, ticket_id: int):
    return (
        db.query(Comment)
        .filter(Comment.ticket_id == ticket_id)
        .order_by(Comment.created_at.asc())
        .all()
    )