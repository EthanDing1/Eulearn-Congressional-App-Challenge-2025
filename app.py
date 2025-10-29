from flask import Flask, request, jsonify, session, render_template, url_for, redirect
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, timezone
from functools import wraps
from authlib.integrations.flask_client import OAuth
import os
import re
import secrets
import json
import sympy as sp
from sympy import symbols, simplify
from flask import Blueprint, request, jsonify
from backend.integral_solver import solve_integral
from backend.parametric_solver import solve_parametric
from backend.polar_solver import solve_polar
from flask_mail import Mail, Message

import sqlite3
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

solver_bp = Blueprint("solver", __name__)

app = Flask(__name__)
oauth = OAuth(app)

app.secret_key = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production-' + secrets.token_hex(16)

CORS(app, origins=[
    'http://localhost:3000',
    'http://localhost:8000',
    'http://127.0.0.1:5500',
    'http://localhost:5500',
    'http://127.0.0.1:5000',
    'http://localhost:5000'
], supports_credentials=True)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///eulearn.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME') or 'ethanding123@gmail.com'
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD') or 'tahg xrds rhgq whtp'
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_USERNAME') or 'ethanding123@gmail.com'
app.permanent_session_lifetime = timedelta(days=7)
mail = Mail(app)
db = SQLAlchemy(app)

google = oauth.register(
    name='google',
    client_id='699278809855-3b5qg71ood78n3oog97ueuvkmuu8f24s.apps.googleusercontent.com',
    client_secret='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',
    access_token_url='https://oauth2.googleapis.com/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    api_base_url='https://www.googleapis.com/oauth2/v2/',
    jwks_uri='https://www.googleapis.com/oauth2/v3/certs',
    client_kwargs={'scope': 'openid email profile'}
)

github = oauth.register(
    name="github",
    client_id="Ov23lifY2uZWu7Pec5pY",
    client_secret="f8549ee6cbe47a64f11e84e26deceba32d192795",
    access_token_url="https://github.com/login/oauth/access_token",
    authorize_url="https://github.com/login/oauth/authorize",
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "read:user user:email"},
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.email}>'

    def to_dict(self):
        return {
            'firstName': self.first_name,
            'lastName': self.last_name,
            'email': self.email,
            'id': self.id
        }

class SolvedProblem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    input = db.Column(db.String(500), nullable=False)
    solution = db.Column(db.Text, nullable=False)
    steps = db.Column(db.Text)
    solver_type = db.Column(db.String(20), default='integral')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('problems', lazy=True))

    def __repr__(self):
        return f'<SolvedProblem {self.input}>'
class UserProgress(db.Model):
    __tablename__ = 'user_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    problem_id = db.Column(db.Integer, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    attempts = db.Column(db.Integer, default=0)
    completed_at = db.Column(db.DateTime)
    
    user = db.relationship('User', backref=db.backref('progress', lazy=True))

class PasswordResetToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    
    user = db.relationship('User', backref=db.backref('reset_tokens', lazy=True))
    
    def is_valid(self):
        return not self.used and datetime.utcnow() < self.expires_at
class ParametricUserProgress(db.Model):
    __tablename__ = 'parametric_user_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    problem_id = db.Column(db.Integer, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    attempts = db.Column(db.Integer, default=0)
    completed_at = db.Column(db.DateTime)
    
    user = db.relationship('User', backref=db.backref('parametric_progress', lazy=True))

class PolarUserProgress(db.Model):
    __tablename__ = 'polar_user_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    problem_id = db.Column(db.Integer, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    attempts = db.Column(db.Integer, default=0)
    completed_at = db.Column(db.DateTime)
    
    user = db.relationship('User', backref=db.backref('polar_progress', lazy=True))

def create_tables():
    with app.app_context():
        db.create_all()
        print("Database tables created!")

create_tables()

import sympy as sp

def format_latex_expression(expr):
    """
    Convert a SymPy expression or math-like string to LaTeX for KaTeX,
    but leave normal text alone.
    """
    try:
        if isinstance(expr, sp.Basic):
            latex_str = sp.latex(expr)
            return f"$${latex_str}$$"

        if isinstance(expr, str):
            expr = expr.replace('theta', '\\theta')
            
            if '+ C' in expr:
                expr_without_c = expr.replace('+ C', '').strip()
                try:
                    temp_expr = expr_without_c.replace('\\theta', 'theta')
                    sym_expr = sp.sympify(temp_expr)
                    latex_str = sp.latex(sym_expr)
                    latex_str = latex_str.replace('theta', '\\theta')
                    return f"$${latex_str} + C$$"
                except Exception:
                    return f"$${expr_without_c}$$"
            else:
                try:
                    temp_expr = expr.replace('\\theta', 'theta')
                    sym_expr = sp.sympify(temp_expr)
                    latex_str = sp.latex(sym_expr)
                    latex_str = latex_str.replace('theta', '\\theta')
                    return f"$${latex_str}$$"
                except Exception:
                    return f"$${expr}$$"

        return str(expr)

    except Exception as e:
        print(f"LaTeX formatting error: {e}")
        return str(expr)


