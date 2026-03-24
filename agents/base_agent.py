"""
Tüm Ajanların Temel Sınıfı — Ortak çalışma döngüsü, loglama ve mesajlaşma.
"""

import time
import logging
import traceback
from abc import ABC, abstractmethod
from datetime import datetime
from database.db import get_session, Base, engine
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, Float
from sqlalchemy.orm import declarative_base

logger = logging.getLogger(__name__)


# ── Ajan mesaj ve çalışma kayıt modelleri ──

class AgentMessage(Base):
    """Ajanlar arası mesaj."""
    __tablename__ = "agent_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    from_agent = Column(String(50))
    to_agent = Column(String(50), default="orkestrator")
    message_type = Column(String(20))  # "result", "alert", "request", "error"
    payload = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)


class AgentRun(Base):
    """Ajan çalışma kaydı."""
    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_name = Column(String(50))
    started_at = Column(DateTime)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="running")  # running, completed, failed
    result_summary = Column(Text, default="")
    items_found = Column(Integer, default=0)
    duration_seconds = Column(Float, default=0.0)
    error_message = Column(Text, default="")


# Tabloları oluştur
Base.metadata.create_all(bind=engine)


class BaseAgent(ABC):
    """Tüm ajanların temel sınıfı."""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.is_running = False
        self.last_run: datetime | None = None
        self.last_result: dict = {}
        self.logger = logging.getLogger(f"agent.{name}")

    @abstractmethod
    def execute(self, **kwargs) -> dict:
        """Ajanın ana görevini çalıştırır.

        Returns:
            {"success": bool, "items_found": int, "summary": str, "data": any}
        """
        pass

    def run(self, **kwargs) -> dict:
        """Ajanı çalıştırır — loglama, hata yönetimi ve kayıt ile."""
        self.is_running = True
        start_time = datetime.utcnow()
        run_record = AgentRun(
            agent_name=self.name,
            started_at=start_time,
            status="running",
        )

        session = get_session()
        try:
            session.add(run_record)
            session.commit()

            self.logger.info(f"🚀 {self.name} başlatıldı")
            result = self.execute(**kwargs)

            # Başarılı tamamlanma
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            run_record.completed_at = end_time
            run_record.status = "completed"
            run_record.result_summary = result.get("summary", "")
            run_record.items_found = result.get("items_found", 0)
            run_record.duration_seconds = duration
            session.commit()

            # Sonucu mesaj olarak kaydet
            self._send_message("result", result)

            self.last_run = end_time
            self.last_result = result
            self.logger.info(
                f"✅ {self.name} tamamlandı ({duration:.1f}s) — "
                f"{result.get('items_found', 0)} sonuç"
            )
            return result

        except Exception as e:
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            run_record.completed_at = end_time
            run_record.status = "failed"
            run_record.error_message = str(e)
            run_record.duration_seconds = duration
            session.commit()

            self._send_message("error", {
                "error": str(e),
                "traceback": traceback.format_exc(),
            })

            self.logger.error(f"❌ {self.name} hata: {e}")
            return {"success": False, "error": str(e), "items_found": 0}

        finally:
            self.is_running = False
            session.close()

    def _send_message(self, msg_type: str, payload: dict):
        """Orkestratöre mesaj gönderir."""
        session = get_session()
        try:
            msg = AgentMessage(
                from_agent=self.name,
                to_agent="orkestrator",
                message_type=msg_type,
                payload=payload,
                created_at=datetime.utcnow(),
            )
            session.add(msg)
            session.commit()
        except Exception as e:
            self.logger.error(f"Mesaj gönderme hatası: {e}")
        finally:
            session.close()

    def get_status(self) -> dict:
        """Ajan durumunu döndürür."""
        session = get_session()
        try:
            last_run = (
                session.query(AgentRun)
                .filter(AgentRun.agent_name == self.name)
                .order_by(AgentRun.started_at.desc())
                .first()
            )
            if last_run:
                return {
                    "name": self.name,
                    "description": self.description,
                    "is_running": self.is_running,
                    "last_status": last_run.status,
                    "last_run": last_run.started_at.strftime("%d.%m.%Y %H:%M") if last_run.started_at else "-",
                    "last_duration": f"{last_run.duration_seconds:.1f}s",
                    "last_items": last_run.items_found,
                    "last_summary": last_run.result_summary[:100],
                    "last_error": last_run.error_message[:100] if last_run.error_message else "",
                }
            return {
                "name": self.name,
                "description": self.description,
                "is_running": self.is_running,
                "last_status": "never_run",
                "last_run": "-",
            }
        finally:
            session.close()

    @staticmethod
    def get_recent_runs(agent_name: str = None, limit: int = 20) -> list[dict]:
        """Son çalışma kayıtlarını döndürür."""
        session = get_session()
        try:
            query = session.query(AgentRun).order_by(AgentRun.started_at.desc())
            if agent_name:
                query = query.filter(AgentRun.agent_name == agent_name)
            runs = query.limit(limit).all()
            return [
                {
                    "agent": r.agent_name,
                    "started": r.started_at.strftime("%d.%m.%Y %H:%M") if r.started_at else "",
                    "status": r.status,
                    "duration": f"{r.duration_seconds:.1f}s",
                    "items": r.items_found,
                    "summary": r.result_summary[:80],
                }
                for r in runs
            ]
        finally:
            session.close()

    @staticmethod
    def get_unread_messages(to_agent: str = "orkestrator", limit: int = 50) -> list[dict]:
        """Okunmamış mesajları döndürür."""
        session = get_session()
        try:
            msgs = (
                session.query(AgentMessage)
                .filter(AgentMessage.to_agent == to_agent, AgentMessage.is_read == False)
                .order_by(AgentMessage.created_at.desc())
                .limit(limit)
                .all()
            )
            results = []
            for m in msgs:
                results.append({
                    "id": m.id,
                    "from": m.from_agent,
                    "type": m.message_type,
                    "payload": m.payload,
                    "time": m.created_at.strftime("%d.%m.%Y %H:%M"),
                })
                m.is_read = True
            session.commit()
            return results
        finally:
            session.close()
