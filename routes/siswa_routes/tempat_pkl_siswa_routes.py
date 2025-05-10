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

@tempat_pkl_siswa_routes.route('/pilih-pkl', methods=['GET', 'POST'])
def tampilkan_tempat_pkl():
    if request.method == 'POST':
        bidang_user = request.form.get('bidang_keahlian', '').strip().lower()
        durasi_user = request.form.get('durasi_pkl', '').strip().lower()
        fasilitas_level_user = request.form.get('fasilitas_level', '').strip().lower()
        kuota_user = request.form.get('kuota', '').strip().lower()
        jarak_user = request.form.get('jarak', '').strip().lower()

        print("\n=== PREPARATION INPUT USER ===")
        print(f"Bidang dipilih     : {bidang_user}")
        print(f"Durasi dipilih     : {durasi_user}")
        print(f"Fasilitas dipilih  : {fasilitas_level_user}")
        print(f"Kuota dipilih      : {kuota_user}")
        print(f"Jarak dipilih      : {jarak_user}")
        print("===============================\n")

        cursor = db.connection.cursor(MySQLdb.cursors.DictCursor)
        
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

        def count_fasilitas_items(fasilitas_str):
            if not fasilitas_str:
                return 0
            return len([item.strip() for item in fasilitas_str.split(',') if item.strip()])
        
        def parse_durasi(durasi_str):
            if "3x Seminggu" in durasi_str:
                return 3
            elif "4x Seminggu" in durasi_str:
                return 4
            elif "5x Seminggu" in durasi_str:
                return 5
            elif "6x Seminggu" in durasi_str:
                return 6
            return 0

        def get_bidang_similarity_score(bidang_user, bidang_tempat):
            if not bidang_user or not bidang_tempat:
                return 0.0
            bidang_user = bidang_user.lower()
            bidang_tempat = bidang_tempat.lower()

            if bidang_user == bidang_tempat:
                return 1.0
            
            tempat_bidang = [b.strip() for b in tempat_bidang.split(',')]
            if bidang_user in tempat_bidang:
                return 1.0
        
            return 
            
        
        def get_bidang_membership(similarity_score):
            memberships = {
                "sangat_cocok": 0.0,
                "cocok": 0.0,
                "cukup_cocok": 0.0, 
                "kurang_cocok": 0.0,
                "tidak_cocok": 0.0
            }
            
            if similarity_score >= 0.9:
                memberships["sangat_cocok"] = 1.0
            elif similarity_score >= 0.7:
                memberships["cocok"] = similarity_score
                memberships["sangat_cocok"] = similarity_score - 0.7
            elif similarity_score >= 0.5:
                memberships["cukup_cocok"] = similarity_score
                memberships["cocok"] = similarity_score - 0.5
            elif similarity_score >= 0.3:
                memberships["kurang_cocok"] = similarity_score
                memberships["cukup_cocok"] = similarity_score - 0.3
            else:
                memberships["tidak_cocok"] = 1.0 - similarity_score
                memberships["kurang_cocok"] = similarity_score
                
            return memberships
        
        def get_durasi_membership(days_per_week):
            memberships = {"pendek": 0.0, "sedang": 0.0, "panjang": 0.0}
            
            if days_per_week == 3:
                memberships["pendek"] = 1.0
            elif days_per_week == 4:
                memberships["sedang"] = 1.0
            elif days_per_week >= 5:
                memberships["panjang"] = 1.0
                
            return memberships
        
        def get_fasilitas_membership(fasilitas_count):
            memberships = {"kurang": 0.0, "sedang": 0.0, "lengkap": 0.0}
            
            if fasilitas_count <= 2:
                memberships["kurang"] = 1.0
            elif 3 <= fasilitas_count <= 4:
                memberships["sedang"] = 1.0
            else:
                memberships["lengkap"] = 1.0
                
            return memberships
        
        def get_kuota_membership(kuota_value):
            memberships = {"sedikit": 0.0, "sedang": 0.0, "banyak": 0.0}
            
            if kuota_value <= 3:
                memberships["sedikit"] = 1.0
            elif 4 <= kuota_value <= 7:
                memberships["sedang"] = 1.0
            else:
                memberships["banyak"] = 1.0
                
            return memberships
        
        def get_jarak_membership(jarak_value):
            memberships = {"dekat": 0.0, "sedang": 0.0, "jauh": 0.0}
            
            if jarak_value < 5:
                memberships["dekat"] = 1.0
            elif 5 <= jarak_value <= 10:
                memberships["sedang"] = 1.0
            else:
                memberships["jauh"] = 1.0
                
            return memberships
        
        def defuzzify_mamdani(rule_strengths, output_categories):
            if not rule_strengths:
                return 3
            
            numerator = 0
            denominator = 0
            
            for strength, category in rule_strengths:
                value = output_categories[category]
                numerator += strength * value
                denominator += strength
            
            if denominator == 0:
                return 3
                
            return numerator / denominator

        for tempat in semua_tempat:
            bidang_similarity = get_bidang_similarity_score(bidang_user, tempat.get('bidang_pekerjaan'))
            
            if bidang_similarity >= 0.7:
                cocok_bidang = 5
            else:
                cocok_bidang = round(bidang_similarity * 5)
            
            bidang_membership = get_bidang_membership(bidang_similarity)
            
            durasi_raw = tempat.get('durasi') or ''
            days_per_week = parse_durasi(durasi_raw)
            durasi_membership = get_durasi_membership(days_per_week)
            
            if days_per_week == 3:
                durasi_fuzzy = 'pendek'
            elif days_per_week == 4:
                durasi_fuzzy = 'sedang'
            else:
                durasi_fuzzy = 'panjang'
            
            durasi_score = 5 if durasi_fuzzy == durasi_user else 1
            
            fasilitas_count = count_fasilitas_items(tempat.get('fasilitas') or '')
            fasilitas_membership = get_fasilitas_membership(fasilitas_count)
            
            if fasilitas_count <= 2:
                fasilitas_fuzzy = 'kurang'
            elif 3 <= fasilitas_count <= 4:
                fasilitas_fuzzy = 'sedang'
            else:
                fasilitas_fuzzy = 'lengkap'
                
            fasilitas_score = 5 if fasilitas_fuzzy == fasilitas_level_user else 1
            
            try:
                kuota_tempat = int(tempat.get('kuota') or 0)
            except (ValueError, TypeError):
                kuota_tempat = 0
                
            kuota_membership = get_kuota_membership(kuota_tempat)
            
            if kuota_tempat <= 3:
                kuota_fuzzy = 'sedikit'
            elif 4 <= kuota_tempat <= 7:
                kuota_fuzzy = 'sedang'
            else:
                kuota_fuzzy = 'banyak'
                
            kuota_score = 5 if kuota_fuzzy == kuota_user else 1
            
            try:
                jarak_tempat = float(tempat.get('jarak') or 0)
            except (ValueError, TypeError):
                jarak_tempat = 0
                
            jarak_membership = get_jarak_membership(jarak_tempat)
            
            if jarak_tempat < 5:
                jarak_fuzzy = 'dekat'
            elif 5 <= jarak_tempat <= 10:
                jarak_fuzzy = 'sedang'
            else:
                jarak_fuzzy = 'jauh'
                
            jarak_score = 5 if jarak_fuzzy == jarak_user else 1
            
            skor_kbrs = (
                bobot['bidang'] * (cocok_bidang / 5) +
                bobot['durasi'] * (durasi_score / 5) +
                bobot['fasilitas'] * (fasilitas_score / 5) +
                bobot['kuota'] * (kuota_score / 5) +
                bobot['jarak'] * (jarak_score / 5)
            )
            
            print(f"\n--- MEMBERSHIP FUNCTION untuk {tempat.get('nama_tempat','Unknown')} ---")
            print(f"Bidang: {bidang_membership}")
            print(f"Durasi: {durasi_membership} (days_per_week: {days_per_week})")
            print(f"Fasilitas: {fasilitas_membership} (count: {fasilitas_count})")
            print(f"Kuota: {kuota_membership} (value: {kuota_tempat})")
            print(f"Jarak: {jarak_membership} (value: {jarak_tempat})")
            
            output_categories = {
                "tidak_direkomendasikan": 1,
                "kurang_direkomendasikan": 2, 
                "direkomendasikan": 4,
                "sangat_direkomendasikan": 5
            }
            
            rule_strengths = []
            rule_evaluations = []
            
            rule1 = min(jarak_membership["dekat"], kuota_membership["banyak"])
            if rule1 > 0:
                rule_strengths.append((rule1, "sangat_direkomendasikan"))
                rule_evaluations.append(("R1", rule1, "sangat_direkomendasikan"))
            
            rule2 = min(jarak_membership["sedang"], kuota_membership["sedang"])
            if rule2 > 0:
                rule_strengths.append((rule2, "direkomendasikan"))
                rule_evaluations.append(("R2", rule2, "direkomendasikan"))
            
            rule3 = min(jarak_membership["jauh"], kuota_membership["sedikit"])
            if rule3 > 0:
                rule_strengths.append((rule3, "tidak_direkomendasikan"))
                rule_evaluations.append(("R3", rule3, "tidak_direkomendasikan"))
            
            rule4 = min(fasilitas_membership["lengkap"], durasi_membership["panjang"])
            if rule4 > 0:
                rule_strengths.append((rule4, "sangat_direkomendasikan"))
                rule_evaluations.append(("R4", rule4, "sangat_direkomendasikan"))
            
            rule5 = min(fasilitas_membership["sedang"], durasi_membership["sedang"])
            if rule5 > 0:
                rule_strengths.append((rule5, "direkomendasikan"))
                rule_evaluations.append(("R5", rule5, "direkomendasikan"))
            
            rule6 = min(fasilitas_membership["kurang"], durasi_membership["pendek"])
            if rule6 > 0:
                rule_strengths.append((rule6, "kurang_direkomendasikan"))
                rule_evaluations.append(("R6", rule6, "kurang_direkomendasikan"))
            
            rule7 = min(bidang_membership["sangat_cocok"], fasilitas_membership["lengkap"])
            if rule7 > 0:
                rule_strengths.append((rule7, "sangat_direkomendasikan"))
                rule_evaluations.append(("R7", rule7, "sangat_direkomendasikan"))
            
            rule8 = min(bidang_membership["sangat_cocok"], durasi_membership["panjang"])
            if rule8 > 0:
                rule_strengths.append((rule8, "sangat_direkomendasikan"))
                rule_evaluations.append(("R8", rule8, "sangat_direkomendasikan"))
            
            rule9 = min(bidang_membership["sangat_cocok"], kuota_membership["banyak"])
            if rule9 > 0:
                rule_strengths.append((rule9, "sangat_direkomendasikan"))
                rule_evaluations.append(("R9", rule9, "sangat_direkomendasikan"))
            
            rule10 = min(bidang_membership["sangat_cocok"], jarak_membership["dekat"])
            if rule10 > 0:
                rule_strengths.append((rule10, "sangat_direkomendasikan"))
                rule_evaluations.append(("R10", rule10, "sangat_direkomendasikan"))
            
            rule11 = min(bidang_membership["tidak_cocok"], jarak_membership["jauh"])
            if rule11 > 0:
                rule_strengths.append((rule11, "tidak_direkomendasikan"))
                rule_evaluations.append(("R11", rule11, "tidak_direkomendasikan"))
            
            rule12 = min(fasilitas_membership["kurang"], jarak_membership["jauh"])
            if rule12 > 0:
                rule_strengths.append((rule12, "tidak_direkomendasikan"))
                rule_evaluations.append(("R12", rule12, "tidak_direkomendasikan"))
            
            rule13 = min(kuota_membership["sedikit"], bidang_membership["tidak_cocok"])
            if rule13 > 0:
                rule_strengths.append((rule13, "tidak_direkomendasikan"))
                rule_evaluations.append(("R13", rule13, "tidak_direkomendasikan"))
            
            rule14 = min(kuota_membership["sedang"], fasilitas_membership["lengkap"])
            if rule14 > 0:
                rule_strengths.append((rule14, "direkomendasikan"))
                rule_evaluations.append(("R14", rule14, "direkomendasikan"))
                
            rule15 = min(kuota_membership["banyak"], durasi_membership["panjang"])
            if rule15 > 0:
                rule_strengths.append((rule15, "sangat_direkomendasikan"))
                rule_evaluations.append(("R15", rule15, "sangat_direkomendasikan"))
            
            rule16 = min(bidang_membership["sangat_cocok"], fasilitas_membership["lengkap"], jarak_membership["dekat"])
            if rule16 > 0:
                rule_strengths.append((rule16, "sangat_direkomendasikan"))
                rule_evaluations.append(("R16", rule16, "sangat_direkomendasikan"))
                
            rule17 = min(bidang_membership["cocok"], fasilitas_membership["sedang"], jarak_membership["sedang"])
            if rule17 > 0:
                rule_strengths.append((rule17, "direkomendasikan"))
                rule_evaluations.append(("R17", rule17, "direkomendasikan"))
                
            rule18 = min(bidang_membership["tidak_cocok"], fasilitas_membership["kurang"], jarak_membership["jauh"])
            if rule18 > 0:
                rule_strengths.append((rule18, "tidak_direkomendasikan"))
                rule_evaluations.append(("R18", rule18, "tidak_direkomendasikan"))
            
            rule19 = min(bidang_membership["cukup_cocok"], kuota_membership["banyak"])
            if rule19 > 0:
                rule_strengths.append((rule19, "direkomendasikan"))
                rule_evaluations.append(("R19", rule19, "direkomendasikan"))
                
            rule20 = min(bidang_membership["kurang_cocok"], kuota_membership["sedikit"])
            if rule20 > 0:
                rule_strengths.append((rule20, "kurang_direkomendasikan"))
                rule_evaluations.append(("R20", rule20, "kurang_direkomendasikan"))
            
            rule21 = min(bidang_membership["sangat_cocok"], durasi_membership["pendek"])
            if rule21 > 0:
                rule_strengths.append((rule21, "direkomendasikan"))
                rule_evaluations.append(("R21", rule21, "direkomendasikan"))
            
            rule22 = min(bidang_membership["cukup_cocok"], durasi_membership["panjang"])
            if rule22 > 0:
                rule_strengths.append((rule22, "direkomendasikan"))
                rule_evaluations.append(("R22", rule22, "direkomendasikan"))
            
            rule23 = min(fasilitas_membership["lengkap"], kuota_membership["banyak"], jarak_membership["dekat"])
            if rule23 > 0:
                rule_strengths.append((rule23, "sangat_direkomendasikan"))
                rule_evaluations.append(("R23", rule23, "sangat_direkomendasikan"))
            
            rule24 = min(fasilitas_membership["sedang"], kuota_membership["sedang"], jarak_membership["sedang"])
            if rule24 > 0:
                rule_strengths.append((rule24, "direkomendasikan"))
                rule_evaluations.append(("R24", rule24, "direkomendasikan"))
            
            rule25 = min(fasilitas_membership["lengkap"], bidang_membership["sangat_cocok"], jarak_membership["jauh"])
            if rule25 > 0:
                rule_strengths.append((rule25, "direkomendasikan"))
                rule_evaluations.append(("R25", rule25, "direkomendasikan"))
            
            print(f"\n--- RULE EVALUATION untuk {tempat.get('nama_tempat','Unknown')} ---")
            
            rules_terpicu = []
            for rule_id, strength, category in rule_evaluations:
                print(f"{rule_id}: {strength:.4f} -> {category}")
                if strength > 0:
                    rules_terpicu.append(f"{rule_id}({strength:.2f})")
            
            if rule_strengths:
                defuzzified_score = defuzzify_mamdani(rule_strengths, output_categories)
            else:
                defuzzified_score = 3
            
            defuzzified_normalized = max(0.2, defuzzified_score / 5)
            
            total_skor = round((skor_kbrs + defuzzified_normalized) / 2, 4)
            
            print(f"[{tempat.get('nama_tempat','Unknown')}] KBRS: {skor_kbrs:.4f}, Fuzzy: {defuzzified_score:.4f}, Normalized: {defuzzified_normalized:.4f}, Total: {total_skor:.4f}")
            
            if total_skor >= 0.75:
                rekomendasi_kategori = "Sangat Direkomendasikan"
            elif total_skor >= 0.5:
                rekomendasi_kategori = "Direkomendasikan"
            elif total_skor >= 0.3:
                rekomendasi_kategori = "Kurang Direkomendasikan"
            else:
                rekomendasi_kategori = "Tidak Direkomendasikan"
                
            bidang_label = "Sesuai Bidang" if bidang_similarity >= 0.7 else "Di Luar Bidang"
            
            keterangan_detail = []
            
            if bidang_user and bidang_similarity >= 0.7:
                keterangan_detail.append(f"bidang {bidang_user}")
            
            keterangan_detail.append(f"fasilitas {fasilitas_fuzzy}")
            keterangan_detail.append(f"kuota {kuota_fuzzy}")
            keterangan_detail.append(f"jarak {jarak_fuzzy}")
            keterangan_detail.append(f"durasi {durasi_fuzzy}")
            
            if rekomendasi_kategori == "Tidak Direkomendasikan":
                if jarak_fuzzy == 'jauh':
                    keterangan_detail.append("jarak terlalu jauh")
                if kuota_fuzzy == 'sedikit':
                    keterangan_detail.append("kuota terlalu sedikit")
            
            rule_explanations = {
                "R1": "Tempat PKL dekat dan memiliki kuota banyak",
                "R2": "Tempat PKL berjarak sedang dan memiliki kuota sedang",
                "R3": "Tempat PKL jauh dan memiliki kuota sedikit",
                "R4": "Tempat PKL memiliki fasilitas lengkap dan durasi panjang",
                "R5": "Tempat PKL memiliki fasilitas sedang dan durasi sedang",
                "R6": "Tempat PKL memiliki fasilitas kurang dan durasi pendek",
                "R7": "Bidang pekerjaan sangat cocok dan fasilitas lengkap",
                "R8": "Bidang pekerjaan sangat cocok dan durasi panjang",
                "R9": "Bidang pekerjaan sangat cocok dan kuota banyak",
                "R10": "Bidang pekerjaan sangat cocok dan jarak dekat",
                "R11": "Bidang pekerjaan tidak cocok dan jarak jauh",
                "R12": "Fasilitas kurang dan jarak jauh",
                "R13": "Kuota sedikit dan bidang pekerjaan tidak cocok",
                "R14": "Kuota sedang dan fasilitas lengkap",
                "R15": "Kuota banyak dan durasi panjang",
                "R16": "Bidang pekerjaan sangat cocok, fasilitas lengkap, dan jarak dekat",
                "R17": "Bidang pekerjaan cocok, fasilitas sedang, dan jarak sedang",
                "R18": "Bidang pekerjaan tidak cocok, fasilitas kurang, dan jarak jauh",
                "R19": "Bidang pekerjaan cukup cocok dan kuota banyak",
                "R20": "Bidang pekerjaan kurang cocok dan kuota sedikit",
                "R21": "Bidang pekerjaan sangat cocok dan durasi pendek",
                "R22": "Bidang pekerjaan cukup cocok dan durasi panjang",
                "R23": "Fasilitas lengkap, kuota banyak, dan jarak dekat",
                "R24": "Fasilitas sedang, kuota sedang, dan jarak sedang",
                "R25": "Fasilitas lengkap, bidang sangat cocok, tapi jarak jauh"
            }
            
            top_rules = sorted(rule_evaluations, key=lambda x: x[1], reverse=True)[:3]
            top_rule_ids = [rule[0] for rule in top_rules]
            top_rule_strengths = [rule[1] for rule in top_rules]
            
            explanation = "Direkomendasikan karena: "
            for i, rule_id in enumerate(top_rule_ids):
                if i > 0:
                    explanation += ", "
                rule_strength_pct = round(top_rule_strengths[i] * 100)
                explanation += f"{rule_explanations.get(rule_id, 'Rule lainnya')} ({rule_strength_pct}%)"
            
            keterangan = f"{rekomendasi_kategori}: {', '.join(keterangan_detail)}. {explanation}"
            rekomendasi_label = f"{bidang_label} - {rekomendasi_kategori}"
            
            if total_skor > 0:
                tempat['score'] = total_skor
                tempat['skor_kbrs'] = skor_kbrs
                tempat['skor_fuzzy'] = defuzzified_normalized
                tempat['rekomendasi'] = rekomendasi_label
                tempat['keterangan'] = keterangan
                tempat['rule_explanation'] = explanation
                
                if rules_terpicu:
                    tempat['rules_terpicu'] = ", ".join(rules_terpicu)
                
                hasil_rekomendasi.append(tempat)
        
        hasil_rekomendasi.sort(key=lambda x: x['score'], reverse=True)
        return render_template('pilih_pkl.html', data_tempat_pkl=hasil_rekomendasi)
        
    else:
        cursor = db.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM tempat_pkl")
        semua_tempat = cursor.fetchall()
        cursor.close()
        
        for tempat in semua_tempat:
            fasilitas_tempat = [f.strip().lower() for f in (tempat.get('fasilitas') or '').split(',')]
            fasilitas_count = len(set(fasilitas_tempat))
            
            if fasilitas_count <= 2:
                fasilitas_desc = "fasilitas kurang"
            elif 3 <= fasilitas_count <= 4:
                fasilitas_desc = "fasilitas sedang"
            else:
                fasilitas_desc = "fasilitas lengkap"
                
            try:
                kuota_tempat = int(tempat.get('kuota') or 0)
            except (ValueError, TypeError):
                kuota_tempat = 0
                
            if kuota_tempat <= 3:
                kuota_desc = "kuota sedikit"
            elif 4 <= kuota_tempat <= 7:
                kuota_desc = "kuota sedang"
            else:
                kuota_desc = "kuota banyak"
                
            try:
                jarak_tempat = float(tempat.get('jarak') or 0)
            except (ValueError, TypeError):
                jarak_tempat = 0
                
            if jarak_tempat < 5:
                jarak_desc = "jarak dekat"
            elif 5 <= jarak_tempat <= 10:
                jarak_desc = "jarak sedang"
            else:
                jarak_desc = "jarak jauh"
                
            durasi_raw = tempat.get('durasi') or ''
            if "3x Seminggu" in durasi_raw:
                durasi_desc = "durasi pendek"
            elif "4x Seminggu" in durasi_raw:
                durasi_desc = "durasi sedang"
            else:
                durasi_desc = "durasi panjang"
                
            skor_kbrs_default = 0.5
            skor_fuzzy_default = 0.5
            
            tempat['keterangan'] = f"Detail: {fasilitas_desc}, {kuota_desc}, {jarak_desc}, {durasi_desc}"
            tempat['skor_kbrs'] = skor_kbrs_default
            tempat['skor_fuzzy'] = skor_fuzzy_default
            
        return render_template('pilih_pkl.html', data_tempat_pkl=semua_tempat)
    
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