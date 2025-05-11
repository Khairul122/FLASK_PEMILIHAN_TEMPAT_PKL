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

@tempat_pkl_siswa_routes.route('/pilih-pkl', methods=['POST'])
def tampilkan_input_user():
    import itertools

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
    semua_tempat = cursor.fetchall()
    cursor.close()

    bobot = {
        "bidang": 0.3,
        "durasi": 0.15,
        "fasilitas": 0.2,
        "kuota": 0.15,
        "jarak": 0.2,
    }

    def μ_durasi_pendek(x): return max(min((4 - x) / (4 - 3), 1), 0) if 3 <= x < 4 else (1 if x < 3 else 0)
    def μ_durasi_sedang(x): return max(min((x - 3) / (4 - 3), (5 - x) / (5 - 4)), 0) if 3 < x < 5 else (1 if x == 4 else 0)
    def μ_durasi_panjang(x): return max(min((x - 4) / (5 - 4), 1), 0) if 4 < x <= 6 else (1 if x > 6 else 0)

    def μ_fasilitas_kurang(x): return max(min((3 - x) / (3 - 2), 1), 0) if 2 < x < 3 else (1 if x <= 2 else 0)
    def μ_fasilitas_sedang(x): return max(min((x - 2) / (3.5 - 2), (5 - x) / (5 - 3.5)), 0) if 2 < x < 5 else (1 if x == 3.5 else 0)
    def μ_fasilitas_lengkap(x): return max(min((x - 4) / (5 - 4), 1), 0) if 4 < x <= 5 else (1 if x >= 5 else 0)

    def μ_kuota_sedikit(x): return max(min((4 - x) / (4 - 3), 1), 0) if 3 < x < 4 else (1 if x <= 3 else 0)
    def μ_kuota_sedang(x): return max(min((x - 3) / (5.5 - 3), (8 - x) / (8 - 5.5)), 0) if 3 < x < 8 else (1 if x == 5.5 else 0)
    def μ_kuota_banyak(x): return max(min((x - 7) / (8 - 7), 1), 0) if 7 < x < 8 else (1 if x >= 8 else 0)

    def μ_jarak_dekat(x): return max(min((5 - x) / (5 - 4), 1), 0) if 4 < x < 5 else (1 if x <= 4 else 0)
    def μ_jarak_sedang(x): return max(min((x - 5) / (7.5 - 5), (10 - x) / (10 - 7.5)), 0) if 5 < x < 10 else (1 if x == 7.5 else 0)
    def μ_jarak_jauh(x): return max(min((x - 10) / (11 - 10), 1), 0) if 10 < x < 11 else (1 if x >= 11 else 0)

    hasil_tempat = []

    for tempat in semua_tempat:
        bidang_score = 1.0 if bidang_user in (tempat['bidang_pekerjaan'] or '').lower() else 0.0

        durasi_str = tempat['durasi']
        durasi_num = 3 if '3x' in durasi_str else 4 if '4x' in durasi_str else 5 if '5x' in durasi_str else 6 if '6x' in durasi_str else 0
        durasi_score = μ_durasi_pendek(durasi_num) if durasi_user == 'pendek' else μ_durasi_sedang(durasi_num) if durasi_user == 'sedang' else μ_durasi_panjang(durasi_num)

        fasilitas_count = len([f.strip() for f in (tempat['fasilitas'] or '').split(',') if f.strip()])
        fasilitas_score = μ_fasilitas_kurang(fasilitas_count) if fasilitas_level_user == 'kurang' else μ_fasilitas_sedang(fasilitas_count) if fasilitas_level_user == 'sedang' else μ_fasilitas_lengkap(fasilitas_count)

        kuota = tempat['kuota'] or 0
        kuota_score = μ_kuota_sedikit(kuota) if kuota_user == 'sedikit' else μ_kuota_sedang(kuota) if kuota_user == 'sedang' else μ_kuota_banyak(kuota)

        try:
            jarak = float(tempat['jarak'])
        except:
            jarak = 0.0
        jarak_score = μ_jarak_dekat(jarak) if jarak_user == 'dekat' else μ_jarak_sedang(jarak) if jarak_user == 'sedang' else μ_jarak_jauh(jarak)

        skor_kbrs = (
            bobot['bidang'] * bidang_score +
            bobot['durasi'] * durasi_score +
            bobot['fasilitas'] * fasilitas_score +
            bobot['kuota'] * kuota_score +
            bobot['jarak'] * jarak_score
        )

        himpunan = {
            'bidang': bidang_score,
            'durasi': durasi_score,
            'fasilitas': fasilitas_score,
            'kuota': kuota_score,
            'jarak': jarak_score
        }

        rule_strengths = []
        kategori_output = {
            'tidak_direkomendasikan': 1,
            'kurang_direkomendasikan': 2,
            'direkomendasikan': 4,
            'sangat_direkomendasikan': 5
        }

        rule_detail = []
        rule_id = 1

        for kombinasi in itertools.combinations(himpunan.keys(), 3):
            a, b, c = kombinasi
            nilai_min = min(himpunan[a], himpunan[b], himpunan[c])
            if nilai_min == 1.0:
                kategori = 'sangat_direkomendasikan'
            elif nilai_min >= 0.5:
                kategori = 'direkomendasikan'
            elif nilai_min > 0:
                kategori = 'kurang_direkomendasikan'
            else:
                continue

            rule_strengths.append((nilai_min, kategori))
            rule_detail.append({
                'rule': f"Rule-{rule_id}",
                'kombinasi': f"IF {a} AND {b} AND {c} THEN {kategori.replace('_', ' ').capitalize()}",
                'α_predikat': round(nilai_min, 4)
            })
            rule_id += 1

        if rule_strengths:
            numerator = sum(s * kategori_output[k] for s, k in rule_strengths)
            denominator = sum(s for s, _ in rule_strengths)
            skor_fuzzy_normalized = (numerator / denominator) / 5  # NORMALISASI KE 0–1
        else:
            skor_fuzzy_normalized = 0.0

        skor_hybrid = (skor_kbrs + skor_fuzzy_normalized) / 2

        # THRESHOLD UNTUK RENTANG 0–1
        if skor_hybrid >= 0.75:
            rekomendasi = "Sangat Direkomendasikan"
        elif skor_hybrid >= 0.5:
            rekomendasi = "Direkomendasikan"
        elif skor_hybrid >= 0.3:
            rekomendasi = "Kurang Direkomendasikan"
        else:
            rekomendasi = "Tidak Rekomendasi"

        tempat['skor_kbrs'] = skor_kbrs
        tempat['skor_fuzzy'] = skor_fuzzy_normalized
        tempat['score'] = skor_hybrid
        tempat['rekomendasi'] = rekomendasi
        tempat['nilai_keanggotaan'] = himpunan
        tempat['rules_terpicu'] = rule_detail

        print(f"{tempat['nama_tempat']}: KBRS = {skor_kbrs}, Fuzzy = {skor_fuzzy_normalized}, Hybrid = {skor_hybrid} → {rekomendasi}")
        for r in rule_detail:
            print(f"{r['rule']}: {r['kombinasi']}, α = {r['α_predikat']}")

        hasil_tempat.append(tempat)

    return render_template('pilih_pkl.html', data_tempat_pkl=hasil_tempat)


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

