from flask import Blueprint, render_template, session, flash, redirect, url_for, request
from flask import current_app as app
from flask_mysqldb import MySQLdb
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import numpy as np

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

def hitung_skor_kbrs(bidang_user, durasi_user, fasilitas_level_user, kuota_user, jarak_user, tempat):
    bobot = {
        'bidang': 0.3,
        'durasi': 0.15,
        'fasilitas': 0.2,
        'kuota': 0.15,
        'jarak': 0.2
    }
    
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
    
    return skor_kbrs

def trapesium_membership(x, a, b, c, d):
    if x <= a or x >= d:
        return 0
    elif a < x <= b:
        return (x - a) / (b - a)
    elif b < x <= c:
        return 1
    elif c < x < d:
        return (d - x) / (d - c)
    return 0

def segitiga_membership(x, a, b, c):
    if x <= a or x >= c:
        return 0
    elif a < x <= b:
        return (x - a) / (b - a)
    elif b < x < c:
        return (c - x) / (c - b)
    return 0

def liner_naik(x, a, b):
    if x <= a:
        return 0
    elif x >= b:
        return 1
    else:
        return (x - a) / (b - a)

def liner_turun(x, a, b):
    if x <= a:
        return 1
    elif x >= b:
        return 0
    else:
        return (b - x) / (b - a)

def fuzzifikasi_bidang(bidang_user, bidang_tempat):
    return 1.0 if bidang_user == bidang_tempat else 0.0

def fuzzifikasi_durasi(durasi_value):
    durasi_map = {'pendek': 1, 'sedang': 2, 'panjang': 3}
    
    if isinstance(durasi_value, str):
        durasi_value = durasi_map.get(durasi_value.lower(), 0)
    
    pendek = liner_turun(durasi_value, 1, 2)
    sedang = segitiga_membership(durasi_value, 1, 2, 3)
    panjang = liner_naik(durasi_value, 2, 3)
    
    return {'pendek': pendek, 'sedang': sedang, 'panjang': panjang}

def fuzzifikasi_fasilitas(fasilitas_value):
    fasilitas_map = {'kurang': 1, 'cukup': 2, 'lengkap': 3, 'sedang': 2, 'sangat lengkap': 4}
    
    if isinstance(fasilitas_value, str):
        fasilitas_value = fasilitas_map.get(fasilitas_value.lower(), 0)
    
    kurang = liner_turun(fasilitas_value, 1, 2)
    cukup = segitiga_membership(fasilitas_value, 1, 2, 3)
    lengkap = segitiga_membership(fasilitas_value, 2, 3, 4)
    sangat_lengkap = liner_naik(fasilitas_value, 3, 4)
    
    return {'kurang': kurang, 'cukup': cukup, 'lengkap': lengkap, 'sangat lengkap': sangat_lengkap}

def fuzzifikasi_kuota(kuota_value):
    kuota_map = {'sedikit': 1, 'sedang': 2, 'banyak': 3}
    
    if isinstance(kuota_value, str):
        kuota_value = kuota_map.get(kuota_value.lower(), 0)
    
    sedikit = liner_turun(kuota_value, 1, 2)
    sedang = segitiga_membership(kuota_value, 1, 2, 3)
    banyak = liner_naik(kuota_value, 2, 3)
    
    return {'sedikit': sedikit, 'sedang': sedang, 'banyak': banyak}

def fuzzifikasi_jarak(jarak_value):
    jarak_map = {'dekat': 1, 'sedang': 2, 'jauh': 3}
    
    if isinstance(jarak_value, str):
        jarak_value = jarak_map.get(jarak_value.lower(), 0)
    
    dekat = liner_turun(jarak_value, 1, 2)
    sedang = segitiga_membership(jarak_value, 1, 2, 3)
    jauh = liner_naik(jarak_value, 2, 3)
    
    return {'dekat': dekat, 'sedang': sedang, 'jauh': jauh}

