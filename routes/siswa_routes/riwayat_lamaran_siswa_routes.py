from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from MySQLdb.cursors import DictCursor

riwayat_lamaran_siswa_routes = Blueprint('riwayat_lamaran_siswa_routes', __name__)
mysql = None

def init_riwayat_lamaran_siswa_routes(mysql_instance):
    global mysql
    mysql = mysql_instance


from datetime import datetime, timedelta

@riwayat_lamaran_siswa_routes.route('/kegiatanku', methods=['GET'])
def kegiatanku():
    if 'role' not in session or session['role'] != 'siswa':
        flash('Akses ditolak!', 'danger')
        return redirect(url_for('auth.login'))

    siswa_id = session.get('user_id')
    cur = mysql.connection.cursor(DictCursor)

    query = """
    SELECT 
        lamaran_pkl.id,
        tempat_pkl.nama_tempat,
        tempat_pkl.bidang_pekerjaan,
        tempat_pkl.alamat,
        lamaran_pkl.tanggal_lamaran,
        lamaran_pkl.tanggal_diterima,
        lamaran_pkl.status,
        lamaran_pkl.konfirmasi,
        lamaran_pkl.status_pkl
    FROM lamaran_pkl
    JOIN tempat_pkl ON lamaran_pkl.tempat_pkl_id = tempat_pkl.id
    WHERE lamaran_pkl.siswa_id = %s
    ORDER BY lamaran_pkl.tanggal_lamaran DESC
    """
    cur.execute(query, (siswa_id,))
    riwayat_lamaran = cur.fetchall()

    # Hitung countdown dan update status jika waktu habis
    for lamaran in riwayat_lamaran:
        if lamaran['status'] == 'Diterima' and lamaran['konfirmasi'] is None and lamaran['tanggal_diterima']:
            batas_waktu = lamaran['tanggal_diterima'] + timedelta(days=3)
            now = datetime.now()

            if now > batas_waktu:
                # Otomatis update status menjadi Ditolak
                update_query = """
                UPDATE lamaran_pkl
                SET status = 'Ditolak'
                WHERE id = %s
                """
                cur.execute(update_query, (lamaran['id'],))
                mysql.connection.commit()
                lamaran['status'] = 'Ditolak'
            else:
                # Hitung sisa waktu dalam detik
                lamaran['sisa_waktu_detik'] = int((batas_waktu - now).total_seconds())

    cur.close()

    return render_template('kegiatanku.html', riwayat_lamaran=riwayat_lamaran)



# === Route untuk tombol AMBIL ===
@riwayat_lamaran_siswa_routes.route('/lamaran/ambil/<int:lamaran_id>', methods=['POST'])
def ambil_lamaran(lamaran_id):
    cur = mysql.connection.cursor()
    query = """
    UPDATE lamaran_pkl
    SET konfirmasi = 'ambil',
        status_pkl = 'Aktif'
    WHERE id = %s AND status = 'Diterima'
    """
    cur.execute(query, (lamaran_id,))
    mysql.connection.commit()
    cur.close()
    flash('Lamaran diambil. Status PKL aktif.', 'success')
    return redirect(url_for('riwayat_lamaran_siswa_routes.kegiatanku'))


# === Route untuk tombol TOLAK ===
@riwayat_lamaran_siswa_routes.route('/lamaran/tolak/<int:lamaran_id>', methods=['POST'])
def tolak_lamaran(lamaran_id):
    cur = mysql.connection.cursor()
    query = """
    UPDATE lamaran_pkl
    SET konfirmasi = 'tolak',
        status = 'Ditolak'
    WHERE id = %s AND status = 'Diterima'
    """
    cur.execute(query, (lamaran_id,))
    mysql.connection.commit()
    cur.close()
    flash('Lamaran ditolak oleh siswa.', 'warning')
    return redirect(url_for('riwayat_lamaran_siswa_routes.kegiatanku'))


# === Route untuk tombol SELESAI ===
@riwayat_lamaran_siswa_routes.route('/lamaran/selesai/<int:lamaran_id>', methods=['POST'])
def selesai_pkl(lamaran_id):
    cur = mysql.connection.cursor()
    query = """
    UPDATE lamaran_pkl
    SET status_pkl = 'Selesai'
    WHERE id = %s AND status_pkl = 'Aktif'
    """
    cur.execute(query, (lamaran_id,))
    mysql.connection.commit()
    cur.close()
    flash('PKL selesai.', 'info')
    return redirect(url_for('riwayat_lamaran_siswa_routes.kegiatanku'))


