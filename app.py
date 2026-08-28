from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, abort
)

from config import Config
from database import init_db, get_ticket_by_token, check_in_ticket, undo_check_in, get_stats, get_all_tickets

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = Config.SECRET_KEY

# Ensure database exists on first request (not at import time)
_db_initialized = False

@app.before_request
def ensure_db():
    global _db_initialized
    if not _db_initialized:
        init_db()
        _db_initialized = True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def is_staff():
    """Check if the current session belongs to an authenticated volunteer."""
    return session.get('staff', False)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    """Landing page — redirect staff to dashboard, others to login."""
    if is_staff():
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Staff login — single shared password, sets session cookie."""
    if is_staff():
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == Config.STAFF_PASSWORD:
            session['staff'] = True
            session.permanent = True
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Incorrect password. Try again.', 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Clear session and return to login."""
    session.clear()
    flash('Logged out.', 'info')
    return redirect(url_for('login'))


# ---------------------------------------------------------------------------
# Core ticket route — the URL encoded in every QR code
# ---------------------------------------------------------------------------

@app.route('/t/<token>')
def ticket(token):
    """
    Public / staff ticket view.

    • Not staff → friendly public page (no check-in controls).
    • Staff + not checked in → attendee info + "Grant Entry" button.
    • Staff + already checked in → warning with timestamp.
    """
    t = get_ticket_by_token(token)
    if not t:
        return render_template('invalid_ticket.html'), 404

    if not is_staff():
        return render_template('ticket_public.html', ticket=t)

    if t['checked_in']:
        return render_template('already_checked.html', ticket=t)

    return render_template('ticket_staff.html', ticket=t)


@app.route('/checkin/<token>', methods=['POST'])
def checkin(token):
    """Perform the check-in — staff only, POST only."""
    if not is_staff():
        abort(403)

    t = get_ticket_by_token(token)
    if not t:
        abort(404)

    if not t['checked_in']:
        check_in_ticket(token)

    return redirect(url_for('ticket', token=token))


@app.route('/undo-checkin/<token>', methods=['POST'])
def undo_checkin(token):
    """Undo a check-in — staff only, POST only."""
    if not is_staff():
        abort(403)

    t = get_ticket_by_token(token)
    if not t:
        abort(404)

    if t['checked_in']:
        undo_check_in(token)
        flash('Check-in undone successfully.', 'success')

    return redirect(url_for('ticket', token=token))


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@app.route('/dashboard')
def dashboard():
    """Live stats and ticket list for staff."""
    if not is_staff():
        return redirect(url_for('login'))

    stats = get_stats()
    tickets = get_all_tickets()
    return render_template('dashboard.html', stats=stats, tickets=tickets)


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
