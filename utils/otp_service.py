"""OTP Service for Phone/Email Verification"""
import random
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from utils.sql_db import get_db

load_dotenv()

OTP_EXPIRY_MINUTES = int(os.getenv('OTP_EXPIRY_MINUTES', 10))
OTP_MAX_ATTEMPTS = int(os.getenv('OTP_MAX_ATTEMPTS', 3))

def generate_otp():
    """Generate 6-digit OTP"""
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])

def send_otp(phone_or_email):
    """Generate and store OTP (mock - doesn't actually send SMS)"""
    otp = generate_otp()
    
    db = get_db()
    expires_at = datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)
    
    # Delete old OTPs
    db.execute('DELETE FROM otp_sessions WHERE email = ?', (phone_or_email,))
    
    # Insert new OTP
    db.execute(
        'INSERT INTO otp_sessions (email, otp, attempts, expires_at) VALUES (?, ?, 0, ?)',
        (phone_or_email, otp, expires_at)
    )
    db.commit()
    
    print(f'[OTP] Generated for {phone_or_email}: {otp}')
    return {'otp': otp, 'expires_in': OTP_EXPIRY_MINUTES}

def verify_otp(phone_or_email, otp):
    """Verify OTP"""
    db = get_db()
    
    session = db.execute(
        'SELECT * FROM otp_sessions WHERE email = ? ORDER BY created_at DESC LIMIT 1',
        (phone_or_email,)
    ).fetchone()
    
    if not session:
        return {'valid': False, 'error': 'No OTP found'}
    
    session = dict(session)
    
    # Check expiry
    expires_at = datetime.fromisoformat(session['expires_at'])
    if datetime.now() > expires_at:
        return {'valid': False, 'error': 'OTP expired'}
    
    # Check attempts
    if session['attempts'] >= OTP_MAX_ATTEMPTS:
        return {'valid': False, 'error': 'Too many attempts'}
    
    # Check OTP
    if session['otp'] != otp:
        db.execute(
            'UPDATE otp_sessions SET attempts = attempts + 1 WHERE id = ?',
            (session['id'],)
        )
        db.commit()
        return {'valid': False, 'error': 'Invalid OTP'}
    
    # Valid - delete session
    db.execute('DELETE FROM otp_sessions WHERE id = ?', (session['id'],))
    db.commit()
    
    return {'valid': True}