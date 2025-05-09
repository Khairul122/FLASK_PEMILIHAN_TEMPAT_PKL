from flask import Blueprint, render_template, session, redirect, url_for, flash
from MySQLdb.cursors import DictCursor

lamaran_pkl_mitra = Blueprint('lamaran_pkl_mitra', __name__)
mysql = None

def init_lamaran_pkl_mitra(mysql_instance):
    global mysql
    mysql = mysql_instance

@lamaran_pkl_mitra.route('/lamaran-mitra', methods=['GET'])
def lamaran_mitra():
    if 'role' not in session or session['role'] != 'mitra':
        flash('Akses ditolak!', 'danger')
        return redirect(url_for('auth.login'))

    mitra_id = session.get('user_id')
    cur = mysql.connection.cursor(DictCursor)  

    query = """
    SELECT
        lamaran_pkl.id,
        siswa.foto,
        siswa.nama_siswa,
        siswa.nis,
        siswa.jurusan,
        siswa.email,
        siswa.no_hp,
        lamaran_pkl.surat_pengantar,
        lamaran_pkl.kartu_pelajar,
        lamaran_pkl.cv,
        lamaran_pkl.status
    FROM lamaran_pkl
    JOIN siswa ON lamaran_pkl.siswa_id = siswa.id
    JOIN tempat_pkl ON lamaran_pkl.tempat_pkl_id = tempat_pkl.id
    WHERE tempat_pkl.mitra_id = %s
    ORDER BY lamaran_pkl.tanggal_lamaran DESC
    """

    cur.execute(query, (mitra_id,))
    lamaran_data = cur.fetchall()
    cur.close()

    return render_template('mitra/lamaran_mitra.html', lamaran_data=lamaran_data)




# @lamaran_pkl_mitra.route('/lamaran-mitra/terima/<int:lamaran_id>', methods=['POST', 'GET'])
# def terima_lamaran(lamaran_id):
#     if 'role' not in session or session['role'] != 'mitra':
#         flash('Akses ditolak!', 'danger')
#         return redirect(url_for('auth.login'))

#     cur = mysql.connection.cursor()
#     cur.execute("UPDATE lamaran_pkl SET status = 'Diterima' WHERE id = %s", (lamaran_id,))
#     mysql.connection.commit()
#     cur.close()
#     flash('Lamaran berhasil diterima.', 'success')
#     return redirect(url_for('lamaran_pkl_mitra.lamaran_mitra'))



@lamaran_pkl_mitra.route('/lamaran-mitra/terima/<int:lamaran_id>', methods=['POST', 'GET'])
def terima_lamaran(lamaran_id):
    if 'role' not in session or session['role'] != 'mitra':
        flash('Akses ditolak!', 'danger')
        return redirect(url_for('auth.login'))

    cur = mysql.connection.cursor()

    # Update status menjadi Diterima dan set tanggal_diterima
    cur.execute("""
        UPDATE lamaran_pkl
        SET status = 'Diterima',
            tanggal_diterima = NOW()
        WHERE id = %s
    """, (lamaran_id,))

    # Cek apakah status_pkl atau konfirmasi tidak NULL
    cur.execute("""
        SELECT status_pkl, konfirmasi 
        FROM lamaran_pkl 
        WHERE id = %s
    """, (lamaran_id,))
    result = cur.fetchone()

    if result and (result[0] is not None or result[1] is not None):
        # Reset nilai jika ada isinya
        cur.execute("""
            UPDATE lamaran_pkl 
            SET status_pkl = NULL, konfirmasi = NULL 
            WHERE id = %s
        """, (lamaran_id,))

    mysql.connection.commit()
    cur.close()

    flash('Lamaran berhasil diterima.', 'success')
    return redirect(url_for('lamaran_pkl_mitra.lamaran_mitra'))





