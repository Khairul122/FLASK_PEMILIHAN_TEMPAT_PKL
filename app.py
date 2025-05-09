from flask import Flask, render_template,session,redirect, url_for, flash
from flask_mysqldb import MySQL,MySQLdb
from config import Config  # Mengimpor konfigurasi
from routes.auth_routes import auth, init_auth
from routes.profil_routes import profil, init_profil
from routes.mitra_routes.tempat_pkl_routes import tempat_pkl, init_tempat_pkl
from routes.admin_routes.tempat_pkl_admin_routes import data_tempat_pkl_view, init_data_tempat_pkl_view
from routes.siswa_routes.tempat_pkl_siswa_routes import tempat_pkl_siswa_routes, init_tempat_pkl_siswa_routes
from routes.mitra_routes.lamaran_mitra_routes import lamaran_pkl_mitra, init_lamaran_pkl_mitra
from routes.siswa_routes.riwayat_lamaran_siswa_routes import riwayat_lamaran_siswa_routes, init_riwayat_lamaran_siswa_routes
from routes.admin_routes.data_siswa_mitra_routes import data_siswa_mitra, init_data_siswa_mitra


from functools import wraps



app = Flask(__name__)


app.secret_key = 'rahasia123'
# Menggunakan konfigurasi dari file config.py
app.config.from_object(Config)

# Inisialisasi koneksi MySQL
mysql = MySQL(app)

init_auth(mysql)
# Register Blueprint
app.register_blueprint(auth)

init_profil(mysql)
# Register Blueprint
app.register_blueprint(profil)

init_tempat_pkl(mysql)
app.register_blueprint(tempat_pkl)

init_data_tempat_pkl_view(mysql)
app.register_blueprint(data_tempat_pkl_view)


# Di bawah init koneksi MySQL
init_tempat_pkl_siswa_routes(mysql)
app.register_blueprint(tempat_pkl_siswa_routes)


# Register Blueprint untuk lamaran pkl
init_lamaran_pkl_mitra(mysql)
app.register_blueprint(lamaran_pkl_mitra)


# Register Blueprint untuk lamaran pkl
init_riwayat_lamaran_siswa_routes(mysql)
app.register_blueprint(riwayat_lamaran_siswa_routes)


init_data_siswa_mitra(mysql)
app.register_blueprint(data_siswa_mitra)

#routuntuk mengatasi antar login
def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session:
                flash('Silakan login terlebih dahulu.', 'warning')
                return redirect(url_for('index'))
            
            user_role = session['role']
            if user_role not in allowed_roles:
                # flash('Kamu tidak memiliki akses ke halaman ini.', 'danger')
                # Redirect sesuai role
                if user_role == 'admin':
                    return redirect(url_for('admin'))
                elif user_role == 'mitra':
                    return redirect(url_for('mitra'))
                elif user_role == 'siswa':
                    return redirect(url_for('index'))
                else:
                    return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@app.route('/')

def index():
    return render_template('index.html')


@app.route('/pilih-pkl')
# @role_required(['siswa'])
def pilih_pkl():
    return render_template('pilih_pkl.html')



@app.route('/kegiatanku')
# @role_required(['siswa'])
def kegiatanku():
    return render_template('kegiatanku.html')


@app.route('/detail-tempat-pkl')
# @role_required(['siswa'])
def detail_tempat_pkl():
    return render_template('detail_tempat_pkl.html')


@app.route('/admin')
@role_required(['admin'])
def admin():
    return render_template('admin/admin.html')

@app.route('/tempat-pkl-admin')
@role_required(['admin'])
def tempat_pkl_admin():
    return render_template('admin/tempat_pkl_admin.html')

@app.route('/lamaran')
@role_required(['admin'])
def lamaran():
    return render_template('admin/lamaran.html')

@app.route("/data-siswa")
@role_required(['admin'])
def data_siswa():
    return render_template("admin/data_siswa.html")
@app.route("/data-mitra")
@role_required(['admin'])
def data_mitra():
    return render_template("admin/data_mitra.html")

@app.route("/profil-admin")
@role_required(['admin'])
def profil_admin():
    return render_template("admin/profil_admin.html")

@app.route("/edit-profil-admin")
@role_required(['admin'])
def edit_profil_admin():
    return render_template("admin/edit_profil_admin.html")

@app.route("/tambah-tempat-pkl-admin")
@role_required(['admin'])
def tambah_tempat_pkl_admin():
    return render_template("admin/tambah_tempat_pkl_admin.html")

@app.route("/siswa-pkl")
@role_required(['admin'])
def siswa_pkl():
    return render_template("admin/siswa_pkl.html")

@app.route("/siswa-selesai-pkl")
@role_required(['admin'])
def siswa_selesai_pkl():
    return render_template("admin/siswa_selesai_pkl.html")


@app.route("/mitra")
@role_required(['mitra'])
def mitra():
    return render_template("mitra/mitra.html")


@app.route('/tempat-pkl-mitra')
@role_required(['mitra'])
def tempat_pkl_mitra():
    return render_template('mitra/tempat_pkl_mitra.html')



@app.route('/lamaran-mitra')
@role_required(['mitra'])
def lamaran_mitra():
    return render_template('mitra/lamaran_mitra.html')


@app.route('/siswa-pkl-mitra')
@role_required(['mitra'])
def siswa_pkl_mitra():
    return render_template('mitra/siswa_pkl_mitra.html')

@app.route("/tambah-tempat-pkl-mitra")
@role_required(['mitra'])
def tambah_tempat_pkl_mitra():
    return render_template("mitra/tambah_tempat_pkl_mitra.html")

@app.route("/edit-tempat-pkl-mitra")
@role_required(['mitra'])
def edit_tempat_pkl_mitra():
    return render_template("mitra/edit_tempat_pkl_mitra.html")

@app.route("/profil-mitra")
@role_required(['mitra'])
def profil_mitra():
    return render_template("mitra/profil_mitra.html")


@app.route("/edit-profil-mitra")
@role_required(['mitra'])
def edit_profil_mitra():
    return render_template("mitra/edit_profil_mitra.html")



@app.context_processor
def inject_user():
    if 'user_id' in session:
        user_id = session['user_id']
        role = session.get('role', '')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        if role == 'siswa':
            cursor.execute("SELECT * FROM siswa WHERE id = %s", (user_id,))
        elif role == 'mitra':
            cursor.execute("SELECT * FROM mitra WHERE id = %s", (user_id,))
        else:
            cursor.execute("SELECT * FROM admin WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        return dict(user=user)
    return dict(user=None)


if __name__ == '__main__':
    app.run(debug=True)
