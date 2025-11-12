import os
from dotenv import load_dotenv
import sqlite3
from pathlib import Path
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session, abort, Response
import requests
import psycopg
from psycopg.rows import dict_row

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')
DB_PATH = BASE_DIR / 'site.db'
DATABASE_URL = os.environ.get('DATABASE_URL')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['WHATSAPP_NUMBER'] = '+77016751231'
app.config['INSTAGRAM_HANDLE'] = 'smart_mabel_kz'
app.config['SITE_DOMAIN'] = 'smartmebel.kz'
app.config['INSTAGRAM_URL'] = 'https://www.instagram.com/smart_mebel_kz?igsh=dmpwam5zajllZ24z'
app.config['ADMIN_PASSWORD'] = os.environ.get('ADMIN_PASSWORD')


def get_db():
    if DATABASE_URL:
        dsn = DATABASE_URL
        try:
            if 'railway.internal' in dsn and 'sslmode=' not in dsn:
                dsn = dsn + ('&sslmode=require' if '?' in dsn else '?sslmode=require')
        except Exception:
            pass
        conn = psycopg.connect(dsn, row_factory=dict_row)
        return conn
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    if DATABASE_URL:
        conn = get_db()
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS leads (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    comment TEXT,
                    utm TEXT,
                    referrer TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'new'
                );
                """
            )
        conn.close()
        return
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            comment TEXT,
            utm TEXT,
            referrer TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'new'
        );
        """
    )
    conn.commit()
    conn.close()


@app.route('/')
def index():
    return render_template(
        'index.html',
        whatsapp_number=app.config['WHATSAPP_NUMBER'],
        instagram_handle=app.config['INSTAGRAM_HANDLE'],
        instagram_url=app.config['INSTAGRAM_URL'],
        site_domain=app.config['SITE_DOMAIN']
    )


_db_inited = False

@app.before_request
def _ensure_db_once():
    global _db_inited
    if not _db_inited:
        try:
            init_db()
        except Exception:
            pass
        _db_inited = True


@app.route('/lead', methods=['POST'])
def lead():
    # Honeypot anti-spam
    if request.form.get('website'):  # hidden field expected to be empty by humans
        return redirect(url_for('index'))

    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    comment = request.form.get('comment', '').strip()
    utm = request.args.get('utm') or request.form.get('utm')
    ref = request.referrer

    if not name or not phone:
        flash('Пожалуйста, заполните имя и телефон.', 'error')
        return redirect(url_for('index'))

    conn = get_db()
    try:
        if DATABASE_URL:
            try:
                print('lead_store db=postgres')
            except Exception:
                pass
            with conn:
                conn.execute(
                    'INSERT INTO leads (name, phone, comment, utm, referrer) VALUES (%s, %s, %s, %s, %s)',
                    (name, phone, comment, utm, ref)
                )
        else:
            try:
                print('lead_store db=sqlite')
            except Exception:
                pass
            conn.execute(
                'INSERT INTO leads (name, phone, comment, utm, referrer) VALUES (?, ?, ?, ?, ?)',
                (name, phone, comment, utm, ref)
            )
            conn.commit()
    except Exception as e:
        try:
            print('lead_store_error', repr(e))
        except Exception:
            pass
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass

    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if token and chat_id:
        try:
            text = (
                f"Новая заявка\n"
                f"Имя: {name}\n"
                f"Телефон: {phone}\n"
                f"Комментарий: {comment or '-'}\n"
                f"UTM: {utm or '-'}\n"
                f"Referrer: {ref or '-'}"
            )
            _tg_resp = requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                data={
                    'chat_id': chat_id,
                    'text': text
                },
                timeout=5
            )
            try:
                print('tg_send_status', _tg_resp.status_code)
                try:
                    with open(BASE_DIR / 'notify.log', 'a', encoding='utf-8') as _lf:
                        _lf.write(f"tg_send_status {_tg_resp.status_code} {_tg_resp.text[:300]}\n")
                except Exception:
                    pass
            except Exception:
                pass
        except Exception:
            try:
                print('tg_send_error')
                try:
                    with open(BASE_DIR / 'notify.log', 'a', encoding='utf-8') as _lf:
                        _lf.write("tg_send_error\n")
                except Exception:
                    pass
            except Exception:
                pass
    else:
        try:
            print('tg_env_missing')
            try:
                with open(BASE_DIR / 'notify.log', 'a', encoding='utf-8') as _lf:
                    _lf.write("tg_env_missing\n")
            except Exception:
                pass
        except Exception:
            pass

    # WhatsApp notification via Cloud API (Meta)
    wa_token = os.environ.get('WHATSAPP_CLOUD_TOKEN')
    wa_phone_id = os.environ.get('WHATSAPP_PHONE_NUMBER_ID')
    wa_to = os.environ.get('WHATSAPP_NOTIFY_TO') or app.config.get('WHATSAPP_NUMBER')
    if wa_token and wa_phone_id and wa_to:
        try:
            wa_text = (
                "Новая заявка\n"
                f"Имя: {name}\n"
                f"Телефон: {phone}\n"
                f"Комментарий: {comment or '-'}\n"
                f"UTM: {utm or '-'}\n"
                f"Referrer: {ref or '-'}"
            )
            requests.post(
                f"https://graph.facebook.com/v19.0/{wa_phone_id}/messages",
                headers={
                    'Authorization': f'Bearer {wa_token}',
                    'Content-Type': 'application/json'
                },
                json={
                    'messaging_product': 'whatsapp',
                    'to': wa_to.replace('+','').strip(),
                    'type': 'text',
                    'text': {'body': wa_text}
                },
                timeout=7
            )
        except Exception:
            pass

    return redirect(url_for('thanks'))


