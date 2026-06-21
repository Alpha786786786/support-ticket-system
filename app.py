import os
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, request, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-this-secret-key-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'tickets.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

os.makedirs(os.path.join(basedir, 'instance'), exist_ok=True)

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'student_login'
login_manager.login_message = 'Please log in first.'
login_manager.login_message_category = 'error'

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class User(UserMixin, db.Model):
    """Students who raise support tickets."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tickets = db.relationship('Ticket', backref='student', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return f"user-{self.id}"


class Admin(UserMixin, db.Model):
    """Support staff who answer tickets."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return f"admin-{self.id}"


class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Open')  # Open, Answered, Closed
    priority = db.Column(db.String(20), default='Normal')  # Normal, Urgent
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    replies = db.relationship('Reply', backref='ticket', lazy=True,
                               cascade='all, delete-orphan', order_by='Reply.created_at')


class Reply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)

    # Who wrote this reply (student or admin) — only one of these is set
    author_student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    author_admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=True)

    author_student = db.relationship('User', foreign_keys=[author_student_id])
    author_admin = db.relationship('Admin', foreign_keys=[author_admin_id])

    @property
    def author_name(self):
        if self.author_admin:
            return self.author_admin.name
        if self.author_student:
            return self.author_student.name
        return 'Unknown'

    @property
    def is_admin_reply(self):
        return self.author_admin_id is not None


@login_manager.user_loader
def load_user(user_id):
    kind, raw_id = user_id.split('-', 1)
    if kind == 'user':
        return User.query.get(int(raw_id))
    elif kind == 'admin':
        return Admin.query.get(int(raw_id))
    return None


def current_is_admin():
    return isinstance(current_user._get_current_object(), Admin) if current_user.is_authenticated else False


app.jinja_env.globals.update(current_is_admin=current_is_admin)


# ---------------------------------------------------------------------------
# Public / landing
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_is_admin():
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('student_dashboard'))
    return render_template('index.html')


# ---------------------------------------------------------------------------
# Student auth
# ---------------------------------------------------------------------------

