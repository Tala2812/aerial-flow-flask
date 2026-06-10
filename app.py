import os
import sqlite3
from datetime import datetime
from functools import wraps

from dotenv import load_dotenv
from openai import OpenAI
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

load_dotenv()

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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS generated_texts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text_type TEXT,
            topic TEXT,
            class_format TEXT,
            audience TEXT,
            tone TEXT,
            length TEXT,
            cta TEXT,
            extra_details TEXT,
            generated_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS planned_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_text_id INTEGER,
            title TEXT,
            post_text TEXT NOT NULL,
            platform TEXT DEFAULT 'VK',
            status TEXT DEFAULT 'draft',
            scheduled_at TEXT,
            char_count INTEGER DEFAULT 0,
            admin_note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    texts_count = conn.execute('SELECT COUNT(*) FROM generated_texts').fetchone()[0]
    posts_count = conn.execute('SELECT COUNT(*) FROM planned_posts').fetchone()[0]
    conn.close()
    return render_template('admin/dashboard.html',
                           leads_count=leads_count, new_leads=new_leads,
                           events_count=events_count, news_count=news_count,
                           texts_count=texts_count, posts_count=posts_count)


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


@app.route('/admin/generator')
@login_required
def admin_generator():
    api_key = os.getenv('OPENAI_API_KEY')
    return render_template('admin/generator.html', has_api_key=bool(api_key))


@app.route('/admin/generator/generate', methods=['POST'])
@login_required
def admin_generator_generate():
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return jsonify({'success': False, 'error': 'OPENAI_API_KEY не задан. Создайте файл .env с ключом.'}), 400

    text_type = request.form.get('text_type', 'пост для соцсетей')
    topic = request.form.get('topic', '')
    class_format = request.form.get('class_format', 'Общая тема студии')
    audience = request.form.get('audience', 'взрослые девушки и женщины')
    tone = request.form.get('tone', 'вдохновляющая')
    length = request.form.get('length', 'средний')
    cta = request.form.get('cta', 'записаться на пробное занятие')
    extra = request.form.get('extra_details', '')

    length_map = {'short': '2-3 предложения', 'medium': '1 небольшой абзац', 'long': '2-3 абзаца'}
    length_ru = length_map.get(length, '1 абзац')

    system_prompt = (
        "Ты — копирайтер студии воздушной гимнастики Aerial Flow. "
        "Пиши на русском языке. Стиль: женственно, воздушно, современно, без лишнего пафоса и клише. "
        "Тон — мягкий, заботливый, с ясной структурой. Без агрессивных продаж. "
        "Призыв к действию — мягкий, но понятный. Используй эмодзи умеренно."
    )

    user_prompt = (
        f"Тип текста: {text_type}\n"
        f"Тема: {topic}\n"
        f"Формат занятия: {class_format}\n"
        f"Целевая аудитория: {audience}\n"
        f"Тональность: {tone}\n"
        f"Длина текста: {length_ru}\n"
        f"Призыв к действию: {cta}\n"
        f"Дополнительные детали: {extra}\n\n"
        f"Напиши текст."
    )

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        generated = response.choices[0].message.content.strip()
    except Exception as e:
        return jsonify({'success': False, 'error': f'Ошибка API: {str(e)}'}), 500

    conn = get_db()
    cursor = conn.execute(
        'INSERT INTO generated_texts (text_type, topic, class_format, audience, tone, length, cta, extra_details, generated_text) '
        'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (text_type, topic, class_format, audience, tone, length, cta, extra, generated)
    )
    text_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'text': generated, 'text_id': text_id})


@app.route('/admin/generated-texts')
@login_required
def admin_generated_texts():
    conn = get_db()
    texts = conn.execute('SELECT * FROM generated_texts ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('admin/generated_texts.html', texts=texts)


@app.route('/admin/generated-texts/<int:text_id>/delete', methods=['POST'])
@login_required
def admin_generated_text_delete(text_id):
    conn = get_db()
    conn.execute('DELETE FROM generated_texts WHERE id = ?', (text_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_generated_texts'))


@app.route('/admin/post-planner')
@login_required
def admin_post_planner():
    conn = get_db()
    posts = conn.execute(
        'SELECT p.*, g.generated_text as source_text, g.topic as source_topic '
        'FROM planned_posts p '
        'LEFT JOIN generated_texts g ON p.source_text_id = g.id '
        'ORDER BY p.updated_at DESC'
    ).fetchall()
    conn.close()
    return render_template('admin/post_planner.html', posts=posts)


@app.route('/admin/post-planner/new', methods=['GET', 'POST'])
@login_required
def admin_post_planner_new():
    if request.method == 'POST':
        post_text = request.form.get('post_text', '')
        conn = get_db()
        conn.execute(
            'INSERT INTO planned_posts (title, post_text, platform, status, scheduled_at, char_count, admin_note) '
            'VALUES (?, ?, ?, ?, ?, ?, ?)',
            (request.form.get('title', ''), post_text,
             request.form.get('platform', 'VK'),
             request.form.get('status', 'draft'),
             request.form.get('scheduled_at') or None,
             len(post_text), request.form.get('admin_note', ''))
        )
        conn.commit()
        conn.close()
        return redirect(url_for('admin_post_planner'))
    return render_template('admin/post_editor.html', post=None)


@app.route('/admin/post-planner/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_post_planner_edit(post_id):
    conn = get_db()
    if request.method == 'POST':
        post_text = request.form.get('post_text', '')
        conn.execute(
            'UPDATE planned_posts SET title=?, post_text=?, platform=?, status=?, scheduled_at=?, '
            'char_count=?, admin_note=?, updated_at=CURRENT_TIMESTAMP WHERE id=?',
            (request.form.get('title', ''), post_text,
             request.form.get('platform', 'VK'),
             request.form.get('status', 'draft'),
             request.form.get('scheduled_at') or None,
             len(post_text), request.form.get('admin_note', ''), post_id)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('admin_post_planner'))
    post = conn.execute('SELECT * FROM planned_posts WHERE id = ?', (post_id,)).fetchone()
    conn.close()
    return render_template('admin/post_editor.html', post=post)


@app.route('/admin/post-planner/<int:post_id>/delete', methods=['POST'])
@login_required
def admin_post_planner_delete(post_id):
    conn = get_db()
    conn.execute('DELETE FROM planned_posts WHERE id = ?', (post_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_post_planner'))


@app.route('/admin/post-planner/add-from-text/<int:text_id>', methods=['POST'])
@login_required
def admin_add_post_from_text(text_id):
    conn = get_db()
    text = conn.execute('SELECT * FROM generated_texts WHERE id = ?', (text_id,)).fetchone()
    if not text:
        conn.close()
        return jsonify({'success': False, 'error': 'Текст не найден'}), 404
    generated = text['generated_text']
    cursor = conn.execute(
        'INSERT INTO planned_posts (source_text_id, title, post_text, platform, status, char_count) '
        'VALUES (?, ?, ?, ?, ?, ?)',
        (text_id, text['topic'] or 'Пост', generated, 'VK', 'draft', len(generated))
    )
    post_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'post_id': post_id})


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
