try:
    from flask import (
        Flask,
        render_template,
        request,
        redirect,
        url_for,
        flash,
        session,
        make_response,
    )
    from flask_login import (
        LoginManager,
        login_user,
        logout_user,
        login_required,
        current_user,
    )
    from authlib.integrations.flask_client import OAuth
    import requests
    import secrets
    from server.web.user import User
    from server.database import DatabaseManager
    import server.config as config
    from server.connection.frame_receiver import receiver as frame_receiver_blueprint


except ImportError as e:
    print(f"Errore nel caricamento dei moduli in appWeb.py: {e}")


app = Flask(__name__)
app.register_blueprint(frame_receiver_blueprint)
# debug, per vedere se la rotta di
if config.VERBOSE:
    print("\n=== ROUTE REGISTRATE ===")
    for rule in app.url_map.iter_rules():
        print(f"   {rule.endpoint}: {rule.rule} {list(rule.methods)}")
    print("========================\n")


app.secret_key = config.SECRET_KEY
app.config["SESSION_COOKIE_SECURE"] = False  # False per debug
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_PERMANENT"] = False


# Database
db = DatabaseManager(config.DATABASE_PATH)


# login manager
login_manager = LoginManager()
login_manager.login_view = "login_page"
login_manager.init_app(app)

# OAuth setup
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


@app.route("/login")
def login_page():
    if current_user.is_authenticated:
        print("Utente già loggato")
        return redirect(url_for("index"))
    return render_template("login.html")


@app.route("/auth/google")
def google_login():
    redirect_uri = url_for("callback", _external=True)
    session["nonce"] = secrets.token_urlsafe(16)
    print(redirect_uri)
    return google.authorize_redirect(redirect_uri, nonce=session["nonce"])


@app.route("/callback")
def callback():
    try:
        token = google.authorize_access_token()
        user_info = google.parse_id_token(token, nonce=session["nonce"])
        email = user_info.get("email")

        # Controlla se l'email è autorizzata
        if email not in config.AUTHORIZED_USERS:
            flash("Non sei autorizzato ad accedere.", "danger")
            return redirect(url_for("login_page"))

        user = User(email)
        login_user(user, remember=False)
        session["user_email"] = email
        session["user_name"] = user_info.get("name", email)

        flash(f"Benvenuto {email}!", "success")
        return redirect(url_for("index"))

    except Exception as e:
        print(f"Error during OAuth callback: {e}")
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


# ============================================================================
# ROUTES
# ============================================================================
@app.route("/")
@login_required
def index():
    stats = {
        "total_plates": len(db.get_all_plates()),
        "recent_logs": db.get_access_history(limit=10),
    }
    return render_template("index.html", stats=stats)


@app.route("/plates")
@login_required
def plates():
    plates = db.get_all_plates()
    # print (plates)
    return render_template("plates.html", plates=plates)


@app.route("/add_plate", methods=["GET", "POST"])
@login_required
def add_plate():
    if request.method == "POST":
        plate = request.form["plate_number"].strip().upper()
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        role = request.form["role"]
        expiration = request.form["expiration_date"]

        if not plate or len(plate) < 6:
            flash("Numero targa non valido!", "danger")
            return render_template("add_plate.html")

        try:
            result = db.add_authorized_plate(
                plate, first_name, last_name, role, expiration
            )
            if result:
                flash(f"Targa {plate} aggiunta con successo!", "success")
            else:
                flash(f"Targa {plate} già esistente!", "warning")
            return redirect(url_for("plates"))
        except Exception as e:
            flash(f"Errore: {str(e)}", "danger")
            return render_template("add_plate.html")

    return render_template("add_plate.html")


@app.route("/edit_plate/<plate_number>", methods=["GET", "POST"])
@login_required
def edit_plate(plate_number):

    plate = db.get_plate(plate_number)
    if not plate:
        flash("Targa non trovata!", "danger")
        return redirect(url_for("plates"))

    if request.method == "POST":
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        role = request.form["role"]
        expiration = request.form["expiration_date"]
        try:
            db.update_plate(plate_number, first_name, last_name, role, expiration)
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
        flash(f"Targa {plate_number} rimossa!", "warning")
    except Exception as e:
        flash(f"Errore: {str(e)}", "danger")

    return redirect(url_for("plates"))


@app.route("/logs")
@login_required
def logs():

    plate_number = request.args.get("plate_number", "").strip().upper()
    status = request.args.get("status", "")

    all_logs = db.get_access_history(limit=200)

    # Filtri
    if plate_number:
        all_logs = [log for log in all_logs if plate_number in log["plate_number"]]
    if status:
        all_logs = [log for log in all_logs if log["status"] == status]

    return render_template("logs.html", logs=all_logs)


@app.route("/logs/export")
@login_required
def export_logs():
    """Esporta i log in formato CSV"""
    try:
        from datetime import datetime
        from flask import send_file
        import tempfile
        import os

        # Crea nome file con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"access_logs_{timestamp}.csv"

        # Usa directory temporanea del sistema
        temp_dir = tempfile.gettempdir()
        filepath = os.path.join(temp_dir, filename)

        # Esporta i log usando il metodo del database
        if db.export_logs_to_csv(filepath):
            # Invia il file al browser per il download
            return send_file(
                filepath,
                mimetype="text/csv",
                as_attachment=True,
                download_name=filename,
            )
        else:
            flash("Nessun log da esportare", "warning")
            return redirect(url_for("logs"))

    except Exception as e:
        flash(f"Errore durante l'esportazione: {str(e)}", "danger")
        return redirect(url_for("logs"))


@app.route("/logs/clear", methods=["POST"])
@login_required
def clear_logs():
    """Elimina tutti i log di accesso"""
    try:
        if db.clear_access_log():
            flash("Tutti i log sono stati eliminati con successo", "success")
        else:
            flash("Errore durante l'eliminazione dei log", "danger")
    except Exception as e:
        flash(f"Errore: {str(e)}", "danger")

    return redirect(url_for("logs"))


# ====================================
# funzionalità da implementare ancora
# ====================================
@app.route("/service/enable", methods=["POST"])
@login_required
def enable_service():
    try:
        resp = requests.post(
            "http://localhost:5000/api/service/set", json={"enabled": True}
        )
        if resp.ok:
            flash("Servizio attivato!", "success")
        else:
            flash(f"Errore attivando servizio: {resp.text}", "danger")
    except Exception as e:
        flash(f"Errore: {str(e)}", "danger")
    return redirect(url_for("index"))


# @app.route("/service/disable", methods=['POST'])
# @login_required
# def disable_service():
#     try:
#         resp = requests.post("http://localhost:5000/api/service/set", json={"enabled": False})
#         if resp.ok:
#             flash("Servizio disattivato!", "warning")
#         else:
#             flash(f"Errore disattivando servizio: {resp.text}", "danger")
#     except Exception as e:
#         flash(f"Errore: {str(e)}", "danger")
#     return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