@app.route('/thanks')
def thanks():
    return render_template(
        'thanks.html',
        whatsapp_number=app.config['WHATSAPP_NUMBER'],
        instagram_handle=app.config['INSTAGRAM_HANDLE'],
        instagram_url=app.config['INSTAGRAM_URL'],
        site_domain=app.config['SITE_DOMAIN']
    )


@app.route('/robots.txt')
def robots():
    return send_from_directory(BASE_DIR / 'static', 'robots.txt')


@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory(BASE_DIR / 'static', 'sitemap.xml')


# --- Admin auth helpers ---
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('admin'):  # simple flag
            return redirect(url_for('admin_login', next=request.path))
        return f(*args, **kwargs)
    return wrapper


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        pwd = request.form.get('password')
        if not app.config.get('ADMIN_PASSWORD'):
            flash('ADMIN_PASSWORD не задан в переменных окружения.', 'error')
        elif pwd == app.config['ADMIN_PASSWORD']:
            session['admin'] = True
            nxt = request.args.get('next') or url_for('admin_leads')
            return redirect(nxt)
        else:
            flash('Неверный пароль.', 'error')
    return render_template(
        'admin_login.html',
        whatsapp_number=app.config['WHATSAPP_NUMBER'],
        instagram_handle=app.config['INSTAGRAM_HANDLE'],
        instagram_url=app.config['INSTAGRAM_URL'],
        site_domain=app.config['SITE_DOMAIN']
    )


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))


@app.route('/admin')
def admin_root():
    return redirect(url_for('admin_leads'))