@lamaran_pkl_mitra.route('/lamaran-mitra/tolak/<int:lamaran_id>', methods=['POST', 'GET'])
def tolak_lamaran(lamaran_id):
    if 'role' not in session or session['role'] != 'mitra':
        flash('Akses ditolak!', 'danger')
        return redirect(url_for('auth.login'))

    cur = mysql.connection.cursor()
    # Pertama update status ke Ditolak
    cur.execute("UPDATE lamaran_pkl SET status = 'Ditolak' WHERE id = %s", (lamaran_id,))

    # Cek apakah status_pkl atau konfirmasi ada isinya (tidak NULL)
    cur.execute("""
        SELECT status_pkl, konfirmasi 
        FROM lamaran_pkl 
        WHERE id = %s
    """, (lamaran_id,))
    result = cur.fetchone()
    if result and (result[0] is not None or result[1] is not None):
        # Reset jika ada isi sebelumnya
        cur.execute("""
            UPDATE lamaran_pkl 
            SET status_pkl = NULL, konfirmasi = NULL 
            WHERE id = %s
        """, (lamaran_id,))

    mysql.connection.commit()
    cur.close()
    flash('Lamaran berhasil ditolak.', 'danger')
    return redirect(url_for('lamaran_pkl_mitra.lamaran_mitra'))



@lamaran_pkl_mitra.route('/mitra', methods=['GET'])
def mitra():
    if 'role' not in session or session['role'] != 'mitra':
        flash('Akses ditolak!', 'danger')
        return redirect(url_for('auth.login'))

    mitra_id = session.get('user_id')
    cur = mysql.connection.cursor(DictCursor)

    # Ambil total semua lamaran (apapun statusnya)
    cur.execute("""
        SELECT COUNT(*) AS total_lamaran
        FROM lamaran_pkl
        JOIN tempat_pkl ON lamaran_pkl.tempat_pkl_id = tempat_pkl.id
        WHERE tempat_pkl.mitra_id = %s
    """, (mitra_id,))
    total_lamaran = cur.fetchone()['total_lamaran']


    # Ambil total lamaran diterima
    cur.execute("""
        SELECT COUNT(*) AS total_diterima
        FROM lamaran_pkl
        JOIN tempat_pkl ON lamaran_pkl.tempat_pkl_id = tempat_pkl.id
        WHERE lamaran_pkl.status = 'Diterima' AND tempat_pkl.mitra_id = %s
    """, (mitra_id,))
    total_diterima = cur.fetchone()['total_diterima']

    # Ambil total lamaran ditolak
    cur.execute("""
        SELECT COUNT(*) AS total_ditolak
        FROM lamaran_pkl
        JOIN tempat_pkl ON lamaran_pkl.tempat_pkl_id = tempat_pkl.id
        WHERE lamaran_pkl.status = 'Ditolak' AND tempat_pkl.mitra_id = %s
    """, (mitra_id,))
    total_ditolak = cur.fetchone()['total_ditolak']

    # Ambil data tempat PKL yang dimiliki oleh mitra
    cur.execute("""
        SELECT *
        FROM tempat_pkl
        WHERE mitra_id = %s
    """, (mitra_id,))
    data_tempat_pkl = cur.fetchall()


    cur.close()

    return render_template('mitra/mitra.html', 
                           total_lamaran=total_lamaran,
                           total_diterima=total_diterima, 
                           total_ditolak=total_ditolak,
                           data_tempat_pkl=data_tempat_pkl)


