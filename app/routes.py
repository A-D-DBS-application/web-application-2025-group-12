# app/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_, func, cast
from . import db
from .models import Ground, Company, Match, Client, Preferences


SAMPLE_CLIENTS = [
    {
        "id": "sample-client-1",
        "name": "Jan Peeters",
        "email": "jan.peeters@email.be",
        "address": "Grote Markt 15, 2000 Antwerpen",
        "match_count": 2,
        "active_matches": 1,
        "preferences": {
            "location": "Antwerpen",
            "subdivision_type": "Residential",
            "soil": "Clay",
            "min_m2": 400,
            "max_m2": 500,
            "min_budget": 300000,
            "max_budget": 400000,
        },
    },
    {
        "id": "sample-client-2",
        "name": "Emma Vandenberghe",
        "email": "emma.vandenberghe@email.be",
        "address": "Kerkstraat 45, 9000 Gent",
        "match_count": 1,
        "active_matches": 1,
        "preferences": {
            "location": "Gent",
            "subdivision_type": "Residential",
            "soil": "Sand",
            "min_m2": 550,
            "max_m2": 650,
            "min_budget": 400000,
            "max_budget": 520000,
        },
    },
    {
        "id": "sample-client-3",
        "name": "Pieter De Smet",
        "email": "pieter.desmet@email.be",
        "address": "Meir 78, 2000 Antwerpen",
        "match_count": 1,
        "active_matches": 0,
        "preferences": {
            "location": "Brussel",
            "subdivision_type": "Mixed-Use",
            "soil": "Loam",
            "min_m2": 350,
            "max_m2": 450,
            "min_budget": 250000,
            "max_budget": 360000,
        },
    },
]

SAMPLE_GROUNDS = [
    {
        "id": "sample-ground-1",
        "location": "Antwerpen Noord",
        "m2": 450,
        "subdivision_type": "Residential",
        "soil": "Clay",
        "owner": "Stad Antwerpen",
        "budget": 350000,
    },
    {
        "id": "sample-ground-2",
        "location": "Gent Oost",
        "m2": 600,
        "subdivision_type": "Residential",
        "soil": "Sand",
        "owner": "Private Developer",
        "budget": 425000,
    },
    {
        "id": "sample-ground-3",
        "location": "Brussel Zuid",
        "m2": 380,
        "subdivision_type": "Mixed-Use",
        "soil": "Loam",
        "owner": "Ontwikkelaar XY",
        "budget": 290000,
    },
]

SAMPLE_MATCHES = [
    {
        "id": "sample-match-1",
        "client": SAMPLE_CLIENTS[0],
        "ground": SAMPLE_GROUNDS[0],
        "status": "accepted",
        "m2_score": 95,
        "budget_score": 88,
        "total_score": 92,
        "preferences": {"client": SAMPLE_CLIENTS[0]},
    },
    {
        "id": "sample-match-2",
        "client": SAMPLE_CLIENTS[1],
        "ground": SAMPLE_GROUNDS[1],
        "status": "in progress",
        "m2_score": 90,
        "budget_score": 85,
        "total_score": 88,
        "preferences": {"client": SAMPLE_CLIENTS[1]},
    },
    {
        "id": "sample-match-3",
        "client": SAMPLE_CLIENTS[2],
        "ground": SAMPLE_GROUNDS[2],
        "status": "pending",
        "m2_score": 82,
        "budget_score": 88,
        "total_score": 85,
        "preferences": {"client": SAMPLE_CLIENTS[2]},
    },
]

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
    if current_user.is_authenticated:
        clients = (
            Client.query.filter_by(company_id=current_user.id)
            .order_by(Client.name.asc())
            .all()
        )
        grounds = Ground.query.order_by(Ground.id.desc()).all()
        matches = (
            Match.query.filter_by(company_id=current_user.id)
            .order_by(Match.id.desc())
            .all()
        )

        clients_sample = not bool(clients)
        grounds_sample = not bool(grounds)
        matches_sample = not bool(matches)

        clients = clients or SAMPLE_CLIENTS
        grounds = grounds or SAMPLE_GROUNDS
        matches = matches or SAMPLE_MATCHES

        def status_lookup(match):
            if isinstance(match, dict):
                return (match.get("status") or "pending").lower()
            return (match.status or "pending").lower()

        active_statuses = {"accepted", "matched", "won", "contacted", "shortlisted"}
        pending_statuses = {"pending", "new", "review", "reviewing", "in progress"}

        total_clients = len(clients)
        total_plots = len(grounds)
        active_matches = sum(1 for m in matches if status_lookup(m) in active_statuses)
        pending_matches = sum(1 for m in matches if status_lookup(m) in pending_statuses)

        def match_total(match):
            if isinstance(match, dict):
                return match.get("total_score")
            return match.total_score

        score_values = [match_total(m) for m in matches if match_total(m) is not None]
        avg_match_score = f"{(sum(score_values) / len(score_values)):.0f}%" if score_values else "0%"

        decision_matches = [m for m in matches if status_lookup(m) in {"accepted", "rejected"}]
        success_rate = (
            f"{(sum(1 for m in decision_matches if status_lookup(m) == 'accepted') / len(decision_matches)) * 100:.0f}%"
            if decision_matches
            else "0%"
        )
        pending_reviews = sum(1 for m in matches if status_lookup(m) in {"pending", "review", "reviewing"})

        recent_matches = matches[:5]

        return render_template(
            "home.html",
            company=current_user,
            clients=clients,
            grounds=grounds,
            matches=matches,
            recent_matches=recent_matches,
            total_clients=total_clients,
            total_plots=total_plots,
            active_matches=active_matches,
            pending_matches=pending_matches,
            avg_match_score=avg_match_score,
            success_rate=success_rate,
            pending_reviews=pending_reviews,
            sample_dashboard=clients_sample or grounds_sample or matches_sample,
        )

    auth_mode = request.args.get("mode", "register")
    if auth_mode not in {"register", "login"}:
        auth_mode = "register"
    return render_template("index.html", auth_mode=auth_mode)