@app.route('/admin/leads')
@login_required
def admin_leads():
    page = max(int(request.args.get('page', 1) or 1), 1)
    per_page = min(max(int(request.args.get('per_page', 20) or 20), 5), 100)
    offset = (page - 1) * per_page

    conn = get_db()
    if DATABASE_URL:
        with conn:
            rows = conn.execute(
                'SELECT id, name, phone, comment, utm, referrer, created_at, status FROM leads ORDER BY created_at DESC LIMIT %s OFFSET %s',
                (per_page, offset)
            ).fetchall()
            total = conn.execute('SELECT COUNT(*) AS c FROM leads').fetchone()['c']
        conn.close()
    else:
        cur = conn.cursor()
        cur.execute('SELECT id, name, phone, comment, utm, referrer, created_at, status FROM leads ORDER BY created_at DESC LIMIT ? OFFSET ?', (per_page, offset))
        rows = cur.fetchall()
        cur.execute('SELECT COUNT(*) AS c FROM leads')
        total = cur.fetchone()['c']
        conn.close()

    pages = (total + per_page - 1) // per_page
    return render_template(
        'admin_leads.html',
        leads=rows,
        page=page,
        pages=pages,
        per_page=per_page,
        total=total,
        whatsapp_number=app.config['WHATSAPP_NUMBER'],
        instagram_handle=app.config['INSTAGRAM_HANDLE'],
        instagram_url=app.config['INSTAGRAM_URL'],
        site_domain=app.config['SITE_DOMAIN']
    )


@app.route('/admin/leads/<int:lead_id>/status', methods=['POST'])
@login_required
def admin_lead_status(lead_id: int):
    status = request.form.get('status', 'new')
    if status not in {'new', 'in_progress', 'done', 'spam'}:
        abort(400)
    conn = get_db()
    if DATABASE_URL:
        with conn:
            conn.execute('UPDATE leads SET status=%s WHERE id=%s', (status, lead_id))
        conn.close()
    else:
        conn.execute('UPDATE leads SET status=? WHERE id=?', (status, lead_id))
        conn.commit()
        conn.close()
    return redirect(url_for('admin_leads'))


@app.route('/admin/export.csv')
@login_required
def admin_export_csv():
    conn = get_db()
    if DATABASE_URL:
        with conn:
            rows = conn.execute('SELECT id, name, phone, comment, utm, referrer, created_at, status FROM leads ORDER BY created_at DESC').fetchall()
        conn.close()
    else:
        cur = conn.cursor()
        cur.execute('SELECT id, name, phone, comment, utm, referrer, created_at, status FROM leads ORDER BY created_at DESC')
        rows = cur.fetchall()
        conn.close()

    def generate():
        yield 'id,name,phone,comment,utm,referrer,created_at,status\n'
        for r in rows:
            # r can be Row (supports dict-style) for both drivers
            row = dict(r)
            def esc(x):
                if x is None:
                    return ''
                s = str(x).replace('"', '""')
                if ',' in s or '"' in s or '\n' in s:
                    return f'"{s}"'
                return s
            yield f"{row['id']},{esc(row.get('name'))},{esc(row.get('phone'))},{esc(row.get('comment'))},{esc(row.get('utm'))},{esc(row.get('referrer'))},{esc(row.get('created_at'))},{esc(row.get('status'))}\n"

    return Response(generate(), mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=leads.csv'})


@app.route('/admin/export')
@login_required
def admin_export_html():
    conn = get_db()
    if DATABASE_URL:
        with conn:
            rows = conn.execute('SELECT id, name, phone, comment, utm, referrer, created_at, status FROM leads ORDER BY created_at DESC').fetchall()
        conn.close()
    else:
        cur = conn.cursor()
        cur.execute('SELECT id, name, phone, comment, utm, referrer, created_at, status FROM leads ORDER BY created_at DESC')
        rows = cur.fetchall()
        conn.close()

    return render_template(
        'admin_export.html',
        leads=rows,
        whatsapp_number=app.config['WHATSAPP_NUMBER'],
        instagram_handle=app.config['INSTAGRAM_HANDLE'],
        instagram_url=app.config['INSTAGRAM_URL'],
        site_domain=app.config['SITE_DOMAIN']
    )


if __name__ == '__main__':
    try:
        print(f"DB: {'PostgreSQL' if DATABASE_URL else 'SQLite'} | DATABASE_URL: {'set' if DATABASE_URL else 'empty'} | env_file: {BASE_DIR / '.env'}")
    except Exception:
        pass
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
