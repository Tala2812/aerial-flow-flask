import os
import sqlite3
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = 'aerial-flow-secret-key-2024'


def get_db():
    conn = sqlite3.connect('aerial_flow.db')
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact TEXT NOT NULL,
            format TEXT,
            comment TEXT,
            consent BOOLEAN DEFAULT 0,
            status TEXT DEFAULT 'new',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            places INTEGER DEFAULT 10,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            date TEXT,
            image_url TEXT,
            status TEXT DEFAULT 'draft',
            social_text TEXT,
            is_published BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()

    count = cursor.execute('SELECT COUNT(*) FROM events').fetchone()[0]
    if count == 0:
        cursor.executemany(
            'INSERT INTO events (title, date, description, places, is_active) VALUES (?, ?, ?, ?, ?)',
            [
                ('Открытый урок для новичков', '2024-04-05',
                 'Пробное занятие для тех, кто никогда не занимался воздушной гимнастикой. Мягкая адаптация, базовые элементы, тёплая атмосфера.',
                 12, 1),
                ('Мягкая растяжка и полотна', '2024-04-12',
                 'Комбинированное занятие: разогрев, растяжка и работа на полотнах. Подходит для любого уровня подготовки.',
                 10, 1),
                ('Мини-группа "Первый полёт"', '2024-04-19',
                 'Закрытая мини-группа до 4 человек. Максимум внимания преподавателя и бережная поддержка.',
                 4, 1),
            ]
        )

    count = cursor.execute('SELECT COUNT(*) FROM news').fetchone()[0]
    if count == 0:
        cursor.executemany(
            'INSERT INTO news (title, description, date, image_url, status, social_text, is_published) VALUES (?, ?, ?, ?, ?, ?, ?)',
            [
                ('Весенний набор в группы',
                 'Приглашаем вас на весенний сезон воздушной гимнастики. Новые группы, удобное расписание и первые результаты уже через месяц.',
                 '2024-03-01', '', 'ready', '', 0),
                ('Как проходят наши занятия',
                 'Рассказываем, как проходит подготовка к тренировке: разминка, настрой, работа с дыханием. Важно не только тело, но и внутреннее состояние.',
                 '2024-03-10', '', 'published', '', 1),
                ('Специальное предложение марта',
                 'Весь март — скидка 20% на первое занятие для всех новых учениц. Приводите подругу и получайте дополнительный бонус.',
                 '2024-03-15', '', 'draft', '', 0),
            ]
        )

    conn.commit()
    conn.close()


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated


@app.route('/')
def index():
    conn = get_db()
    events = conn.execute(
        'SELECT * FROM events WHERE is_active = 1 ORDER BY date ASC'
    ).fetchall()
    conn.close()
    return render_template('index.html', events=events)


@app.route('/submit-lead', methods=['POST'])
def submit_lead():
    name = request.form.get('name')
    contact = request.form.get('contact')
    format_type = request.form.get('format')
    comment = request.form.get('comment')
    consent = 1 if request.form.get('consent') else 0

    if not name or not contact:
        return jsonify({'success': False, 'error': 'Имя и контакт обязательны'}), 400

    conn = get_db()
    conn.execute(
        'INSERT INTO leads (name, contact, format, comment, consent) VALUES (?, ?, ?, ?, ?)',
        (name, contact, format_type, comment, consent)
    )
    conn.commit()
    conn.close()

    return jsonify({'success': True})


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form.get('username') == 'admin' and request.form.get('password') == 'demo123':
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        return render_template('admin_login.html', error='Неверный логин или пароль')
    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))


@app.route('/admin')
@login_required
def admin_dashboard():
    conn = get_db()
    leads_count = conn.execute('SELECT COUNT(*) FROM leads').fetchone()[0]
    new_leads = conn.execute("SELECT COUNT(*) FROM leads WHERE status = 'new'").fetchone()[0]
    events_count = conn.execute('SELECT COUNT(*) FROM events').fetchone()[0]
    news_count = conn.execute('SELECT COUNT(*) FROM news').fetchone()[0]
    conn.close()
    return render_template('admin/dashboard.html',
                           leads_count=leads_count, new_leads=new_leads,
                           events_count=events_count, news_count=news_count)