@bp.route("/clients")
@login_required
def manage_clients():
    search = request.args.get("q", "").strip()
    query = Client.query.filter_by(company_id=current_user.id)
    if search:
        like_pattern = f"%{search}%"
        query = query.filter(or_(Client.name.ilike(like_pattern), Client.email.ilike(like_pattern)))
    clients = query.order_by(Client.name.asc()).all()

    match_counts = dict(
        db.session.query(Client.id, func.count(Match.id))
        .outerjoin(Preferences, Preferences.client_id == Client.id)
        .outerjoin(Match, Match.preferences_id == Preferences.id)
        .filter(Client.company_id == current_user.id)
        .group_by(Client.id)
        .all()
    )

    active_statuses = ["accepted", "in progress", "contacted"]

    active_counts = dict(
        db.session.query(Client.id, func.count(Match.id))
        .join(Preferences, Preferences.id == Match.preferences_id)
        .join(Client, Client.id == Preferences.client_id)
        .filter(
            Client.company_id == current_user.id,
            func.lower(cast(Match.status, db.Text)).in_(active_statuses),
        )
        .group_by(Client.id)
        .all()
    )

    for client in clients:
        client.match_count = match_counts.get(client.id, 0)
        client.active_matches = active_counts.get(client.id, 0)

    sample_clients = not bool(clients)
    if sample_clients:
        clients = [dict(client, matches=[{"status": "accepted"}] * client["match_count"]) for client in SAMPLE_CLIENTS]

    return render_template("clients.html", clients=clients, search=search, sample_clients=sample_clients)

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

    return render_template("clients/form.html", client=None, sample_mode=False)

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

    return render_template("clients/form.html", client=client, sample_mode=False)

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

    return render_template("preferences.html", client=client, pref=None, clients=[client], preferences_readonly=False, selected_client_id=str(client.id))

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

    return render_template("preferences.html", client=client, pref=preferences, clients=[client], preferences_readonly=False, selected_client_id=str(client.id))


@bp.route("/clients/<int:client_id>/preferences/delete", methods=["POST"])
@login_required
def delete_preferences(client_id):
    client = Client.query.get_or_404(client_id)

    if client.company_id != current_user.id:
        flash("You do not have access to this client", "error")
        return redirect(url_for("main.manage_clients"))

    preferences = client.preferences
    if not preferences:
        flash("No preferences to delete.", "info")
        return redirect(url_for("main.manage_clients"))

    db.session.delete(preferences)
    db.session.commit()
    flash("Preferences removed for this client.", "success")
    return redirect(url_for("main.preferences_dashboard", client_id=client.id))


