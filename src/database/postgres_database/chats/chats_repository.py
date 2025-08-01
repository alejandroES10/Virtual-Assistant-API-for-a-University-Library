from datetime import datetime
import os
from typing import Any

from dotenv import load_dotenv
import sqlalchemy as sa
from sqlalchemy.orm import declarative_base
from langchain_community.chat_message_histories.sql import BaseMessageConverter
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from src.database.postgres_database.chats.custom_sql_chat_message_history import CustomSQLChatMessageHistory


# Declarar base para el modelo
Base = declarative_base()

# Modelo de mensaje
class CustomMessage(Base):
    __tablename__ = "message_store"

    id = sa.Column(sa.BigInteger, primary_key=True, autoincrement=True)
    session_id = sa.Column(sa.Text, index=True)  
    type = sa.Column(sa.Text)
    content = sa.Column(sa.Text)
    created_at = sa.Column(sa.DateTime)

# Convertidor personalizado
class CustomMessageConverter(BaseMessageConverter):
    def __init__(self):
        super().__init__()

    def from_sql_model(self, sql_message: Any) -> BaseMessage:
        if sql_message.type == "human":
            return HumanMessage(content=sql_message.content)
        elif sql_message.type == "ai":
            return AIMessage(content=sql_message.content)
        elif sql_message.type == "system":
            return SystemMessage(content=sql_message.content)
        else:
            raise ValueError(f"Unknown message type: {sql_message.type}")

    def to_sql_model(self, message: BaseMessage, session_id: str) -> Any:
        return CustomMessage(
            session_id=session_id,
            type=message.type,
            content=message.content,
            created_at=datetime.now()
        )

    def get_sql_model_class(self) -> Any:
        return CustomMessage
    

from abc import ABC, abstractmethod
from langchain_core.chat_history import BaseChatMessageHistory


from psycopg_pool import AsyncConnectionPool



class BaseChatWithDatabase(ABC):
    """Clase base para manejar la conexión a la base de datos y el historial de mensajes."""

    @abstractmethod
    def get_chat_history(self, session_id: str)  -> BaseChatMessageHistory:
        """Método abstracto para obtener la conexión a la base de datos."""
        pass




import psycopg
from langchain_postgres import PostgresChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = "chats"

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
# DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/chats"
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from langchain_community.chat_message_histories import SQLChatMessageHistory

class ChatWithPostgres(BaseChatWithDatabase):
    def __init__(self):
        self._connection = self.init_connection()
        

    def init_connection(self):
        """Inicializa la conexión a la base de datos PostgreSQL."""
        return create_async_engine(url=
            DATABASE_URL)
        
        

    def get_chat_history(self, session_id: str) -> BaseChatMessageHistory:
        return CustomSQLChatMessageHistory(
            session_id=session_id,
            connection=self._connection,
            engine_args={"echo": False},
			custom_message_converter=CustomMessageConverter(),
            max_messages=4
        )



from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(url= DATABASE_URL)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def delete_old_messages():
    async with async_session() as session:
        cutoff_date = datetime.now() - timedelta(days=60)
        await session.execute(
            sa.delete(CustomMessage).where(CustomMessage.created_at < cutoff_date)
        )
        await session.commit()
        print(f"[{datetime.now()}] ✅ Messages older than {cutoff_date} have been deleted.")


