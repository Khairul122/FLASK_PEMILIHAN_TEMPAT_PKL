

from flask import Blueprint, render_template, session, flash, redirect, url_for, request
from flask import current_app as app
from flask_mysqldb import MySQLdb
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import re

tempat_pkl_siswa_routes = Blueprint('tempat_pkl_siswa_routes', __name__)

def init_tempat_pkl_siswa_routes(mysql):
    global db
    db = mysql

    

# @tempat_pkl_siswa_routes.route('/pilih-pkl')
# def tampilkan_tempat_pkl():
#     cursor = db.connection.cursor(MySQLdb.cursors.DictCursor)
#     cursor.execute("SELECT * FROM tempat_pkl")
#     data_tempat_pkl = cursor.fetchall()
#     cursor.close()
#     return render_template('pilih_pkl.html', data_tempat_pkl=data_tempat_pkl)



import re

@tempat_pkl_siswa_routes.route('/pilih-pkl', methods=['GET', 'POST'])
def tampilkan_tempat_pkl():
    cursor = db.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM tempat_pkl")
    semua_tempat = cursor.fetchall()
    cursor.close()

    if request.method == 'POST':
        bidang_user = request.form.get('bidang_keahlian', '').strip().lower()
        durasi_user = int(request.form.get('durasi_pkl')) if request.form.get('durasi_pkl') else 0
        fasilitas_user = [f.strip().lower() for f in request.form.getlist('fasilitas')]
        kuota_user = int(request.form.get('kuota')) if request.form.get('kuota') else 0
        jarak_user = int(request.form.get('jarak')) if request.form.get('jarak') else 0

        bobot = {
            "bidang": 0.3,
            "durasi": 0.15,
            "fasilitas": 0.2,
            "kuota": 0.15,
            "jarak": 0.2,
        }

        hasil_rekomendasi = []

        for tempat in semua_tempat:
            # --- Data Preparation ---
            cocok_bidang = 5 if bidang_user and bidang_user in (tempat.get('bidang_pekerjaan') or '').lower() else 1

            durasi_raw = tempat.get('durasi') or ''
            durasi_tempat = 0
            match = re.search(r'(\d+)\s*x', durasi_raw)
            if match:
                try:
                    durasi_tempat = int(match.group(1))
                except ValueError:
                    durasi_tempat = 0
            durasi_score = 5 if durasi_tempat == durasi_user else 1

            fasilitas_tempat = [f.strip().lower() for f in (tempat.get('fasilitas') or '').split(',')]
            fasilitas_score = len(set(fasilitas_user).intersection(fasilitas_tempat))
            fasilitas_score = min(fasilitas_score, 5)

            try:
                kuota_tempat = int(tempat.get('kuota') or 0)
            except (ValueError, TypeError):
                kuota_tempat = 0
            if kuota_tempat < 5:
                kuota_score = 1
            elif 5 <= kuota_tempat <= 10:
                kuota_score = 3
            else:
                kuota_score = 5

            try:
                jarak_tempat = float(tempat.get('jarak') or 0)
            except (ValueError, TypeError):
                jarak_tempat = 0
            if jarak_tempat <= 1:
                jarak_score = 5
            elif jarak_tempat <= 5:
                jarak_score = 4
            elif jarak_tempat <= 10:
                jarak_score = 3
            else:
                jarak_score = 1

            # --- Fuzzyfikasi ---
            jarak_fuzzy = 'dekat' if jarak_tempat <=1 else 'sedang' if jarak_tempat <=5 else 'jauh'
            kuota_fuzzy = 'sedikit' if kuota_tempat <5 else 'sedang' if kuota_tempat <=10 else 'banyak'
            fasilitas_fuzzy = 'minim' if fasilitas_score <=2 else 'sedang' if fasilitas_score <=4 else 'lengkap'
            durasi_fuzzy = 'pendek' if durasi_tempat <=3 else 'sedang' if durasi_tempat <=5 else 'panjang'

            # --- Aturan & Implikasi (min) ---
            rule_results = []

            if jarak_fuzzy == 'dekat' and kuota_fuzzy == 'banyak':
                rule_results.append(min(5,5))  # sangat tinggi
            if jarak_fuzzy == 'sedang' and kuota_fuzzy == 'sedang':
                rule_results.append(min(4,3))  # tinggi
            if jarak_fuzzy == 'jauh' and kuota_fuzzy == 'sedikit':
                rule_results.append(min(2,1))  # rendah
            if fasilitas_fuzzy == 'lengkap' and durasi_fuzzy == 'panjang':
                rule_results.append(min(5,5))  # sangat tinggi
            if fasilitas_fuzzy == 'sedang' and durasi_fuzzy == 'sedang':
                rule_results.append(min(3,3))  # sedang
            if fasilitas_fuzzy == 'minim' and durasi_fuzzy == 'pendek':
                rule_results.append(min(1,1))  # rendah

            # --- Defuzzyfikasi ---
            fuzzy_numeric = []
            for r in rule_results:
                if r >=5:
                    fuzzy_numeric.append(5)
                elif r >=4:
                    fuzzy_numeric.append(4)
                elif r >=3:
                    fuzzy_numeric.append(3)
                elif r >=2:
                    fuzzy_numeric.append(2)
                else:
                    fuzzy_numeric.append(1)

            if fuzzy_numeric:
                defuzzified_score = sum(fuzzy_numeric) / len(fuzzy_numeric)
            else:
                defuzzified_score = 1  # default rendah

            # --- KBRS Calculation ---
            skor_kbrs = (
                bobot['bidang'] * (cocok_bidang / 5) +
                bobot['durasi'] * (durasi_score / 5) +
                bobot['fasilitas'] * (fasilitas_score / 5) +
                bobot['kuota'] * (kuota_score / 5) +
                bobot['jarak'] * (jarak_score / 5)
            )

            # --- Final Score ---
            total_skor = round((skor_kbrs + (defuzzified_score / 5)) / 2, 4)

            # --- Label ---
            if total_skor >= 0.75:
                rekomendasi_label = "Sangat Rekomendasi"
            elif total_skor >= 0.5:
                rekomendasi_label = "Kurang Rekomendasi"
            else:
                rekomendasi_label = "Tidak Rekomendasi"

            print(f"[{tempat.get('nama_tempat','Unknown')}] KBRS: {skor_kbrs}, Fuzzy: {defuzzified_score}, Total: {total_skor}, Label: {rekomendasi_label}")

            if total_skor > 0:
                tempat['score'] = total_skor
                tempat['rekomendasi'] = rekomendasi_label
                hasil_rekomendasi.append(tempat)

        hasil_rekomendasi.sort(key=lambda x: x['score'], reverse=True)
        return render_template('pilih_pkl.html', data_tempat_pkl=hasil_rekomendasi)

    return render_template('pilih_pkl.html', data_tempat_pkl=semua_tempat)