def format_input_for_display(input_str, solver_type):
    """Format input string for LaTeX display based on solver type"""
    try:
        if solver_type == 'parametric':
            if ',' in input_str:
                parts = input_str.split(',')
                if len(parts) == 2:
                    x_part = parts[0].split('=')[1].strip() if '=' in parts[0] else parts[0].strip()
                    y_part = parts[1].split('=')[1].strip() if '=' in parts[1] else parts[1].strip()
                    
                    try:
                        x_expr = sp.sympify(x_part.replace('theta', 'theta_sym'))
                        y_expr = sp.sympify(y_part.replace('theta', 'theta_sym'))
                        x_latex = sp.latex(x_expr).replace('theta\\_sym', '\\theta')
                        y_latex = sp.latex(y_expr).replace('theta\\_sym', '\\theta')
                        return f"$$x(t) = {x_latex}, \\quad y(t) = {y_latex}$$"
                    except:
                        x_display = x_part.replace('theta', '\\theta')
                        y_display = y_part.replace('theta', '\\theta')
                        return f"$$x(t) = {x_display}, \\quad y(t) = {y_display}$$"
            return input_str
        
        elif solver_type == 'polar':
            input_with_symbol = input_str.replace('theta', '\\theta')
            
            if 'Inner:' in input_str and 'Outer:' in input_str:
                parts = input_str.split(',')
                if len(parts) == 2:
                    inner_part = parts[0].replace('Inner:', '').strip()
                    outer_part = parts[1].replace('Outer:', '').strip()
                    
                    try:
                        inner_expr = sp.sympify(inner_part.replace('theta', 'theta_sym'))
                        outer_expr = sp.sympify(outer_part.replace('theta', 'theta_sym'))
                        inner_latex = sp.latex(inner_expr).replace('theta\\_sym', '\\theta').replace('\\_sym', '')
                        outer_latex = sp.latex(outer_expr).replace('theta\\_sym', '\\theta').replace('\\_sym', '')
                        return f"$$\\text{{Inner: }} r_1(\\theta) = {inner_latex}, \\quad \\text{{Outer: }} r_2(\\theta) = {outer_latex}$$"
                    except:
                        inner_display = inner_part.replace('theta', '\\theta')
                        outer_display = outer_part.replace('theta', '\\theta')
                        return f"$$\\text{{Inner: }} {inner_display}, \\quad \\text{{Outer: }} {outer_display}$$"
            
            elif 'r(θ)' in input_str or 'r(theta)' in input_str:
                if '=' in input_str:
                    expr_part = input_str.split('=')[1].strip()
                    try:
                        expr = sp.sympify(expr_part.replace('theta', 'theta_sym').replace('θ', 'theta_sym'))
                        expr_latex = sp.latex(expr).replace('theta\\_sym', '\\theta').replace('\\_sym', '')
                        return f"$$r(\\theta) = {expr_latex}$$"
                    except:
                        expr_display = expr_part.replace('theta', '\\theta').replace('θ', '\\theta')
                        return f"$$r(\\theta) = {expr_display}$$"
            
            return f"$${input_with_symbol}$$"
        
        else:
            input_clean = input_str.replace('theta', '\\theta').replace('θ', '\\theta')
            try:
                expr = sp.sympify(input_clean.replace('\\theta', 'theta'))
                expr_latex = sp.latex(expr).replace('theta', '\\theta')
                return f"$$\\int {expr_latex} \\, dx$$"
            except:
                return f"$$\\int {input_clean} \\, dx$$"
                
    except Exception as e:
        print(f"Format input error: {e}")
        theta_replaced = input_str.replace('theta', '\\theta').replace('θ', '\\theta')
        return f"$${theta_replaced}$$"

def process_steps_for_katex(steps):
    """
    Process steps array to ensure proper KaTeX formatting.
    The steps from our solvers already contain LaTeX markup, so we format them
    for KaTeX rendering by wrapping them in appropriate delimiters.
    """
    if not steps or not isinstance(steps, list):
        return []
    
    processed_steps = []
    for step in steps:
        step_str = str(step).strip()
        
        if step_str.startswith('\\'):
            processed_steps.append(f"$${step_str}$$")
        elif '$$' in step_str:
            processed_steps.append(step_str)
        else:
            processed_steps.append(step_str)
    
    return processed_steps

def validate_email(email):
    return re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email) is not None

def validate_name(name):
    return 1 <= len(name.strip()) <= 100

def validate_password(password):
    return len(password) >= 8
def normalize_math_expression(expr):
    """Normalize a mathematical expression for comparison"""
    import re
    
    expr = expr.replace(' ', '')
    
    expr = expr.replace('**', '^')
    
    expr = re.sub(r'\+[Cc]$', '', expr)
    
    expr = re.sub(r'(\d)\*([a-z])', r'\1\2', expr)
    
    expr = expr.replace('/', '/')
    
    return expr.lower()

def compare_math_expressions(user_expr, correct_expr, variable='x'):
    """
    Compare two mathematical expressions using SymPy for semantic equivalence.
    """
    try:
        var = symbols(variable)
        
        transformations = standard_transformations + (implicit_multiplication_application,)
        
        user_clean = user_expr.strip().replace(' ', '').replace('+C', '').replace('+c', '')
        correct_clean = correct_expr.strip().replace(' ', '').replace('+C', '').replace('+c', '')
        
        user_clean = user_clean.replace('^', '**')
        correct_clean = correct_clean.replace('^', '**')
        
        user_parsed = parse_expr(user_clean, transformations=transformations)
        correct_parsed = parse_expr(correct_clean, transformations=transformations)
        
        user_simplified = simplify(user_parsed)
        correct_simplified = simplify(correct_parsed)
        
        difference = simplify(user_simplified - correct_simplified)
        
        return difference == 0 or abs(float(difference.evalf(subs={var: 1}))) < 1e-10
        
    except Exception as e:
        print(f"Expression comparison error: {e}")
        return normalize_math_expression(user_expr) == normalize_math_expression(correct_expr)

def format_bound_for_display(bound):
    """Helper function to format a single bound in terms of π"""
    import math
    
    if bound == 0:
        return "0"
    
    pi_multiple = bound / math.pi
    tolerance = 1e-10
    
    if abs(pi_multiple - round(pi_multiple)) < tolerance:
        multiple = int(round(pi_multiple))
        if multiple == 1:
            return "π"
        elif multiple == -1:
            return "-π"
        else:
            return f"{multiple}π"
    
    half_multiple = pi_multiple * 2
    if abs(half_multiple - round(half_multiple)) < tolerance:
        numerator = int(round(half_multiple))
        if numerator == 1:
            return "π/2"
        elif numerator == -1:
            return "-π/2"
        else:
            return f"{numerator}π/2"
    
    third_multiple = pi_multiple * 3
    if abs(third_multiple - round(third_multiple)) < tolerance:
        numerator = int(round(third_multiple))
        if numerator == 1:
            return "π/3"
        elif numerator == -1:
            return "-π/3"
        else:
            return f"{numerator}π/3"
    
    fourth_multiple = pi_multiple * 4
    if abs(fourth_multiple - round(fourth_multiple)) < tolerance:
        numerator = int(round(fourth_multiple))
        if numerator == 1:
            return "π/4"
        elif numerator == -1:
            return "-π/4"
        else:
            return f"{numerator}π/4"
    
    return f"{bound:.4f}"

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        current_user = User.query.get(user_id)
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        return f(current_user, *args, **kwargs)
    return decorated

def clean_polar_expression(expr_str):
    """Clean polar expression from various input formats"""
    expr_str = str(expr_str).strip()
    
    prefixes_to_remove = [
        "Inner:", "Outer:", "r1:", "r2:", "r1 =", "r2 =",
        "r(theta) =", "r(θ) =", "r1(theta)", "r2(theta)",
        "r1(θ)", "r2(θ)", "Inner", "Outer", "Function:",
        "r =", "r(theta)", "r(θ)"
    ]
    
    for prefix in prefixes_to_remove:
        if expr_str.startswith(prefix):
            expr_str = expr_str[len(prefix):].strip()
        expr_str = expr_str.replace(prefix, "").strip()
    
    expr_str = expr_str.lstrip(":=").strip()
    
    expr_str = expr_str.replace('θ', 'theta')
    
    return expr_str

