import os
import logging
from typing import Optional
import psycopg2
from psycopg2 import pool
from sqlalchemy import create_engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "chat_db"), 
    "user": os.getenv("DB_USER", "chat_user"),
    "password": os.getenv("DB_PASSWORD", "chat_pass"),
    "port": int(os.getenv("DB_PORT", "5432"))
}

# Connection pool
_connection_pool: Optional[psycopg2.pool.SimpleConnectionPool] = None

def get_connection_pool():
    """Get or create database connection pool."""
    global _connection_pool
    if _connection_pool is None:
        try:
            _connection_pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=5,
                **DB_CONFIG
            )
            logger.info("Database connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise
    return _connection_pool

def get_db_connection():
    """Get database connection and cursor from pool."""
    pool = get_connection_pool()
    try:
        conn = pool.getconn()
        cur = conn.cursor()
        return conn, cur
    except Exception as e:
        logger.error(f"Failed to get connection from pool: {e}")
        raise

def close_db_connection(conn, cur):
    """Return connection to pool and close cursor."""
    try:
        if cur:
            cur.close()
        if conn:
            pool = get_connection_pool()
            pool.putconn(conn)
    except Exception as e:
        logger.error(f"Error closing connection: {e}")

def get_database_url():
    """Get SQLAlchemy database URL."""
    return f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"

def get_sqlalchemy_engine():
    """Get SQLAlchemy engine."""
    return create_engine(get_database_url())

def close_connection_pool():
    """Close all connections in the pool."""
    global _connection_pool
    if _connection_pool:
        _connection_pool.closeall()
        _connection_pool = None
        logger.info("Connection pool closed")