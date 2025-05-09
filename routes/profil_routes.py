from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from flask_mysqldb import MySQL, MySQLdb
from werkzeug.utils import secure_filename
import os

profil = Blueprint('profil', __name__)
mysql = None

def init_profil(mysql_instance):
    global mysql
    mysql = mysql_instance

UPLOAD_FOLDER = 'static/img'  # Pastikan folder ini ada
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@profil.route('/profil_siswa')
def profil_siswa():
    if 'user_id' in session and session.get('role') == 'siswa':
        user_id = session['user_id']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM siswa WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        return render_template('index.html', user=user)
    return redirect(url_for('auth.login'))


@profil.route('/edit_profil_siswa', methods=['POST'])
def edit_profil_siswa():
    if 'user_id' in session and session.get('role') == 'siswa':
        user_id = session['user_id']

        # Ambil data lama dari database
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM siswa WHERE id = %s", (user_id,))
        old_data = cursor.fetchone()

        # Ambil data baru dari form, tapi fallback ke data lama jika kosong
        nama = request.form.get('nama') or old_data['nama_siswa']
        nis = request.form.get('nis') or old_data['nis']
        jurusan = request.form.get('jurusan') or old_data['jurusan']
        kelas = request.form.get('kelas') or old_data['kelas']
        email = request.form.get('email') or old_data['email']
        nohp = request.form.get('nohp') or old_data['no_hp']

        # Handle foto
        foto = request.files.get('fotoProfil')
        foto_filename = old_data['foto']  # default ke yang lama

        if foto and allowed_file(foto.filename):
            foto_filename = secure_filename(foto.filename)
            foto.save(os.path.join(UPLOAD_FOLDER, foto_filename))

        # Update data siswa
        cursor = mysql.connection.cursor()
        cursor.execute("""
            UPDATE siswa SET nama_siswa=%s, nis=%s, jurusan=%s, kelas=%s, email=%s, no_hp=%s, foto=%s WHERE id=%s
        """, (nama, nis, jurusan, kelas, email, nohp, foto_filename, user_id))

        mysql.connection.commit()
        cursor.close()
        flash('Profil berhasil diperbarui.', 'success')
        return redirect(url_for('profil.profil_siswa'))

    flash('Akses ditolak.', 'danger')
    return redirect(url_for('auth.login'))


@profil.route('/profil_admin')
def profil_admin():
    if 'user_id' in session and session.get('role') == 'admin':
        user_id = session['user_id']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM admin WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        return render_template('admin/profil_admin.html', user=user)
    return redirect(url_for('auth.login'))


@profil.route('/edit_profil_admin', methods=['POST'])
def edit_profil_admin():
    if 'user_id' in session and session.get('role') == 'admin':
        user_id = session['user_id']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM admin WHERE id = %s", (user_id,))
        old_data = cursor.fetchone()

        nama = request.form.get('nama') or old_data['nama']
        email = request.form.get('email') or old_data['email']
        no_hp = request.form.get('no_hp') or old_data['no_hp']

        foto = request.files.get('foto')
        foto_filename = old_data['foto']

        if foto and allowed_file(foto.filename):
            foto_filename = secure_filename(foto.filename)
            foto.save(os.path.join(UPLOAD_FOLDER, foto_filename))

        cursor = mysql.connection.cursor()
        cursor.execute("""
            UPDATE admin SET nama=%s, email=%s, no_hp=%s, foto=%s WHERE id=%s
        """, (nama, email, no_hp, foto_filename, user_id))
        mysql.connection.commit()
        cursor.close()

        flash('Profil admin berhasil diperbarui.', 'success')
        return redirect(url_for('profil.profil_admin'))
    

    flash('Akses ditolak.', 'danger')
    return redirect(url_for('auth.login'))




@profil.route('/profil_mitra')
def profil_mitra():
    if 'user_id' in session and session.get('role') == 'mitra':
        user_id = session['user_id']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM mitra WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        return render_template('mitra/profil_mitra.html', user=user)
    return redirect(url_for('auth.login'))





@profil.route('/edit_profil_mitra', methods=['POST'])
def edit_profil_mitra():
    if 'user_id' in session and session.get('role') == 'mitra':
        user_id = session['user_id']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM mitra WHERE id = %s", (user_id,))
        old_data = cursor.fetchone()

        nama_perusahaan = request.form.get('nama_perusahaan') or old_data['nama_perusahaan']
        institusi = request.form.get('institusi') or old_data['institusi']
        alamat = request.form.get('alamat') or old_data['alamat']
        no_hp = request.form.get('no_hp') or old_data['no_hp']
        email = request.form.get('email') or old_data['email']

        foto = request.files.get('foto')
        foto_filename = old_data['foto']

        if foto and allowed_file(foto.filename):
            foto_filename = secure_filename(foto.filename)
            foto.save(os.path.join(UPLOAD_FOLDER, foto_filename))

        cursor = mysql.connection.cursor()
        cursor.execute("""
            UPDATE mitra 
            SET nama_perusahaan=%s, institusi=%s, alamat=%s, email=%s, no_hp=%s, foto=%s 
            WHERE id=%s
        """, (nama_perusahaan, institusi, alamat, email, no_hp, foto_filename, user_id))

        mysql.connection.commit()
        cursor.close()

        flash('Profil mitra berhasil diperbarui.', 'success')
        return redirect(url_for('profil.profil_mitra'))

    flash('Akses ditolak.', 'danger')
    return redirect(url_for('auth.login'))