@app.route('/admin/leads')
@login_required
def admin_leads():
    conn = get_db()
    leads = conn.execute('SELECT * FROM leads ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('admin/leads.html', leads=leads)


@app.route('/admin/leads/<int:lead_id>/status', methods=['POST'])
@login_required
def update_lead_status(lead_id):
    status = request.form.get('status')
    if status not in ('new', 'in_progress', 'completed'):
        return jsonify({'success': False, 'error': 'Недопустимый статус'}), 400
    conn = get_db()
    conn.execute('UPDATE leads SET status = ? WHERE id = ?', (status, lead_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/admin/events')
@login_required
def admin_events():
    conn = get_db()
    events = conn.execute('SELECT * FROM events ORDER BY date ASC').fetchall()
    conn.close()
    return render_template('admin/events.html', events=events)


@app.route('/admin/events/new', methods=['GET', 'POST'])
@login_required
def admin_event_new():
    if request.method == 'POST':
        conn = get_db()
        conn.execute(
            'INSERT INTO events (title, date, description, places, is_active) VALUES (?, ?, ?, ?, ?)',
            (request.form['title'], request.form['date'],
             request.form.get('description', ''), request.form.get('places', 10),
             1 if request.form.get('is_active') else 0)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('admin_events'))
    return render_template('admin/event_form.html', event=None)


@app.route('/admin/events/<int:event_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_event_edit(event_id):
    conn = get_db()
    if request.method == 'POST':
        conn.execute(
            'UPDATE events SET title=?, date=?, description=?, places=?, is_active=? WHERE id=?',
            (request.form['title'], request.form['date'],
             request.form.get('description', ''), request.form.get('places', 10),
             1 if request.form.get('is_active') else 0, event_id)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('admin_events'))
    event = conn.execute('SELECT * FROM events WHERE id = ?', (event_id,)).fetchone()
    conn.close()
    return render_template('admin/event_form.html', event=event)


@app.route('/admin/events/<int:event_id>/delete', methods=['POST'])
@login_required
def admin_event_delete(event_id):
    conn = get_db()
    conn.execute('DELETE FROM events WHERE id = ?', (event_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_events'))


@app.route('/admin/news')
@login_required
def admin_news():
    conn = get_db()
    news_list = conn.execute('SELECT * FROM news ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('admin/news.html', news_list=news_list)


@app.route('/admin/news/new', methods=['GET', 'POST'])
@login_required
def admin_news_new():
    if request.method == 'POST':
        conn = get_db()
        conn.execute(
            'INSERT INTO news (title, description, date, image_url, status, is_published) VALUES (?, ?, ?, ?, ?, ?)',
            (request.form['title'], request.form.get('description', ''),
             request.form.get('date', ''), request.form.get('image_url', ''),
             request.form.get('status', 'draft'),
             1 if request.form.get('is_published') else 0)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('admin_news'))
    return render_template('admin/news_form.html', news_item=None)


@app.route('/admin/news/<int:news_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_news_edit(news_id):
    conn = get_db()
    if request.method == 'POST':
        conn.execute(
            'UPDATE news SET title=?, description=?, date=?, image_url=?, status=?, is_published=? WHERE id=?',
            (request.form['title'], request.form.get('description', ''),
             request.form.get('date', ''), request.form.get('image_url', ''),
             request.form.get('status', 'draft'),
             1 if request.form.get('is_published') else 0, news_id)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('admin_news'))
    news_item = conn.execute('SELECT * FROM news WHERE id = ?', (news_id,)).fetchone()
    conn.close()
    return render_template('admin/news_form.html', news_item=news_item)


@app.route('/admin/news/<int:news_id>/delete', methods=['POST'])
@login_required
def admin_news_delete(news_id):
    conn = get_db()
    conn.execute('DELETE FROM news WHERE id = ?', (news_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_news'))


@app.route('/admin/news/<int:news_id>/generate-post', methods=['POST'])
@login_required
def admin_news_generate_post(news_id):
    conn = get_db()
    item = conn.execute('SELECT * FROM news WHERE id = ?', (news_id,)).fetchone()

    template = (
        f"✨ Открыта запись на пробное занятие по воздушной гимнастике.\n\n"
        f"Если вы давно хотели попробовать что-то новое, почувствовать лёгкость "
        f"в теле и сделать первый шаг к красивому движению — это хороший момент.\n\n"
        f"📌 {item['title']}\n"
        f"📅 {item['date'] if item['date'] else 'Уточняется'}\n"
        f"📝 {item['description'][:100] + '...' if item['description'] and len(item['description']) > 100 else item['description']}\n\n"
        f"Записаться можно через форму на сайте 🌸\n\n"
        f"#AerialFlow #ВоздушнаяГимнастика #ПробноеЗанятие"
    )

    conn.execute('UPDATE news SET social_text = ? WHERE id = ?', (template, news_id))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'social_text': template})


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
