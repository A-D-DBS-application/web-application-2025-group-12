# app/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from . import db
from .models import Ground, Company, Match, Client, Preferences

bp = Blueprint("main", __name__)

@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    if request.method == "POST":
        company_name = request.form.get("company_name")
        company = Company.query.filter_by(name=company_name).first()

        if company:
            login_user(company)
            flash("Successfully logged in!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("main.home"))
        
        flash("Company name not found", "error")
    
    return render_template("auth/login.html")

@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email", "")  # Email is now optional

        if not name:
            flash("Company name is required", "error")
            return redirect(url_for("main.register"))

        if Company.query.filter_by(name=name).first():
            flash("This company name is already registered", "error")
            return redirect(url_for("main.register"))

        try:
            company = Company(name=name, email=email)
            db.session.add(company)
            db.session.commit()
            login_user(company)
            flash("Account successfully created!", "success")
            return redirect(url_for("main.home"))
        except Exception as e:
            db.session.rollback()
            flash("An error occurred while creating your account. Please try again.", "error")
            return redirect(url_for("main.register"))

    return render_template("auth/register.html")

@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out", "info")
    return redirect(url_for("main.home"))

@bp.route("/")
def home():
    # order by id desc (schema doesn't define a created_at column)
    grounds = Ground.query.order_by(Ground.id.desc()).all()
    return render_template("index.html", grounds=grounds)

@bp.route("/clients")
@login_required
def manage_clients():
    clients = current_user.clients
    return render_template("clients/list.html", clients=clients)

@bp.route("/clients/new", methods=["GET", "POST"])
@login_required
def create_client():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        address = request.form.get("address")

        if not all([name, email, address]):
            flash("All fields are required", "error")
            return redirect(url_for("main.create_client"))

        # Check if email is already used
        if Client.query.filter_by(email=email).first():
            flash("This email address is already registered", "error")
            return redirect(url_for("main.create_client"))

        client = Client(
            company=current_user,
            name=name,
            email=email,
            address=address
        )
        db.session.add(client)
        db.session.commit()

        flash("Client added successfully!", "success")
        return redirect(url_for("main.manage_clients"))

    return render_template("clients/form.html", client=None)

@bp.route("/clients/<int:client_id>/edit", methods=["GET", "POST"])
@login_required
def edit_client(client_id):
    client = Client.query.get_or_404(client_id)
    
    # Security check
    if client.company_id != current_user.id:
        flash("You do not have access to this client", "error")
        return redirect(url_for("main.manage_clients"))

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        address = request.form.get("address")

        if not all([name, email, address]):
            flash("All fields are required", "error")
            return redirect(url_for("main.edit_client", client_id=client.id))

        # Check if email is already used by another client
        existing_client = Client.query.filter_by(email=email).first()
        if existing_client and existing_client.id != client.id:
            flash("This email address is already registered", "error")
            return redirect(url_for("main.edit_client", client_id=client.id))

        client.name = name
        client.email = email
        client.address = address
        db.session.commit()

        flash("Client updated successfully!", "success")
        return redirect(url_for("main.manage_clients"))

    return render_template("clients/form.html", client=client)

@bp.route("/clients/<int:client_id>/delete", methods=["POST"])
@login_required
def delete_client(client_id):
    client = Client.query.get_or_404(client_id)
    
    # Security check
    if client.company_id != current_user.id:
        flash("You do not have access to this client", "error")
        return redirect(url_for("main.manage_clients"))

    db.session.delete(client)
    db.session.commit()

    flash("Client deleted successfully!", "success")
    return redirect(url_for("main.manage_clients"))

@bp.route("/clients/<int:client_id>/preferences/new", methods=["GET", "POST"])
@login_required
def create_preferences(client_id):
    client = Client.query.get_or_404(client_id)
    
    # Security check
    if client.company_id != current_user.id:
        flash("You do not have access to this client", "error")
        return redirect(url_for("main.manage_clients"))

    if client.preferences:
        flash("This client already has preferences", "error")
        return redirect(url_for("main.manage_clients"))

    if request.method == "POST":
        preferences = Preferences(
            client=client,
            location=request.form.get("location"),
            soil=request.form.get("soil"),
            subdivision_type=request.form.get("subdivision_type"),
            min_m2=request.form.get("min_m2") or None,
            max_m2=request.form.get("max_m2") or None,
            min_budget=request.form.get("min_budget") or None,
            max_budget=request.form.get("max_budget") or None
        )
        db.session.add(preferences)
        db.session.commit()

        flash("Preferences added successfully!", "success")
        return redirect(url_for("main.manage_clients"))

    return render_template("clients/preferences.html", client=client, preferences=None)

@bp.route("/clients/<int:client_id>/preferences/edit", methods=["GET", "POST"])
@login_required
def edit_preferences(client_id):
    client = Client.query.get_or_404(client_id)
    
    # Security check
    if client.company_id != current_user.id:
        flash("You do not have access to this client", "error")
        return redirect(url_for("main.manage_clients"))

    preferences = client.preferences
    if not preferences:
        flash("This client has no preferences yet", "error")
        return redirect(url_for("main.manage_clients"))

    if request.method == "POST":
        preferences.location = request.form.get("location")
        preferences.soil = request.form.get("soil")
        preferences.subdivision_type = request.form.get("subdivision_type")
        preferences.min_m2 = request.form.get("min_m2") or None
        preferences.max_m2 = request.form.get("max_m2") or None
        preferences.min_budget = request.form.get("min_budget") or None
        preferences.max_budget = request.form.get("max_budget") or None
        
        db.session.commit()

        flash("Preferences updated successfully!", "success")
        return redirect(url_for("main.manage_clients"))

    return render_template("clients/preferences.html", client=client, preferences=preferences)

@bp.route("/matches")
@login_required
def view_matches():
    # Get filter parameters
    client_id = request.args.get("client_id", type=int)
    min_score = request.args.get("min_score", type=float)
    
    # Base query
    query = Match.query.filter_by(company_id=current_user.id)
    
    # Apply filters
    if client_id:
        query = query.join(Preferences).join(Client).filter(Client.id == client_id)
    
    if min_score is not None:
        query = query.filter(Match.total_score >= min_score)
    
    # Order by score descending
    matches = query.order_by(Match.total_score.desc()).all()
    
    # Get all clients for the filter dropdown
    clients = current_user.clients
    
    return render_template("matches.html", matches=matches, clients=clients)

@bp.route("/matches/generate")
@login_required
def generate_matches():
    from .services import generate_matches_for_company
    
    # Generate new matches
    new_matches = generate_matches_for_company(current_user)
    
    if new_matches:
        flash(f"{len(new_matches)} new matches found!", "success")
    else:
        flash("No new matches found.", "info")
    
    return redirect(url_for("main.view_matches"))

@bp.route("/matches/<int:match_id>/status", methods=["POST"])
@login_required
def update_match_status(match_id):
    match = Match.query.get_or_404(match_id)
    
    # Security check
    if match.company_id != current_user.id:
        flash("You do not have access to this match", "error")
        return redirect(url_for("main.view_matches"))
    
    status = request.form.get("status")
    if status in ["pending", "accepted", "rejected"]:
        match.status = status
        db.session.commit()
        flash("Match status updated", "success")
    
    return redirect(url_for("main.view_matches"))

@bp.route("/grounds/new", methods=["GET", "POST"])
@login_required
def create_ground():
    if request.method == "POST":
        # fields matching DB schema: location, m2, budget, subdivision_type, owner, soil
        location = request.form.get("location", "").strip()
        m2 = request.form.get("m2", "").strip()
        budget = request.form.get("budget", "").strip()
        subdivision_type = request.form.get("subdivision_type", "").strip() or "unknown"
        owner = request.form.get("owner", "").strip() or ""
        soil = request.form.get("soil", "").strip() or "unknown"

        if not location or not m2 or not budget:
            flash("Please provide location, area (m2) and budget.", "error")
            return redirect(url_for("main.create_ground"))

        try:
            m2_val = int(m2)
            budget_val = float(budget)
        except ValueError:
            flash("Area and budget must be numeric.", "error")
            return redirect(url_for("main.create_ground"))

        ground = Ground(
            location=location,
            m2=m2_val,
            budget=budget_val,
            subdivision_type=subdivision_type,
            owner=owner,
            soil=soil,
        )
        db.session.add(ground)
        db.session.commit()
        flash("Ground added!", "success")
        return redirect(url_for("main.home"))

    return render_template("new_listing.html")

@bp.route("/my-company")
@login_required
def my_company():
    company_grounds = (
        Ground.query.join(Match)
        .filter(Match.company_id == current_user.id)
        # Ground model does not have created_at in the current schema — order by id instead
        .order_by(Ground.id.desc())
        .all()
    )
    return render_template("my_listings.html", grounds=company_grounds, company=current_user)
