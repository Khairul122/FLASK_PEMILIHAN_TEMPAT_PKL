from flask import Blueprint, render_template, session, flash, redirect, url_for, request
from flask import current_app as app
from flask_mysqldb import MySQLdb
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import itertools

tempat_pkl_siswa_routes = Blueprint('tempat_pkl_siswa_routes', __name__)

def init_tempat_pkl_siswa_routes(mysql):
    global db
    db = mysql

@tempat_pkl_siswa_routes.route('/pilih-pkl', methods=['POST'])
def tampilkan_input_user():
    bidang_user = request.form.get('bidang_keahlian', '').strip().lower()
    durasi_user = request.form.get('durasi_pkl', '').strip().lower()
    fasilitas_level_user = request.form.get('fasilitas_level', '').strip().lower()
    kuota_user = request.form.get('kuota', '').strip().lower()
    jarak_user = request.form.get('jarak', '').strip().lower()

    print(f"\n=== INPUT YANG DIISI USER ===")
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

    # Fungsi keanggotaan fuzzy untuk durasi
    def μ_durasi_pendek(durasi_str):
        if '3x' in durasi_str:
            return 1.0
        elif '4x' in durasi_str:
            return 0.5
        elif '5x' in durasi_str:
            return 0.1
        else:
            return 0.0

    def μ_durasi_sedang(durasi_str):
        if '4x' in durasi_str:
            return 1.0
        elif '3x' in durasi_str or '5x' in durasi_str:
            return 0.5
        else:
            return 0.0

    def μ_durasi_panjang(durasi_str):
        if '6x' in durasi_str:
            return 1.0
        elif '5x' in durasi_str:
            return 0.8
        elif '4x' in durasi_str:
            return 0.2
        else:
            return 0.0

    # Fungsi keanggotaan fuzzy untuk fasilitas
    def μ_fasilitas(fasilitas_str, target_level):
        jumlah_fasilitas = len([f.strip() for f in fasilitas_str.split(',') if f.strip()])
        
        if target_level == 'kurang':
            if jumlah_fasilitas <= 2:
                return 1.0
            elif jumlah_fasilitas == 3:
                return 0.5
            else:
                return 0.0
        elif target_level == 'sedang':
            if jumlah_fasilitas in [3, 4]:
                return 1.0
            elif jumlah_fasilitas in [2, 5]:
                return 0.5
            else:
                return 0.0
        elif target_level == 'sangat lengkap':
            if jumlah_fasilitas >= 5:
                return 1.0
            elif jumlah_fasilitas == 4:
                return 0.7
            elif jumlah_fasilitas == 3:
                return 0.3
            else:
                return 0.0
        return 0.0

    # Fungsi keanggotaan fuzzy untuk kuota
    def μ_kuota_sedikit(kuota):
        if kuota <= 3:
            return 1.0
        elif 3 < kuota <= 5:
            return (5 - kuota) / 2
        else:
            return 0.0

    def μ_kuota_sedang(kuota):
        if 4 <= kuota <= 7:
            return 1.0
        elif 2 <= kuota < 4:
            return (kuota - 2) / 2
        elif 7 < kuota <= 9:
            return (9 - kuota) / 2
        else:
            return 0.0

    def μ_kuota_banyak(kuota):
        if kuota >= 8:
            return 1.0
        elif 6 <= kuota < 8:
            return (kuota - 6) / 2
        else:
            return 0.0

    # Fungsi keanggotaan fuzzy untuk jarak
    def μ_jarak_dekat(jarak):
        if jarak <= 1:
            return 1.0
        elif 1 < jarak < 5:
            return (5 - jarak) / 4
        else:
            return 0.0

    def μ_jarak_sedang(jarak):
        if 5 <= jarak <= 8:
            return 1.0
        elif 2 <= jarak < 5:
            return (jarak - 2) / 3
        elif 8 < jarak <= 12:
            return (12 - jarak) / 4
        else:
            return 0.0

    def μ_jarak_jauh(jarak):
        if jarak >= 15:
            return 1.0
        elif 10 <= jarak < 15:
            return (jarak - 10) / 5
        else:
            return 0.0

    hasil_tempat = []

    for tempat in semua_tempat:
        # Skor untuk bidang (similarity antara bidang user dan bidang tempat)
        if bidang_user and tempat['bidang_pekerjaan']:
            if bidang_user in tempat['bidang_pekerjaan'].lower():
                bidang_score = 1.0
            elif any(b.strip().lower() in bidang_user or bidang_user in b.strip().lower() 
                    for b in tempat['bidang_pekerjaan'].split(',')):
                bidang_score = 0.6
            else:
                bidang_score = 0.0
        else:
            bidang_score = 0.0
        
        # Skor durasi (berdasarkan fuzzy membership)
        if durasi_user == 'pendek':
            durasi_score = μ_durasi_pendek(tempat['durasi'])
        elif durasi_user == 'sedang':
            durasi_score = μ_durasi_sedang(tempat['durasi'])
        elif durasi_user == 'panjang':
            durasi_score = μ_durasi_panjang(tempat['durasi'])
        else:
            durasi_score = 0.0
        
        # Skor fasilitas (berdasarkan fuzzy membership)
        fasilitas_score = μ_fasilitas(tempat['fasilitas'] or '', fasilitas_level_user)
        
        # Skor kuota (berdasarkan fuzzy membership)
        kuota_nilai = int(tempat['kuota'] or 0)
        if kuota_user == 'sedikit':
            kuota_score = μ_kuota_sedikit(kuota_nilai)
        elif kuota_user == 'sedang':
            kuota_score = μ_kuota_sedang(kuota_nilai)
        elif kuota_user == 'banyak':
            kuota_score = μ_kuota_banyak(kuota_nilai)
        else:
            kuota_score = 0.0
        
        # Skor jarak (berdasarkan fuzzy membership)
        try:
            jarak_nilai = float(tempat['jarak'] or 0)
        except (ValueError, TypeError):
            jarak_nilai = 0
            
        if jarak_user == 'dekat':
            jarak_score = μ_jarak_dekat(jarak_nilai)
        elif jarak_user == 'sedang':
            jarak_score = μ_jarak_sedang(jarak_nilai)
        elif jarak_user == 'jauh':
            jarak_score = μ_jarak_jauh(jarak_nilai)
        else:
            jarak_score = 0.0

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
            if nilai_min >= 0.8:
                kategori = 'sangat_direkomendasikan'
            elif nilai_min >= 0.5:
                kategori = 'direkomendasikan'
            elif nilai_min >= 0.2:
                kategori = 'kurang_direkomendasikan'
            elif nilai_min > 0:
                kategori = 'tidak_direkomendasikan'
            else:
                continue

            rule_strengths.append((nilai_min, kategori))
            rule_detail.append({
                'rule': f"Rule-{rule_id}",
                'kombinasi': f"IF {a} ({himpunan[a]:.2f}) AND {b} ({himpunan[b]:.2f}) AND {c} ({himpunan[c]:.2f}) THEN {kategori.replace('_', ' ').capitalize()}",
                'α_predikat': round(nilai_min, 4)
            })
            rule_id += 1

        if rule_strengths:
            numerator = sum(s * kategori_output[k] for s, k in rule_strengths)
            denominator = sum(s for s, _ in rule_strengths)
            skor_fuzzy_normalized = (numerator / denominator) / 5
        else:
            skor_fuzzy_normalized = 0.0

        skor_hybrid = (skor_kbrs + skor_fuzzy_normalized) / 2

        if skor_hybrid >= 0.75:
            rekomendasi = "Sangat Direkomendasikan"
        elif skor_hybrid >= 0.5:
            rekomendasi = "Direkomendasikan"
        elif skor_hybrid >= 0.3:
            rekomendasi = "Kurang Direkomendasikan"
        else:
            rekomendasi = "Tidak Direkomendasikan"

        tempat['skor_kbrs'] = round(skor_kbrs, 3)
        tempat['skor_fuzzy'] = round(skor_fuzzy_normalized, 3)
        tempat['score'] = round(skor_hybrid, 3)
        tempat['rekomendasi'] = rekomendasi
        tempat['nilai_keanggotaan'] = {k: round(v, 3) for k, v in himpunan.items()}
        tempat['rules_terpicu'] = rule_detail

        print(f"{tempat['nama_tempat']}: KBRS = {skor_kbrs:.3f}, Fuzzy = {skor_fuzzy_normalized:.3f}, Hybrid = {skor_hybrid:.3f} → {rekomendasi}")
        for r in rule_detail:
            print(f"{r['rule']}: {r['kombinasi']}, α = {r['α_predikat']}")

        hasil_tempat.append(tempat)

    # Urutkan hasil berdasarkan skor (dari tinggi ke rendah)
    hasil_tempat.sort(key=lambda x: x['score'], reverse=True)
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
    jarak = request.form.get('jarak')

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

    # Fungsi fuzzy untuk kemiripan bidang
    def bidang_similarity_fuzzy(bidang_tempat, bidang_user):
        if not bidang_user or not bidang_tempat:
            return 0.0
            
        if bidang_user.lower() in bidang_tempat.lower():
            return 1.0
        
        # Cek kemiripan berdasarkan kata individual
        bidang_tempat_keywords = [k.strip().lower() for k in bidang_tempat.split(',')]
        bidang_user_keywords = [k.strip().lower() for k in bidang_user.split(',')]
        
        matches = sum(1 for k1 in bidang_user_keywords for k2 in bidang_tempat_keywords if k1 in k2 or k2 in k1)
        total_keywords = max(len(bidang_user_keywords), 1)
        
        return min(matches / total_keywords, 1.0)
    
    # Fungsi fuzzy untuk kemiripan fasilitas
    def fasilitas_similarity_fuzzy(fasilitas_tempat, fasilitas_user):
        if not fasilitas_user or not fasilitas_tempat:
            return 0.0
            
        fasilitas_tempat_list = [f.strip().lower() for f in fasilitas_tempat.split(',')]
        fasilitas_user_list = [f.strip().lower() for f in fasilitas_user]
        
        # Hitung jumlah fasilitas yang cocok (dengan pencocokan parsial)
        matches = 0
        for f_user in fasilitas_user_list:
            best_match = max([1.0 if f_user in f_tempat or f_tempat in f_user else 0.0 for f_tempat in fasilitas_tempat_list], default=0.0)
            matches += best_match
            
        return min(matches / max(len(fasilitas_user_list), 1), 1.0)
    
    # Fungsi fuzzy untuk kemiripan kuota
    def kuota_similarity_fuzzy(kuota_tempat, kuota_option):
        if not kuota_option:
            return 0.0
            
        kuota_nilai = int(kuota_tempat or 0)
        
        if kuota_option == '1':  # Sedikit
            if kuota_nilai <= 3:
                return 1.0
            elif 3 < kuota_nilai <= 5:
                return (5 - kuota_nilai) / 2
            else:
                return 0.0
        elif kuota_option == '2':  # Sedang
            if 4 <= kuota_nilai <= 7:
                return 1.0
            elif 2 <= kuota_nilai < 4:
                return (kuota_nilai - 2) / 2
            elif 7 < kuota_nilai <= 9:
                return (9 - kuota_nilai) / 2
            else:
                return 0.0
        elif kuota_option == '3':  # Banyak
            if kuota_nilai >= 8:
                return 1.0
            elif 6 <= kuota_nilai < 8:
                return (kuota_nilai - 6) / 2
            else:
                return 0.0
        else:
            return 0.0
    
    # Fungsi fuzzy untuk kemiripan jarak
    def jarak_similarity_fuzzy(jarak_tempat, jarak_option):
        if not jarak_option:
            return 0.0
            
        try:
            jarak_nilai = float(jarak_tempat or 0)
        except (ValueError, TypeError):
            jarak_nilai = 0.0
            
        if jarak_option == '1':  # Dekat
            if jarak_nilai <= 1:
                return 1.0
            elif 1 < jarak_nilai < 5:
                return (5 - jarak_nilai) / 4
            else:
                return 0.0
        elif jarak_option == '2':  # Sedang
            if 5 <= jarak_nilai <= 8:
                return 1.0
            elif 2 <= jarak_nilai < 5:
                return (jarak_nilai - 2) / 3
            elif 8 < jarak_nilai <= 12:
                return (12 - jarak_nilai) / 4
            else:
                return 0.0
        elif jarak_option == '3':  # Jauh
            if jarak_nilai >= 15:
                return 1.0
            elif 10 <= jarak_nilai < 15:
                return (jarak_nilai - 10) / 5
            else:
                return 0.0
        else:
            return 0.0

    for tempat in all_tempat_pkl:
        bidang_sim = bidang_similarity_fuzzy(tempat['bidang_pekerjaan'], bidang)
        fasilitas_sim = fasilitas_similarity_fuzzy(tempat['fasilitas'], fasilitas)
        
        durasi_match = 1.0 if durasi and str(tempat['durasi']) == durasi else 0.0
        
        kuota_sim = kuota_similarity_fuzzy(tempat['kuota'], kuota)
        jarak_sim = jarak_similarity_fuzzy(tempat['jarak'], jarak)
            
        similarity_score = (
            0.35 * bidang_sim + 
            0.20 * fasilitas_sim + 
            0.15 * durasi_match + 
            0.15 * kuota_sim + 
            0.15 * jarak_sim
        )

        tempat['score'] = round(similarity_score, 3)
        
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
        if bidang_sim > 0:
            keterangan.append(f"bidang {bidang} (kecocokan: {int(bidang_sim*100)}%)")
        if fasilitas_sim > 0:
            keterangan.append(f"fasilitas sesuai {int(fasilitas_sim*100)}%")
        if durasi_match > 0:
            keterangan.append(f"durasi sesuai 100%")
        if kuota_sim > 0:
            keterangan.append(f"kuota kecocokan {int(kuota_sim*100)}%")
        if jarak_sim > 0:
            jarak_value = tempat.get('jarak', 0)
            keterangan.append(f"jarak {jarak_value} km (kecocokan: {int(jarak_sim*100)}%)")
            
        tempat['keterangan'] = f"{kategori}: {', '.join(keterangan)}"
        hasil_rekomendasi.append(tempat)

    hasil_rekomendasi.sort(key=lambda x: x['score'], reverse=True)

    cursor.close()
    return render_template('pilih_pkl.html', data_tempat_pkl=hasil_rekomendasi)