from flask import render_template, request, redirect, url_for, flash, session, Response, send_file
import os
from .models import db, Company, Client, Ground, Preferences, Match
from .matching import compute_match_scores
from functools import wraps

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

def init_routes(app):
    
    @app.route('/')
    def home():
        return render_template('home.html')
    
    @app.route('/company/register', methods=['GET', 'POST'])
    def company_register():
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            
            # Basic validation
            if not name or not email:
                flash('Name and email are required', 'danger')
                return render_template('company_register.html')
            
            # Check for duplicate email
            existing = Company.query.filter_by(email=email).first()
            if existing:
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
        
        return render_template('company_register.html')
    
    @app.route('/company/login', methods=['GET', 'POST'])
    def company_login():
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
    
    @app.route('/dashboard')
    @requires_company
    def dashboard():
        company_id = session['company_id']
        clients = Client.query.filter_by(company_id=company_id).all()
        grounds = Ground.query.all()
        # Get all matches for clients of this company
        matches = Match.query.join(Client).filter(Client.company_id == company_id).all()
        
        return render_template('dashboard.html', 
                             clients=clients, 
                             grounds=grounds, 
                             matches=matches)
    
    @app.route('/client/dashboard')
    @requires_client
    def client_dashboard():
        client_id = session['client_id']
        client = Client.query.get(client_id)
        preferences = client.preferences
        
        # Get matches for this client (directly via relationship)
        matches = client.matches
        # Sort by total score (highest first) - total_score is computed column
        matches = sorted(matches, key=lambda m: m.total_score or 0, reverse=True)
        
        return render_template('client_dashboard.html',
                             client=client,
                             preferences=preferences,
                             matches=matches)
    
    @app.route('/clients')
    @requires_company
    def clients_list():
        company_id = session['company_id']
        search = request.args.get('search', '')
        
        query = Client.query.filter_by(company_id=company_id)
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
            address = request.form.get('address', '').strip()
            
            # Basic validation
            if not name or not email:
                flash('Name and email are required', 'danger')
                return render_template('client_form.html', client=None)
            
            # Check for duplicate email
            existing = Client.query.filter_by(email=email).first()
            if existing:
                flash('Email already exists', 'danger')
                return render_template('client_form.html', client=None)
            
            try:
                client = Client(
                    company_id=session['company_id'],
                    name=name,
                    email=email,
                    address=address
                )
                db.session.add(client)
                db.session.commit()
                
                flash('Client added!', 'success')
                return redirect(url_for('clients_list'))
            except Exception as e:
                db.session.rollback()
                flash(f'Failed to add client: {str(e)}', 'danger')
                return render_template('client_form.html', client=None)
        
        return render_template('client_form.html', client=None)
    
    @app.route('/clients/<int:client_id>/edit', methods=['GET', 'POST'])
    @requires_company
    def client_edit(client_id):
        client = Client.query.get_or_404(client_id)
        
        # Check authorization
        if client.company_id != session['company_id']:
            flash('Access denied', 'danger')
            return redirect(url_for('clients_list'))
        
        if request.method == 'POST':
            client.name = request.form.get('name')
            client.email = request.form.get('email')
            client.address = request.form.get('address', '')
            db.session.commit()
            
            flash('Client updated!', 'success')
            return redirect(url_for('clients_list'))
        
        return render_template('client_form.html', client=client)
    
    @app.route('/clients/<int:client_id>/delete', methods=['POST'])
    @requires_company
    def client_delete(client_id):
        client = Client.query.get_or_404(client_id)
        
        # Check authorization
        if client.company_id != session['company_id']:
            flash('Access denied', 'danger')
            return redirect(url_for('clients_list'))
        
        db.session.delete(client)
        db.session.commit()
        
        flash('Client deleted!', 'success')
        return redirect(url_for('clients_list'))
    
    @app.route('/grounds')
    @requires_company
    def grounds_list():
        location = request.args.get('location', '')
        min_price = request.args.get('min_price', '')
        max_price = request.args.get('max_price', '')
        min_m2 = request.args.get('min_m2', '')
        max_m2 = request.args.get('max_m2', '')
        subdivision_type = request.args.get('subdivision_type', '')
        
        query = Ground.query
        
        if location:
            query = query.filter(Ground.location.ilike(f'%{location}%'))
        if min_price:
            query = query.filter(Ground.budget >= float(min_price))
        if max_price:
            query = query.filter(Ground.budget <= float(max_price))
        if min_m2:
            query = query.filter(Ground.m2 >= int(min_m2))
        if max_m2:
            query = query.filter(Ground.m2 <= int(max_m2))
        if subdivision_type:
            query = query.filter(Ground.subdivision_type.ilike(f'%{subdivision_type}%'))
        
        grounds = query.all()
        return render_template('grounds_list.html', grounds=grounds)

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
                m2 = int(request.form.get('m2', 0))
                budget = float(request.form.get('budget', 0))
                subdivision_type = request.form.get('subdivision_type', '').strip()
                owner = request.form.get('owner', '').strip()
                
                # Validation
                if not location or not subdivision_type or not owner:
                    flash('Location, type and owner are required', 'danger')
                    return render_template('ground_form.html', ground=None)
                
                if m2 <= 0:
                    flash('Size must be positive', 'danger')
                    return render_template('ground_form.html', ground=None)
                
                if budget <= 0:
                    flash('Budget must be positive', 'danger')
                    return render_template('ground_form.html', ground=None)
                
                ground = Ground(
                    location=location,
                    m2=m2,
                    budget=budget,
                    subdivision_type=subdivision_type,
                    owner=owner
                )
                db.session.add(ground)
                db.session.commit()
                
                flash('Ground added!', 'success')
                return redirect(url_for('grounds_list'))
            except ValueError:
                flash('Invalid number format', 'danger')
                return render_template('ground_form.html', ground=None)
            except Exception as e:
                db.session.rollback()
                flash(f'Failed to add ground: {str(e)}', 'danger')
                return render_template('ground_form.html', ground=None)
        
        return render_template('ground_form.html', ground=None)
    
    @app.route('/grounds/<int:ground_id>')
    def ground_detail(ground_id):
        ground = Ground.query.get_or_404(ground_id)
        return render_template('ground_detail.html', ground=ground)
    
    @app.route('/grounds/<int:ground_id>/edit', methods=['GET', 'POST'])
    @requires_company
    def ground_edit(ground_id):
        ground = Ground.query.get_or_404(ground_id)
        
        if request.method == 'POST':
            ground.location = request.form.get('location')
            ground.m2 = int(request.form.get('m2'))
            ground.budget = float(request.form.get('budget'))
            ground.subdivision_type = request.form.get('subdivision_type')
            ground.owner = request.form.get('owner')
            db.session.commit()
            
            flash('Ground updated!', 'success')
            return redirect(url_for('grounds_list'))
        
        return render_template('ground_form.html', ground=ground)
    
    @app.route('/grounds/<int:ground_id>/delete', methods=['POST'])
    @requires_company
    def ground_delete(ground_id):
        ground = Ground.query.get_or_404(ground_id)
        db.session.delete(ground)
        db.session.commit()
        
        flash('Ground deleted!', 'success')
        return redirect(url_for('grounds_list'))
    
    @app.route('/preferences')
    def preferences_list():
        # Handle both company and client roles
        print(f"DEBUG: /preferences accessed - role: {session.get('role')}, client_id: {session.get('client_id')}, company_id: {session.get('company_id')}")
        if session.get('role') == 'company':
            print("DEBUG: Company user - showing preferences list")
            company_id = session['company_id']
            clients = Client.query.filter_by(company_id=company_id).all()
            client_ids = [c.id for c in clients]
            preferences = Preferences.query.filter(Preferences.client_id.in_(client_ids)).all() if client_ids else []
            
            # Add client info to each preference
            for pref in preferences:
                pref.client = Client.query.get(pref.client_id)
            
            return render_template('preferences_list.html', preferences=preferences)
        elif session.get('role') == 'client':
            # Redirect client to their own preferences view
            print("DEBUG: Client user - redirecting to client_preferences_view")
            target_url = url_for('client_preferences_view')
            print(f"DEBUG: Target URL: {target_url}")
            return redirect(target_url)
        else:
            print(f"DEBUG: No role found - redirecting to home")
            flash('Access denied', 'danger')
            return redirect(url_for('home'))
    
    @app.route('/preferences/<int:client_id>', methods=['GET', 'POST'])
    @requires_company
    def preferences_edit(client_id):
        client = Client.query.get_or_404(client_id)
        
        # Check authorization
        if client.company_id != session['company_id']:
            flash('Access denied', 'danger')
            return redirect(url_for('preferences_list'))
        
        pref = Preferences.query.filter_by(client_id=client_id).first()
        
        if not pref:
            pref = Preferences(client_id=client_id)
            db.session.add(pref)
        
        if request.method == 'POST':
            pref.location = request.form.get('location')
            pref.subdivision_type = request.form.get('subdivision_type')
            pref.min_m2 = int(request.form.get('min_m2')) if request.form.get('min_m2') else None
            pref.max_m2 = int(request.form.get('max_m2')) if request.form.get('max_m2') else None
            pref.min_budget = float(request.form.get('min_budget')) if request.form.get('min_budget') else None
            pref.max_budget = float(request.form.get('max_budget')) if request.form.get('max_budget') else None
            
            db.session.commit()
            
            flash('Preferences updated!', 'success')
            return redirect(url_for('preferences_list'))
        
        return render_template('preferences_form.html', client=client, pref=pref)
    
    @app.route('/client/preferences')
    @requires_client
    def client_preferences_view():
        client_id = session['client_id']
        client = Client.query.get(client_id)
        pref = Preferences.query.filter_by(client_id=client_id).first()
        
        return render_template('client_preferences.html', client=client, pref=pref)
    
    @app.route('/client/preferences/edit', methods=['GET', 'POST'])
    @requires_client
    def client_preferences_edit():
        client_id = session['client_id']
        client = Client.query.get(client_id)
        pref = Preferences.query.filter_by(client_id=client_id).first()
        
        if not pref:
            pref = Preferences(client_id=client_id)
            db.session.add(pref)
        
        if request.method == 'POST':
            pref.location = request.form.get('location')
            pref.subdivision_type = request.form.get('subdivision_type')
            pref.min_m2 = int(request.form.get('min_m2')) if request.form.get('min_m2') else None
            pref.max_m2 = int(request.form.get('max_m2')) if request.form.get('max_m2') else None
            pref.min_budget = float(request.form.get('min_budget')) if request.form.get('min_budget') else None
            pref.max_budget = float(request.form.get('max_budget')) if request.form.get('max_budget') else None
            
            db.session.commit()
            
            flash('Preferences updated!', 'success')
            return redirect(url_for('client_dashboard'))
        
        return render_template('client_preferences_form.html', client=client, pref=pref)
    
    @app.route('/matches')
    def matches_list():
        status_filter = request.args.get('status', '')
        
        if session.get('role') == 'company':
            company_id = session['company_id']
            # Get matches via client relationship
            query = Match.query.join(Client).filter(Client.company_id == company_id)
        elif session.get('role') == 'client':
            client_id = session['client_id']
            query = Match.query.filter_by(client_id=client_id)
        else:
            return redirect(url_for('home'))
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        matches = query.all()
        
        # Sort by total score (highest first) - total_score is computed column
        matches = sorted(matches, key=lambda m: m.total_score or 0, reverse=True)
        
        return render_template('matches_list.html', matches=matches, status_filter=status_filter)
    
    @app.route('/matches/<int:match_id>/status', methods=['POST'])
    @requires_company
    def match_update_status(match_id):
        match = Match.query.get_or_404(match_id)
        
        # Check authorization - access company via client
        if match.client.company_id != session['company_id']:
            flash('Access denied', 'danger')
            return redirect(url_for('matches_list'))
        
        new_status = request.form.get('status')
        if new_status in ['pending', 'accepted', 'rejected']:
            match.status = new_status
            db.session.commit()
            flash(f'Match status updated to {new_status}!', 'success')
        
        return redirect(url_for('matches_list'))
    
    @app.route('/match/run', methods=['POST'])
    @requires_company
    def match_run():
        company_id = session['company_id']
        clients = Client.query.filter_by(company_id=company_id).all()
        grounds = Ground.query.all()
        
        count = 0
        for client in clients:
            # Access preferences via client relationship
            pref = client.preferences
            if not pref:
                continue
            
            for ground in grounds:
                # Check if match exists (client_id + ground_id is unique)
                existing = Match.query.filter_by(
                    client_id=client.id,
                    ground_id=ground.id
                ).first()
                
                if existing:
                    continue
                
                scores = compute_match_scores(ground, pref)
                
                match = Match(
                    client_id=client.id,
                    ground_id=ground.id,
                    budget_score=scores['budget_score'],
                    m2_score=scores['m2_score'],
                    status='pending'
                )
                db.session.add(match)
                count += 1
        
        db.session.commit()
        flash(f'{count} matches created!', 'success')
        return redirect(url_for('matches_list'))
    
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
                    subdivision_type=plot.get('subdivision_type', 'Unknown'),
                    owner='Vansweevelt'
                )
                db.session.add(ground)
                count += 1

            db.session.commit()

            # After inserting, attempt to download real images for the newly
            # scraped plots so the UI shows real photos immediately.
            try:
                import requests
                import os
                from urllib.parse import urlparse
                from bs4 import BeautifulSoup

                base_dir = os.path.join(os.path.dirname(__file__), 'static', 'images', 'grounds')
                os.makedirs(base_dir, exist_ok=True)
                saved = 0
                for p in plots:
                    # match inserted ground
                    q = Ground.query.filter_by(location=p['location'], m2=p['m2'], budget=p['budget']).first()
                    if not q:
                        continue

                    img_url = p.get('image_url') or p.get('detail_url')
                    if img_url and 'pixel' in img_url and p.get('detail_url'):
                        try:
                            dresp = requests.get(p['detail_url'], timeout=15)
                            dresp.raise_for_status()
                            dsoup = BeautifulSoup(dresp.text, 'html.parser')
                            candidates = [img.get('src') for img in dsoup.find_all('img') if img.get('src')]
                            picked = None
                            for c in candidates:
                                if c.startswith('http') and ('.jpg' in c or '.png' in c):
                                    picked = c
                                    break
                            if picked:
                                img_url = picked
                        except Exception:
                            pass

                    if not img_url:
                        continue

                    try:
                        resp = requests.get(img_url, timeout=15)
                        resp.raise_for_status()
                        out_path = os.path.join(base_dir, f"{q.id}.jpg")
                        with open(out_path, 'wb') as fh:
                            fh.write(resp.content)
                        saved += 1
                    except Exception:
                        continue

                flash(f'Scraper ran! {count} grounds added. {saved} images downloaded.', 'success')
            except Exception:
                flash(f'Scraper ran! {count} grounds added. Images not downloaded due to an internal error.', 'warning')
        except Exception as e:
            flash(f'Scraper error: {str(e)}', 'danger')
        
        return redirect(url_for('grounds_list'))

    @app.route('/grounds/fetch_images', methods=['POST'])
    @requires_company
    def grounds_fetch_images():
        """Fetch images for existing grounds using the scraper's image URLs.

        The function will call the scraper parser to obtain image URLs and try
        to match each scraped plot to an existing Ground (by location, m2 and
        budget). When matched and an image URL is present, it downloads the
        image and saves it to `app/static/images/grounds/<ground.id>.jpg`.
        """
        try:
            import scraper
            import requests
            import os
            from urllib.parse import urlparse

            plots = scraper.scrape_vansweevelt()
            saved = 0
            failed = 0
            base_dir = os.path.join(os.path.dirname(__file__), 'static', 'images', 'grounds')
            os.makedirs(base_dir, exist_ok=True)

            for p in plots:
                # Simple matching strategy: location + m2 + budget
                q = Ground.query.filter_by(location=p['location'], m2=p['m2'], budget=p['budget']).first()
                if not q:
                    # try looser match on location and m2
                    q = Ground.query.filter_by(location=p['location'], m2=p['m2']).first()
                if not q:
                    continue

                img_url = p.get('image_url') or p.get('detail_url')
                if not img_url:
                    failed += 1
                    continue
                # If the scraped image is a small placeholder, try to get a
                # real image from the detail page.
                try:
                    is_placeholder = False
                    if img_url and 'pixel' in img_url:
                        is_placeholder = True

                    real_img_url = img_url
                    if is_placeholder and p.get('detail_url'):
                        try:
                            dresp = requests.get(p['detail_url'], timeout=15)
                            dresp.raise_for_status()
                            from bs4 import BeautifulSoup
                            dsoup = BeautifulSoup(dresp.text, 'html.parser')
                            # prefer absolute https image URLs
                            candidates = [img.get('src') for img in dsoup.find_all('img') if img.get('src')]
                            # pick first candidate that looks like a real photo
                            picked = None
                            for c in candidates:
                                if c.startswith('http') and ('.jpg' in c or '.png' in c):
                                    picked = c
                                    break
                            if picked:
                                real_img_url = picked
                        except Exception:
                            real_img_url = img_url

                    resp = requests.get(real_img_url, timeout=15)
                    resp.raise_for_status()
                    # determine extension
                    path = urlparse(real_img_url).path
                    ext = os.path.splitext(path)[1] or '.jpg'
                    # normalize to .jpg
                    out_path = os.path.join(base_dir, f"{q.id}.jpg")
                    with open(out_path, 'wb') as fh:
                        fh.write(resp.content)
                    saved += 1
                except Exception:
                    failed += 1

            flash(f'Image fetch complete: {saved} saved, {failed} failed', 'success')
        except Exception as e:
            flash(f'Failed to fetch images: {str(e)}', 'danger')

        return redirect(url_for('grounds_list'))
    
    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('home'))
