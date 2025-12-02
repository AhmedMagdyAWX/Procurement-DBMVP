# services.py
from sqlalchemy.orm import Session
from models import ExampleItem


def create_example_item(db: Session, name: str, description: str | None = None) -> ExampleItem:
    item = ExampleItem(name=name, description=description)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def list_example_items(db: Session) -> list[ExampleItem]:
    return db.query(ExampleItem).order_by(ExampleItem.created_at.desc()).all()


def delete_example_item(db: Session, item_id: int) -> bool:
    item = db.query(ExampleItem).filter(ExampleItem.id == item_id).first()
    if not item:
        return False
    db.delete(item)
    db.commit()
    return True
