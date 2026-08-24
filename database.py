import sqlite3
import datetime
from typing import Optional, List, Dict, Any
from config import DB_NAME

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes SQLite database tables."""
    conn = get_connection()
    cursor = conn.cursor()

    # Table for registered users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table for movies catalog
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_code TEXT UNIQUE,
            title TEXT NOT NULL,
            description TEXT,
            file_id TEXT,
            file_type TEXT DEFAULT 'document',
            download_url TEXT,
            poster_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

def add_or_update_user(user_id: int, username: Optional[str], first_name: Optional[str]):
    """Records or updates a user who used the bot."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (user_id, username, first_name, joined_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username=excluded.username,
            first_name=excluded.first_name
    """, (user_id, username, first_name, datetime.datetime.now()))
    conn.commit()
    conn.close()

def get_all_users() -> List[int]:
    """Returns all user IDs for broadcasting."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [row["user_id"] for row in rows]

def get_user_count() -> int:
    """Returns the total number of users."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM users")
    row = cursor.fetchone()
    conn.close()
    return row["count"] if row else 0

def add_movie(
    title: str,
    movie_code: Optional[str] = None,
    description: Optional[str] = None,
    file_id: Optional[str] = None,
    file_type: str = "document",
    download_url: Optional[str] = None,
    poster_url: Optional[str] = None
) -> int:
    """Adds a new movie to the database."""
    conn = get_connection()
    cursor = conn.cursor()

    if not movie_code:
        # Generate default movie code if not provided
        base_code = "".join(c.lower() for c in title if c.isalnum() or c == "_")[:20]
        timestamp = int(datetime.datetime.now().timestamp())
        movie_code = f"{base_code}_{timestamp}"

    cursor.execute("""
        INSERT INTO movies (movie_code, title, description, file_id, file_type, download_url, poster_url)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (movie_code, title, description, file_id, file_type, download_url, poster_url))
    
    movie_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return movie_id

def get_movie_by_code(movie_code: str) -> Optional[Dict[str, Any]]:
    """Fetches a movie by its unique code."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM movies WHERE movie_code = ?", (movie_code,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_movie_by_id(movie_id: int) -> Optional[Dict[str, Any]]:
    """Fetches a movie by its primary key ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM movies WHERE id = ?", (movie_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def search_movies(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Searches for movies by title or description."""
    conn = get_connection()
    cursor = conn.cursor()
    search_term = f"%{query.strip()}%"
    cursor.execute("""
        SELECT * FROM movies 
        WHERE title LIKE ? OR description LIKE ? OR movie_code LIKE ?
        ORDER BY id DESC LIMIT ?
    """, (search_term, search_term, search_term, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_latest_movies(limit: int = 10) -> List[Dict[str, Any]]:
    """Returns the latest added movies."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM movies ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_movie_count() -> int:
    """Returns total number of movies stored."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM movies")
    row = cursor.fetchone()
    conn.close()
    return row["count"] if row else 0

def delete_movie(movie_id: int) -> bool:
    """Deletes a movie by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM movies WHERE id = ?", (movie_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted
