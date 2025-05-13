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

# Fungsi untuk metode KBRS
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

# Fuzzy Mamdani Tradisional
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
    if bidang_user == bidang_tempat:
        return 1.0
    return 0.0

def fuzzifikasi_durasi(durasi_value):
    durasi_map = {'pendek': 1, 'sedang': 2, 'panjang': 3}
    
    if isinstance(durasi_value, str):
        durasi_value = durasi_map.get(durasi_value.lower(), 0)
    
    pendek = liner_turun(durasi_value, 1, 2)
    sedang = segitiga_membership(durasi_value, 1, 2, 3)
    panjang = liner_naik(durasi_value, 2, 3)
    
    return {'pendek': pendek, 'sedang': sedang, 'panjang': panjang}

def fuzzifikasi_fasilitas(fasilitas_value):
    fasilitas_map = {'kurang': 1, 'cukup': 2, 'lengkap': 3, 'sangat lengkap': 4}
    
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

def inferensi_mamdani(fuzzy_bidang, fuzzy_durasi, fuzzy_fasilitas, fuzzy_kuota, fuzzy_jarak):
    rules = [
        {"kondisi": [True, 'pendek', 'kurang', 'sedikit', 'dekat'], "hasil": "Tidak Direkomendasikan"},
        {"kondisi": [True, 'pendek', 'kurang', 'sedikit', 'sedang'], "hasil": "Tidak Direkomendasikan"},
        {"kondisi": [True, 'pendek', 'kurang', 'sedikit', 'jauh'], "hasil": "Tidak Direkomendasikan"},
        {"kondisi": [True, 'pendek', 'kurang', 'sedang', 'dekat'], "hasil": "Tidak Direkomendasikan"},
        {"kondisi": [True, 'pendek', 'kurang', 'sedang', 'sedang'], "hasil": "Tidak Direkomendasikan"},
        {"kondisi": [True, 'pendek', 'kurang', 'sedang', 'jauh'], "hasil": "Tidak Direkomendasikan"},
        {"kondisi": [True, 'pendek', 'kurang', 'banyak', 'dekat'], "hasil": "Tidak Direkomendasikan"},
        {"kondisi": [True, 'pendek', 'kurang', 'banyak', 'sedang'], "hasil": "Tidak Direkomendasikan"},
        {"kondisi": [True, 'pendek', 'kurang', 'banyak', 'jauh'], "hasil": "Tidak Direkomendasikan"},
        {"kondisi": [True, 'pendek', 'cukup', 'sedikit', 'dekat'], "hasil": "Dipertimbangkan"},
        {"kondisi": [True, 'pendek', 'cukup', 'sedikit', 'sedang'], "hasil": "Tidak Direkomendasikan"},
        {"kondisi": [True, 'pendek', 'cukup', 'sedikit', 'jauh'], "hasil": "Tidak Direkomendasikan"},
        {"kondisi": [True, 'pendek', 'cukup', 'sedang', 'dekat'], "hasil": "Dipertimbangkan"},
        {"kondisi": [True, 'pendek', 'cukup', 'sedang', 'sedang'], "hasil": "Dipertimbangkan"},
        {"kondisi": [True, 'pendek', 'cukup', 'sedang', 'jauh'], "hasil": "Tidak Direkomendasikan"},
        {"kondisi": [True, 'pendek', 'cukup', 'banyak', 'dekat'], "hasil": "Dipertimbangkan"},
        {"kondisi": [True, 'pendek', 'cukup', 'banyak', 'sedang'], "hasil": "Dipertimbangkan"},
        {"kondisi": [True, 'pendek', 'cukup', 'banyak', 'jauh'], "hasil": "Tidak Direkomendasikan"},
        {"kondisi": [True, 'pendek', 'lengkap', 'sedikit', 'dekat'], "hasil": "Direkomendasikan"},
        {"kondisi": [True, 'pendek', 'lengkap', 'sedikit', 'sedang'], "hasil": "Dipertimbangkan"},
        {"kondisi": [True, 'pendek', 'lengkap', 'sedikit', 'jauh'], "hasil": "Tidak Direkomendasikan"},
        {"kondisi": [True, 'pendek', 'lengkap', 'sedang', 'dekat'], "hasil": "Direkomendasikan"},
        {"kondisi": [True, 'pendek', 'lengkap', 'sedang', 'sedang'], "hasil": "Dipertimbangkan"},
        {"kondisi": [True, 'pendek', 'lengkap', 'sedang', 'jauh'], "hasil": "Dipertimbangkan"},
        {"kondisi": [True, 'pendek', 'lengkap', 'banyak', 'dekat'], "hasil": "Direkomendasikan"},
        {"kondisi": [True, 'pendek', 'lengkap', 'banyak', 'sedang'], "hasil": "Direkomendasikan"},
        {"kondisi": [True, 'pendek', 'lengkap', 'banyak', 'jauh'], "hasil": "Dipertimbangkan"},
        {"kondisi": [True, 'pendek', 'sangat lengkap', 'sedikit', 'dekat'], "hasil": "Direkomendasikan"},
        {"kondisi": [True, 'pendek', 'sangat lengkap', 'sedikit', 'sedang'], "hasil": "Direkomendasikan"},
        {"kondisi": [True, 'pendek', 'sangat lengkap', 'sedikit', 'jauh'], "hasil": "Dipertimbangkan"},
        {"kondisi": [True, 'pendek', 'sangat lengkap', 'sedang', 'dekat'], "hasil": "Direkomendasikan"},
        {"kondisi": [True, 'pendek', 'sangat lengkap', 'sedang', 'sedang'], "hasil": "Direkomendasikan"},
        {"kondisi": [True, 'pendek', 'sangat lengkap', 'sedang', 'jauh'], "hasil": "Dipertimbangkan"},
        {"kondisi": [True, 'pendek', 'sangat lengkap', 'banyak', 'dekat'], "hasil": "Direkomendasikan"},
        {"kondisi": [True, 'pendek', 'sangat lengkap', 'banyak', 'sedang'], "hasil": "Direkomendasikan"},
        {"kondisi": [True, 'pendek', 'sangat lengkap', 'banyak', 'jauh'], "hasil": "Direkomendasikan"},
        
        {"kondisi": [True, 'sedang', 'kurang', 'sedikit', 'dekat'], "hasil": "Tidak Direkomendasikan"},
        {"kondisi": [True, 'sedang', 'kurang', 'sedikit', 'sedang'], "hasil": "Tidak Direkomendasikan"},
        {"kondisi": [True, 'sedang', 'kurang', 'sedikit', 'jauh'], "hasil": "Tidak Direkomendasikan"},
        {"kondisi": [True, 'sedang', 'kurang', 'sedang', 'dekat'], "hasil": "Tidak Direkomendasikan"},
        {"kondisi": [True, 'sedang', 'kurang', 'sedang', 'sedang'], "hasil": "Tidak Direkomendasikan"},
        {"kondisi": [True, 'sedang', 'kurang', 'sedang', 'jauh'], "hasil": "Tidak Direkomendasikan"},
        {"kondisi": [True, 'sedang', 'kurang', 'banyak', 'dekat'], "hasil": "Dipertimbangkan"},
        {"kondisi": [True, 'sedang', 'kurang', 'banyak', 'sedang'], "hasil": "Tidak Direkomendasikan"},
        {"kondisi": [True, 'sedang', 'kurang', 'banyak', 'jauh'], "hasil": "Tidak Direkomendasikan"},
        {"kondisi": [True, 'sedang', 'cukup', 'sedikit', 'dekat'], "hasil": "Dipertimbangkan"},
        {"kondisi": [True, 'sedang', 'cukup', 'sedikit', 'sedang'], "hasil": "Dipertimbangkan"},
        {"kondisi": [True, 'sedang', 'cukup', 'sedikit', 'jauh'], "hasil": "Tidak Direkomendasikan"},
        {"kondisi": [True, 'sedang', 'cukup', 'sedang', 'dekat'], "hasil": "Dipertimbangkan"},
        {"kondisi": [True, 'sedang', 'cukup', 'sedang', 'sedang'], "hasil": "Dipertimbangkan"},
        {"kondisi": [True, 'sedang', 'cukup', 'sedang', 'jauh'], "hasil": "Dipertimbangkan"},
        {"kondisi": [True, 'sedang', 'cukup', 'banyak', 'dekat'], "hasil": "Direkomendasikan"},
        {"kondisi": [True, 'sedang', 'cukup', 'banyak', 'sedang'], "hasil": "Dipertimbangkan"},
        {"kondisi": [True, 'sedang', 'cukup', 'banyak', 'jauh'], "hasil": "Dipertimbangkan"},
        {"kondisi": [True, 'sedang', 'lengkap', 'sedikit', 'dekat'], "hasil": "Direkomendasikan"},
        {"kondisi": [True, 'sedang', 'lengkap', 'sedikit', 'sedang'], "hasil": "Dipertimbangkan"},
        {"kondisi": [True, 'sedang', 'lengkap', 'sedikit', 'jauh'], "hasil": "Dipertimbangkan"},
        {"kondisi": [True, 'sedang', 'lengkap', 'sedang', 'dekat'], "hasil": "Direkomendasikan"},
        {"kondisi": [True, 'sedang', 'lengkap', 'sedang', 'sedang'], "hasil": "Direkomendasikan"},
        {"kondisi": [True, 'sedang', 'lengkap', 'sedang', 'jauh'], "hasil": "Dipertimbangkan"},
        {"kondisi": [True, 'sedang', 'lengkap', 'banyak', 'dekat'], "hasil": "Direkomendasikan"},
        {"kondisi": [True, 'sedang', 'lengkap', 'banyak', 'sedang'], "hasil": "Direkomendasikan"},
        {"kondisi": [True, 'sedang', 'lengkap', 'banyak', 'jauh'], "hasil": "Dipertimbangkan"},
        {"kondisi": [True, 'sedang', 'sangat lengkap', 'sedikit', 'dekat'], "hasil": "Direkomendasikan"},
        {"kondisi": [True, 'sedang', 'sangat lengkap', 'sedikit', 'sedang'], "hasil": "Direkomendasikan"},
        {"kondisi": [True, 'sedang', 'sangat lengkap', 'sedikit', 'jauh'], "hasil": "Dipertimbangkan"},
        {"kondisi": [True, 'sedang', 'sangat lengkap', 'sedang', 'dekat'], "hasil": "Direkomendasikan"},
        {"kondisi": [True, 'sedang', 'sangat lengkap', 'sedang', 'sedang'], "hasil": "Direkomendasikan"},
        {"kondisi": [True, 'sedang', 'sangat lengkap', 'sedang', 'jauh'], "hasil": "Direkomendasikan"},
        {"kondisi": [True, 'sedang', 'sangat lengkap', 'banyak', 'dekat'], "hasil": "Direkomendasikan"},
        {"kondisi": [True, 'sedang', 'sangat lengkap', 'banyak', 'sedang'], "hasil": "Direkomendasikan"},
        {"kondisi": [True, 'sedang', 'sangat lengkap', 'banyak', 'jauh'], "hasil": "Direkomendasikan"},
        
        {"kondisi": [True, 'panjang', 'kurang', 'sedikit', 'dekat'], "hasil": "Tidak Direkomendasikan"},
        {"kondisi": [True, 'panjang', 'kurang', 'sedikit', 'sedang'], "hasil": "Tidak Direkomendasikan"},
        {"kondisi": [True, 'panjang', 'kurang', 'sedikit', 'jauh'], "hasil": "Tidak Direkomendasikan"},
        {"kondisi": [True, 'panjang', 'kurang', 'sedang', 'dekat'], "hasil": "Dipertimbangkan"},
        {"kondisi": [True, 'panjang', 'kurang', 'sedang', 'sedang'], "hasil": "Tidak Direkomendasikan"},
        {"kondisi": [True, 'panjang', 'kurang', 'sedang', 'jauh'], "hasil": "Tidak Direkomendasikan"},
        {"kondisi": [True, 'panjang', 'kurang', 'banyak', 'dekat'], "hasil": "Dipertimbangkan"},
        {"kondisi": [True, 'panjang', 'kurang', 'banyak', 'sedang'], "hasil": "Dipertimbangkan"},
        {"kondisi": [True, 'panjang', 'kurang', 'banyak', 'jauh'], "hasil": "Tidak Direkomendasikan"},
        {"kondisi": [True, 'panjang', 'cukup', 'sedikit', 'dekat'], "hasil": "Dipertimbangkan"},
        {"kondisi": [True, 'panjang', 'cukup', 'sedikit', 'sedang'], "hasil": "Dipertimbangkan"},
        {"kondisi": [True, 'panjang', 'cukup', 'sedikit', 'jauh'], "hasil": "Tidak Direkomendasikan"},
        {"kondisi": [True, 'panjang', 'cukup', 'sedang', 'dekat'], "hasil": "Direkomendasikan"},
        {"kondisi": [True, 'panjang', 'cukup', 'sedang', 'sedang'], "hasil": "Dipertimbangkan"},
        {"kondisi": [True, 'panjang', 'cukup', 'sedang', 'jauh'], "hasil": "Dipertimbangkan"},
        {"kondisi": [True, 'panjang', 'cukup', 'banyak', 'dekat'], "hasil": "Direkomendasikan"},
        {"kondisi": [True, 'panjang', 'cukup', 'banyak', 'sedang'], "hasil": "Dipertimbangkan"},
        {"kondisi": [True, 'panjang', 'cukup', 'banyak', 'jauh'], "hasil": "Dipertimbangkan"},
        {"kondisi": [True, 'panjang', 'lengkap', 'sedikit', 'dekat'], "hasil": "Direkomendasikan"},
        {"kondisi": [True, 'panjang', 'lengkap', 'sedikit', 'sedang'], "hasil": "Direkomendasikan"},
        {"kondisi": [True, 'panjang', 'lengkap', 'sedikit', 'jauh'], "hasil": "Dipertimbangkan"},
        {"kondisi": [True, 'panjang', 'lengkap', 'sedang', 'dekat'], "hasil": "Direkomendasikan"},
        {"kondisi": [True, 'panjang', 'lengkap', 'sedang', 'sedang'], "hasil": "Direkomendasikan"},
        {"kondisi": [True, 'panjang', 'lengkap', 'sedang', 'jauh'], "hasil": "Dipertimbangkan"},
        {"kondisi": [True, 'panjang', 'lengkap', 'banyak', 'dekat'], "hasil": "Direkomendasikan"},
        {"kondisi": [True, 'panjang', 'lengkap', 'banyak', 'sedang'], "hasil": "Direkomendasikan"},
        {"kondisi": [True, 'panjang', 'lengkap', 'banyak', 'jauh'], "hasil": "Direkomendasikan"},
        {"kondisi": [True, 'panjang', 'sangat lengkap', 'sedikit', 'dekat'], "hasil": "Direkomendasikan"},
        {"kondisi": [True, 'panjang', 'sangat lengkap', 'sedikit', 'sedang'], "hasil": "Direkomendasikan"},
        {"kondisi": [True, 'panjang', 'sangat lengkap', 'sedikit', 'jauh'], "hasil": "Direkomendasikan"},
        {"kondisi": [True, 'panjang', 'sangat lengkap', 'sedang', 'dekat'], "hasil": "Direkomendasikan"},
        {"kondisi": [True, 'panjang', 'sangat lengkap', 'sedang', 'sedang'], "hasil": "Direkomendasikan"},
        {"kondisi": [True, 'panjang', 'sangat lengkap', 'sedang', 'jauh'], "hasil": "Direkomendasikan"},
        {"kondisi": [True, 'panjang', 'sangat lengkap', 'banyak', 'dekat'], "hasil": "Direkomendasikan"},
        {"kondisi": [True, 'panjang', 'sangat lengkap', 'banyak', 'sedang'], "hasil": "Direkomendasikan"},
        {"kondisi": [True, 'panjang', 'sangat lengkap', 'banyak', 'jauh'], "hasil": "Direkomendasikan"},
        
        {"kondisi": [False, 'pendek', 'kurang', 'sedikit', 'dekat'], "hasil": "Tidak Direkomendasikan"},
        {"kondisi": [False, 'pendek', 'lengkap', 'banyak', 'dekat'], "hasil": "Tidak Direkomendasikan"},
        {"kondisi": [False, 'panjang', 'sangat lengkap', 'banyak', 'dekat'], "hasil": "Tidak Direkomendasikan"},
    ]
    
    hasil_tidak_rekomendasi = 0
    hasil_pertimbangkan = 0
    hasil_rekomendasi = 0
    
    for rule in rules:
        bidang_matched = rule["kondisi"][0] == fuzzy_bidang
        durasi_key = rule["kondisi"][1]
        fasilitas_key = rule["kondisi"][2]
        kuota_key = rule["kondisi"][3]
        jarak_key = rule["kondisi"][4]
        
        durasi_val = fuzzy_durasi[durasi_key]
        fasilitas_val = fuzzy_fasilitas[fasilitas_key]
        kuota_val = fuzzy_kuota[kuota_key]
        jarak_val = fuzzy_jarak[jarak_key]
        
        if not bidang_matched:
            continue
        
        alpha = min(durasi_val, fasilitas_val, kuota_val, jarak_val)
        
        if alpha == 0:
            continue
            
        if rule["hasil"] == "Tidak Direkomendasikan":
            hasil_tidak_rekomendasi = max(hasil_tidak_rekomendasi, alpha)
        elif rule["hasil"] == "Dipertimbangkan":
            hasil_pertimbangkan = max(hasil_pertimbangkan, alpha)
        elif rule["hasil"] == "Direkomendasikan":
            hasil_rekomendasi = max(hasil_rekomendasi, alpha)
    
    return {
        "Tidak Direkomendasikan": hasil_tidak_rekomendasi,
        "Dipertimbangkan": hasil_pertimbangkan,
        "Direkomendasikan": hasil_rekomendasi
    }

