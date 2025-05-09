

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
    if request.method == 'POST':
        bidang_user = request.form.get('bidang_keahlian', '').strip().lower()
        durasi_user = request.form.get('durasi_pkl', '').strip().lower()
        fasilitas_level_user = request.form.get('fasilitas_level', '').strip().lower()
        kuota_user = request.form.get('kuota', '').strip().lower()
        jarak_user = request.form.get('jarak', '').strip().lower()  # Simpan sebagai string

        print("\n=== PREPARATION INPUT USER ===")
        print(f"Bidang dipilih     : {bidang_user}")
        print(f"Durasi dipilih     : {durasi_user}")
        print(f"Fasilitas dipilih  : {fasilitas_level_user}")
        print(f"Kuota dipilih      : {kuota_user}")
        print(f"Jarak dipilih      : {jarak_user}")
        print("===============================\n")

        cursor = db.connection.cursor(MySQLdb.cursors.DictCursor)
        
        # Jika user memilih bidang, gunakan query dengan filter LIKE
        if bidang_user:
            cursor.execute("SELECT * FROM tempat_pkl WHERE LOWER(bidang_pekerjaan) LIKE %s", (f'%{bidang_user}%',))
        else:
            cursor.execute("SELECT * FROM tempat_pkl")
        
        semua_tempat = cursor.fetchall()
        cursor.close()

        bobot = {
            "bidang": 0.3,
            "durasi": 0.15,
            "fasilitas": 0.2,
            "kuota": 0.15,
            "jarak": 0.2,
        }

        hasil_rekomendasi = []

        for tempat in semua_tempat:
            cocok_bidang = 5 if bidang_user and bidang_user in (tempat.get('bidang_pekerjaan') or '').lower() else 1
            bidang_fuzzy = 'cocok' if cocok_bidang == 5 else 'tidak cocok'
            
            durasi_raw = tempat.get('durasi') or ''
            durasi_tempat = 0
            match = re.search(r'(\d+)\s*x', durasi_raw)
            if match:
                try:
                    durasi_tempat = int(match.group(1))
                except ValueError:
                    durasi_tempat = 0

            if durasi_tempat <= 3:
                durasi_fuzzy = 'pendek'
            elif durasi_tempat <= 5:
                durasi_fuzzy = 'sedang'
            else:
                durasi_fuzzy = 'panjang'
            durasi_score = 5 if durasi_fuzzy == durasi_user else 1

            fasilitas_tempat = [f.strip().lower() for f in (tempat.get('fasilitas') or '').split(',')]
            fasilitas_match_count = len(set(fasilitas_tempat))
            if fasilitas_match_count <= 2:
                fasilitas_fuzzy = 'kurang'
            elif fasilitas_match_count <= 4:
                fasilitas_fuzzy = 'sedang'
            else:
                fasilitas_fuzzy = 'lengkap'
            fasilitas_score = 5 if fasilitas_fuzzy == fasilitas_level_user else 1

            try:
                kuota_tempat = int(tempat.get('kuota') or 0)
            except (ValueError, TypeError):
                kuota_tempat = 0
            if kuota_tempat < 5:
                kuota_fuzzy = 'sedikit'
            elif 5 <= kuota_tempat <= 10:
                kuota_fuzzy = 'sedang'
            else:
                kuota_fuzzy = 'banyak'
            kuota_score = 5 if kuota_fuzzy == kuota_user else 1

            try:
                jarak_tempat = float(tempat.get('jarak') or 0)
            except (ValueError, TypeError):
                jarak_tempat = 0
                
            # Klasifikasi jarak disederhanakan menjadi 3 kategori
            if jarak_tempat <= 1:
                jarak_fuzzy = 'dekat'
            elif jarak_tempat <= 5:
                jarak_fuzzy = 'sedang'
            else:
                jarak_fuzzy = 'jauh'
            
            # Skor jarak berdasarkan kecocokan dengan preferensi user
            jarak_score = 5 if jarak_fuzzy == jarak_user else 1

            rule_results = []

            if jarak_fuzzy == 'dekat' and kuota_fuzzy == 'banyak':
                rule_results.append(min(5,5))
            if jarak_fuzzy == 'sedang' and kuota_fuzzy == 'sedang':
                rule_results.append(min(4,3))
            if jarak_fuzzy == 'jauh' and kuota_fuzzy == 'sedikit':
                rule_results.append(min(2,1))
            if fasilitas_fuzzy == 'lengkap' and durasi_fuzzy == 'panjang':
                rule_results.append(min(5,5))
            if fasilitas_fuzzy == 'sedang' and durasi_fuzzy == 'sedang':
                rule_results.append(min(3,3))
            if fasilitas_fuzzy == 'kurang' and durasi_fuzzy == 'pendek':
                rule_results.append(min(1,1))
            if bidang_fuzzy == 'cocok' and fasilitas_fuzzy == 'lengkap':
                rule_results.append(min(5,5))
            if bidang_fuzzy == 'cocok' and durasi_fuzzy == 'panjang':
                rule_results.append(min(5,5))
            if bidang_fuzzy == 'cocok' and kuota_fuzzy == 'banyak':
                rule_results.append(min(5,5))
            if bidang_fuzzy == 'cocok' and jarak_fuzzy == 'dekat':
                rule_results.append(min(5,5))

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
                defuzzified_score = 3

            skor_kbrs = (
                bobot['bidang'] * (cocok_bidang / 5) +
                bobot['durasi'] * (durasi_score / 5) +
                bobot['fasilitas'] * (fasilitas_score / 5) +
                bobot['kuota'] * (kuota_score / 5) +
                bobot['jarak'] * (jarak_score / 5)
            )

            defuzzified_normalized = max(0.2, defuzzified_score / 5)
            total_skor = round((skor_kbrs + defuzzified_normalized) / 2, 4)

            bidang_label = "Sesuai Bidang" if bidang_fuzzy == 'cocok' else "Di Luar Bidang"
            
            if total_skor >= 0.75:
                rekomendasi_kategori = "Sangat Direkomendasikan"
            elif total_skor >= 0.5:
                rekomendasi_kategori = "Direkomendasikan"
            elif total_skor >= 0.3:
                rekomendasi_kategori = "Kurang Direkomendasikan"
            else:
                rekomendasi_kategori = "Tidak Direkomendasikan"
                
            # Buat detail keterangan untuk setiap tempat
            keterangan_detail = []
            
            # Tambahkan keterangan bidang jika user memilih bidang
            if bidang_user and bidang_fuzzy == 'cocok':
                keterangan_detail.append(f"bidang {bidang_user}")
            
            # Keterangan fasilitas
            keterangan_detail.append(f"fasilitas {fasilitas_fuzzy}")
                
            # Keterangan kuota
            keterangan_detail.append(f"kuota {kuota_fuzzy}")
            
            # Keterangan jarak
            keterangan_detail.append(f"jarak {jarak_fuzzy}")
            
            # Tambahkan alasan tidak direkomendasikan
            if rekomendasi_kategori == "Tidak Direkomendasikan":
                if jarak_fuzzy == 'jauh':
                    keterangan_detail.append("jarak terlalu jauh")
                if kuota_fuzzy == 'sedikit':
                    keterangan_detail.append("kuota terlalu sedikit")
            
            keterangan = f"{rekomendasi_kategori}: {', '.join(keterangan_detail)}"
                
            rekomendasi_label = f"{bidang_label} - {rekomendasi_kategori}"

            print(f"[{tempat.get('nama_tempat','Unknown')}] KBRS: {skor_kbrs}, Fuzzy: {defuzzified_score}, Total: {total_skor}, Label: {rekomendasi_label}")

            if total_skor > 0:
                tempat['score'] = total_skor
                tempat['rekomendasi'] = rekomendasi_label
                tempat['keterangan'] = keterangan
                hasil_rekomendasi.append(tempat)

        hasil_rekomendasi.sort(key=lambda x: x['score'], reverse=True)
        return render_template('pilih_pkl.html', data_tempat_pkl=hasil_rekomendasi)
    else:
        # Untuk GET request, ambil semua data dan tambahkan keterangan default
        cursor = db.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM tempat_pkl")
        semua_tempat = cursor.fetchall()
        cursor.close()
        
        for tempat in semua_tempat:
            # Membuat keterangan dasar untuk tampilan awal
            fasilitas_tempat = [f.strip().lower() for f in (tempat.get('fasilitas') or '').split(',')]
            fasilitas_count = len(set(fasilitas_tempat))
            
            if fasilitas_count <= 2:
                fasilitas_desc = "fasilitas kurang"
            elif fasilitas_count <= 4:
                fasilitas_desc = "fasilitas sedang"
            else:
                fasilitas_desc = "fasilitas lengkap"
                
            try:
                kuota_tempat = int(tempat.get('kuota') or 0)
            except (ValueError, TypeError):
                kuota_tempat = 0
                
            if kuota_tempat < 5:
                kuota_desc = "kuota sedikit"
            elif 5 <= kuota_tempat <= 10:
                kuota_desc = "kuota sedang"
            else:
                kuota_desc = "kuota banyak"
                
            try:
                jarak_tempat = float(tempat.get('jarak') or 0)
            except (ValueError, TypeError):
                jarak_tempat = 0
                
            if jarak_tempat <= 1:
                jarak_desc = "jarak dekat"
            elif jarak_tempat <= 5:
                jarak_desc = "jarak sedang"
            else:
                jarak_desc = "jarak jauh"
                
            tempat['keterangan'] = f"Detail: {fasilitas_desc}, {kuota_desc}, {jarak_desc}"
            
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
