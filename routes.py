from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User, Booking, AdminLog
from app.forms import LoginForm, SignupForm, UserForm, BookingForm
from datetime import datetime, timedelta
import logging

main = Blueprint('main', __name__)
auth = Blueprint('auth', __name__)
booking = Blueprint('booking', __name__)
admin = Blueprint('admin', __name__)

@main.route('/')
def index():
    today = datetime.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    bookings = Booking.query.filter(Booking.day >= start_of_week, Booking.day <= end_of_week).all()
    
    user_bookings = []
    if current_user.is_authenticated:
        user_bookings = Booking.query.filter(
            (Booking.email1 == current_user.email) | (Booking.email2 == current_user.email),
            Booking.day >= today
        ).order_by(Booking.day).all()

    return render_template('index.html', bookings=bookings, user_bookings=user_bookings)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))
        flash('Invalid email or password', 'danger')
    return render_template('login.html', form=form)

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = SignupForm()
    if form.validate_on_submit():
        user = User(email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!', 'success')
        return redirect(url_for('auth.login'))
    return render_template('signup.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@booking.route('/book', methods=['GET', 'PUT'])
@login_required
def book():
    logging.info(f"Booking attempt by user: {current_user.email}")
    
    if not Booking.can_book(current_user.email):
        flash('Vous avez déjà une réservation pour cette semaine.', 'warning')
        return redirect(url_for('main.index'))

    form = BookingForm()
    
    today = datetime.now().date()
    current_week_start = today - timedelta(days=today.weekday())
    next_week_start = current_week_start + timedelta(days=7)
    next_week_end = next_week_start + timedelta(days=6)

    if current_user.is_team:
        available_days = [(next_week_start + timedelta(days=i)) for i in range(3)]
    else:
        available_days = [(next_week_start + timedelta(days=i)) for i in range(3, 5)]

    potential_opponents = User.query.filter(
        User.is_team == current_user.is_team,
        User.email != current_user.email
    ).all()
    form.opponent.choices = [(u.email, u.email) for u in potential_opponents]

    logging.info(f"Available opponents: {[u.email for u in potential_opponents]}")

    if form.validate_on_submit():
        logging.info(f"Form submitted. Data: {form.data}")
        try:
            booking = Booking(
                email1=current_user.email,
                email2=form.opponent.data,
                timeslot=form.timeslot.data,
                day=form.day.data,
                is_team_booking=current_user.is_team
            )
            db.session.add(booking)
            db.session.commit()
            logging.info(f"Booking created successfully: {booking}")
            flash('Réservation effectuée avec succès!', 'success')
            return redirect(url_for('main.index'))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating booking: {str(e)}")
            flash(f'Erreur lors de la réservation: {str(e)}', 'danger')

    return render_template(
        'book.html',
        form=form,
        available_days=available_days,
        next_week_start=next_week_start,
        next_week_end=next_week_end
    )

@booking.route('/get_available_slots')
@login_required
def get_available_slots():
    day = request.args.get('day')
    date = datetime.strptime(day, '%Y-%m-%d').date()
    
    today = datetime.now().date()
    current_week_start = today - timedelta(days=today.weekday())
    next_week_start = current_week_start + timedelta(days=7)
    next_week_end = next_week_start + timedelta(days=6)
    
    if not (next_week_start <= date <= next_week_end):
        return jsonify([])
        
    available_slots = Booking.get_available_slots(date, current_user.is_team)
    return jsonify(available_slots)

@admin.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        flash('Accès refusé.', 'danger')
        return redirect(url_for('main.index'))
    users = User.query.all()
    bookings = Booking.query.all()
    return render_template('admin/dashboard.html', users=users, bookings=bookings)

@admin.route('/admin/create_user', methods=['GET', 'POST'])
@login_required
def create_user():
    if not current_user.is_admin:
        flash('Accès refusé.', 'danger')
        return redirect(url_for('main.index'))
    
    form = UserForm()
    if form.validate_on_submit():
        user = User(email=form.email.data, is_team=form.is_team.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        log_entry = AdminLog(admin_email=current_user.email, action=f"Created user: {user.email}")
        db.session.add(log_entry)
        db.session.commit()
        flash(f'Utilisateur {user.email} créé avec succès.', 'success')
        return redirect(url_for('admin.admin_panel'))
    return render_template('admin/create_user.html', form=form)

@admin.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        flash('Accès refusé.', 'danger')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    log_entry = AdminLog(admin_email=current_user.email, action=f"Deleted user: {user.email}")
    db.session.add(log_entry)
    db.session.commit()
    flash(f'Utilisateur {user.email} supprimé avec succès.', 'success')
    return redirect(url_for('admin.admin_panel'))

@admin.route('/admin/toggle_team/<int:user_id>', methods=['POST'])
@login_required
def toggle_team(user_id):
    if not current_user.is_admin:
        flash('Accès refusé.', 'danger')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(user_id)
    user.is_team = not user.is_team
    log_entry = AdminLog(admin_email=current_user.email, 
                         action=f"{'Added' if user.is_team else 'Removed'} {user.email} {'to' if user.is_team else 'from'} team")
    db.session.add(log_entry)
    db.session.commit()
    flash(f"Utilisateur {user.email} {'ajouté à' if user.is_team else 'retiré de'} l'équipe.", 'success')
    return redirect(url_for('admin.admin_panel'))

@admin.route('/admin/create_booking', methods=['GET', 'POST'])
@login_required
def create_booking():
    if not current_user.is_admin:
        flash('Accès refusé.', 'danger')
        return redirect(url_for('main.index'))
    
    form = BookingForm()
    form.email1.choices = [(u.email, u.email) for u in User.query.all()]
    form.email2.choices = [(u.email, u.email) for u in User.query.all()]
    if form.validate_on_submit():
        booking = Booking(
            email1=form.email1.data,
            email2=form.email2.data,
            day=form.day.data,
            timeslot=form.timeslot.data,
            is_team_booking=User.query.filter_by(email=form.email1.data).first().is_team
        )
        db.session.add(booking)
        log_entry = AdminLog(admin_email=current_user.email, action=f"Created booking: {booking.email1} vs {booking.email2} on {booking.day}")
        db.session.add(log_entry)
        db.session.commit()
        flash('Réservation créée avec succès.', 'success')
        return redirect(url_for('admin.admin_panel'))
    return render_template('admin/create_booking.html', form=form)

@admin.route('/admin/delete_booking/<int:booking_id>', methods=['POST'])
@login_required
def delete_booking(booking_id):
    if not current_user.is_admin:
        flash('Accès refusé.', 'danger')
        return redirect(url_for('main.index'))
    
    booking = Booking.query.get_or_404(booking_id)
    db.session.delete(booking)
    log_entry = AdminLog(admin_email=current_user.email, action=f"Deleted booking: {booking.email1} vs {booking.email2} on {booking.day}")
    db.session.add(log_entry)
    db.session.commit()
    flash('Réservation supprimée avec succès.', 'success')
    return redirect(url_for('admin.admin_panel'))

@admin.route('/admin/logs')
@login_required
def view_logs():
    if not current_user.is_admin:
        flash('Accès refusé.', 'danger')
        return redirect(url_for('main.index'))
    
    logs = AdminLog.query.order_by(AdminLog.timestamp.desc()).all()
    return render_template('admin/logs.html', logs=logs)