def hitung_similarity_linguistik(user_value, tempat_value):
    if user_value == tempat_value:
        return 1.0
    
    linguistic_map = {
        'durasi': ['pendek', 'sedang', 'panjang'],
        'fasilitas': ['kurang', 'cukup', 'lengkap', 'sangat lengkap'],
        'kuota': ['sedikit', 'sedang', 'banyak'],
        'jarak': ['dekat', 'sedang', 'jauh']
    }
    
    for category, values in linguistic_map.items():
        if user_value in values and tempat_value in values:
            user_idx = values.index(user_value)
            tempat_idx = values.index(tempat_value)
            max_distance = len(values) - 1
            distance = abs(user_idx - tempat_idx)
            return 1 - (distance / max_distance)
    
    return 0.0

def inferensi_mamdani(user_prefrence, tempat_values):
    bidang_match = 1.0 if user_prefrence['bidang'] == tempat_values['bidang'] else 0.0
    
    similarity = {
        'durasi': hitung_similarity_linguistik(user_prefrence['durasi'], tempat_values['durasi']),
        'fasilitas': hitung_similarity_linguistik(user_prefrence['fasilitas'], tempat_values['fasilitas']),
        'kuota': hitung_similarity_linguistik(user_prefrence['kuota'], tempat_values['kuota']),
        'jarak': hitung_similarity_linguistik(user_prefrence['jarak'], tempat_values['jarak'])
    }
    
    hasil_tidak_rekomendasi = 0
    hasil_pertimbangkan = 0
    hasil_rekomendasi = 0
    
    if bidang_match == 0:
        hasil_tidak_rekomendasi = 1.0
        return {
            "Tidak Direkomendasikan": hasil_tidak_rekomendasi,
            "Dipertimbangkan": 0,
            "Direkomendasikan": 0
        }
    
    similarity_total = sum(similarity.values()) / len(similarity)
    
    if similarity_total >= 0.8:
        hasil_rekomendasi = similarity_total
    elif similarity_total >= 0.5:
        hasil_pertimbangkan = similarity_total
    else:
        hasil_tidak_rekomendasi = 1 - similarity_total
    
    hasil_rekomendasi = min(1.0, hasil_rekomendasi)
    hasil_pertimbangkan = min(1.0, hasil_pertimbangkan)
    hasil_tidak_rekomendasi = min(1.0, hasil_tidak_rekomendasi)
    
    kriteria_weights = {
        'durasi': 0.15,
        'fasilitas': 0.25,
        'kuota': 0.15,
        'jarak': 0.45
    }
    
    weighted_similarity = sum(similarity[key] * kriteria_weights[key] for key in similarity)
    
    if weighted_similarity >= 0.7:
        hasil_rekomendasi = weighted_similarity
        hasil_pertimbangkan = 0.3
        hasil_tidak_rekomendasi = 0
    elif weighted_similarity >= 0.4:
        hasil_rekomendasi = 0
        hasil_pertimbangkan = weighted_similarity
        hasil_tidak_rekomendasi = 0.2
    else:
        hasil_rekomendasi = 0
        hasil_pertimbangkan = 0.3
        hasil_tidak_rekomendasi = 1 - weighted_similarity
    
    return {
        "Tidak Direkomendasikan": hasil_tidak_rekomendasi,
        "Dipertimbangkan": hasil_pertimbangkan,
        "Direkomendasikan": hasil_rekomendasi
    }

def defuzzifikasi_centroid(inferensi_output, num_points=100):
    x_range = np.linspace(0, 100, num_points)
    
    numerator = 0
    denominator = 0
    
    for x in x_range:
        if x <= 40:
            mu = min(inferensi_output["Tidak Direkomendasikan"], trapesium_membership(x, 0, 10, 30, 40))
        elif 40 < x <= 70:
            mu = min(inferensi_output["Dipertimbangkan"], trapesium_membership(x, 40, 50, 60, 70))
        else:
            mu = min(inferensi_output["Direkomendasikan"], trapesium_membership(x, 70, 80, 90, 100))
        
        if mu > 0:
            numerator += x * mu
            denominator += mu
    
    if denominator == 0:
        return 50  
    
    return numerator / denominator

