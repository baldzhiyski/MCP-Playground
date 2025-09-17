from sqlalchemy import create_engine,Column,Integer,String,Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import List, Any

engine = create_engine('sqlite:///notes.db')
SessionLocal = sessionmaker(autocommit = False, autoflush=False,bind=engine)
Base = declarative_base()


class Note(Base):
    __tablename__ = 'notes'

    id=Column(Integer,primary_key=True,index=True)
    user_id=Column(String,nullable=False,index=True)
    content = Column(Text,nullable=False)

Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class NoteRepository:

    @staticmethod
    def get_notes_by_user(user_id:str) -> List[Note]:
        db = SessionLocal()
        try:
            return db.query(Note).filter(Note.user_id==user_id).all()
        finally:
            db.close()

    @staticmethod
    def create_note(user_id: str,content:str) -> Note:
        db = SessionLocal()
        try:
            note = Note(user_id=user_id,content=content)
            db.add(note)
            db.commit()
            db.refresh(note)
            return note
        finally:
            db.close()