def clean_single_polar_expression(expr_str):
    """Clean single polar expression"""
    expr_str = str(expr_str).strip()
    
    prefixes_to_remove = [
        "r(theta) =", "r(θ) =", "r =", "Function:",
        "r(theta)", "r(θ)", "Polar:", ":"
    ]
    
    for prefix in prefixes_to_remove:
        if expr_str.startswith(prefix):
            expr_str = expr_str[len(prefix):].strip()
        expr_str = expr_str.replace(prefix, "").strip()
    
    expr_str = expr_str.lstrip(":=").strip()
    
    expr_str = expr_str.replace('θ', 'theta')
    
    return expr_str

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request'}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/test')
def test():
    return jsonify({'message': 'Flask backend with sessions is working!'})

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    try:
        data = request.json or {}
        first_name = data.get('firstName', '').strip()
        last_name = data.get('lastName', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not validate_name(first_name):
            return jsonify({'error': 'First name must be 1-100 characters'}), 400
        if not validate_name(last_name):
            return jsonify({'error': 'Last name must be 1-100 characters'}), 400
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        if not validate_password(password):
            return jsonify({'error': 'Password must be at least 8 characters'}), 400
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already registered'}), 400

        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()

        session.permanent = True
        session['user_id'] = new_user.id
        return jsonify({'message': 'Account created successfully!', 'user': new_user.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create account', 'details': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login_user():
    try:
        data = request.json or {}
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({'error': 'Invalid email or password'}), 401

        session.permanent = True
        session['user_id'] = user.id
        return jsonify({'message': 'Login successful!', 'user': user.to_dict()})
    except Exception as e:
        return jsonify({'error': 'Login failed', 'details': str(e)}), 500

@app.route('/api/auth/me')
def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401
    user = User.query.get(user_id)
    return jsonify({'user': user.to_dict()}) if user else (jsonify({'error': 'User not found'}), 404)

@app.route('/api/auth/update-profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    try:
        data = request.json or {}
        first_name = data.get('firstName', '').strip()
        last_name = data.get('lastName', '').strip()
        email = data.get('email', '').strip().lower()

        if not validate_name(first_name) or not validate_name(last_name):
            return jsonify({'error': 'Invalid name'}), 400
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        if email != current_user.email and User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already in use'}), 400

        current_user.first_name = first_name
        current_user.last_name = last_name
        current_user.email = email
        db.session.commit()

        return jsonify({'message': 'Profile updated successfully!', 'user': current_user.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update profile', 'details': str(e)}), 500

@app.route('/api/auth/change-password', methods=['PUT'])
@token_required
def change_password(current_user):
    try:
        data = request.json or {}
        current_password = data.get('currentPassword', '')
        new_password = data.get('newPassword', '')

        if not check_password_hash(current_user.password_hash, current_password):
            return jsonify({'error': 'Current password is incorrect'}), 400
        if not validate_password(new_password):
            return jsonify({'error': 'New password must be at least 8 characters'}), 400
        if check_password_hash(current_user.password_hash, new_password):
            return jsonify({'error': 'New password must be different'}), 400

        current_user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        return jsonify({'message': 'Password changed successfully!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to change password', 'details': str(e)}), 500


@app.route('/api/auth/delete-account', methods=['DELETE'])
@token_required
def delete_account(current_user):
    try:
        SolvedProblem.query.filter_by(user_id=current_user.id).delete()
        UserProgress.query.filter_by(user_id=current_user.id).delete()
        ParametricUserProgress.query.filter_by(user_id=current_user.id).delete()
        PolarUserProgress.query.filter_by(user_id=current_user.id).delete()
        PasswordResetToken.query.filter_by(user_id=current_user.id).delete()
        
        db.session.delete(current_user)
        db.session.commit()
        
        session.clear()
        
        return jsonify({'message': 'Account deleted successfully'})
    except Exception as e:
        db.session.rollback()
        print(f"❌ Delete account error: {e}")
        return jsonify({'error': 'Failed to delete account', 'details': str(e)}), 500        

@app.route('/api/auth/user-stats')
@token_required
def get_user_stats(current_user):
    try:
        problem_count = SolvedProblem.query.filter_by(user_id=current_user.id).count()
        member_since = current_user.created_at.strftime('%B %d, %Y')
        latest_problem = SolvedProblem.query.filter_by(user_id=current_user.id).order_by(SolvedProblem.created_at.desc()).first()
        last_activity = latest_problem.created_at.strftime('%B %d, %Y') if latest_problem else 'No activity yet'
        return jsonify({
            'problemsSolved': problem_count,
            'memberSince': member_since,
            'lastActivity': last_activity,
            'user': current_user.to_dict()
        })
    except Exception as e:
        return jsonify({'error': 'Failed to load stats', 'details': str(e)}), 500

@app.route('/api/solver/solve', methods=['POST'])
@token_required
def solve_integral_api(current_user):
    data = request.json or {}
    integral = data.get('integral', '').strip()
    solver_type = data.get("solverType", "integral")

    if not integral:
        return jsonify({'error': 'Expression required'}), 400
    if len(integral) > 500:
        return jsonify({'error': 'Expression too long'}), 400

    solution = None
    steps = []
    
    if solver_type == "integral":
        try:
            solution, steps = solve_integral(integral, "x")
            if solution and '+ C' not in str(solution):
                solution = f"{solution} + C"
        except Exception as e:
            app.logger.error(f'Integral solver error: {str(e)}')
            return jsonify({'error': f'Integral solver error: {str(e)}'}), 400

    elif solver_type == "parametric":
        if "," not in integral:
            return jsonify({'error': 'Parametric equations must contain both x(t) and y(t) separated by comma'}), 400
        
        parts = [p.strip() for p in integral.split(",")]
        if len(parts) != 2:
            return jsonify({'error': 'Parametric equations must contain exactly two functions'}), 400
        
        xt = parts[0].replace("x(t)", "").replace("x(t) =", "").replace("x =", "").replace("=", "").strip()
        yt = parts[1].replace("y(t)", "").replace("y(t) =", "").replace("y =", "").replace("=", "").strip()
        
        if not xt or not yt:
            return jsonify({'error': 'Both parametric functions must be provided and non-empty'}), 400
        
        try:
            solution, steps = solve_parametric(xt, yt, "t")
            if solution and '+ C' not in str(solution):
                solution = f"{solution} + C"
        except Exception as e:
            app.logger.error(f'Parametric solver error: {str(e)}')
            return jsonify({'error': f'Parametric solver error: {str(e)}'}), 400

    elif solver_type == "polar":
        try:
            app.logger.info(f'Raw polar input received: {integral}')
            
            if "," in integral:
                parts = [p.strip() for p in integral.split(",")]
                if len(parts) != 2:
                    return jsonify({'error': 'Polar format should be "r1, r2" for intersection or just "r" for single curve'}), 400
                
                app.logger.info(f'Parsed parts: {parts}')
                
                r1_str = clean_polar_expression(parts[0])
                r2_str = clean_polar_expression(parts[1])
                
                app.logger.info(f'Cleaned r1: "{r1_str}", r2: "{r2_str}"')
                
                if not r1_str or not r2_str:
                    return jsonify({'error': 'Both polar functions must contain valid mathematical expressions'}), 400
                
                invalid_patterns = ['Inner', 'Outer', 'Function', ':']
                for pattern in invalid_patterns:
                    if pattern in r1_str or pattern in r2_str:
                        return jsonify({'error': f'Invalid expression format. Please provide mathematical expressions only (e.g., "sin(theta), cos(theta)")'}), 400
                
                theta = sp.Symbol('theta')
                try:
                    r1_expr = sp.sympify(r1_str)
                    r2_expr = sp.sympify(r2_str)
                except Exception as parse_e:
                    return jsonify({'error': f'Invalid mathematical expressions in polar functions: {str(parse_e)}'}), 400
                
                r1_vars = r1_expr.free_symbols
                r2_vars = r2_expr.free_symbols
                
                if r1_vars and theta not in r1_vars:
                    return jsonify({'error': f'First polar function contains unknown variables: {r1_vars}. Use "theta" as the variable.'}), 400
                if r2_vars and theta not in r2_vars:
                    return jsonify({'error': f'Second polar function contains unknown variables: {r2_vars}. Use "theta" as the variable.'}), 400
                
                area = solve_polar(r2_expr, r1_expr, theta)
                solution = f"$$\\text{{Result: {area:.6f}}}$$"
                r1_display = r1_str.replace('theta', '\\theta')
                r2_display = r2_str.replace('theta', '\\theta')
                steps = [
                    f"Finding area between polar curves: $$r_1 = {r1_display}$$ and $$r_2 = {r2_display}$$\n\nFound all intersection points. Integrated $$\\int \\frac{{r_{{\\text{{outer}}}}^2}}{{2}} \\, d\\theta - \\int \\frac{{r_{{\\text{{inner}}}}^2}}{{2}} \\, d\\theta$$ for each sector and added the result.",
                    f"Computed intersection area: {area:.6f}"
                ]
                
            else:
                r_str = clean_single_polar_expression(integral)
                
                app.logger.info(f'Cleaned single expression: "{r_str}"')
                
                if not r_str:
                    return jsonify({'error': 'Polar function r(θ) must contain a valid mathematical expression'}), 400
                
                if any(pattern in r_str for pattern in ['Inner', 'Outer', 'Function']):
                    return jsonify({'error': 'Invalid expression format. Please provide a mathematical expression only (e.g., "sin(theta)")'}), 400
                
                theta = sp.Symbol('theta')
                try:
                    r_expr = sp.sympify(r_str)
                except Exception as parse_e:
                    return jsonify({'error': f'Invalid mathematical expression in polar function: {str(parse_e)}'}), 400
                
                r_vars = r_expr.free_symbols
                if r_vars and theta not in r_vars:
                    return jsonify({'error': f'Polar function contains unknown variables: {r_vars}. Use "theta" as the variable.'}), 400
                
                import numpy as np
                zero_expr = sp.sympify("0")
                area = solve_polar(zero_expr, r_expr, theta, theta_start=0.0, theta_end=2*np.pi)
                
                solution = f"Area enclosed: {area:.6f}"
                r_display = r_str.replace('theta', '\\theta')
                steps = [
                    f"Finding area enclosed by polar curve $$r = {r_display}$$",
                    "Using polar area formula: $$A = \\frac{1}{2}\\int_0^{2\\pi} r^2 \\, d\\theta$$",
                    f"Computed enclosed area: {area:.6f}"
                ]

        except Exception as e:
            app.logger.error(f'Polar solver error: {str(e)}')
            return jsonify({'error': f'Polar solver error: {str(e)}'}), 400

    else:
        return jsonify({'error': f'Unknown solver type: {solver_type}. Use: integral, parametric, or polar'}), 400

    processed_steps = process_steps_for_katex(steps)
    
    if not isinstance(processed_steps, list):
        processed_steps = [str(processed_steps)] if processed_steps else []
    
    solution_str = str(solution) if solution is not None else "No solution found"

    try:
        display_input = integral
        
        if solver_type == "parametric":
            if "," in integral:
                parts = [p.strip() for p in integral.split(",")]
                if len(parts) == 2:
                    xt = parts[0].replace("x(t)", "").replace("x(t) =", "").replace("x =", "").replace("=", "").strip()
                    yt = parts[1].replace("y(t)", "").replace("y(t) =", "").replace("y =", "").replace("=", "").strip()
                    display_input = f"x(t) = {xt}, y(t) = {yt}"
        
        elif solver_type == "polar":
            if "," in integral:
                parts = [p.strip() for p in integral.split(",")]
                if len(parts) == 2:
                    r1 = clean_polar_expression(parts[0])
                    r2 = clean_polar_expression(parts[1])
                    display_input = f"Inner: {r1}, Outer: {r2}"
            else:
                r = clean_single_polar_expression(integral)
                display_input = f"r(θ) = {r}"
        
        new_problem = SolvedProblem(
            user_id=current_user.id,
            input=display_input,
            solution=solution_str,
            steps=json.dumps(steps),
            solver_type=solver_type
        )
        db.session.add(new_problem)
        db.session.commit()

        if solver_type == 'polar':
            if ',' in integral:
                parts = [p.strip() for p in integral.split(',')]
                if len(parts) == 2:
                    inner_func = parts[0].replace('theta', '\\theta')
                    outer_func = parts[1].replace('theta', '\\theta')
                    formatted_input_latex = f"$$\\text{{Inner: }} r_1(\\theta) = {inner_func}, \\quad \\text{{Outer: }} r_2(\\theta) = {outer_func}$$"
                else:
                    formatted_input_latex = format_latex_expression(integral)
            else:
                func = integral.replace('theta', '\\theta')
                formatted_input_latex = f"$$r(\\theta) = {func}$$"
        else:
            formatted_input_latex = format_latex_expression(integral)

        return jsonify({
            'input': integral,
            'input_latex': formatted_input_latex,
            'solution': solution_str,
            'solution_latex': format_latex_expression(solution_str),
            'steps': processed_steps,
            'solver_type': solver_type,
            'solved_at': datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(),
            'id': new_problem.id
        })

    except Exception as db_e:
        db.session.rollback()
        app.logger.error(f'Database error: {str(db_e)}')
        return jsonify({
            'input': integral,
            'input_latex': format_latex_expression(integral),
            'solution': solution_str,
            'solution_latex': format_latex_expression(solution_str),
            'steps': processed_steps,
            'solver_type': solver_type,
            'solved_at': datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(),
            'db_warning': 'Solution computed but not saved to history'
        })

@app.route('/api/solver/save', methods=['POST'])
@token_required
def save_problem(current_user):
    try:
        data = request.json or {}
        input_expr = data.get('input', '').strip()
        solution = data.get('solution', '').strip()
        steps = json.dumps(data.get('steps', [])) if data.get('steps') else None
        solver_type = data.get('solver_type', 'integral')

        if not input_expr or not solution:
            return jsonify({'error': 'Input and solution required'}), 400
        if len(input_expr) > 500:
            return jsonify({'error': 'Input expression too long'}), 400

        new_problem = SolvedProblem(
            user_id=current_user.id, 
            input=input_expr, 
            solution=solution, 
            steps=steps,
            solver_type=solver_type
        )
        db.session.add(new_problem)
        db.session.commit()
        return jsonify({'message': 'Problem saved successfully!', 'id': new_problem.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to save problem', 'details': str(e)}), 500

@app.route('/api/solver/history')
@token_required
def get_history(current_user):
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 50)
        problems = SolvedProblem.query.filter_by(user_id=current_user.id).order_by(SolvedProblem.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
        problem_list = []
        for problem in problems.items:
            try:
                steps = json.loads(problem.steps) if problem.steps else []
                processed_steps = process_steps_for_katex(steps)
            except json.JSONDecodeError:
                steps = []
                processed_steps = []
            
            formatted_input = format_input_for_display(problem.input, getattr(problem, 'solver_type', 'integral'))
            
            problem_list.append({
                'id': problem.id,
                'input': problem.input,
                'input_latex': formatted_input,
                'solution': problem.solution,
                'solution_latex': format_latex_expression(problem.solution),
                'steps': processed_steps,
                'solver_type': getattr(problem, 'solver_type', 'integral'),
                'created_at': problem.created_at.replace(tzinfo=timezone.utc).isoformat()
            })
        return jsonify({'problems': problem_list, 'total': problems.total, 'pages': problems.pages, 'current_page': page})
    except Exception as e:
        return jsonify({'error': 'Failed to load history', 'details': str(e)}), 500

@app.route('/api/dev/clear-database', methods=['POST'])
def clear_database():
    if not app.debug:
        return jsonify({'error': 'Not available in production'}), 403
    try:
        SolvedProblem.query.delete()
        User.query.delete()
        db.session.commit()
        return jsonify({'message': 'Database cleared successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to clear database', 'details': str(e)}), 500

def logged_in():
    return 'user_id' in session

@app.route("/")
def main():
    return render_template("main.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/getstarted")
def getstarted():
    return render_template("getStarted.html")

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/solver")
def solver_page():
    if (logged_in()):
        return render_template("solver.html")
    return redirect('/getstarted')

@app.route('/profilesettings')
def profilesettings():
    if (logged_in()):
        return render_template("profile-settings.html")
    return redirect('/getstarted')

@app.route('/reset-password')
def reset_password_page():
    return render_template('reset-password.html')
@app.route('/login/google')
def login_google():
    redirect_uri = url_for('authorize_google', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/login/github')
def login_github():
    redirect_uri = url_for('authorize_github', _external=True)
    return github.authorize_redirect(redirect_uri)

@app.route('/authorize/google')
def authorize_google():
    token = google.authorize_access_token()
    resp = google.get('userinfo')
    resp.raise_for_status()
    user_info = resp.json()
    email = user_info['email'].lower()
    name = user_info.get('name', 'Unknown Name')
    
    parts = name.split(' ', 1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else 'OAuthUser'

    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password_hash=generate_password_hash(secrets.token_hex(16))
        )
        db.session.add(user)
        db.session.commit()

    session['user_id'] = user.id
    session['oauth_provider'] = 'google'

    return redirect('/')

@app.route('/authorize/github')
def authorize_github():
    token = github.authorize_access_token()
    resp = github.get('user')
    resp.raise_for_status()
    user_info = resp.json()
    email = user_info.get('email')
    if not email:
        emails_resp = github.get('user/emails')
        emails_resp.raise_for_status()
        emails = emails_resp.json()
        primary_emails = [e['email'] for e in emails if e.get('primary') and e.get('verified')]
        if not primary_emails:
            return "No verified primary email found on GitHub", 400
        email = primary_emails[0]

    email = email.lower()
    name = user_info.get('name') or user_info.get('login') or 'GitHubUser'
    
    parts = name.split(' ', 1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else 'OAuthUser'

    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password_hash=generate_password_hash(secrets.token_hex(16))
        )
        db.session.add(user)
        db.session.commit()

    session['user_id'] = user.id
    session['oauth_provider'] = 'github'

    return redirect('/')
@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    
    return jsonify({'success': True, 'message': 'Logged out'})


@app.route("/techniques")
def techniques_page():
    return render_template("techniques.html")
@app.route('/api/practice/random')
@token_required
def get_random_problem(current_user):
    """Get a random practice problem"""
    try:
        difficulty = request.args.get('difficulty', type=int)
        technique = request.args.get('technique')
        exclude_completed = request.args.get('exclude_completed', 'false').lower() == 'true'
        
        conn = sqlite3.connect('practice_integrals.db')
        cursor = conn.cursor()
        
        query = "SELECT * FROM practice_problems WHERE 1=1"
        params = []
        
        if difficulty:
            query += " AND difficulty = ?"
            params.append(difficulty)
        
        if technique:
            query += " AND technique = ?"
            params.append(technique)
        
        if exclude_completed:
            completed_ids = [p.problem_id for p in UserProgress.query.filter_by(
                user_id=current_user.id, completed=True
            ).all()]
            
            if completed_ids:
                placeholders = ','.join('?' * len(completed_ids))
                query += f" AND id NOT IN ({placeholders})"
                params.extend(completed_ids)
        
        query += " ORDER BY RANDOM() LIMIT 1"
        cursor.execute(query, params)
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return jsonify({'error': 'No problems found'}), 404
        
        columns = ['id', 'problem_text', 'problem_latex', 'solution_text', 
                  'solution_latex', 'technique', 'difficulty', 'hint', 'steps', 'created_at']
        problem = dict(zip(columns, result))
        problem['steps'] = problem['steps'].split('\n') if problem['steps'] else []
        
        progress = UserProgress.query.filter_by(
            user_id=current_user.id, problem_id=problem['id']
        ).first()
        
        problem['user_progress'] = {
            'completed': progress.completed if progress else False,
            'attempts': progress.attempts if progress else 0
        }
        
        return jsonify({'problem': problem})
        
    except Exception as e:
        print(f"❌ Random problem error: {e}")
        return jsonify({'error': 'Failed to get problem'}), 500

@app.route('/api/practice/by-difficulty/<int:difficulty>')
@token_required
def get_problems_by_difficulty(current_user, difficulty):
    """Get problems by difficulty level"""
    try:
        if difficulty < 1 or difficulty > 7:
            return jsonify({'error': 'Difficulty must be between 1 and 7'}), 400
        
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 20)
        
        conn = sqlite3.connect('practice_integrals.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM practice_problems WHERE difficulty = ?', (difficulty,))
        total = cursor.fetchone()[0]
        
        offset = (page - 1) * per_page
        cursor.execute('''
            SELECT * FROM practice_problems 
            WHERE difficulty = ? 
            ORDER BY id LIMIT ? OFFSET ?
        ''', (difficulty, per_page, offset))
        
        results = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'problem_text', 'problem_latex', 'solution_text', 
                  'solution_latex', 'technique', 'difficulty', 'hint', 'steps', 'created_at']
        
        problems = []
        for result in results:
            problem = dict(zip(columns, result))
            problem['steps'] = problem['steps'].split('\n') if problem['steps'] else []
            
            progress = UserProgress.query.filter_by(
                user_id=current_user.id, problem_id=problem['id']
            ).first()
            
            problem['user_progress'] = {
                'completed': progress.completed if progress else False,
                'attempts': progress.attempts if progress else 0
            }
            problems.append(problem)
        
        return jsonify({
            'problems': problems,
            'total': total,
            'pages': (total + per_page - 1) // per_page,
            'current_page': page
        })
        
    except Exception as e:
        print(f"❌ Problems by difficulty error: {e}")
        return jsonify({'error': 'Failed to get problems'}), 500

@app.route('/api/practice/techniques')
def get_available_techniques():
    """Get all available integration techniques"""
    try:
        conn = sqlite3.connect('practice_integrals.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT technique, COUNT(*) as count, 
                   MIN(difficulty) as min_difficulty,
                   MAX(difficulty) as max_difficulty
            FROM practice_problems 
            GROUP BY technique 
            ORDER BY technique
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        techniques = []
        for technique, count, min_diff, max_diff in results:
            techniques.append({
                'name': technique,
                'problem_count': count,
                'difficulty_range': f"{min_diff}-{max_diff}"
            })
        
        return jsonify({'techniques': techniques})
        
    except Exception as e:
        print(f"❌ Techniques error: {e}")
        return jsonify({'error': 'Failed to get techniques'}), 500

@app.route('/api/practice/submit-answer', methods=['POST'])
@token_required
def submit_practice_answer(current_user):
    """Submit answer for practice problem"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        problem_id = data.get('problem_id')
        user_answer = data.get('answer', '').strip()
        
        if not problem_id or not user_answer:
            return jsonify({'error': 'Problem ID and answer required'}), 400
        
        conn = sqlite3.connect('practice_integrals.db')
        cursor = conn.cursor()
        cursor.execute('SELECT solution_text FROM practice_problems WHERE id = ?', (problem_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return jsonify({'error': 'Problem not found'}), 404
        
        correct_answer = result[0]
        
        progress = UserProgress.query.filter_by(
            user_id=current_user.id, problem_id=problem_id
        ).first()
        
        if not progress:
            progress = UserProgress(
                user_id=current_user.id,
                problem_id=problem_id,
                attempts=0,
                completed=False
            )
            db.session.add(progress)
        
        progress.attempts += 1
        
        is_correct = compare_math_expressions(user_answer, correct_answer, variable='x')
        
        if is_correct and not progress.completed:
            progress.completed = True
            progress.completed_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'correct': is_correct,
            'correct_answer': correct_answer,
            'attempts': progress.attempts,
            'completed': progress.completed,
            'message': 'Correct!' if is_correct else 'Incorrect, try again!'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Submit answer error: {e}")
        return jsonify({'error': 'Failed to submit answer'}), 500

@app.route('/api/practice/user-stats')
@token_required
def get_practice_stats(current_user):
    """Get user's practice statistics"""
    try:
        total_attempted = UserProgress.query.filter_by(user_id=current_user.id).count()
        total_completed = UserProgress.query.filter_by(user_id=current_user.id, completed=True).count()
        
        conn = sqlite3.connect('practice_integrals.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM practice_problems')
        total_available = cursor.fetchone()[0]
        conn.close()
        
        difficulty_progress = {}
        for diff in range(1, 8):
            attempted = UserProgress.query.join(db.session.query(UserProgress).filter_by(user_id=current_user.id)).count()
            difficulty_progress[str(diff)] = {'attempted': 0, 'completed': 0}
        
        return jsonify({
            'total_attempted': total_attempted,
            'total_completed': total_completed,
            'total_available': total_available,
            'completion_percentage': round((total_completed / total_available * 100), 1) if total_available > 0 else 0,
            'accuracy': round((total_completed / total_attempted * 100), 1) if total_attempted > 0 else 0
        })
        
    except Exception as e:
        print(f"❌ Practice stats error: {e}")
        return jsonify({'error': 'Failed to get statistics'}), 500

@app.route('/api/practice/problem/<int:problem_id>')
@token_required
def get_specific_problem(current_user, problem_id):
    """Get a specific practice problem by ID"""
    try:
        conn = sqlite3.connect('practice_integrals.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM practice_problems WHERE id = ?', (problem_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return jsonify({'error': 'Problem not found'}), 404
        
        columns = ['id', 'problem_text', 'problem_latex', 'solution_text', 
                  'solution_latex', 'technique', 'difficulty', 'hint', 'steps', 'created_at']
        problem = dict(zip(columns, result))
        problem['steps'] = problem['steps'].split('\n') if problem['steps'] else []
        
        progress = UserProgress.query.filter_by(
            user_id=current_user.id, problem_id=problem_id
        ).first()
        
        problem['user_progress'] = {
            'completed': progress.completed if progress else False,
            'attempts': progress.attempts if progress else 0
        }
        
        return jsonify({'problem': problem})
        
    except Exception as e:
        print(f"❌ Get specific problem error: {e}")
        return jsonify({'error': 'Failed to get problem'}), 500

@app.route('/api/practice/problems/<int:difficulty>')
@token_required
def get_practice_problems_by_difficulty(current_user, difficulty):
    """Get practice problems by difficulty level (1-4) - cycles through all problems"""
    try:
        if difficulty < 1 or difficulty > 4:
            return jsonify({'error': 'Difficulty must be between 1 and 4'}), 400
        
        conn = sqlite3.connect('practice_integrals.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM practice_problems 
            WHERE difficulty = ? 
            ORDER BY id
        ''', (difficulty,))
        
        all_problems = cursor.fetchall()
        conn.close()
        
        if not all_problems:
            return jsonify({'error': f'No problems found for difficulty {difficulty}'}), 404
        
        attempted_problem_ids = [p.problem_id for p in UserProgress.query.filter_by(user_id=current_user.id).all()]
        difficulty_problem_ids = [prob[0] for prob in all_problems]
        
        attempts_for_difficulty = len([pid for pid in attempted_problem_ids if pid in difficulty_problem_ids])
        
        problem_index = attempts_for_difficulty % len(all_problems)
        result = all_problems[problem_index]
        
        columns = ['id', 'problem_text', 'problem_latex', 'solution_text', 
                  'solution_latex', 'technique', 'difficulty', 'hint', 'steps', 'created_at']
        problem = dict(zip(columns, result))
        problem['steps'] = problem['steps'].split('\n') if problem['steps'] else []
        
        progress = UserProgress.query.filter_by(
            user_id=current_user.id, problem_id=problem['id']
        ).first()
        
        problem['user_progress'] = {
            'completed': progress.completed if progress else False,
            'attempts': progress.attempts if progress else 0
        }
        
        return jsonify({'problem': problem})
        
    except Exception as e:
        print(f"❌ Get practice problem error: {e}")
        return jsonify({'error': 'Failed to get practice problem'}), 500

@app.route('/api/practice/parametric/problems/<int:difficulty>')
@token_required
def get_parametric_problems_by_difficulty(current_user, difficulty):
    """Get parametric problems by difficulty level (1-4)"""
    try:
        if difficulty < 1 or difficulty > 4:
            return jsonify({'error': 'Difficulty must be between 1 and 4'}), 400
        
        conn = sqlite3.connect('practice_integrals.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM parametric_practice_problems 
            WHERE difficulty = ? 
            ORDER BY id
        ''', (difficulty,))
        
        all_problems = cursor.fetchall()
        conn.close()
        
        if not all_problems:
            return jsonify({'error': f'No parametric problems found for difficulty {difficulty}'}), 404
        
        attempted_problem_ids = [p.problem_id for p in ParametricUserProgress.query.filter_by(user_id=current_user.id).all()]
        difficulty_problem_ids = [prob[0] for prob in all_problems]
        attempts_for_difficulty = len([pid for pid in attempted_problem_ids if pid in difficulty_problem_ids])
        
        problem_index = attempts_for_difficulty % len(all_problems)
        result = all_problems[problem_index]
        
        columns = ['id', 'x_t_text', 'x_t_latex', 'y_t_text', 'y_t_latex',
                  'solution_text', 'solution_latex', 'difficulty', 'hint', 'steps', 'created_at']
        problem = dict(zip(columns, result))
        problem['steps'] = problem['steps'].split('\n') if problem['steps'] else []
        
        progress = ParametricUserProgress.query.filter_by(
            user_id=current_user.id, problem_id=problem['id']
        ).first()
        
        problem['user_progress'] = {
            'completed': progress.completed if progress else False,
            'attempts': progress.attempts if progress else 0
        }
        
        return jsonify({'problem': problem})
        
    except Exception as e:
        print(f"❌ Get parametric problem error: {e}")
        return jsonify({'error': 'Failed to get parametric problem'}), 500

@app.route('/api/practice/parametric/submit-answer', methods=['POST'])
@token_required
def submit_parametric_answer(current_user):
    """Submit answer for parametric practice problem"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        problem_id = data.get('problem_id')
        user_answer = data.get('answer', '').strip()
        
        if not problem_id or not user_answer:
            return jsonify({'error': 'Problem ID and answer required'}), 400
        
        conn = sqlite3.connect('practice_integrals.db')
        cursor = conn.cursor()
        cursor.execute('SELECT solution_text FROM parametric_practice_problems WHERE id = ?', (problem_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return jsonify({'error': 'Problem not found'}), 404
        
        correct_answer = result[0]
        
        progress = ParametricUserProgress.query.filter_by(
            user_id=current_user.id, problem_id=problem_id
        ).first()
        
        if not progress:
            progress = ParametricUserProgress(
                user_id=current_user.id,
                problem_id=problem_id,
                attempts=0,
                completed=False
            )
            db.session.add(progress)
        
        progress.attempts += 1
        
        is_correct = compare_math_expressions(user_answer, correct_answer, variable='t')
        
        if is_correct and not progress.completed:
            progress.completed = True
            progress.completed_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'correct': is_correct,
            'correct_answer': correct_answer,
            'attempts': progress.attempts,
            'completed': progress.completed,
            'message': 'Correct!' if is_correct else 'Incorrect, try again!'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Submit parametric answer error: {e}")
        return jsonify({'error': 'Failed to submit answer'}), 500

@app.route('/api/practice/give-up', methods=['POST'])
@token_required
def handle_give_up(current_user):
    """Handle when user gives up on a practice problem"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        problem_id = data.get('problem_id')
        problem_type = data.get('problem_type', 'integral')
        
        if not problem_id:
            return jsonify({'error': 'Problem ID required'}), 400
        
        if problem_type == 'parametric':
            ProgressModel = ParametricUserProgress
            table_name = 'parametric_practice_problems'
        elif problem_type == 'polar':
            ProgressModel = PolarUserProgress
            table_name = 'polar_practice_problems'
        else:
            ProgressModel = UserProgress
            table_name = 'practice_problems'
        
        conn = sqlite3.connect('practice_integrals.db')
        cursor = conn.cursor()
        
        if problem_type == 'polar':
            cursor.execute(f'SELECT solution_text FROM {table_name} WHERE id = ?', (problem_id,))
        else:
            cursor.execute(f'SELECT solution_text, solution_latex FROM {table_name} WHERE id = ?', (problem_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return jsonify({'error': 'Problem not found'}), 404
        
        progress = ProgressModel.query.filter_by(
            user_id=current_user.id, problem_id=problem_id
        ).first()
        
        if not progress:
            progress = ProgressModel(
                user_id=current_user.id,
                problem_id=problem_id,
                attempts=0,
                completed=False
            )
            db.session.add(progress)
        
        progress.attempts += 1
        progress.completed = True
        db.session.commit()
        
        response_data = {
            'correct_answer': result[0],
            'attempts': progress.attempts,
            'message': 'Problem skipped'
        }
        
        if problem_type != 'polar' and len(result) > 1:
            response_data['correct_answer_latex'] = result[1]
        
        return jsonify(response_data)
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Give up error: {e}")
        return jsonify({'error': 'Failed to process give up'}), 500

@app.route('/api/practice/polar/problems/<int:difficulty>')
@token_required
def get_polar_problems_by_difficulty(current_user, difficulty):
    """Get polar problems by difficulty level (1-4)"""
    try:
        if difficulty < 1 or difficulty > 4:
            return jsonify({'error': 'Difficulty must be between 1 and 4'}), 400
        
        conn = sqlite3.connect('practice_integrals.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM polar_practice_problems 
            WHERE difficulty = ? 
            ORDER BY id
        ''', (difficulty,))
        
        all_problems = cursor.fetchall()
        conn.close()
        
        if not all_problems:
            return jsonify({'error': f'No polar problems found for difficulty {difficulty}'}), 404
        
        attempted_problem_ids = [p.problem_id for p in PolarUserProgress.query.filter_by(user_id=current_user.id).all()]
        difficulty_problem_ids = [prob[0] for prob in all_problems]
        attempts_for_difficulty = len([pid for pid in attempted_problem_ids if pid in difficulty_problem_ids])
        
        problem_index = attempts_for_difficulty % len(all_problems)
        result = all_problems[problem_index]
        
        columns = ['id', 'inner_function_text', 'inner_function_latex', 'outer_function_text', 'outer_function_latex',
                  'lower_bound', 'upper_bound', 'solution_text', 'solution_latex', 'difficulty', 'hint', 'steps', 'created_at']
        problem = dict(zip(columns, result))
        problem['steps'] = problem['steps'].split('\n') if problem['steps'] else []
        
        problem['lower_bound_display'] = format_bound_for_display(problem['lower_bound'])
        problem['upper_bound_display'] = format_bound_for_display(problem['upper_bound'])
        
        progress = PolarUserProgress.query.filter_by(
            user_id=current_user.id, problem_id=problem['id']
        ).first()
        
        problem['user_progress'] = {
            'completed': progress.completed if progress else False,
            'attempts': progress.attempts if progress else 0
        }
        
        return jsonify({'problem': problem})
        
    except Exception as e:
        print(f"❌ Get polar problem error: {e}")
        return jsonify({'error': 'Failed to get polar problem'}), 500

@app.route('/api/practice/polar/submit-answer', methods=['POST'])
@token_required
def submit_polar_answer(current_user):
    """Submit answer for polar practice problem"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        problem_id = data.get('problem_id')
        user_answer = data.get('answer', '').strip()
        
        if not problem_id or not user_answer:
            return jsonify({'error': 'Problem ID and answer required'}), 400
        
        conn = sqlite3.connect('practice_integrals.db')
        cursor = conn.cursor()
        cursor.execute('SELECT solution_text FROM polar_practice_problems WHERE id = ?', (problem_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return jsonify({'error': 'Problem not found'}), 404
        
        correct_answer = result[0]
        
        progress = PolarUserProgress.query.filter_by(
            user_id=current_user.id, problem_id=problem_id
        ).first()
        
        if not progress:
            progress = PolarUserProgress(
                user_id=current_user.id,
                problem_id=problem_id,
                attempts=0,
                completed=False
            )
            db.session.add(progress)
        
        progress.attempts += 1
        
        try:
            user_float = round(float(user_answer), 3)
            correct_float = round(float(correct_answer), 3)
            is_correct = abs(user_float - correct_float) < 0.001
        except ValueError:
            is_correct = False
        
        if is_correct and not progress.completed:
            progress.completed = True
            progress.completed_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'correct': is_correct,
            'correct_answer': correct_answer,
            'attempts': progress.attempts,
            'completed': progress.completed,
            'message': 'Correct!' if is_correct else 'Incorrect, try again!'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Submit polar answer error: {e}")
        return jsonify({'error': 'Failed to submit answer'}), 500
    



@app.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    try:
        data = request.json or {}
        email = data.get('email', '').strip().lower()
        
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            token = secrets.token_urlsafe(32)
            
            reset_token = PasswordResetToken(
                user_id=user.id,
                token=token,
                expires_at=datetime.utcnow() + timedelta(hours=1)
            )
            
            db.session.add(reset_token)
            db.session.commit()
            
            send_password_reset_email(user.email, user.first_name, token)
            
            print(f"✅ Password reset email sent to: {email}")
        else:
            print(f"⚠️ Password reset requested for non-existent email: {email}")
        
        return jsonify({
            'message': 'If an account exists with this email, you will receive password reset instructions.'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Forgot password error: {e}")
        return jsonify({'error': 'Failed to process request'}), 500

def send_password_reset_email(email, first_name, token):
    """Send password reset email"""
    try:
        reset_link = f"http://127.0.0.1:5000/reset-password?token={token}"
        
        msg = Message(
            subject='Reset Your Eulearn Password',
            recipients=[email],
            html=f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #00A1FF;">Reset Your Password</h2>
                        <p>Hi {first_name},</p>
                        <p>We received a request to reset your password for your Eulearn account.</p>
                        <p>Click the button below to reset your password:</p>
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{reset_link}" 
                               style="background-color: #00A1FF; 
                                      color: white; 
                                      padding: 12px 30px; 
                                      text-decoration: none; 
                                      border-radius: 5px; 
                                      display: inline-block;">
                                Reset Password
                            </a>
                        </div>
                        <p style="color: #666; font-size: 14px;">
                            This link will expire in 1 hour.
                        </p>
                        <p style="color: #666; font-size: 14px;">
                            Don't recognize this request? Please ignore this email.
                        </p>
                    </div>
                </body>
            </html>
            """
        )
        
        mail.send(msg)
        return True
        
    except Exception as e:
        print(f"❌ Email sending error: {e}")
        return False

@app.route('/api/auth/verify-reset-token', methods=['POST'])
def verify_reset_token():
    try:
        data = request.json or {}
        token = data.get('token', '').strip()
        
        if not token:
            return jsonify({'error': 'Token required'}), 400
        
        reset_token = PasswordResetToken.query.filter_by(token=token).first()
        
        if not reset_token or not reset_token.is_valid():
            return jsonify({'error': 'Invalid or expired token'}), 400
        
        return jsonify({
            'valid': True,
            'email': reset_token.user.email
        })
        
    except Exception as e:
        print(f"❌ Verify token error: {e}")
        return jsonify({'error': 'Failed to verify token'}), 500

@app.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    try:
        data = request.json or {}
        token = data.get('token', '').strip()
        new_password = data.get('newPassword', '')
        
        if not token or not new_password:
            return jsonify({'error': 'Token and new password required'}), 400
        
        if not validate_password(new_password):
            return jsonify({'error': 'Password must be at least 8 characters'}), 400
        
        reset_token = PasswordResetToken.query.filter_by(token=token).first()
        
        if not reset_token or not reset_token.is_valid():
            return jsonify({'error': 'Invalid or expired token'}), 400
        
        user = reset_token.user
        user.password_hash = generate_password_hash(new_password)
        reset_token.used = True
        
        db.session.commit()
        
        print(f"✅ Password reset successful for: {user.email}")
        
        return jsonify({
            'message': 'Password reset successful! You can now login with your new password.'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Reset password error: {e}")
        return jsonify({'error': 'Failed to reset password'}), 500    
    


    
if __name__ == '__main__':
    app.run(debug=True, port=5000)