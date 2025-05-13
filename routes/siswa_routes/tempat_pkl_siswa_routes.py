from flask import Blueprint, render_template, session, flash, redirect, url_for, request
from flask import current_app as app
from flask_mysqldb import MySQLdb
from werkzeug.utils import secure_filename
from datetime import datetime
import os

tempat_pkl_siswa_routes = Blueprint('tempat_pkl_siswa_routes', __name__)

def init_tempat_pkl_siswa_routes(mysql):
    global db
    db = mysql

@tempat_pkl_siswa_routes.route('/')
def temapt_pkl_scrolbar():
    cursor = db.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM tempat_pkl")
    data_tempat_pkl = cursor.fetchall()
    cursor.close()
    return render_template('index.html', data_tempat_pkl=data_tempat_pkl)

@tempat_pkl_siswa_routes.route('/detail-tempat-pkl/<int:id>')
def detail_tempat_pkl(id):
    cursor = db.connection.cursor(MySQLdb.cursors.DictCursor)
    query = """
    SELECT t.*, m.nama_perusahaan
    FROM tempat_pkl t
    LEFT JOIN mitra m ON t.mitra_id = m.id
    WHERE t.id = %s
    """
    cursor.execute(query, (id,))
    data_tempat_pkl = cursor.fetchone()
    cursor.close()
    return render_template('detail_tempat_pkl.html', data_tempat_pkl=data_tempat_pkl)

@tempat_pkl_siswa_routes.route('/ajukan-lamaran/<int:tempat_id>', methods=['POST'])
def ajukan_lamaran(tempat_id):
    if 'role' not in session or session['role'] != 'siswa':
        flash('Akses ditolak!', 'danger')
        return redirect(url_for('auth.login'))

    siswa_id = session.get('user_id')

    surat_pengantar = request.files.get('surat_pengantar')
    cv = request.files.get('cv')
    kartu_pelajar = request.files.get('kartu_pelajar')

    if not (surat_pengantar and cv and kartu_pelajar):
        flash("Semua file wajib diupload!", "danger")
        return redirect(request.referrer)

    uploads_path = os.path.join('static', 'dokumen')
    os.makedirs(uploads_path, exist_ok=True)

    surat_filename = secure_filename(surat_pengantar.filename)
    cv_filename = secure_filename(cv.filename)
    kartu_filename = secure_filename(kartu_pelajar.filename)

    surat_pengantar.save(os.path.join(uploads_path, surat_filename))
    cv.save(os.path.join(uploads_path, cv_filename))
    kartu_pelajar.save(os.path.join(uploads_path, kartu_filename))

    cursor = db.connection.cursor()
    insert_query = """
    INSERT INTO lamaran_pkl (siswa_id, tempat_pkl_id, surat_pengantar, cv, kartu_pelajar, tanggal_lamaran, status)
    VALUES (%s, %s, %s, %s, %s, %s, 'Menunggu')
    """
    cursor.execute(insert_query, (
        siswa_id,
        tempat_id,
        surat_filename,
        cv_filename,
        kartu_filename,
        datetime.now()
    ))
    db.connection.commit()
    cursor.close()

    flash("Lamaran berhasil diajukan!", "success")
    return redirect(url_for('riwayat_lamaran_siswa_routes.kegiatanku'))
