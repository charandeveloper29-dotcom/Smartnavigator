"""Email OTP Functions"""
import os
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from dotenv import load_dotenv
from utils.sql_db import get_db

load_dotenv()

GMAIL_USER = os.getenv('GMAIL_USER')
GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')
OTP_EXPIRY_MINUTES = int(os.getenv('OTP_EXPIRY_MINUTES', 10))
OTP_MAX_ATTEMPTS = int(os.getenv('OTP_MAX_ATTEMPTS', 3))

def generate_otp():
    """Generate 6-digit OTP"""
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])

def send_otp_email(to_email, otp):
    """Send OTP via Gmail"""
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        raise Exception('Gmail not configured')
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'Your Smart Navigator OTP: {otp}'
        msg['From'] = GMAIL_USER
        msg['To'] = to_email
        
        html = f'''
        <html><body style="font-family:Arial,sans-serif;padding:40px 20px;background:#f5f5f5">
        <div style="max-width:600px;margin:0 auto;background:white;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,.1)">
        <div style="background:linear-gradient(135deg,#1A1614,#C9A84C);padding:30px;text-align:center">
        <h1 style="color:white;margin:0;font-size:28px">🧭 Smart Navigator</h1>
        </div>
        <div style="padding:40px 30px">
        <h2 style="color:#1A1614;margin:0 0 20px">Your Verification Code</h2>
        <p style="color:#666;font-size:15px;line-height:1.6;margin-bottom:30px">
        Enter this code to complete your registration:
        </p>
        <div style="background:#f8f8f8;border:2px dashed #C9A84C;border-radius:8px;padding:20px;text-align:center;margin-bottom:30px">
        <div style="font-size:36px;font-weight:700;color:#C9A84C;letter-spacing:8px">{otp}</div>
        </div>
        <p style="color:#999;font-size:13px;margin:0">
        This code expires in {OTP_EXPIRY_MINUTES} minutes.
        </p>
        </div>
        </div>
        </body></html>
        '''
        
        msg.attach(MIMEText(html, 'html'))
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f'Email send failed: {e}')
        raise

def store_email_otp(email, otp, purpose='register'):
    """Store OTP in database"""
    db = get_db()
    expires_at = datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)
    db.execute('DELETE FROM otp_sessions WHERE email = ?', (email,))
    db.execute(
        'INSERT INTO otp_sessions (email, otp, purpose, attempts, expires_at) VALUES (?, ?, ?, 0, ?)',
        (email, otp, purpose, expires_at)
    )
    db.commit()

def check_email_otp(email, otp, purpose='register'):
    """Verify OTP"""
    db = get_db()
    session = db.execute(
        'SELECT * FROM otp_sessions WHERE email = ? AND purpose = ? ORDER BY created_at DESC LIMIT 1',
        (email, purpose)
    ).fetchone()
    
    if not session:
        return {'valid': False, 'error': 'No OTP found'}
    
    session = dict(session)
    expires_at = datetime.fromisoformat(session['expires_at'])
    if datetime.now() > expires_at:
        return {'valid': False, 'error': 'OTP expired'}
    
    if session['attempts'] >= OTP_MAX_ATTEMPTS:
        return {'valid': False, 'error': 'Too many attempts'}
    
    if session['otp'] != otp:
        db.execute('UPDATE otp_sessions SET attempts = attempts + 1 WHERE id = ?', (session['id'],))
        db.commit()
        return {'valid': False, 'error': 'Invalid OTP'}
    
    db.execute('DELETE FROM otp_sessions WHERE id = ?', (session['id'],))
    db.commit()
    return {'valid': True}

def check_email_otp(email, otp):
    """Verify OTP"""
    db = get_db()
    session = db.execute(
        'SELECT * FROM otp_sessions WHERE email = ? ORDER BY created_at DESC LIMIT 1',
        (email,)
    ).fetchone()
    
    if not session:
        return {'valid': False, 'error': 'No OTP found'}
    
    session = dict(session)
    expires_at = datetime.fromisoformat(session['expires_at'])
    if datetime.now() > expires_at:
        return {'valid': False, 'error': 'OTP expired'}
    
    if session['attempts'] >= OTP_MAX_ATTEMPTS:
        return {'valid': False, 'error': 'Too many attempts'}
    
    if session['otp'] != otp:
        db.execute('UPDATE otp_sessions SET attempts = attempts + 1 WHERE id = ?', (session['id'],))
        db.commit()
        return {'valid': False, 'error': 'Invalid OTP'}
    
    db.execute('DELETE FROM otp_sessions WHERE id = ?', (session['id'],))
    db.commit()
    return {'valid': True}