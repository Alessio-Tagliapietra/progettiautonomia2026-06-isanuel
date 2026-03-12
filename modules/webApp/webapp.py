try:
    from flask import (
        Flask, render_template, request, redirect,
        url_for, flash, session, make_response,
    )
    from flask_login import (
        LoginManager, login_user, logout_user,
        login_required, current_user,
    )
    from datetime import date
    from authlib.integrations.flask_client import OAuth
    import secrets

    from modules.webApp.user import User
    from modules.database.database import DatabaseManager
    import modules.webApp.config as config
    import modules.webApp.mqtt_client as mqtt_client
    from modules.webApp.users_db import UsersDatabase


except ImportError as e:
    print(f"Errore import webapp.py: {e}")


app = Flask(__name__, template_folder="templates")
app.secret_key = config.SECRET_KEY
app.config["SESSION_COOKIE_SECURE"]  = False
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_PERMANENT"]       = False

# Database (accesso diretto)
db = DatabaseManager(config.DATABASE_PATH)

users_db = UsersDatabase(config.USERS_DATABASE_PATH)
users_db.seed(config.SEED_AUTHORIZED_USERS) 

# Login manager
login_manager = LoginManager()
login_manager.login_view = "login_page"
login_manager.init_app(app)

# OAuth
oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=config.GOOGLE_CLIENT_ID,
    client_secret=config.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


# ── Auth ───────────────────────────────────────────────────────────────────

@app.route("/login")
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    return render_template("login.html")


@app.route("/auth/google")
def google_login():
    redirect_uri = url_for("callback", _external=True)
    session["nonce"] = secrets.token_urlsafe(16)
    return google.authorize_redirect(redirect_uri, nonce=session["nonce"])


@app.route("/callback")
def callback():
    try:
        token     = google.authorize_access_token()
        user_info = google.parse_id_token(token, nonce=session["nonce"])
        email     = user_info.get("email", "").lower().strip()

        if not users_db.is_authorized(email): #controlla all'interno del databsae
            flash("Non sei autorizzato ad accedere.", "danger")
            return redirect(url_for("login_page"))

        login_user(User(email), remember=False)
        session["user_email"] = email
        session["user_name"]  = user_info.get("name", email)
        flash(f"Benvenuto {user_info.get('name', email)}!", "success")
        return redirect(url_for("index"))

    except Exception as e:
        print(f"Errore OAuth callback: {e}")
        flash("Errore durante l'autenticazione.", "danger")
        return redirect(url_for("login_page"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    resp = make_response(redirect(url_for("login_page")))
    resp.set_cookie("remember_token", "", expires=0, max_age=0)
    flash("Logout effettuato con successo.", "info")
    return resp


# ── Routes principali ──────────────────────────────────────────────────────

@app.route("/")
@login_required
def index():
    stats = {
        "total_plates": len(db.get_all_plates()),
        "recent_logs":  db.get_access_history(limit=10),
    }
    return render_template("index.html", stats=stats)


@app.route("/plates")
@login_required
def plates():
    return render_template("plates.html", plates=db.get_all_plates())


@app.route("/add_plate", methods=["GET", "POST"])
@login_required
def add_plate():
    if request.method == "POST":
        plate      = request.form["plate_number"].strip().upper()
        first_name = request.form["first_name"]
        last_name  = request.form["last_name"]
        role       = request.form["role"]
        expiration = request.form["expiration_date"]

        if not plate or len(plate) < 6:
            flash("Numero targa non valido!", "danger")
            return render_template("add_plate.html")

        try:
            result = db.add_authorized_plate(plate, first_name, last_name, role, expiration)
            if result:
                mqtt_client.publish_plates_update("add", plate)   # notifica altri moduli
                flash(f"Targa {plate} aggiunta con successo!", "success")
            else:
                flash(f"Targa {plate} già esistente!", "warning")
            return redirect(url_for("plates"))
        except Exception as e:
            flash(f"Errore: {str(e)}", "danger")

    return render_template("add_plate.html")


@app.route("/edit_plate/<plate_number>", methods=["GET", "POST"])
@login_required
def edit_plate(plate_number):
    plate = db.get_plate(plate_number)
    if not plate:
        flash("Targa non trovata!", "danger")
        return redirect(url_for("plates"))

    if request.method == "POST":
        try:
            db.update_plate(
                plate_number,
                request.form["first_name"],
                request.form["last_name"],
                request.form["role"],
                request.form["expiration_date"],
            )
            mqtt_client.publish_plates_update("update", plate_number)
            flash("Targa aggiornata con successo!", "success")
            return redirect(url_for("plates"))
        except Exception as e:
            flash(f"Errore: {str(e)}", "danger")

    return render_template("edit_plate.html", plate=plate)


@app.route("/delete_plate/<plate_number>", methods=["POST"])
@login_required
def delete_plate(plate_number):
    try:
        db.remove_plate(plate_number)
        mqtt_client.publish_plates_update("remove", plate_number)
        flash(f"Targa {plate_number} rimossa!", "warning")
    except Exception as e:
        flash(f"Errore: {str(e)}", "danger")
    return redirect(url_for("plates"))


# ── Logs ────────────────────────────────────

@app.route("/logs")
@login_required
def logs():
    today = date.today().isoformat()
    selected_date = request.args.get("selected_date", today).strip() or today
    all_logs = db.get_access_history(date=selected_date, status="authorized")
    return render_template("logs.html", logs=all_logs, selected_date=selected_date, today=today)


@app.route("/logs/storico")
@login_required
def logs_storico():
    today = date.today().isoformat()
    filters = {
        "plate_number": request.args.get("plate_number", "").strip().upper(),
        "first_name":   request.args.get("first_name", "").strip(),
        "last_name":    request.args.get("last_name", "").strip(),
        "role":         request.args.get("role", "").strip(),
        "status":       request.args.get("status", "").strip(),
        "date_single":  request.args.get("date_single", "").strip(),
        "date_from":    request.args.get("date_from", "").strip(),
        "date_to":      request.args.get("date_to", "").strip(),
        "limit":        request.args.get("limit", "100").strip(),
    }
    limit_val = int(filters["limit"]) if filters["limit"].isdigit() else 100
    all_logs = db.get_access_history_advanced(
        **{k: v or None for k, v in filters.items() if k != "limit"},
        limit=limit_val,
    )
    return render_template("logs_storico.html", logs=all_logs, filters=filters, today=today)


@app.route("/logs/storico/delete", methods=["POST"])
@login_required
def delete_selected_logs():
    try:
        log_ids = [int(i) for i in request.form.getlist("log_ids") if i.isdigit()]
        if not log_ids:
            flash("Nessun log selezionato.", "warning")
        else:
            deleted = db.delete_logs_by_ids(log_ids)
            flash(f"Eliminati {deleted} log.", "success")
    except Exception as e:
        flash(f"Errore: {str(e)}", "danger")
    return redirect(url_for("logs_storico"))


@app.route("/logs/storico/export")
@login_required
def export_logs_filtered():
    try:
        from datetime import datetime as dt
        from flask import send_file
        import tempfile, os, csv

        filters = {
            "plate_number": request.args.get("plate_number", "").strip().upper(),
            "first_name":   request.args.get("first_name", "").strip(),
            "last_name":    request.args.get("last_name", "").strip(),
            "role":         request.args.get("role", "").strip(),
            "status":       request.args.get("status", "").strip(),
            "date_single":  request.args.get("date_single", "").strip(),
            "date_from":    request.args.get("date_from", "").strip(),
            "date_to":      request.args.get("date_to", "").strip(),
        }
        all_logs = db.get_access_history_advanced(
            **{k: v or None for k, v in filters.items()}, limit=0
        )
        if not all_logs:
            flash("Nessun log da esportare.", "warning")
            return redirect(url_for("logs_storico"))

        filename = f"storico_{dt.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(tempfile.gettempdir(), filename)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID","Targa","Data e Ora","Stato","Evento","Nome","Cognome","Ruolo"])
            for row in all_logs:
                writer.writerow([row["id"], row["plate_number"], row["timestamp"],
                                  row["status"], row.get("event",""),
                                  row.get("first_name",""), row.get("last_name",""), row.get("role","")])
        return send_file(filepath, mimetype="text/csv", as_attachment=True, download_name=filename)

    except Exception as e:
        flash(f"Errore esportazione: {str(e)}", "danger")
        return redirect(url_for("logs_storico"))


