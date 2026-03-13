import argparse
import os
import sqlite3
import psycopg2
from dotenv import load_dotenv


def fetch_rows(sqlite_conn, table_name):
    sqlite_conn.row_factory = sqlite3.Row
    cur = sqlite_conn.cursor()
    table_exists = cur.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    if not table_exists:
        return []
    return cur.execute(f"SELECT * FROM {table_name}").fetchall()


def ensure_schema(pg_cur):
    pg_cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            phone VARCHAR(30),
            notification_preference VARCHAR(20) DEFAULT 'email',
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(100) NOT NULL,
            title VARCHAR(500) NOT NULL,
            importance VARCHAR(20) DEFAULT 'not-important',
            urgency VARCHAR(20) DEFAULT 'not-urgent',
            completed BOOLEAN DEFAULT FALSE,
            emotion_applied VARCHAR(50),
            due_at TIMESTAMP,
            reminder_at TIMESTAMP,
            reminder_method VARCHAR(20),
            reminder_sent BOOLEAN DEFAULT FALSE,
            reminder_phone VARCHAR(30),
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS emotion_logs (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(100) NOT NULL,
            emotion VARCHAR(50) NOT NULL,
            confidence FLOAT DEFAULT 0.0,
            scanned_at TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);
        """
    )


def migrate_users(pg_cur, rows):
    for row in rows:
        pg_cur.execute(
            """
            INSERT INTO users (id, email, password_hash, phone, notification_preference, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (email) DO UPDATE SET
                password_hash = EXCLUDED.password_hash,
                phone = EXCLUDED.phone,
                notification_preference = EXCLUDED.notification_preference,
                updated_at = EXCLUDED.updated_at
            """,
            (
                row["id"],
                row["email"],
                row["password_hash"],
                row["phone"] if "phone" in row.keys() else None,
                row["notification_preference"] if "notification_preference" in row.keys() else "email",
                row["created_at"] if "created_at" in row.keys() else None,
                row["updated_at"] if "updated_at" in row.keys() else None,
            ),
        )


def migrate_tasks(pg_cur, rows):
    for row in rows:
        pg_cur.execute(
            """
            INSERT INTO tasks (
                id, user_id, title, importance, urgency, completed, emotion_applied,
                due_at, reminder_at, reminder_method, reminder_sent, reminder_phone,
                created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                user_id = EXCLUDED.user_id,
                title = EXCLUDED.title,
                importance = EXCLUDED.importance,
                urgency = EXCLUDED.urgency,
                completed = EXCLUDED.completed,
                emotion_applied = EXCLUDED.emotion_applied,
                due_at = EXCLUDED.due_at,
                reminder_at = EXCLUDED.reminder_at,
                reminder_method = EXCLUDED.reminder_method,
                reminder_sent = EXCLUDED.reminder_sent,
                reminder_phone = EXCLUDED.reminder_phone,
                updated_at = EXCLUDED.updated_at
            """,
            (
                row["id"],
                row["user_id"],
                row["title"],
                row["importance"] if "importance" in row.keys() else "not-important",
                row["urgency"] if "urgency" in row.keys() else "not-urgent",
                bool(row["completed"]) if "completed" in row.keys() else False,
                row["emotion_applied"] if "emotion_applied" in row.keys() else None,
                row["due_at"] if "due_at" in row.keys() else None,
                row["reminder_at"] if "reminder_at" in row.keys() else None,
                row["reminder_method"] if "reminder_method" in row.keys() else None,
                bool(row["reminder_sent"]) if "reminder_sent" in row.keys() else False,
                row["reminder_phone"] if "reminder_phone" in row.keys() else None,
                row["created_at"] if "created_at" in row.keys() else None,
                row["updated_at"] if "updated_at" in row.keys() else None,
            ),
        )


def migrate_emotion_logs(pg_cur, rows):
    for row in rows:
        pg_cur.execute(
            """
            INSERT INTO emotion_logs (id, user_id, emotion, confidence, scanned_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                user_id = EXCLUDED.user_id,
                emotion = EXCLUDED.emotion,
                confidence = EXCLUDED.confidence,
                scanned_at = EXCLUDED.scanned_at
            """,
            (
                row["id"],
                row["user_id"],
                row["emotion"],
                row["confidence"] if "confidence" in row.keys() else 0.0,
                row["scanned_at"] if "scanned_at" in row.keys() else None,
            ),
        )


def reset_sequences(pg_cur):
    for table_name in ["users", "tasks", "emotion_logs"]:
        pg_cur.execute(
            f"""
            SELECT setval(
                pg_get_serial_sequence('{table_name}', 'id'),
                COALESCE((SELECT MAX(id) FROM {table_name}), 1),
                (SELECT COUNT(*) > 0 FROM {table_name})
            )
            """
        )


def main():
    parser = argparse.ArgumentParser(description="Migrate SQLite data to PostgreSQL")
    parser.add_argument("--sqlite", default=os.path.join("Backend", "tasks.db"), help="Path to SQLite database")
    parser.add_argument("--postgres", default=None, help="PostgreSQL URL")
    args = parser.parse_args()

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    load_dotenv(os.path.join(project_root, ".env"))

    postgres_url = args.postgres or os.getenv("DATABASE_URL")
    if not postgres_url:
        raise SystemExit("DATABASE_URL missing. Set it in .env or pass --postgres")
    if not (postgres_url.startswith("postgresql://") or postgres_url.startswith("postgresql+psycopg2://")):
        raise SystemExit("DATABASE_URL must be a PostgreSQL URL")
    if not os.path.exists(args.sqlite):
        raise SystemExit(f"SQLite file not found: {args.sqlite}")

    sqlite_conn = sqlite3.connect(args.sqlite)
    pg_conn = psycopg2.connect(postgres_url)
    pg_conn.autocommit = False
    pg_cur = pg_conn.cursor()

    try:
        ensure_schema(pg_cur)

        users = fetch_rows(sqlite_conn, "users")
        tasks = fetch_rows(sqlite_conn, "tasks")
        emotion_logs = fetch_rows(sqlite_conn, "emotion_logs")

        migrate_users(pg_cur, users)
        migrate_tasks(pg_cur, tasks)
        migrate_emotion_logs(pg_cur, emotion_logs)
        reset_sequences(pg_cur)

        pg_conn.commit()
        print(
            "Migration completed successfully: "
            f"users={len(users)}, tasks={len(tasks)}, emotion_logs={len(emotion_logs)}"
        )
    except Exception:
        pg_conn.rollback()
        raise
    finally:
        pg_cur.close()
        pg_conn.close()
        sqlite_conn.close()


if __name__ == "__main__":
    main()
