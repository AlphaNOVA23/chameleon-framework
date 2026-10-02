from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import datetime
import os

Base = declarative_base()

class SessionData(Base):
    __tablename__ = 'sessions'
    
    id = Column(String, primary_key=True)  # Cowrie session_id (e.g., ecd5f8b42f05)
    src_ip = Column(String)
    connected_at = Column(DateTime)
    closed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, default=0)
    
    classification = Column(String, default="UNKNOWN")
    mean_iat = Column(Float, default=0.0)
    variance_iat = Column(Float, default=0.0)
    
    # Relationships
    commands = relationship("CommandData", back_populates="session")
    deceptions = relationship("DeceptionData", back_populates="session")

class CommandData(Base):
    __tablename__ = 'commands'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey('sessions.id'))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    text = Column(String)
    intent_tactic = Column(String, nullable=True)
    intent_severity = Column(Integer, default=0)
    
    session = relationship("SessionData", back_populates="commands")

class DeceptionData(Base):
    __tablename__ = 'deceptions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey('sessions.id'))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    action = Column(String)    # e.g., "STATIC_TARPIT", "HONEYTOKEN_INJECTED"
    payload = Column(String)   # The actual fake file content or poison string generated
    
    session = relationship("SessionData", back_populates="deceptions")

# Initialize Database
DB_PATH = os.path.join(os.path.dirname(__file__), 'chameleon.db')
engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)
Base.metadata.create_all(engine)

SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