@tempat_pkl_siswa_routes.route('/rekomendasi-tempat-pkl', methods=['POST'])
def rekomendasi_tempat_pkl():
    cursor = db.connection.cursor(MySQLdb.cursors.DictCursor)

    institusi = request.form.get('institusi')
    bidang = request.form.get('bidang_pekerjaan')
    fasilitas = request.form.getlist('fasilitas')
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

    query_params = []
    query = "SELECT * FROM tempat_pkl WHERE 1=1"
    
    if institusi:
        query += " AND institusi = %s"
        query_params.append(institusi)
        
    if bidang:
        query += " AND LOWER(bidang_pekerjaan) LIKE %s"
        query_params.append(f'%{bidang.lower()}%')
        
    if durasi:
        query += " AND durasi = %s"
        query_params.append(durasi)
        
    cursor.execute(query, tuple(query_params))
    all_tempat_pkl = cursor.fetchall()

    hasil_rekomendasi = []

    for tempat in all_tempat_pkl:
        bidang_similarity = 0
        if bidang and tempat['bidang_pekerjaan']:
            if bidang.lower() in tempat['bidang_pekerjaan'].lower():
                bidang_similarity = 1
            elif any(b.strip().lower() in bidang.lower() for b in tempat['bidang_pekerjaan'].split(',')):
                bidang_similarity = 0.7
                
        tempat_fasilitas = tempat['fasilitas'].split(',') if tempat['fasilitas'] else []
        match_fasilitas = len(set(fasilitas) & set(tempat_fasilitas)) / max(len(fasilitas), 1) if fasilitas else 0
        
        durasi_match = 1 if durasi and str(tempat['durasi']) == durasi else 0
        
        kategori_kuota = kuota_to_category(tempat['kuota'])
        kategori_user = 'sedikit' if kuota == '1' else 'sedang' if kuota == '2' else 'banyak'
        kuota_match = 1 if kategori_kuota == kategori_user else 0
        
        try:
            jarak_tempat = float(tempat.get('jarak') or 0)
        except (ValueError, TypeError):
            jarak_tempat = 0
            
        jarak_score = 1 if jarak_tempat < 5 else 0.6 if 5 <= jarak_tempat <= 10 else 0.2
        
        similarity_score = (
            0.35 * bidang_similarity + 
            0.20 * match_fasilitas + 
            0.15 * durasi_match + 
            0.15 * kuota_match + 
            0.15 * jarak_score
        )

        tempat['score'] = round(similarity_score, 2)
        
        if similarity_score >= 0.75:
            kategori = "Sangat Direkomendasikan"
        elif similarity_score >= 0.5:
            kategori = "Direkomendasikan"
        elif similarity_score >= 0.3:
            kategori = "Kurang Direkomendasikan"
        else:
            kategori = "Tidak Direkomendasikan"
            
        tempat['rekomendasi'] = kategori
        
        keterangan = []
        if bidang_similarity > 0:
            keterangan.append(f"bidang {bidang}")
        if match_fasilitas > 0:
            keterangan.append(f"fasilitas sesuai {int(match_fasilitas*100)}%")
        if durasi_match > 0:
            keterangan.append(f"durasi sesuai")
        if kuota_match > 0:
            keterangan.append(f"kuota {kategori_kuota}")
        if jarak_tempat < 5:
            keterangan.append(f"jarak dekat ({jarak_tempat} km)")
        elif 5 <= jarak_tempat <= 10:
            keterangan.append(f"jarak sedang ({jarak_tempat} km)")
        else:
            keterangan.append(f"jarak jauh ({jarak_tempat} km)")
            
        tempat['keterangan'] = f"{kategori}: {', '.join(keterangan)}"
        hasil_rekomendasi.append(tempat)

    hasil_rekomendasi.sort(key=lambda x: x['score'], reverse=True)

    cursor.close()
    return render_template('pilih_pkl.html', data_tempat_pkl=hasil_rekomendasi)