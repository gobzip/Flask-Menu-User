import os
import sqlite3

from flask import session
from werkzeug.security import check_password_hash, generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), 'app.db')


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            group_name TEXT NOT NULL
        )
        '''
    )
    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT UNIQUE NOT NULL
        )
        '''
    )
    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS user_groups (
            user_id INTEGER NOT NULL,
            group_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, group_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE
        )
        '''
    )

    default_groups = ['admin', 'reguler']
    for group_name in default_groups:
        conn.execute(
            'INSERT OR IGNORE INTO groups (group_name) VALUES (?)',
            (group_name,),
        )

    user_count = conn.execute('SELECT COUNT(*) AS total FROM users').fetchone()['total']
    if user_count == 0:
        conn.executemany(
            'INSERT INTO users (username, password, group_name) VALUES (?, ?, ?)',
            [
                ('admin', generate_password_hash('rahasia'), 'admin'),
                ('pemakai', generate_password_hash('rahasia'), 'reguler'),
            ],
        )

    existing_groups = {
        row['group_name']
        for row in conn.execute('SELECT DISTINCT group_name FROM users').fetchall()
    }
    for group_name in existing_groups:
        conn.execute(
            'INSERT OR IGNORE INTO groups (group_name) VALUES (?)',
            (group_name,),
        )

    user_rows = conn.execute(
        'SELECT id, group_name FROM users ORDER BY id ASC'
    ).fetchall()
    for user in user_rows:
        if not user['group_name']:
            continue

        group_row = conn.execute(
            'SELECT id FROM groups WHERE group_name = ?',
            (user['group_name'],),
        ).fetchone()
        if group_row is None:
            continue

        conn.execute(
            'INSERT OR IGNORE INTO user_groups (user_id, group_id) VALUES (?, ?)',
            (user['id'], group_row['id']),
        )

    conn.commit()
    conn.close()


def get_groups():
    conn = get_db_connection()
    groups = conn.execute(
        'SELECT id, group_name FROM groups ORDER BY id ASC'
    ).fetchall()
    conn.close()
    return groups


def get_user_groups(user_id, conn=None):
    close_conn = conn is None
    if conn is None:
        conn = get_db_connection()

    rows = conn.execute(
        '''
        SELECT g.id, g.group_name
        FROM user_groups ug
        INNER JOIN groups g ON g.id = ug.group_id
        WHERE ug.user_id = ?
        ORDER BY g.id ASC
        ''',
        (user_id,),
    ).fetchall()

    if close_conn:
        conn.close()

    return rows


def get_user_group_names(user_id, conn=None):
    return [row['group_name'] for row in get_user_groups(user_id, conn)]


def sync_user_groups(conn, user_id, group_names):
    selected_groups = []
    seen = set()

    for group_name in group_names:
        group_name = group_name.strip()
        if group_name and group_name not in seen:
            selected_groups.append(group_name)
            seen.add(group_name)

    conn.execute('DELETE FROM user_groups WHERE user_id = ?', (user_id,))

    for group_name in selected_groups:
        existing_group = conn.execute(
            'SELECT id FROM groups WHERE group_name = ?',
            (group_name,),
        ).fetchone()

        if existing_group is None:
            conn.execute(
                'INSERT INTO groups (group_name) VALUES (?)',
                (group_name,),
            )
            existing_group = conn.execute(
                'SELECT id FROM groups WHERE group_name = ?',
                (group_name,),
            ).fetchone()

        conn.execute(
            'INSERT INTO user_groups (user_id, group_id) VALUES (?, ?)',
            (user_id, existing_group['id']),
        )

    primary_group = selected_groups[0] if selected_groups else ''
    conn.execute(
        'UPDATE users SET group_name = ? WHERE id = ?',
        (primary_group, user_id),
    )


def is_admin_session():
    groups = session.get('groups') or []
    return 'admin' in groups or session.get('group') == 'admin'


def login_user(username, password):
    conn = get_db_connection()
    user = conn.execute(
        'SELECT id, username, password, group_name FROM users WHERE username = ?',
        (username,),
    ).fetchone()
    conn.close()

    if user and check_password_hash(user['password'], password):
        connected_groups = get_user_group_names(user['id'])
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['groups'] = connected_groups
        session['group'] = 'admin' if 'admin' in connected_groups else (
            connected_groups[0] if connected_groups else ''
        )
        return user

    return None