@bp.route("/preferences", methods=["GET", "POST"])
@login_required
def preferences_dashboard():
    clients = (
        Client.query.filter_by(company_id=current_user.id)
        .order_by(Client.name.asc())
        .all()
    )

    has_real_clients = bool(clients)
    clients = clients or SAMPLE_CLIENTS

    selected_client_id = request.values.get("client_id")
    client = None
    pref = None

    def find_sample_client(cid):
        return next((c for c in clients if str(c.get("id")) == str(cid)), None)

    if request.method == "POST":
        selected_client_id = request.form.get("client_id")

    if selected_client_id:
        if has_real_clients:
            try:
                selected_int = int(selected_client_id)
            except (TypeError, ValueError):
                selected_int = None

            if selected_int:
                client = Client.query.filter_by(id=selected_int, company_id=current_user.id).first()
                if not client:
                    flash("Client not found.", "error")
                    return redirect(url_for("main.preferences_dashboard"))
                pref = client.preferences
        else:
            client = find_sample_client(selected_client_id)
            if client:
                pref = client.get("preferences")

    if request.method == "POST":
        if not selected_client_id:
            flash("Select a client first.", "error")
            return redirect(url_for("main.preferences_dashboard"))

        if not has_real_clients:
            flash("Add a client before saving real preferences.", "info")
            return redirect(url_for("main.preferences_dashboard"))

        if not client:
            flash("Client not found.", "error")
            return redirect(url_for("main.preferences_dashboard"))

        if not pref:
            pref = Preferences(client=client)

        pref.location = request.form.get("location") or None
        pref.soil = request.form.get("soil") or None
        pref.subdivision_type = request.form.get("subdivision_type") or None
        pref.min_m2 = request.form.get("min_m2") or None
        pref.max_m2 = request.form.get("max_m2") or None
        pref.min_budget = request.form.get("min_budget") or None
        pref.max_budget = request.form.get("max_budget") or None

        db.session.add(pref)
        db.session.commit()

        flash("Preferences saved.", "success")
        return redirect(url_for("main.preferences_dashboard", client_id=client.id))

    return render_template(
        "preferences.html",
        clients=clients,
        pref=pref,
        client=client,
        preferences_readonly=not has_real_clients,
        selected_client_id=str(selected_client_id) if selected_client_id else "",
    )

@bp.route("/matches")
@login_required
def view_matches():
    client_id = request.args.get("client_id", type=int)
    status_filter = request.args.get("status", "").lower()
    search = request.args.get("q", "").strip()

    query = (
        Match.query.filter_by(company_id=current_user.id)
        .outerjoin(Preferences, Match.preferences_id == Preferences.id)
        .outerjoin(Client, Client.id == Preferences.client_id)
        .outerjoin(Ground, Ground.id == Match.ground_id)
    )

    if client_id:
        query = query.filter(Client.id == client_id)

    if status_filter:
        query = query.filter(func.lower(Match.status) == status_filter)

    if search:
        like_pattern = f"%{search}%"
        query = query.filter(or_(Client.name.ilike(like_pattern), Ground.location.ilike(like_pattern)))

    matches = query.order_by(Match.total_score.desc().nullslast(), Match.id.desc()).all()

    clients = (
        Client.query.filter_by(company_id=current_user.id)
        .order_by(Client.name.asc())
        .all()
    )

    sample_matches = not bool(matches)
    sample_clients = not bool(clients)

    matches = matches or SAMPLE_MATCHES
    clients = clients or SAMPLE_CLIENTS

    return render_template(
        "matches.html",
        matches=matches,
        clients=clients,
        sample_matches=sample_matches,
        filters_disabled=sample_clients,
    )

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


@bp.route("/plots")
@login_required
def view_plots():
    query = Ground.query

    search = request.args.get("q", "").strip()
    if search:
        like_pattern = f"%{search}%"
        query = query.filter(or_(Ground.location.ilike(like_pattern), Ground.owner.ilike(like_pattern)))

    location_filter = request.args.get("location")
    if location_filter:
        query = query.filter(Ground.location == location_filter)

    type_filter = request.args.get("type")
    if type_filter:
        query = query.filter(Ground.subdivision_type == type_filter)

    soil_filter = request.args.get("soil")
    if soil_filter:
        query = query.filter(Ground.soil == soil_filter)

    grounds = query.order_by(Ground.id.desc()).all()

    location_rows = db.session.query(Ground.location).distinct().all()
    locations = sorted({row[0] for row in location_rows if row[0]})

    type_rows = db.session.query(Ground.subdivision_type).distinct().all()
    subdivision_types = sorted({row[0] for row in type_rows if row[0]})

    soil_rows = db.session.query(Ground.soil).distinct().all()
    soils = sorted({row[0] for row in soil_rows if row[0]})

    sample_plots = not bool(grounds)
    if sample_plots:
        grounds = SAMPLE_GROUNDS
        locations = sorted({ground["location"] for ground in SAMPLE_GROUNDS})
        subdivision_types = sorted({ground["subdivision_type"] for ground in SAMPLE_GROUNDS})
        soils = sorted({ground["soil"] for ground in SAMPLE_GROUNDS})

    return render_template(
        "plots.html",
        grounds=grounds,
        locations=locations,
        subdivision_types=subdivision_types,
        soils=soils,
        sample_plots=sample_plots,
    )


@bp.route("/my-company")
@login_required
def my_company():
    return redirect(url_for("main.view_plots"))


@bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    edit_mode = request.args.get("mode") == "edit"

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()

        if not name or not email:
            flash("Name and email are required.", "error")
            return redirect(url_for("main.profile", mode="edit"))

        current_user.name = name
        current_user.email = email
        db.session.commit()

        flash("Profile updated.", "success")
        return redirect(url_for("main.profile"))

    return render_template("profile.html", company=current_user, edit_mode=edit_mode)

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
