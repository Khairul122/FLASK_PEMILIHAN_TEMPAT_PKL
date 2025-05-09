from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from flask_mysqldb import MySQL, MySQLdb
import os

tempat_pkl = Blueprint('tempat_pkl', __name__)
mysql = None

def init_tempat_pkl(mysql_instance):
    global mysql
    mysql = mysql_instance



@tempat_pkl.route('/tambah-tempat-pkl', methods=['GET', 'POST'])
def tambah_tempat_pkl():
    # Cek apakah user adalah mitra
    if session.get('role') != 'mitra':
        flash('Anda tidak memiliki akses.', 'danger')
        return redirect(url_for('index'))

    mitra_id = session.get('user_id')  # ID mitra dari session
    
    if request.method == 'POST':
        foto = request.files['foto']
        nama_tempat = request.form['nama_tempat']
        institusi = request.form['institusi']
        bidang_pekerjaan = request.form.getlist('bidang_pekerjaan')
        fasilitas = request.form.getlist('fasilitas')
        durasi = request.form['durasi']
        kuota = request.form['kuota']
        alamat = request.form['alamat']
        deskripsi = request.form['deskripsi']

        print(fasilitas)

        # Simpan file foto
        filename = secure_filename(foto.filename)
        foto_path = os.path.join('static/img', filename)
        foto.save(foto_path)

        # Gabung bidang dan fasilitas ke string
        bidang_str = ', '.join(bidang_pekerjaan)
        fasilitas_str = ', '.join(fasilitas)

        # Simpan ke database
        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO tempat_pkl (foto, nama_tempat, institusi, bidang_pekerjaan, fasilitas, durasi, kuota, alamat, deskripsi, mitra_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (filename, nama_tempat, institusi, bidang_str, fasilitas_str, durasi, kuota, alamat, deskripsi, mitra_id))
        mysql.connection.commit()
        cursor.close()

        flash('Tempat PKL berhasil ditambahkan!', 'success')
        return redirect(url_for('tempat_pkl.tempat_pkl_mitra'))

      



@tempat_pkl.route('/tempat-pkl-mitra')
def tempat_pkl_mitra():
    if session.get('role') != 'mitra':
        flash('Anda tidak memiliki akses ke halaman ini.', 'danger')
        return redirect(url_for('auth.login'))

    mitra_id = session.get('user_id')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)  # <- ini bagian penting
    cursor.execute("SELECT * FROM tempat_pkl WHERE mitra_id = %s", (mitra_id,))
    data_tempat_pkl = cursor.fetchall()
    cursor.close()

    return render_template('mitra/tempat_pkl_mitra.html', data_tempat_pkl=data_tempat_pkl)
   

@tempat_pkl.route('/mitra-yo')
def mitra():
    if session.get('role') != 'mitra':
        flash('Anda tidak memiliki akses ke halaman ini.', 'danger')
        return redirect(url_for('auth.login'))

    mitra_id = session.get('user_id')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)  # <- ini bagian penting
    cursor.execute("SELECT * FROM tempat_pkl WHERE mitra_id = %s", (mitra_id,))
    data_tempat_pkl = cursor.fetchall()
    cursor.close()

    return render_template('mitra/mitra.html', data_tempat_pkl=data_tempat_pkl)



@tempat_pkl.route('/edit-tempat-pkl/<int:id>', methods=['GET','POST'])
def edit_tempat_pkl(id):
    # hanya mitra yang boleh akses
    if session.get('role') != 'mitra':
        flash('Anda tidak memiliki akses.', 'danger')
        return redirect(url_for('index'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == 'POST':
        # 1) ambil data lama
        cursor.execute("SELECT * FROM tempat_pkl WHERE id = %s", (id,))
        old = cursor.fetchone()
        if not old:
            flash('Data tidak ditemukan.', 'danger')
            return redirect(url_for('tempat_pkl.tempat_pkl_mitra'))

        # 2) baca form, fallback ke old jika kosong
        nama_tempat = request.form.get('nama_tempat') or old['nama_tempat']
        institusi   = request.form.get('institusi')   or old['institusi']
        bidang      = request.form.getlist('bidang_pekerjaan')
        fasilitas   = request.form.getlist('fasilitas')
        durasi      = request.form.get('durasi')      or old['durasi']
        kuota       = request.form.get('kuota')       or old['kuota']
        alamat       = request.form.get('alamat')       or old['alamat']
        deskripsi   = request.form.get('deskripsi')       or old['deskripsi']

        bidang_str    = ', '.join(bidang)      if bidang     else old['bidang_pekerjaan']
        fasilitas_str = ', '.join(fasilitas)  if fasilitas  else old['fasilitas']

        # 3) foto baru? kalau tidak, pakai old['foto']
        file = request.files.get('foto')
        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join('static/img', filename))
        else:
            filename = old['foto']

        # 4) eksekusi update
        cursor.execute("""
            UPDATE tempat_pkl SET
              foto=%s,
              nama_tempat=%s,
              institusi=%s,
              bidang_pekerjaan=%s,
              fasilitas=%s,
              durasi=%s,
              kuota=%s,
              alamat=%s,
              deskripsi=%s
            WHERE id=%s
        """, (filename, nama_tempat, institusi,
              bidang_str, fasilitas_str, durasi, kuota, alamat, deskripsi, id))
        mysql.connection.commit()
        cursor.close()

        flash('Data tempat PKL berhasil diperbarui.', 'success')
        return redirect(url_for('tempat_pkl.tempat_pkl_mitra'))

    # ---- kalau GET ----
    cursor.execute("SELECT * FROM tempat_pkl WHERE id = %s", (id,))
    data = cursor.fetchone()
    cursor.close()
    if not data:
        flash('Data tidak ditemukan.', 'danger')
        return redirect(url_for('tempat_pkl.tempat_pkl_mitra'))

    return render_template('mitra/edit_tempat_pkl_mitra.html', data=data)



@tempat_pkl.route('/hapus-tempat-pkl/<int:id>', methods=['POST'])
def hapus_tempat_pkl(id):
    # Pastikan hanya mitra yang boleh menghapus
    if session.get('role') != 'mitra':
        flash('Anda tidak memiliki akses.', 'danger')
        return redirect(url_for('tempat_pkl.tempat_pkl_mitra'))

    mitra_id = session.get('user_id')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Ambil nama file foto (optional: untuk dihapus dari disk)
    cursor.execute("SELECT foto FROM tempat_pkl WHERE id = %s AND mitra_id = %s", (id, mitra_id))
    row = cursor.fetchone()
    if not row:
        cursor.close()
        flash('Data tidak ditemukan atau bukan milik Anda.', 'danger')
        return redirect(url_for('tempat_pkl.tempat_pkl_mitra'))

    foto_filename = row['foto']
    # Hapus record dari database
    cursor.execute("DELETE FROM tempat_pkl WHERE id = %s AND mitra_id = %s", (id, mitra_id))
    mysql.connection.commit()
    cursor.close()

    # Optional: hapus file foto di disk
    try:
        path = os.path.join('static/img', foto_filename)
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass

    flash('Tempat PKL berhasil dihapus.', 'success')
    return redirect(url_for('tempat_pkl.tempat_pkl_mitra'))

