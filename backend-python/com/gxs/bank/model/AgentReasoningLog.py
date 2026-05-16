from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, Float, String, Text

from com.gxs.bank.config.database import Base


class AgentReasoningLog(Base):
    __tablename__ = "agent_reasoning_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    userId = Column("user_id", String(36), nullable=False)
    agentName = Column("agent_name", String(100), nullable=False)
    intent = Column(String(100), nullable=True)
    inputMessage = Column("input_message", Text, nullable=True)
    outputSummary = Column("output_summary", Text, nullable=True)
    routingChain = Column("routing_chain", Text, nullable=True)   # JSON array string
    agentsCalled = Column("agents_called", Text, nullable=True)   # JSON array string
    durationMs = Column("duration_ms", Float, nullable=True)
    graphMode = Column("graph_mode", String(50), nullable=True)
    createdAt = Column("created_at", DateTime, nullable=False, default=datetime.utcnow)
