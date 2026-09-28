import sqlite3

from flask import Blueprint, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash

from helpers import (
    get_db_connection,
    get_groups,
    get_user_group_names,
    is_admin_session,
    sync_user_groups,
)

bp = Blueprint('settings', __name__, url_prefix='/settings')


@bp.route('/groups', methods=['GET', 'POST'])
def groups():
    if not is_admin_session():
        return redirect(url_for('auth.login'))

    error = None
    success = None

    if request.method == 'POST':
        group_name = request.form.get('group_name', '').strip()

        if not group_name:
            error = 'Nama group wajib diisi.'
        else:
            conn = get_db_connection()
            try:
                conn.execute(
                    'INSERT INTO groups (group_name) VALUES (?)',
                    (group_name,),
                )
                conn.commit()
                success = f'Group {group_name} berhasil ditambahkan.'
            except sqlite3.IntegrityError:
                error = 'Group sudah terdaftar.'
            finally:
                conn.close()

    group_rows = get_groups()

    return render_template(
        'groups.html',
        groups=group_rows,
        error=error,
        success=success,
        title='Group Management',
    )


@bp.route('/groups/<int:group_id>/edit', methods=['GET', 'POST'])
def edit_group(group_id):
    if not is_admin_session():
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    group = conn.execute(
        'SELECT id, group_name FROM groups WHERE id = ?',
        (group_id,),
    ).fetchone()
    conn.close()

    if group is None:
        return redirect(url_for('settings.groups'))

    error = None
    success = None

    if request.method == 'POST':
        group_name = request.form.get('group_name', '').strip()

        if not group_name:
            error = 'Nama group wajib diisi.'
        else:
            conn = get_db_connection()
            try:
                old_group_name = group['group_name']
                conn.execute(
                    'UPDATE groups SET group_name = ? WHERE id = ?',
                    (group_name, group_id),
                )
                conn.execute(
                    'UPDATE users SET group_name = ? WHERE group_name = ?',
                    (group_name, old_group_name),
                )
                conn.commit()
                success = f'Group berhasil diperbarui menjadi {group_name}.'
                group = {'id': group_id, 'group_name': group_name}
            except sqlite3.IntegrityError:
                error = 'Group sudah terdaftar.'
            finally:
                conn.close()

    return render_template(
        'edit_group.html',
        group=group,
        error=error,
        success=success,
        title='Edit Group',
    )


@bp.route('/groups/<int:group_id>/delete', methods=['POST'])
def delete_group(group_id):
    if not is_admin_session():
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    deleted_group = conn.execute(
        'SELECT group_name FROM groups WHERE id = ?',
        (group_id,),
    ).fetchone()

    if deleted_group is not None:
        conn.execute('DELETE FROM user_groups WHERE group_id = ?', (group_id,))
        conn.execute('DELETE FROM groups WHERE id = ?', (group_id,))
        conn.execute(
            'UPDATE users SET group_name = ? WHERE group_name = ?',
            ('', deleted_group['group_name']),
        )
        conn.commit()

    conn.close()

    return redirect(url_for('settings.groups'))


@bp.route('/users', methods=['GET', 'POST'])
def users():
    if not is_admin_session():
        return redirect(url_for('auth.login'))

    error = None
    success = None
    groups = get_groups()

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        group_names = request.form.getlist('group_names')

        if not username or not password or not group_names:
            error = 'Semua field wajib diisi.'
        else:
            conn = get_db_connection()
            try:
                conn.execute(
                    'INSERT INTO users (username, password, group_name) VALUES (?, ?, ?)',
                    (username, generate_password_hash(password), group_names[0]),
                )
                user_id = conn.execute('SELECT last_insert_rowid() AS id').fetchone()['id']
                sync_user_groups(conn, user_id, group_names)
                conn.commit()
                success = f'User {username} berhasil ditambahkan.'
            except sqlite3.IntegrityError:
                error = 'Username sudah terdaftar.'
            finally:
                conn.close()

    conn = get_db_connection()
    user_rows = conn.execute(
        'SELECT id, username, group_name FROM users ORDER BY id ASC'
    ).fetchall()

    users_data = []
    for user in user_rows:
        users_data.append(
            {
                'id': user['id'],
                'username': user['username'],
                'group_name': user['group_name'],
                'groups': get_user_group_names(user['id'], conn),
            }
        )

    conn.close()

    return render_template(
        'users.html',
        users=users_data,
        groups=groups,
        error=error,
        success=success,
        title='User Management',
    )


@bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
def edit_user(user_id):
    if not is_admin_session():
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    user = conn.execute(
        'SELECT id, username, group_name FROM users WHERE id = ?',
        (user_id,),
    ).fetchone()

    if user is None:
        conn.close()
        return redirect(url_for('settings.users'))

    existing_groups = get_user_group_names(user_id, conn)
    groups = get_groups()
    conn.close()

    error = None
    success = None

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        group_names = request.form.getlist('group_names')

        if not username or not group_names:
            error = 'Username dan minimal satu group wajib diisi.'
        else:
            conn = get_db_connection()
            try:
                if password:
                    conn.execute(
                        'UPDATE users SET username = ?, password = ?, group_name = ? WHERE id = ?',
                        (username, generate_password_hash(password), group_names[0], user_id),
                    )
                else:
                    conn.execute(
                        'UPDATE users SET username = ?, group_name = ? WHERE id = ?',
                        (username, group_names[0], user_id),
                    )

                sync_user_groups(conn, user_id, group_names)
                conn.commit()
                success = f'User {username} berhasil diperbarui.'
                user = {'id': user_id, 'username': username, 'group_name': group_names[0]}
                existing_groups = group_names
            except sqlite3.IntegrityError:
                error = 'Username sudah terdaftar.'
            finally:
                conn.close()

    return render_template(
        'edit_user.html',
        user=user,
        groups=groups,
        existing_groups=existing_groups,
        error=error,
        success=success,
        title='Edit User',
    )


@bp.route('/users/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):
    if not is_admin_session():
        return redirect(url_for('auth.login'))

    if session.get('user_id') == user_id:
        return redirect(url_for('settings.users'))

    conn = get_db_connection()
    conn.execute('DELETE FROM user_groups WHERE user_id = ?', (user_id,))
    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('settings.users'))