def defuzzifikasi_centroid(inferensi_output, num_points=100):
    x_range = np.linspace(0, 100, num_points)
    
    membership_values = []
    for x in x_range:
        if 0 <= x <= 40:
            value_tidak = inferensi_output["Tidak Direkomendasikan"]
            membership_values.append(min(value_tidak, segitiga_membership(x, 0, 20, 40)))
        elif 40 < x <= 70:
            value_pertimbangkan = inferensi_output["Dipertimbangkan"]
            membership_values.append(min(value_pertimbangkan, segitiga_membership(x, 40, 55, 70)))
        else:
            value_rekomendasi = inferensi_output["Direkomendasikan"]
            membership_values.append(min(value_rekomendasi, segitiga_membership(x, 70, 85, 100)))
    
    numerator = sum(x_range[i] * membership_values[i] for i in range(num_points))
    denominator = sum(membership_values)
    
    if denominator == 0:
        return 50
    
    return numerator / denominator

def get_rekomendasi_label(nilai):
    if nilai >= 0.75 or nilai >= 70:
        return "Direkomendasikan"
    elif nilai >= 0.60 or nilai >= 40:
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

    for tempat in hasil_tempat:
        # Metode KBRS (Rule-Based)
        skor_kbrs = hitung_skor_kbrs(bidang_user, durasi_user, fasilitas_level_user, kuota_user, jarak_user, tempat)
        
        # Metode Fuzzy Mamdani tradisional
        fuzzy_bidang = fuzzifikasi_bidang(bidang_user, tempat['bidang_pekerjaan'].lower())
        fuzzy_durasi = fuzzifikasi_durasi(durasi_user)
        fuzzy_fasilitas = fuzzifikasi_fasilitas(fasilitas_level_user)
        fuzzy_kuota = fuzzifikasi_kuota(kuota_user)
        fuzzy_jarak = fuzzifikasi_jarak(jarak_user)
        
        inferensi_output = inferensi_mamdani(fuzzy_bidang, fuzzy_durasi, fuzzy_fasilitas, fuzzy_kuota, fuzzy_jarak)
        nilai_mamdani = defuzzifikasi_centroid(inferensi_output)
        
        # Normalisasi skor Mamdani ke range 0-1 untuk hybrid
        skor_mamdani_normalized = nilai_mamdani / 100
        
        # Menghitung skor hybrid (KBRS + Mamdani)
        hybrid_score = (skor_kbrs + skor_mamdani_normalized) / 2
        
        # Menyimpan semua skor ke dalam data tempat
        tempat['skor_kbrs'] = round(skor_kbrs, 2)
        tempat['skor_mamdani'] = round(nilai_mamdani, 2)
        tempat['skor_hybrid'] = round(hybrid_score, 2)
        
        # Menentukan label rekomendasi berdasarkan skor hybrid
        tempat['label_rekomendasi'] = get_rekomendasi_label(hybrid_score)

        print(f"Tempat: {tempat['nama_tempat']}")
        print(f"Skor KBRS      : {skor_kbrs:.2f}")
        print(f"Skor Mamdani   : {nilai_mamdani:.2f}")
        print(f"Skor Hybrid    : {hybrid_score:.2f}")
        print(f"Rekomendasi    : {tempat['label_rekomendasi']}")
        print("-------------------------------------------")

    hasil_tempat_sorted = sorted(hasil_tempat, key=lambda x: x['skor_hybrid'], reverse=True)
    flash('Perhitungan KBRS + Fuzzy Mamdani selesai', 'info')
    return render_template('pilih_pkl.html', data_tempat_pkl=hasil_tempat_sorted)