@lamaran_pkl_mitra.route('/siswa-pkl-mitra', methods=['GET'])
def siswa_pkl_mitra():
    if 'role' not in session or session['role'] != 'mitra':
        flash('Akses ditolak!', 'danger')
        return redirect(url_for('auth.login'))

    mitra_id = session.get('user_id')
    cur = mysql.connection.cursor(DictCursor)

    try:
        # Update status_pkl menjadi 'Aktif' kalau masih kosong
        cur.execute("""
            SELECT COUNT(*) AS jumlah FROM lamaran_pkl
            JOIN tempat_pkl ON lamaran_pkl.tempat_pkl_id = tempat_pkl.id
            WHERE lamaran_pkl.status = 'Diterima' 
            AND (lamaran_pkl.status_pkl IS NULL OR lamaran_pkl.status_pkl = '')
            AND tempat_pkl.mitra_id = %s
        """, (mitra_id,))
        count = cur.fetchone()['jumlah']

        if count > 0:
            cur.execute("""
                UPDATE lamaran_pkl
                JOIN tempat_pkl ON lamaran_pkl.tempat_pkl_id = tempat_pkl.id
                SET lamaran_pkl.status_pkl = 'Aktif'
                WHERE lamaran_pkl.konfirmasi = 'ambil' 
                AND (lamaran_pkl.status_pkl IS NULL OR lamaran_pkl.status_pkl = '')
                AND tempat_pkl.mitra_id = %s
            """, (mitra_id,))
            mysql.connection.commit()

        # Update status_pkl menjadi NULL kalau status Ditolak
        cur.execute("""
            SELECT COUNT(*) AS jumlah FROM lamaran_pkl
            JOIN tempat_pkl ON lamaran_pkl.tempat_pkl_id = tempat_pkl.id
            WHERE lamaran_pkl.status = 'Ditolak'
            AND lamaran_pkl.status_pkl IS NOT NULL
            AND tempat_pkl.mitra_id = %s
        """, (mitra_id,))
        count_rejected = cur.fetchone()['jumlah']

        if count_rejected > 0:
            cur.execute("""
                UPDATE lamaran_pkl
                JOIN tempat_pkl ON lamaran_pkl.tempat_pkl_id = tempat_pkl.id
                SET lamaran_pkl.status_pkl = NULL
                WHERE lamaran_pkl.status = 'Ditolak'
                AND lamaran_pkl.status_pkl IS NOT NULL
                AND tempat_pkl.mitra_id = %s
            """, (mitra_id,))
            mysql.connection.commit()

        # Ambil semua siswa PKL
        cur.execute("""
            SELECT
                siswa.id, 
                siswa.nama_siswa,
                siswa.nis,
                siswa.kelas,
                siswa.jurusan,
                siswa.email,
                tempat_pkl.bidang_pekerjaan,
                tempat_pkl.durasi,
                lamaran_pkl.status_pkl
            FROM lamaran_pkl
            JOIN siswa ON lamaran_pkl.siswa_id = siswa.id
            JOIN tempat_pkl ON lamaran_pkl.tempat_pkl_id = tempat_pkl.id
            WHERE lamaran_pkl.status = 'Diterima'
            AND tempat_pkl.mitra_id = %s
        """, (mitra_id,))

        data_siswa_pkl = cur.fetchall()

        # Hitung jumlah siswa sedang PKL (status_pkl = Aktif)
        cur.execute("""
            SELECT COUNT(*) as sedang_pkl FROM lamaran_pkl
            JOIN tempat_pkl ON lamaran_pkl.tempat_pkl_id = tempat_pkl.id
            WHERE lamaran_pkl.status = 'Diterima' 
            AND lamaran_pkl.status_pkl = 'Aktif'
            AND tempat_pkl.mitra_id = %s
        """, (mitra_id,))
        sedang_pkl = cur.fetchone()['sedang_pkl']

        # Hitung jumlah siswa selesai PKL (status_pkl = Selesai)
        cur.execute("""
            SELECT COUNT(*) as selesai_pkl FROM lamaran_pkl
            JOIN tempat_pkl ON lamaran_pkl.tempat_pkl_id = tempat_pkl.id
            WHERE lamaran_pkl.status = 'Diterima' 
            AND lamaran_pkl.status_pkl = 'Selesai'
            AND tempat_pkl.mitra_id = %s
        """, (mitra_id,))
        selesai_pkl = cur.fetchone()['selesai_pkl']

    except Exception as e:
        print(f"Error: {e}")
        flash('Terjadi kesalahan saat memproses data!', 'danger')
        data_siswa_pkl = []
        sedang_pkl = 0
        selesai_pkl = 0
    finally:
        cur.close()

    return render_template(
        'mitra/siswa_pkl_mitra.html',
        data_siswa_pkl=data_siswa_pkl,
        sedang_pkl=sedang_pkl,
        selesai_pkl=selesai_pkl
    )



@lamaran_pkl_mitra.route('/selesai-pkl/<int:siswa_id>', methods=['POST'])
def selesai_pkl(siswa_id):
    if 'role' not in session or session['role'] != 'mitra':
        flash('Akses ditolak!', 'danger')
        return redirect(url_for('auth.login'))

    try:
        cur = mysql.connection.cursor()
        # Update status_pkl menjadi "Selesai" berdasarkan ID siswa
        cur.execute("""
            UPDATE lamaran_pkl
            SET status_pkl = 'Selesai'
            WHERE siswa_id = %s
        """, (siswa_id,))
        mysql.connection.commit()
        flash('Status PKL berhasil diubah menjadi Selesai.', 'success')
    except Exception as e:
        print(f"Error: {e}")
        flash('Terjadi kesalahan saat mengubah status!', 'danger')
    finally:
        cur.close()

    return redirect(url_for('lamaran_pkl_mitra.siswa_pkl_mitra'))