def get_rekomendasi_label(nilai):
    if nilai >= 0.6 or nilai >= 75:
        return "Direkomendasikan"
    elif nilai >= 0.5 or nilai >= 40:
        return "Dipertimbangkan"
    else:
        return "Tidak Direkomendasikan"

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

    direkomendasikan = []
    dipertimbangkan = []
    tidak_direkomendasikan = []

    user_preferences = {
        'bidang': bidang_user,
        'durasi': durasi_user,
        'fasilitas': fasilitas_level_user,
        'kuota': kuota_user,
        'jarak': jarak_user
    }

    for tempat in hasil_tempat:
        # Skor KBRS
        skor_kbrs = hitung_skor_kbrs(
            bidang_user, durasi_user, fasilitas_level_user, kuota_user, jarak_user, tempat
        )

        # Fuzzy Mamdani - directly compare user preferences with location values
        tempat_values = {
            'bidang': tempat['bidang_pekerjaan'].lower(),
            'durasi': tempat['label_durasi'].lower(),
            'fasilitas': tempat['label_fasilitas'].lower(),
            'kuota': tempat['label_kuota'].lower(),
            'jarak': tempat['label_jarak'].lower()
        }
        
        print(f"\nTempat: {tempat['nama_tempat']}")
        print(f"User durasi: {durasi_user}, Tempat durasi: {tempat_values['durasi']}")
        print(f"User fasilitas: {fasilitas_level_user}, Tempat fasilitas: {tempat_values['fasilitas']}")
        print(f"User kuota: {kuota_user}, Tempat kuota: {tempat_values['kuota']}")
        print(f"User jarak: {jarak_user}, Tempat jarak: {tempat_values['jarak']}")
        
        # Calculate similarity for visualization
        similarity = {
            'bidang': 1.0 if bidang_user == tempat_values['bidang'] else 0.0,
            'durasi': hitung_similarity_linguistik(durasi_user, tempat_values['durasi']),
            'fasilitas': hitung_similarity_linguistik(fasilitas_level_user, tempat_values['fasilitas']),
            'kuota': hitung_similarity_linguistik(kuota_user, tempat_values['kuota']),
            'jarak': hitung_similarity_linguistik(jarak_user, tempat_values['jarak'])
        }

        # Run the Mamdani fuzzy inference
        inferensi_output = inferensi_mamdani(user_preferences, tempat_values)
        nilai_mamdani = defuzzifikasi_centroid(inferensi_output)
        
        print(f"Inferensi output: {inferensi_output}")
        print(f"Nilai Mamdani: {nilai_mamdani}")
        
        skor_mamdani_normalized = nilai_mamdani / 100
        hybrid_score = (skor_kbrs + skor_mamdani_normalized) / 2

        # Simpan skor dan label
        tempat['skor_kbrs'] = round(skor_kbrs, 2)
        tempat['skor_mamdani'] = round(nilai_mamdani, 2)
        tempat['skor_hybrid'] = round(hybrid_score, 2)
        tempat['label_rekomendasi'] = get_rekomendasi_label(hybrid_score)

        # Simpan nilai keanggotaan untuk ditampilkan di chart
        tempat['nilai_keanggotaan'] = similarity

        # Cetak log
        print(f"Tempat: {tempat['nama_tempat']}")
        print(f"Skor KBRS      : {skor_kbrs:.2f}")
        print(f"Skor Mamdani   : {nilai_mamdani:.2f}")
        print(f"Skor Hybrid    : {hybrid_score:.2f}")
        print(f"Rekomendasi    : {tempat['label_rekomendasi']}")
        print("-------------------------------------------")

        # Kategorisasi rekomendasi
        if tempat['label_rekomendasi'] == 'Direkomendasikan':
            direkomendasikan.append(tempat)
        elif tempat['label_rekomendasi'] == 'Dipertimbangkan':
            dipertimbangkan.append(tempat)
        else:
            tidak_direkomendasikan.append(tempat)

    hasil_tempat_sorted = sorted(hasil_tempat, key=lambda x: x['skor_hybrid'], reverse=True)
    flash('Perhitungan KBRS + Fuzzy Mamdani selesai', 'info')

    return render_template(
        'pilih_pkl.html',
        data_tempat_pkl=hasil_tempat_sorted,
        direkomendasikan=direkomendasikan,
        dipertimbangkan=dipertimbangkan,
        tidak_direkomendasikan=tidak_direkomendasikan
    )