@tempat_pkl_siswa_routes.route('/pilih-pkl', methods=['POST'])
def tampilkan_input_user():
    bidang_user = request.form.get('bidang_keahlian', '').strip().lower()
    durasi_user = request.form.get('durasi_pkl', '').strip().lower()
    fasilitas_level_user = request.form.get('fasilitas_level', '').strip().lower()
    kuota_user = request.form.get('kuota', '').strip().lower()
    jarak_user = request.form.get('jarak', '').strip().lower()

    print("\n=== INPUT YANG DIISI USER ===")
    print(f"Bidang Keahlian  : {bidang_user}")
    print(f"Durasi PKL       : {durasi_user}")
    print(f"Fasilitas Level  : {fasilitas_level_user}")
    print(f"Kuota            : {kuota_user}")
    print(f"Jarak            : {jarak_user}")
    print("================================\n")

    cursor = db.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM tempat_pkl")
    hasil_tempat = cursor.fetchall()
    cursor.close()

    bobot = {
        'bidang': 0.3,
        'durasi': 0.15,
        'fasilitas': 0.2,
        'kuota': 0.15,
        'jarak': 0.2
    }

    durasi_map = {'pendek': 1, 'sedang': 2, 'panjang': 3}
    fasilitas_map = {'kurang': 1, 'cukup': 2, 'lengkap': 3, 'sangat lengkap': 4}
    kuota_map = {'sedikit': 1, 'sedang': 2, 'banyak': 3}
    jarak_map = {'dekat': 1, 'sedang': 2, 'jauh': 3}

    for tempat in hasil_tempat:
        cocok_bidang = 1 if bidang_user == tempat['bidang_pekerjaan'].lower() else 0
        cocok_durasi = 1 if durasi_user == tempat['label_durasi'].lower() else 0
        cocok_fasilitas = 1 if fasilitas_level_user == tempat['label_fasilitas'].lower() else 0
        cocok_kuota = 1 if kuota_user == tempat['label_kuota'].lower() else 0
        cocok_jarak = 1 if jarak_user == tempat['label_jarak'].lower() else 0

        skor_kbrs = (
            bobot['bidang'] * cocok_bidang +
            bobot['durasi'] * cocok_durasi +
            bobot['fasilitas'] * cocok_fasilitas +
            bobot['kuota'] * cocok_kuota +
            bobot['jarak'] * cocok_jarak
        )

        sim_bidang = 1.0 if cocok_bidang else 0.0
        diff_durasi = abs(durasi_map.get(durasi_user, 0) - durasi_map.get(tempat['label_durasi'].lower(), 0))
        diff_fasilitas = abs(fasilitas_map.get(fasilitas_level_user, 0) - fasilitas_map.get(tempat['label_fasilitas'].lower(), 0))
        diff_kuota = abs(kuota_map.get(kuota_user, 0) - kuota_map.get(tempat['label_kuota'].lower(), 0))
        diff_jarak = abs(jarak_map.get(jarak_user, 0) - jarak_map.get(tempat['label_jarak'].lower(), 0))

        sim_durasi = max(0, 1 - 0.5 * diff_durasi)
        sim_fasilitas = max(0, 1 - 0.5 * diff_fasilitas)
        sim_kuota = max(0, 1 - 0.5 * diff_kuota)
        sim_jarak = max(0, 1 - 0.25 * diff_jarak)

        mu_tinggi = (sim_bidang * 0.4 + sim_durasi * 0.15 + sim_fasilitas * 0.2 + sim_kuota * 0.15 + sim_jarak * 0.1)
        mu_sedang = (sim_bidang + sim_durasi + sim_fasilitas + sim_kuota + sim_jarak) / 5
        mu_rendah = 1 - mu_tinggi

        penyebut = mu_rendah + mu_sedang + mu_tinggi
        fuzzy_score = 0 if penyebut == 0 else (
            40 * mu_rendah + 70 * mu_sedang + 100 * mu_tinggi
        ) / penyebut

        hybrid_score = (skor_kbrs + fuzzy_score / 100) / 2

        if hybrid_score >= 0.75:
            label_output = 'Direkomendasikan'
        elif hybrid_score >= 0.60:
            label_output = 'Dipertimbangkan'
        else:
            label_output = 'Tidak Direkomendasikan'

        tempat['skor_kbrs'] = skor_kbrs
        tempat['skor_fuzzy'] = fuzzy_score
        tempat['skor_hybrid'] = hybrid_score
        tempat['label_rekomendasi'] = label_output

        print(f"Tempat: {tempat['nama_tempat']}")
        print(f"Skor KBRS  : {skor_kbrs:.2f}")
        print(f"Skor Fuzzy : {fuzzy_score:.2f}")
        print(f"Skor Hybrid: {hybrid_score:.2f}")
        print(f"Rekomendasi: {label_output}")
        print("-------------------------------------------")

    hasil_tempat_sorted = sorted(hasil_tempat, key=lambda x: x['skor_hybrid'], reverse=True)
    flash('Perhitungan KBRS + Fuzzy Mamdani selesai', 'info')
    return render_template('pilih_pkl.html', data_tempat_pkl=hasil_tempat_sorted)