import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

# =======================
# CONFIGURACIÓN DE BASE DE DATOS
# =======================
DB_HOST = os.getenv("POSTGRES_HOST", "postgres")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "rips_database")
DB_USER = os.getenv("POSTGRES_USER", "rips_user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "rips_password")

@contextmanager
def get_db_connection():
    """Context manager para manejar conexiones a la base de datos."""
    conn = None
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        yield conn
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

def init_db():
    """Crear la tabla de mensajes si no existe."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id SERIAL PRIMARY KEY,
                        user_name VARCHAR(100) NOT NULL,
                        user_message TEXT NOT NULL,
                        bot_response TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                conn.commit()
                print("✅ Tabla 'messages' creada/verificada correctamente")
    except Exception as e:
        print(f"❌ Error al inicializar la base de datos: {e}")
        raise e

def save_message(user_name: str, user_message: str, bot_response: str):
    """Guardar un mensaje en la base de datos."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO messages (user_name, user_message, bot_response)
                    VALUES (%s, %s, %s)
                """, (user_name, user_message, bot_response))
                conn.commit()
                print(f"✅ Mensaje guardado para usuario: {user_name}")
    except Exception as e:
        print(f"❌ Error al guardar mensaje: {e}")
        raise e

def fetch_messages(limit: int = 20):
    """Obtener los últimos mensajes de la base de datos."""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, user_name, user_message, bot_response, created_at
                    FROM messages
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (limit,))
                messages = cursor.fetchall()
                return [dict(msg) for msg in messages]
    except Exception as e:
        print(f"❌ Error al obtener mensajes: {e}")
        return []
