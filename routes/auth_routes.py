from flask import Blueprint, request, redirect, url_for, flash, session
from flask import render_template
from flask_mysqldb import MySQL,MySQLdb
from flask_bcrypt import Bcrypt

# Blueprint untuk authentication
auth = Blueprint('auth', __name__)
mysql = None  # Akan kita set dari app utama
bcrypt = Bcrypt()  # Inisialisasi bcrypt

def init_auth(mysql_instance):
    global mysql
    mysql = mysql_instance
@auth.route('/daftar', methods=['POST'])
def daftar():
    peran = request.form['peran']
    email = request.form['email']
    password = request.form['password']

    # Ambil data siswa
    nama_siswa = request.form.get('nama_siswa')
    nis = request.form.get('nis')
    jurusan = request.form.get('jurusan')
    kelas = request.form.get('kelas')

    # Ambil data mitra
    nama_perusahaan = request.form.get('nama_perusahaan')
    institusi = request.form.get('institusi')
    alamat = request.form.get('alamat')
    no_hp = request.form.get('no_hp')

    # Validasi umum
    if not peran or not email or not password:
        flash('Semua field wajib diisi!', 'danger')
        return redirect(url_for('index'))

    # Validasi khusus siswa
    if peran == 'siswa':
        if not nama_siswa or not nis or not jurusan or not kelas:
            flash('Nama siswa, NIS, jurusan, dan kelas wajib diisi!', 'danger')
            return redirect(url_for('index'))

    # Validasi khusus mitra
    if peran == 'mitra':
        if not nama_perusahaan or not institusi or not alamat or not no_hp:
            flash('Nama perusahaan, institusi, alamat, dan no HP wajib diisi!', 'danger')
            return redirect(url_for('index'))

    # Cek apakah email sudah terdaftar
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM siswa WHERE email = %s", (email,))
    siswa_exists = cursor.fetchone()
    cursor.execute("SELECT * FROM mitra WHERE email = %s", (email,))
    mitra_exists = cursor.fetchone()
    cursor.close()

    if siswa_exists or mitra_exists:
        flash('Email sudah terdaftar! Silakan gunakan email lain.', 'danger')
        return redirect(url_for('index'))

    # Enkripsi password
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    cursor = mysql.connection.cursor()

    if peran == 'siswa':
        cursor.execute(
            "INSERT INTO siswa (nama_siswa, nis, jurusan, kelas, email, password) VALUES (%s, %s, %s, %s, %s, %s)",
            (nama_siswa, nis, jurusan, kelas, email, hashed_password)
        )
    elif peran == 'mitra':
        cursor.execute(
            "INSERT INTO mitra (nama_perusahaan, institusi, alamat, no_hp, email, password) VALUES (%s, %s, %s, %s, %s, %s)",
            (nama_perusahaan, institusi, alamat, no_hp, email, hashed_password)
        )
    else:
        flash('Peran tidak valid!', 'danger')
        return redirect(url_for('index'))

    mysql.connection.commit()
    cursor.close()
    flash('Pendaftaran berhasil! Silakan login.', 'success')
    return redirect(url_for('index'))

@auth.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    # Validasi input
    if not email or not password:
        flash('Email dan password wajib diisi!', 'danger')
        return redirect(url_for('index'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Cek apakah email terdaftar di siswa
    cursor.execute("SELECT * FROM siswa WHERE email = %s", (email,))
    siswa = cursor.fetchone()

    # Cek apakah email terdaftar di mitra
    cursor.execute("SELECT * FROM mitra WHERE email = %s", (email,))
    mitra = cursor.fetchone()

    # Cek apakah email terdaftar di admin
    cursor.execute("SELECT * FROM admin WHERE email = %s", (email,))
    admin = cursor.fetchone()
    cursor.close()

    # Jika tidak ada data siswa, mitra, atau admin
    if not siswa and not mitra and not admin:
        flash('Email tidak terdaftar!', 'danger')
        return redirect(url_for('index'))

    # Cek password
    if siswa and bcrypt.check_password_hash(siswa['password'], password):  # Menggunakan nama kolom 'password'
        session['user_id'] = siswa['id']  # simpan id siswa ke session
        session['role'] = 'siswa'  # role siswa
        return redirect(url_for('index'))
    
    elif mitra and bcrypt.check_password_hash(mitra['password'], password):  # Menggunakan nama kolom 'password'
        session['user_id'] = mitra['id']  # simpan id mitra ke session
        session['role'] = 'mitra'  # role mitra
        return redirect(url_for('mitra'))  # arahkan ke halaman mitra
    
    elif admin and bcrypt.check_password_hash(admin['password'], password):  # Menggunakan nama kolom 'password'
        session['user_id'] = admin['id']  # simpan id admin ke session
        session['role'] = 'admin'  # role admin
        return redirect(url_for('admin'))  # arahkan ke halaman admin
    
    else:
        flash('Password salah!', 'danger')
        return redirect(url_for('index'))
    


@auth.route('/logout')
def logout():
    session.pop('user_id', None)  # Hapus user_id dari session
    session.pop('role', None)      # Hapus role dari session
    return redirect(url_for('index'))  # Redirect ke halaman utama



