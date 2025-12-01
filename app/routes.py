from flask import render_template, request, redirect, url_for, flash, session
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
    @requires_company
    def preferences_list():
        company_id = session['company_id']
        clients = Client.query.filter_by(company_id=company_id).all()
        client_ids = [c.id for c in clients]
        preferences = Preferences.query.filter(Preferences.client_id.in_(client_ids)).all() if client_ids else []
        
        # Add client info to each preference
        for pref in preferences:
            pref.client = Client.query.get(pref.client_id)
        
        return render_template('preferences_list.html', preferences=preferences)
    
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
            flash(f'Scraper ran! {count} grounds added.', 'success')
        except Exception as e:
            flash(f'Scraper error: {str(e)}', 'danger')
        
        return redirect(url_for('grounds_list'))
    
    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('home'))