@tempat_pkl_siswa_routes.route('/')
def temapt_pkl_scrolbar():
    cursor = db.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM tempat_pkl")
    data_tempat_pkl = cursor.fetchall()
    cursor.close()
    return render_template('index.html', data_tempat_pkl=data_tempat_pkl)




# @tempat_pkl_siswa_routes.route('/detail-tempat-pkl/<int:id>')
# def detail_tempat_pkl(id):
#     cursor = db.connection.cursor(MySQLdb.cursors.DictCursor)
#     cursor.execute("SELECT * FROM tempat_pkl WHERE id = %s", (id,))
#     data_tempat_pkl = cursor.fetchone()
#     cursor.close()
#     return render_template('detail_tempat_pkl.html', data_tempat_pkl=data_tempat_pkl)


@tempat_pkl_siswa_routes.route('/detail-tempat-pkl/<int:id>')
def detail_tempat_pkl(id):
    cursor = db.connection.cursor(MySQLdb.cursors.DictCursor)
    # Query join antara tempat_pkl dan mitra untuk mendapatkan nama_perusahaan
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

    # Simpan file
    surat_filename = secure_filename(surat_pengantar.filename)
    cv_filename = secure_filename(cv.filename)
    kartu_filename = secure_filename(kartu_pelajar.filename)

    surat_pengantar.save(os.path.join(uploads_path, surat_filename))
    cv.save(os.path.join(uploads_path, cv_filename))
    kartu_pelajar.save(os.path.join(uploads_path, kartu_filename))

    # Simpan nama file (bukan path lengkap) ke database
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

@tempat_pkl_siswa_routes.route('/rekomendasi-tempat-pkl', methods=['POST'])
def rekomendasi_tempat_pkl():
    cursor = db.connection.cursor(MySQLdb.cursors.DictCursor)

    # Ambil data dari form
    institusi = request.form.get('institusi')
    bidang = request.form.get('bidang_pekerjaan')
    fasilitas = request.form.getlist('fasilitas')  # list
    durasi = request.form.get('durasi')
    kuota = request.form.get('kuota')

    def kuota_to_category(kuota_angka):
        kuota_angka = int(kuota_angka)
        if kuota_angka < 5:
            return "sedikit"
        elif 5 <= kuota_angka <= 10:
            return "sedang"
        else:
            return "banyak"

    # Ambil tempat PKL yang sesuai institusi (filter dari awal di query)
    cursor.execute("SELECT * FROM tempat_pkl WHERE institusi = %s", (institusi,))
    all_tempat_pkl = cursor.fetchall()

    hasil_rekomendasi = []

    for tempat in all_tempat_pkl:
        score = 0

        # Similarity institusi (sudah pasti 1 karena hasil query sudah disaring)
        s1 = 1

        # Similarity bidang
        s2 = 1 if str(tempat['bidang_pekerjaan']) == bidang else 0

        # Similarity fasilitas
        tempat_fasilitas = tempat['fasilitas'].split(',') if tempat['fasilitas'] else []
        match_fasilitas = len(set(fasilitas) & set(tempat_fasilitas)) / len(fasilitas) if fasilitas else 0
        s3 = match_fasilitas

        # Similarity durasi
        s4 = 1 if str(tempat['durasi']) == durasi else 0

        # Similarity kuota (kategori)
        kategori_kuota = kuota_to_category(tempat['kuota'])
        kategori_user = 'sedikit' if kuota == '1' else 'sedang' if kuota == '2' else 'banyak'
        s5 = 1 if kategori_kuota == kategori_user else 0

        # Total skor
        similarity_score = 0.20 * s1 + 0.25 * s2 + 0.20 * s3 + 0.15 * s4 + 0.20 * s5

        tempat['score'] = round(similarity_score, 2)
        hasil_rekomendasi.append(tempat)

    # Urutkan hasil rekomendasi berdasarkan skor
    hasil_rekomendasi.sort(key=lambda x: x['score'], reverse=True)

    cursor.close()
    return render_template('pilih_pkl.html', data_tempat_pkl=hasil_rekomendasi)
