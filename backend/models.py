from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
import datetime
from database import Base

class SessionRecord(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, index=True)
    session_type = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Store all initial setup config
    configuration = Column(JSON)
    
    # Relationships
    messages = relationship("MessageRecord", back_populates="session")
    memories = relationship("UserMemory", back_populates="session")


class MessageRecord(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id"))
    sender = Column(String) # 'User' or 'AI'
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    session = relationship("SessionRecord", back_populates="messages")


class UserMemory(Base):
    __tablename__ = "user_memories"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id"))
    fact_key = Column(String, index=True)
    fact_value = Column(Text)
    
    session = relationship("SessionRecord", back_populates="memories")