@app.route('/student/signup', methods=['GET', 'POST'])
def student_signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not name or not email or not password:
            flash('Please fill in all fields.', 'error')
            return render_template('student_signup.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('student_signup.html')

        if User.query.filter_by(email=email).first():
            flash('An account with this email already exists. Please log in.', 'error')
            return render_template('student_signup.html')

        user = User(name=name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash('Welcome! Your account has been created.', 'success')
        return redirect(url_for('student_dashboard'))

    return render_template('student_signup.html')


@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('student_dashboard'))

        flash('Incorrect email or password.', 'error')

    return render_template('student_login.html')


# ---------------------------------------------------------------------------
# Admin auth
# ---------------------------------------------------------------------------

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        admin = Admin.query.filter_by(email=email).first()
        if admin and admin.check_password(password):
            login_user(admin)
            return redirect(url_for('admin_dashboard'))

        flash('Incorrect email or password.', 'error')

    return render_template('admin_login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# ---------------------------------------------------------------------------
# Student area
# ---------------------------------------------------------------------------

@app.route('/dashboard')
@login_required
def student_dashboard():
    if current_is_admin():
        return redirect(url_for('admin_dashboard'))

    status_filter = request.args.get('status', 'all')
    query = Ticket.query.filter_by(student_id=current_user.id)
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    tickets = query.order_by(Ticket.updated_at.desc()).all()

    counts = {
        'all': Ticket.query.filter_by(student_id=current_user.id).count(),
        'Open': Ticket.query.filter_by(student_id=current_user.id, status='Open').count(),
        'Answered': Ticket.query.filter_by(student_id=current_user.id, status='Answered').count(),
        'Closed': Ticket.query.filter_by(student_id=current_user.id, status='Closed').count(),
    }

    return render_template('student_dashboard.html', tickets=tickets, status_filter=status_filter, counts=counts)


@app.route('/ticket/new', methods=['GET', 'POST'])
@login_required
def new_ticket():
    if current_is_admin():
        abort(403)

    if request.method == 'POST':
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        priority = request.form.get('priority', 'Normal')

        if not subject or not message:
            flash('Please write a subject and your question.', 'error')
            return render_template('new_ticket.html')

        ticket = Ticket(
            subject=subject,
            message=message,
            priority=priority if priority in ('Normal', 'Urgent') else 'Normal',
            student_id=current_user.id,
            status='Open'
        )
        db.session.add(ticket)
        db.session.commit()
        flash('Your question has been submitted. You will get a reply soon.', 'success')
        return redirect(url_for('view_ticket', ticket_id=ticket.id))

    return render_template('new_ticket.html')


@app.route('/ticket/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def view_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)

    is_admin = current_is_admin()
    if not is_admin and ticket.student_id != current_user.id:
        abort(403)

    if request.method == 'POST':
        message = request.form.get('message', '').strip()
        if message:
            reply = Reply(message=message, ticket_id=ticket.id)
            if is_admin:
                reply.author_admin_id = current_user.id
                ticket.status = 'Answered'
            else:
                reply.author_student_id = current_user.id
                if ticket.status == 'Answered':
                    ticket.status = 'Open'
            ticket.updated_at = datetime.utcnow()
            db.session.add(reply)
            db.session.commit()
            flash('Reply sent.', 'success')
        return redirect(url_for('view_ticket', ticket_id=ticket.id))

    return render_template('view_ticket.html', ticket=ticket, is_admin=is_admin)


@app.route('/ticket/<int:ticket_id>/close', methods=['POST'])
@login_required
def close_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    is_admin = current_is_admin()
    if not is_admin and ticket.student_id != current_user.id:
        abort(403)
    ticket.status = 'Closed'
    ticket.updated_at = datetime.utcnow()
    db.session.commit()
    flash('Ticket closed.', 'success')
    return redirect(url_for('view_ticket', ticket_id=ticket.id))


@app.route('/ticket/<int:ticket_id>/reopen', methods=['POST'])
@login_required
def reopen_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    is_admin = current_is_admin()
    if not is_admin and ticket.student_id != current_user.id:
        abort(403)
    ticket.status = 'Open'
    ticket.updated_at = datetime.utcnow()
    db.session.commit()
    flash('Ticket reopened.', 'success')
    return redirect(url_for('view_ticket', ticket_id=ticket.id))


# ---------------------------------------------------------------------------
# Admin area
# ---------------------------------------------------------------------------

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_is_admin():
        abort(403)

    status_filter = request.args.get('status', 'all')
    query = Ticket.query
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    tickets = query.order_by(Ticket.updated_at.desc()).all()

    counts = {
        'all': Ticket.query.count(),
        'Open': Ticket.query.filter_by(status='Open').count(),
        'Answered': Ticket.query.filter_by(status='Answered').count(),
        'Closed': Ticket.query.filter_by(status='Closed').count(),
    }

    return render_template('admin_dashboard.html', tickets=tickets, status_filter=status_filter, counts=counts)


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@app.errorhandler(403)
def forbidden(e):
    return render_template('error.html', code=403, message='You do not have access to this page.'), 403


@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', code=404, message='This page does not exist.'), 404


# ---------------------------------------------------------------------------
# CLI helper to create the first admin account
# ---------------------------------------------------------------------------

@app.cli.command('create-admin')
def create_admin():
    """Usage: flask --app app.py create-admin"""
    import getpass
    name = input('Admin name: ').strip()
    email = input('Admin email: ').strip().lower()
    password = getpass.getpass('Password: ')

    if Admin.query.filter_by(email=email).first():
        print('An admin with this email already exists.')
        return

    admin = Admin(name=name, email=email)
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    print(f'Admin "{name}" has been created.')


with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