@app.route("/logs/analytics")
@login_required
def logs_analytics():
    from datetime import timedelta
    today         = date.today().isoformat()
    default_start = (date.today() - timedelta(days=6)).isoformat()
    start_date    = request.args.get("start_date", default_start).strip()
    end_date      = request.args.get("end_date", today).strip()

    dati_stato      = db.get_accessi_per_stato(start_date, end_date)
    kpi_ev          = db.get_kpi_entrate_uscite(start_date, end_date)

    kpi = {
        "total":          sum(dati_stato.values()),
        **dati_stato,
        "entrate":        kpi_ev.get("entrate", 0),
        "uscite":         kpi_ev.get("uscite", 0),
        "presenti":       kpi_ev.get("presenti", 0),
    }

    return render_template(
        "logs_analytics.html",
        start_date=start_date, end_date=end_date, today=today, kpi=kpi,
        dati_per_giorno=db.get_accessi_per_giorno(start_date, end_date),
        dati_stato=dati_stato,
        dati_orario=db.get_accessi_per_ora(start_date, end_date),
        dati_top_targhe=db.get_top_targhe(start_date, end_date, limit=10),
        dati_trend=db.get_trend_per_stato(start_date, end_date),
        dati_distrib_ev=db.get_distribuzione_entrate_uscite(start_date, end_date),
        dati_flusso_ore=db.get_flusso_orario_entrate_uscite(start_date, end_date),
        dati_saldo=db.get_saldo_giornaliero(start_date, end_date),
    )

# ── Users ────────────────────────────────────

@app.route("/users")
@login_required
def users_list():
    return render_template("users.html", users=users_db.get_all())


@app.route("/users/add", methods=["POST"])
@login_required
def user_add():
    email = request.form.get("email", "").strip().lower()
    note  = request.form.get("note", "").strip()

    if not email or "@" not in email:
        flash("Email non valida.", "danger")
        return redirect(url_for("users_list"))

    if users_db.add(email, note):
        flash(f"Utente {email} aggiunto.", "success")
    else:
        flash(f"L'email {email} è già autorizzata.", "warning")
    return redirect(url_for("users_list"))


@app.route("/users/delete/<path:email>", methods=["POST"])
@login_required
def user_delete(email):
    if email.lower() == session.get("user_email", "").lower():
        flash("Non puoi rimuovere te stesso!", "danger")
        return redirect(url_for("users_list"))

    if users_db.remove(email):
        flash(f"Utente {email} rimosso.", "warning")
    else:
        flash("Utente non trovato.", "danger")
    return redirect(url_for("users_list"))


@app.route("/users/edit/<path:email>", methods=["POST"])
@login_required
def user_edit_note(email):
    note = request.form.get("note", "").strip()
    users_db.update_note(email, note)
    flash("Nota aggiornata.", "success")
    return redirect(url_for("users_list"))

# ── Entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mqtt_client.start()
    app.run(debug=True, use_reloader=False)
