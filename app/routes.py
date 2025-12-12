from flask import render_template, request, redirect, url_for, flash, session, Response, send_file
import os
import uuid
from werkzeug.utils import secure_filename
from functools import wraps
from sqlalchemy.orm import joinedload

from .models import db, Company, Client, Ground, Preferences, Match
from .matching import compute_match_scores
from .helpers import (
    get_subdivision_types,
    get_subdivision_types_display,
    normalize_subdivision_type,
    parse_int_filter,
    parse_float_filter
)

# ============================================================================
# CONFIGURATION
# ============================================================================

UPLOAD_FOLDER = 'app/static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def allowed_file(filename):
    """Check if uploaded file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ============================================================================
# DECORATORS - Access control
# ============================================================================

def requires_company(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'company_id' not in session or session.get('role') != 'company':
            flash('Access denied', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated

def requires_client(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'client_id' not in session or session.get('role') != 'client':
            flash('Access denied', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def check_ground_ownership(ground):
    """Check if current company owns the ground. Returns True if authorized."""
    company = Company.query.get(session['company_id'])
    if not company or not getattr(ground, 'provider', None):
        return False
    try:
        return ground.provider.strip().lower() == (company.name or '').strip().lower()
    except Exception:
        return False

def check_client_ownership(client):
    """Check if current company owns the client. Returns True if authorized."""
    return client.company_id == session['company_id']

def handle_photo_upload():
    """Handle photo upload from request.files. Returns image_url or None."""
    if 'photo' not in request.files:
        return None
    
    file = request.files['photo']
    if not file or not file.filename or not allowed_file(file.filename):
        return None
    
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    return f"/static/uploads/{filename}"

def get_sorted_matches(matches):
    """Sort matches with approved first, then by score (highest first)."""
    def score_of(m):
        try:
            if getattr(m, 'total_score', None) is not None:
                return float(m.total_score)
        except Exception:
            pass
        # Fallback: sum existing component scores if present
        return float((getattr(m, 'budget_score', 0) or 0) + (getattr(m, 'm2_score', 0) or 0) + (getattr(m, 'location_score', 0) or 0) + (getattr(m, 'type_score', 0) or 0))

    def sort_key(m):
        status = (m.status or '').lower()
        approved_first = 0 if status in ('approved', 'accepted') else 1
        return (approved_first, -score_of(m))

    return sorted(matches, key=sort_key)

def get_user_company_name():
    """Get current user's company name if they're a company user."""
    if session.get('role') != 'company':
        return None
    company = Company.query.get(session['company_id'])
    return company.name if company else None

def apply_ground_filters(query, filters):
    """Apply search filters to ground query."""
    if filters.get('location'):
        query = query.filter(Ground.location.ilike(f"%{filters['location']}%"))
    if filters.get('min_price'):
        query = query.filter(Ground.budget >= float(filters['min_price']))
    if filters.get('max_price'):
        query = query.filter(Ground.budget <= float(filters['max_price']))
    if filters.get('min_m2'):
        query = query.filter(Ground.m2 >= int(filters['min_m2']))
    if filters.get('max_m2'):
        query = query.filter(Ground.m2 <= int(filters['max_m2']))
    if filters.get('subdivision_type'):
        query = query.filter(Ground.subdivision_type.ilike(f"%{filters['subdivision_type']}%"))
    return query

def download_ground_image(plot_data, ground_id):
    """Download image for a ground from scraped plot data. Returns True if successful.
    Gracefully no-ops if optional deps (requests, bs4) are unavailable.
    """
    try:
        import requests
        from urllib.parse import urlparse
        from bs4 import BeautifulSoup
    except Exception:
        return False
    
    img_url = plot_data.get('image_url') or plot_data.get('detail_url')
    if not img_url:
        return False
    
    # If placeholder image, try to get real image from detail page
    if 'pixel' in img_url and plot_data.get('detail_url'):
        try:
            resp = requests.get(plot_data['detail_url'], timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            candidates = [img.get('src') for img in soup.find_all('img') if img.get('src')]
            for c in candidates:
                if c.startswith('http') and ('.jpg' in c or '.png' in c):
                    img_url = c
                    break
        except:
            pass
    
    try:
        resp = requests.get(img_url, timeout=15)
        resp.raise_for_status()
        base_dir = os.path.join(os.path.dirname(__file__), 'static', 'images', 'grounds')
        os.makedirs(base_dir, exist_ok=True)
        out_path = os.path.join(base_dir, f"{ground_id}.jpg")
        with open(out_path, 'wb') as f:
            f.write(resp.content)
        return True
    except:
        return False

def init_routes(app):
    """Initialize all application routes"""
    
    # ========================================================================
    # PUBLIC ROUTES - Accessible to all users
    # ========================================================================
    
    @app.route('/')
    def home():
        """Landing page showing available building plots"""
        try:
            # Fetch recent grounds for display (order by id descending for most recent)
            grounds = Ground.query.order_by(Ground.id.desc()).limit(6).all()
        except:
            grounds = []
        
        return render_template('home.html', grounds=grounds)
    
    # ========================================================================
    # AUTHENTICATION ROUTES - Registration and login
    # ========================================================================
    
    @app.route('/company/register', methods=['GET', 'POST'])
    def company_register():
        """Register a new company account"""
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            
            if not name or not email:
                flash('Name and email are required', 'danger')
                return render_template('company_register.html')
            
            if Company.query.filter_by(email=email).first():
                flash('Email already registered', 'danger')
                return render_template('company_register.html')
            
            try:
                company = Company(name=name, email=email)
                db.session.add(company)
                db.session.commit()
                session['company_id'] = company.id
                session['role'] = 'company'
                flash('Company registered!', 'success')
                return redirect(url_for('dashboard'))
            except Exception as e:
                db.session.rollback()
                flash(f'Registration failed: {str(e)}', 'danger')
        
        return render_template('company_register.html')
    
    @app.route('/company/login', methods=['GET', 'POST'])
    def company_login():
        """Login for company users"""
        if request.method == 'POST':
            email = request.form.get('email')
            company = Company.query.filter_by(email=email).first()
            
            if company:
                session['company_id'] = company.id
                session['role'] = 'company'
                flash('Logged in!', 'success')
                return redirect(url_for('dashboard'))
            
            flash('Company not found', 'danger')
        
        return render_template('company_login.html')
    
    @app.route('/client/login', methods=['GET', 'POST'])
    def client_login():
        """Login for client users"""
        if request.method == 'POST':
            email = request.form.get('email')
            client = Client.query.filter_by(email=email).first()
            
            if client:
                session['client_id'] = client.id
                session['role'] = 'client'
                session['company_id'] = client.company_id
                flash('Logged in!', 'success')
                return redirect(url_for('client_dashboard'))
            
            flash('Client not found', 'danger')
        
        return render_template('client_login.html')
    
    # ========================================================================
    # COMPANY DASHBOARD ROUTES
    # ========================================================================
    
    @app.route('/dashboard')
    @requires_company
    def dashboard():
        """Company dashboard showing overview of clients, grounds, and matches"""
        company_id = session['company_id']
        clients = Client.query.filter_by(company_id=company_id).all()
        grounds = Ground.query.all()
        # Get all matches for clients of this company
        matches = Match.query.join(Client).filter(Client.company_id == company_id).all()
        
        return render_template('dashboard.html', 
                             clients=clients, 
                             grounds=grounds, 
                             matches=matches)
    
    # ========================================================================
    # CLIENT DASHBOARD & PROFILE ROUTES
    # ========================================================================
    
    @app.route('/client/dashboard')
    @requires_client
    def client_dashboard():
        """Client dashboard showing preferences and approved matches"""
        client = Client.query.get(session['client_id'])
        matches = [m for m in client.matches if m.status == 'approved']
        
        return render_template('client_dashboard.html',
                             client=client,
                             preferences=client.preferences,
                             matches=get_sorted_matches(matches))
    
    # ========================================================================
    # CLIENT CRUD ROUTES - Manage clients
    # ========================================================================
    
    @app.route('/clients')
    @requires_company
    def clients_list():
        """List all clients with search filtering"""
        search = request.args.get('search', '')
        query = Client.query.filter_by(company_id=session['company_id'])
        if search:
            query = query.filter(
                (Client.name.ilike(f'%{search}%')) |
                (Client.email.ilike(f'%{search}%')) |
                (Client.address.ilike(f'%{search}%'))
            )
        
        clients = query.all()
        return render_template('clients_list.html', clients=clients, search=search)
    
    @app.route('/clients/add', methods=['GET', 'POST'])
    @requires_company
    def client_add():
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            
            if not name or not email:
                flash('Name and email are required', 'danger')
                return render_template('client_form.html', client=None)
            
            if Client.query.filter_by(email=email).first():
                flash('Email already exists', 'danger')
                return render_template('client_form.html', client=None)
            
            try:
                client = Client(
                    company_id=session['company_id'],
                    name=name,
                    email=email,
                    location=request.form.get('location', '').strip(),
                    address=request.form.get('address', '').strip()
                )
                db.session.add(client)
                db.session.commit()
                flash('Client added!', 'success')
                return redirect(url_for('clients_list'))
            except Exception as e:
                db.session.rollback()
                flash(f'Failed to add client: {str(e)}', 'danger')
        
        return render_template('client_form.html', client=None)
    
    @app.route('/clients/<int:client_id>/edit', methods=['GET', 'POST'])
    @requires_company
    def client_edit(client_id):
        client = Client.query.get_or_404(client_id)
        
        if not check_client_ownership(client):
            flash('Access denied', 'danger')
            return redirect(url_for('clients_list'))
        
        if request.method == 'POST':
            client.name = request.form.get('name')
            client.email = request.form.get('email')
            client.location = request.form.get('location', '')
            client.address = request.form.get('address', '')
            try:
                db.session.commit()
                flash('Client updated!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Failed to update client: {str(e)}', 'danger')
            return redirect(url_for('clients_list'))
        
        return render_template('client_form.html', client=client)
    
    @app.route('/clients/<int:client_id>/delete', methods=['POST'])
    @requires_company
    def client_delete(client_id):
        client = Client.query.get_or_404(client_id)
        
        if not check_client_ownership(client):
            flash('Access denied', 'danger')
            return redirect(url_for('clients_list'))
        
        try:
            db.session.delete(client)
            db.session.commit()
            flash('Client deleted!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Failed to delete client: {str(e)}', 'danger')
        db.session.commit()
        
        flash('Client deleted!', 'success')
        return redirect(url_for('clients_list'))
    
    # ========================================================================
    # GROUND CRUD ROUTES - Manage building plots
    # ========================================================================
    
    @app.route('/grounds')
    def grounds_list():
        """List all building plots with filtering (location, price, m2, subdivision_type)"""
        # Collect distinct values for quick-select filters
        available_locations = [row[0] for row in db.session.query(Ground.location).filter(Ground.location != None).distinct().order_by(Ground.location).all()]
        available_subdivision_types = [row[0] for row in db.session.query(Ground.subdivision_type).filter(Ground.subdivision_type != None).distinct().order_by(Ground.subdivision_type).all()]
        merged_subdivision_types = sorted({t for t in (available_subdivision_types + get_subdivision_types()) if t})

        query = Ground.query
        
        # Filter grounds for clients: only their company's grounds + scraped grounds
        if session.get('role') == 'client':
            client = Client.query.get(session['client_id'])
            if client and client.company:
                query = query.filter(
                    db.or_(
                        Ground.provider == client.company.name,
                        Ground.provider == None,
                        Ground.provider == ''
                    )
                )
        
        # Apply search filters
        filters = {
            'location': request.args.get('location', ''),
            'min_price': request.args.get('min_price', ''),
            'max_price': request.args.get('max_price', ''),
            'min_m2': request.args.get('min_m2', ''),
            'max_m2': request.args.get('max_m2', ''),
            'subdivision_type': request.args.get('subdivision_type', '')
        }
        query = apply_ground_filters(query, filters)
        
        grounds = query.all()

        # Sort: own company's grounds first, then the rest
        user_company = get_user_company_name()
        if user_company:
            try:
                uc_norm = user_company.strip().lower()
                grounds = sorted(grounds, key=lambda g: (0 if (getattr(g, 'provider', None) or '').strip().lower() == uc_norm else 1, g.id or 0))
            except Exception:
                pass

        return render_template(
            'grounds_list.html',
            grounds=grounds,
            user_company=user_company,
            subdivision_types=merged_subdivision_types,
            available_locations=available_locations
        )

    @app.route('/grounds/<int:ground_id>/image')
    def ground_image(ground_id):
        """Dynamically generate a placeholder SVG image for a ground.

        This avoids broken <img> icons when no static JPG is available. The
        SVG includes the location and a small caption with m2 and budget.
        """
        ground = Ground.query.get(ground_id)
        if not ground:
            # return a 404 transparent SVG
            svg = """<svg xmlns='http://www.w3.org/2000/svg' width='800' height='400'></svg>"""
            return Response(svg, mimetype='image/svg+xml')
        # If a real JPG exists in static/images/grounds/<id>.jpg, serve it.
        static_path = os.path.join(os.path.dirname(__file__), 'static', 'images', 'grounds', f"{ground_id}.jpg")
        if os.path.exists(static_path):
            return send_file(static_path, mimetype='image/jpeg')

        # Safe text values
        location = (ground.location or 'Unknown')
        try:
            m2 = int(ground.m2) if ground.m2 is not None else None
        except Exception:
            m2 = None
        try:
            budget_val = float(ground.budget) if ground.budget is not None else None
        except Exception:
            budget_val = None

        budget_text = f"€{budget_val:,.0f}" if budget_val is not None else ''
        m2_text = f"{m2} m²" if m2 is not None else ''

        # Simple SVG composition
        svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="800" height="400" viewBox="0 0 800 400">
  <rect width="100%" height="100%" fill="#f6fbf8" />
  <rect x="24" y="24" width="752" height="352" rx="10" ry="10" fill="#ffffff" stroke="#e6f3ed"/>
  <text x="50%" y="45%" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="28" fill="#193127">{location}</text>
  <text x="50%" y="60%" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="20" fill="#1f6f4a">{m2_text} {('•' if m2_text and budget_text else '')} {budget_text}</text>
  <text x="50%" y="85%" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" font-size="14" fill="#6b7a71">Provided by local preview</text>
</svg>
'''

        return Response(svg, mimetype='image/svg+xml')
    
    @app.route('/grounds/add', methods=['GET', 'POST'])
    @requires_company
    def ground_add():
        if request.method == 'POST':
            try:
                location = request.form.get('location', '').strip()
                address = request.form.get('address', '').strip()
                m2 = int(request.form.get('m2', 0))
                budget = float(request.form.get('budget', 0))
                subdivision_type = normalize_subdivision_type(request.form.get('subdivision_type', '')) or 'development_plot'
                owner = request.form.get('owner', '').strip()
                
                # Get company name as provider
                company = Company.query.get(session['company_id'])
                provider = company.name if company else 'Unknown'
                
                # Validation
                if not location or not subdivision_type or not owner:
                    flash('Location, type and owner are required', 'danger')
                    return render_template('ground_form.html', ground=None, subdivision_types=get_subdivision_types(), is_edit=False)
                
                if m2 <= 0 or budget <= 0:
                    flash('Size and budget must be positive', 'danger')
                    return render_template('ground_form.html', ground=None, subdivision_types=get_subdivision_types(), is_edit=False)
                
                # Handle image upload
                image_url = handle_photo_upload()
                
                # If no image uploaded, use random placeholder
                if not image_url:
                    image_url = f"https://picsum.photos/seed/{uuid.uuid4()}/800/400"
                
                ground = Ground(
                    location=location,
                    address=address,
                    m2=m2,
                    budget=budget,
                    subdivision_type=subdivision_type,
                    owner=owner,
                    provider=provider,
                    image_url=image_url
                )
                db.session.add(ground)
                db.session.commit()
                
                flash('Ground added!', 'success')
                return redirect(url_for('grounds_list'))
            except ValueError:
                flash('Invalid number format', 'danger')
                return render_template('ground_form.html', ground=None, subdivision_types=get_subdivision_types(), is_edit=False)
            except Exception as e:
                db.session.rollback()
                flash(f'Failed to add ground: {str(e)}', 'danger')
                return render_template('ground_form.html', ground=None, subdivision_types=get_subdivision_types(), is_edit=False)
        
        return render_template('ground_form.html', ground=None, subdivision_types=get_subdivision_types(), is_edit=False)
    
    @app.route('/grounds/<int:ground_id>')
    def ground_detail(ground_id):
        ground = Ground.query.get_or_404(ground_id)
        return render_template('ground_detail.html', ground=ground, user_company=get_user_company_name())
    
    @app.route('/grounds/<int:ground_id>/edit', methods=['GET', 'POST'])
    @requires_company
    def ground_edit(ground_id):
        ground = Ground.query.get_or_404(ground_id)
        
        if not check_ground_ownership(ground):
            flash('You can only edit grounds added by your company', 'danger')
            return redirect(url_for('grounds_list'))
        
        if request.method == 'POST':
            ground.location = request.form.get('location')
            ground.address = request.form.get('address')
            ground.m2 = int(request.form.get('m2'))
            ground.budget = float(request.form.get('budget'))
            ground.subdivision_type = normalize_subdivision_type(request.form.get('subdivision_type')) or ground.subdivision_type
            ground.owner = request.form.get('owner')
            
            # Handle image upload
            image_url = handle_photo_upload()
            if image_url:
                ground.image_url = image_url
            
            try:
                db.session.commit()
                flash('Ground updated!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Failed to update ground: {str(e)}', 'danger')
                return render_template('ground_form.html', ground=ground, subdivision_types=get_subdivision_types(), is_edit=True)
            return redirect(url_for('grounds_list'))
        
        return render_template('ground_form.html', ground=ground, subdivision_types=get_subdivision_types(), is_edit=True)
    
    @app.route('/grounds/<int:ground_id>/delete', methods=['POST'])
    @requires_company
    def ground_delete(ground_id):
        ground = Ground.query.get_or_404(ground_id)
        
        if not check_ground_ownership(ground):
            flash('You can only delete grounds added by your company', 'danger')
            return redirect(url_for('grounds_list'))
        
        try:
            db.session.delete(ground)
            db.session.commit()
            flash('Ground deleted!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Failed to delete ground: {str(e)}', 'danger')
        return redirect(url_for('grounds_list'))
    
    # ========================================================================
    # PREFERENCES ROUTES - Manage client search criteria
    # ========================================================================
    
    @app.route('/preferences')
    def preferences_list():
        """List all client preferences (company view) or redirect to client preferences"""
        if session.get('role') == 'company':
            clients = Client.query.filter_by(company_id=session['company_id']).all()
            client_ids = [c.id for c in clients]
            preferences = Preferences.query.filter(Preferences.client_id.in_(client_ids)).all() if client_ids else []
            
            for pref in preferences:
                pref.client = Client.query.get(pref.client_id)
            
            return render_template('preferences_list.html', preferences=preferences)
        elif session.get('role') == 'client':
            return redirect(url_for('client_preferences_view'))
        
        flash('Access denied', 'danger')
        return redirect(url_for('home'))
    
    @app.route('/preferences/<int:client_id>')
    @requires_company
    def preferences_view(client_id):
        """View-only preferences for companies. Clients must edit their own preferences."""
        client = Client.query.get_or_404(client_id)
        
        if not check_client_ownership(client):
            flash('Access denied', 'danger')
            return redirect(url_for('preferences_list'))
        
        pref = Preferences.query.filter_by(client_id=client_id).first()
        
        if not pref:
            flash('Client has not set preferences yet', 'info')
            return redirect(url_for('preferences_list'))
        
        return render_template('preferences_view.html', client=client, pref=pref, subdivision_types=get_subdivision_types())
    
    @app.route('/client/preferences')
    @requires_client
    def client_preferences_view():
        client = Client.query.get(session['client_id'])
        return render_template('client_preferences.html', client=client, pref=client.preferences)
    
    @app.route('/client/preferences/edit', methods=['GET', 'POST'])
    @requires_client
    def client_preferences_edit():
        client = Client.query.get(session['client_id'])
        pref = Preferences.query.filter_by(client_id=client.id).first()
        
        if not pref:
            pref = Preferences(client_id=client.id)
            db.session.add(pref)
        
        if request.method == 'POST':
            pref.location = request.form.get('location')
            pref.subdivision_type = request.form.get('subdivision_type')
            pref.min_m2 = int(request.form.get('min_m2')) if request.form.get('min_m2') else None
            pref.max_m2 = int(request.form.get('max_m2')) if request.form.get('max_m2') else None
            pref.min_budget = float(request.form.get('min_budget')) if request.form.get('min_budget') else None
            pref.max_budget = float(request.form.get('max_budget')) if request.form.get('max_budget') else None
            
            try:
                db.session.commit()
                flash('Preferences updated!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating preferences: {str(e)}', 'danger')
                return render_template('client_preferences_form.html', client=client, pref=pref, subdivision_types=get_subdivision_types())
            
            return redirect(url_for('client_dashboard'))
        
        return render_template('client_preferences_form.html', client=client, pref=pref, subdivision_types=get_subdivision_types())
    
    # ========================================================================
    # MATCHING ROUTES - Run algorithm and review matches
    # ========================================================================
    
    @app.route('/match/review', methods=['GET', 'POST'])
    @requires_company
    def match_review():
        """Review and approve computed matches (in-memory); save only approved to DB"""
        if request.method == 'POST':
            # Parse approved match keys (client_id:ground_id)
            approved_keys = request.form.getlist('approved_matches')
            
            # Retrieve computed matches from session
            computed = session.get('computed_matches', [])
            if not computed:
                flash('No computed matches in session. Please run matching again.', 'warning')
                return redirect(url_for('dashboard'))
            
            # Build dict for quick lookup
            match_dict = {f"{m['client_id']}:{m['ground_id']}": m for m in computed}
            
            # Save only approved matches to DB
            saved_count = 0
            for key in approved_keys:
                match_data = match_dict.get(key)
                if not match_data:
                    continue
                
                # Check if already exists
                existing = Match.query.filter_by(
                    client_id=match_data['client_id'],
                    ground_id=match_data['ground_id']
                ).first()
                
                if existing:
                    # Update to approved if was pending (shouldn't happen now, but safeguard)
                    existing.status = 'approved'
                    existing.budget_score = match_data['budget_score']
                    existing.m2_score = match_data['m2_score']
                    existing.location_score = match_data['location_score']
                    existing.type_score = match_data['type_score']
                else:
                    # Insert new approved match
                    new_match = Match(
                        client_id=match_data['client_id'],
                        ground_id=match_data['ground_id'],
                        budget_score=match_data['budget_score'],
                        m2_score=match_data['m2_score'],
                        location_score=match_data['location_score'],
                        type_score=match_data['type_score'],
                        status='approved'
                    )
                    db.session.add(new_match)
                saved_count += 1
            
            try:
                db.session.commit()
                # Clear session matches
                session.pop('computed_matches', None)
                flash(f'{saved_count} matches approved and saved!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error saving matches: {str(e)}', 'danger')
                return redirect(url_for('match_review'))
            return redirect(url_for('matches_list'))
        
        # GET: Build preview from session-stored computed matches
        computed = session.get('computed_matches', [])
        if not computed:
            flash('No matches to review. Run the matching algorithm first.', 'info')
            return redirect(url_for('dashboard'))
        
        clients = Client.query.options(
            joinedload(Client.preferences)
        ).filter_by(company_id=session['company_id']).all()
        client_matches = {}
        
        for client in clients:
            # Filter computed matches for this client
            client_computed = [m for m in computed if m['client_id'] == client.id]
            if not client_computed:
                continue
            
            # Build pseudo-Match objects with score for sorting
            pseudo_matches = []
            for mc in client_computed:
                ground = Ground.query.get(mc['ground_id'])
                if not ground:
                    continue
                # Create a dict resembling Match attributes
                pm = type('obj', (object,), {
                    'client_id': mc['client_id'],
                    'ground_id': mc['ground_id'],
                    'ground': ground,
                    'client': client,
                    'budget_score': mc['budget_score'],
                    'm2_score': mc['m2_score'],
                    'location_score': mc['location_score'],
                    'type_score': mc['type_score'],
                    'total_score': (mc['budget_score'] + mc['m2_score'] + mc['location_score'] + mc['type_score']) / 4.0,
                    'status': 'computed',  # not in DB yet
                    'match_key': f"{mc['client_id']}:{mc['ground_id']}"
                })()
                pseudo_matches.append(pm)
            
            # Sort and take top 10
            pseudo_matches = get_sorted_matches(pseudo_matches)[:10]
            if pseudo_matches:
                client_matches[client] = pseudo_matches
        
        return render_template('match_review.html', client_matches=client_matches, is_preview=True)
    
    @app.route('/matches')
    def matches_list():
        client_filter = request.args.get('client_id', '')
        
        if session.get('role') == 'company':
            # Show only approved matches
            query = Match.query.options(
                joinedload(Match.client),
                joinedload(Match.ground)
            ).join(Client).filter(Client.company_id == session['company_id'], Match.status == 'approved')
            
            if client_filter:
                query = query.filter_by(client_id=int(client_filter))
            
            clients = Client.query.filter_by(company_id=session['company_id']).order_by(Client.name).all()
            client = None
        elif session.get('role') == 'client':
            query = Match.query.options(
                joinedload(Match.client),
                joinedload(Match.ground)
            ).filter_by(client_id=session['client_id'], status='approved')
            clients = []
            client = Client.query.get(session['client_id'])
        else:
            return redirect(url_for('home'))
        
        return render_template('matches_list.html', matches=get_sorted_matches(query.all()), client_filter=client_filter, clients=clients, client=client)

    @app.route('/matches/<int:match_id>/delete', methods=['POST'])
    @requires_company
    def match_delete(match_id):
        """Delete (unapprove) a match"""
        match = Match.query.get_or_404(match_id)
        if not check_client_ownership(match.client):
            flash('Access denied', 'danger')
            return redirect(url_for('matches_list'))
        
        try:
            db.session.delete(match)
            db.session.commit()
            flash('Match removed', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error removing match: {str(e)}', 'danger')
        
        # Preserve client filter if present
        client_filter = request.args.get('client_id')
        if client_filter:
            return redirect(url_for('matches_list', client_id=client_filter))
        return redirect(url_for('matches_list'))
    
    # Note: Status updates are managed via Match Review only; per-match status route removed
    
    @app.route('/match/run', methods=['POST'])
    @requires_company
    def match_run():
        clients = Client.query.filter_by(company_id=session['company_id']).all()
        grounds = Ground.query.all()
        
        # Compute matches in-memory; store in session for review
        computed_matches = []
        
        for client in clients:
            if not client.preferences:
                continue
            
            for ground in grounds:
                # Skip if already approved
                if Match.query.filter_by(client_id=client.id, ground_id=ground.id, status='approved').first():
                    continue
                
                scores = compute_match_scores(ground, client.preferences)
                computed_matches.append({
                    'client_id': client.id,
                    'ground_id': ground.id,
                    'budget_score': scores['budget_score'],
                    'm2_score': scores['m2_score'],
                    'location_score': scores.get('location_score', 0),
                    'type_score': scores.get('type_score', 0),
                })
        
        # Store computed matches in session
        session['computed_matches'] = computed_matches
        flash(f'{len(computed_matches)} potential matches computed. Review and approve below.', 'success')
        return redirect(url_for('match_review'))
    
    @app.route('/scrape', methods=['POST'])
    @requires_company
    def scrape():
        try:
            import scraper
            plots = scraper.scrape_vansweevelt()

            count = 0
            for plot in plots:
                ground = Ground(
                    location=plot.get('location', 'Unknown'),
                    m2=plot.get('m2', 0),
                    budget=plot.get('budget', 0),
                    subdivision_type=normalize_subdivision_type(plot.get('subdivision_type')) or 'development_plot',
                    owner='Vansweevelt'
                )
                db.session.add(ground)
                count += 1

            db.session.commit()

            # Download images for scraped grounds
            saved = 0
            for p in plots:
                q = Ground.query.filter_by(location=p['location'], m2=p['m2'], budget=p['budget']).first()
                if q and download_ground_image(p, q.id):
                    saved += 1

            flash(f'Scraper ran! {count} grounds added. {saved} images downloaded.', 'success')
        except Exception as e:
            flash(f'Scraper error: {str(e)}', 'danger')
        
        return redirect(url_for('grounds_list'))

    @app.route('/grounds/fetch_images', methods=['POST'])
    @requires_company
    def grounds_fetch_images():
        """Fetch images for existing grounds using the scraper's image URLs."""
        try:
            import scraper
            plots = scraper.scrape_vansweevelt()
            saved = 0
            failed = 0

            for p in plots:
                # Match by location + m2 + budget, or fallback to location + m2
                q = Ground.query.filter_by(location=p['location'], m2=p['m2'], budget=p['budget']).first()
                if not q:
                    q = Ground.query.filter_by(location=p['location'], m2=p['m2']).first()
                
                if q:
                    if download_ground_image(p, q.id):
                        saved += 1
                    else:
                        failed += 1

            flash(f'Image fetch complete: {saved} saved, {failed} failed', 'success')
        except Exception as e:
            flash(f'Failed to fetch images: {str(e)}', 'danger')

        return redirect(url_for('grounds_list'))
    
    # ========================================================================
    # AUTHENTICATION & USER MANAGEMENT
    # ========================================================================
    
    @app.route('/logout')
    def logout():
        """Clear session and log out user"""
        session.clear()
        return redirect(url_for('home'))

    @app.route('/company/profile', methods=['GET', 'POST'])
    @requires_company
    def company_profile():
        company = Company.query.get(session['company_id'])
        if request.method == 'POST':
            company.name = request.form['name']
            company.email = request.form['email']
            company.address = request.form.get('address')
            company.phone = request.form.get('phone')
            try:
                db.session.commit()
                flash('Profile updated successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating profile: {str(e)}', 'danger')
                return render_template('company_profile.html', company=company)
            return redirect(url_for('dashboard'))
        return render_template('company_profile.html', company=company)

    @app.route('/client/profile', methods=['GET', 'POST'])
    @requires_client
    def client_profile():
        client = Client.query.get(session['client_id'])
        if request.method == 'POST':
            client.name = request.form['name']
            client.email = request.form['email']
            client.location = request.form.get('location')
            client.address = request.form.get('address')
            client.phone = request.form.get('phone')
            try:
                db.session.commit()
                flash('Profile updated successfully!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating profile: {str(e)}', 'danger')
                return render_template('client_profile.html', client=client)
            return redirect(url_for('client_dashboard'))
        return render_template('client_profile.html', client=client)