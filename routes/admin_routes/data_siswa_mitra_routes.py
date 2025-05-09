from flask import Blueprint, render_template, session, redirect, url_for, flash
from flask_mysqldb import MySQLdb, MySQL
from MySQLdb.cursors import DictCursor

data_siswa_mitra = Blueprint('data_siswa_mitra', __name__)
mysql = None

def init_data_siswa_mitra(mysql_instance):
    global mysql
    mysql = mysql_instance

@data_siswa_mitra.route('/data-siswa')
def data_siswa():
    if session.get('role') != 'admin':
        flash('Anda tidak memiliki akses ke halaman ini.', 'danger')
        return redirect(url_for('auth.login'))

    try:
        cur = mysql.connection.cursor(DictCursor)
        cur.execute("SELECT * FROM siswa")
        data_siswa = cur.fetchall()
        cur.close()

        return render_template('admin/data_siswa.html', data_siswa=data_siswa)

    except Exception as e:
        print(f"Error saat mengambil data siswa: {e}")
        flash('Terjadi kesalahan saat mengambil data siswa.', 'danger')
        return render_template("admin/data_siswa.html")


@data_siswa_mitra.route('/hapus-siswa/<int:id>', methods=['POST', 'GET'])
def hapus_siswa(id):
    if session.get('role') != 'admin':
        flash('Anda tidak memiliki akses ke halaman ini.', 'danger')
        return redirect(url_for('auth.login'))

    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM siswa WHERE id = %s", (id,))
        mysql.connection.commit()
        cur.close()
        flash('Data siswa berhasil dihapus.', 'success')
    except Exception as e:
        print(f"Error saat menghapus data siswa: {e}")
        flash('Terjadi kesalahan saat menghapus data siswa.', 'danger')

    return redirect(url_for('data_siswa_mitra.data_siswa'))



@data_siswa_mitra.route('/data-mitra')
def data_mitra():
    if session.get('role') != 'admin':
        flash('Anda tidak memiliki akses ke halaman ini.', 'danger')
        return redirect(url_for('auth.login'))

    try:
        cur = mysql.connection.cursor(DictCursor)
        cur.execute("SELECT * FROM mitra")
        data_mitra = cur.fetchall()
        cur.close()

        return render_template('admin/data_mitra.html', data_mitra=data_mitra)

    except Exception as e:
        print(f"Error saat mengambil data mitra: {e}")
        flash('Terjadi kesalahan saat mengambil data mitra.', 'danger')
        return render_template("admin/data_mitra.html")



@data_siswa_mitra.route('/hapus-mitra/<int:id>', methods=['GET', 'POST'])
def hapus_mitra(id):
    if session.get('role') != 'admin':
        flash('Anda tidak memiliki akses ke halaman ini.', 'danger')
        return redirect(url_for('auth.login'))

    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM mitra WHERE id = %s", (id,))
        mysql.connection.commit()
        cur.close()
        flash('Data mitra berhasil dihapus.', 'success')
    except Exception as e:
        print(f"Error saat menghapus data mitra: {e}")
        flash('Terjadi kesalahan saat menghapus data mitra.', 'danger')

    return redirect(url_for('data_siswa_mitra.data_mitra'))





@data_siswa_mitra.route('/siswa-pkl', methods=['GET'])
def siswa_pkl_page():
    if 'role' not in session or session['role'] != 'admin':
        flash('Akses ditolak! Anda tidak memiliki akses ke halaman ini.', 'danger')
        return redirect(url_for('auth.login'))

    try:
        # Query untuk mengambil data siswa yang sedang PKL
        cur = mysql.connection.cursor(DictCursor)
        cur.execute("""
            SELECT
        siswa.id,
        siswa.nama_siswa,
        siswa.nis,
        siswa.kelas,
        tempat_pkl.nama_tempat,
        mitra.nama_perusahaan,  -- Menambahkan kolom nama_perusahaan dari tabel mitra
        tempat_pkl.institusi,
        tempat_pkl.bidang_pekerjaan,
        tempat_pkl.durasi,
        lamaran_pkl.status_pkl,
        tempat_pkl.alamat  -- Menambahkan alamat tempat_pkl
        FROM lamaran_pkl
        JOIN siswa ON lamaran_pkl.siswa_id = siswa.id
        JOIN tempat_pkl ON lamaran_pkl.tempat_pkl_id = tempat_pkl.id
        JOIN mitra ON tempat_pkl.mitra_id = mitra.id  -- Menggabungkan dengan tabel mitra untuk mendapatkan nama_perusahaan
        WHERE lamaran_pkl.status_pkl = 'Aktif'
        """)
        data_siswa_pkl = cur.fetchall()

        # Query untuk menghitung jumlah siswa yang sedang PKL
        cur.execute("""
            SELECT COUNT(*) as jumlah_siswa_pkl
            FROM lamaran_pkl
            WHERE status_pkl = 'Aktif'
        """)
        jumlah_siswa_pkl = cur.fetchone()['jumlah_siswa_pkl']
        cur.close()

        return render_template('admin/siswa_pkl.html', data_siswa_pkl=data_siswa_pkl, jumlah_siswa_pkl=jumlah_siswa_pkl)

    except Exception as e:
        print(f"Error saat mengambil data siswa PKL: {e}")
        flash('Terjadi kesalahan saat mengambil data siswa PKL.', 'danger')
        return redirect(url_for('admin'))



@data_siswa_mitra.route('/siswa-selesai-pkl', methods=['GET'])
def siswa_selesai_pkl_page():
    if 'role' not in session or session['role'] != 'admin':
        flash('Akses ditolak! Anda tidak memiliki akses ke halaman ini.', 'danger')
        return redirect(url_for('auth.login'))

    try:
        # Query untuk mengambil data siswa yang sudah selesai PKL
        cur = mysql.connection.cursor(DictCursor)
        cur.execute("""
            SELECT
                siswa.id,
                siswa.nama_siswa,
                siswa.nis,
                siswa.kelas,
                tempat_pkl.nama_tempat,
                mitra.nama_perusahaan,
                tempat_pkl.institusi,
                tempat_pkl.bidang_pekerjaan,
                tempat_pkl.durasi,
                lamaran_pkl.status_pkl,
                tempat_pkl.alamat
            FROM lamaran_pkl
            JOIN siswa ON lamaran_pkl.siswa_id = siswa.id
            JOIN tempat_pkl ON lamaran_pkl.tempat_pkl_id = tempat_pkl.id
            JOIN mitra ON tempat_pkl.mitra_id = mitra.id
            WHERE lamaran_pkl.status_pkl = 'Selesai'
        """)
        data_siswa_selesai_pkl = cur.fetchall()

        # Query untuk menghitung jumlah siswa yang selesai PKL
        cur.execute("""
            SELECT COUNT(*) as jumlah_siswa_selesai_pkl
            FROM lamaran_pkl
            WHERE status_pkl = 'Selesai'
        """)
        jumlah_siswa_selesai_pkl = cur.fetchone()['jumlah_siswa_selesai_pkl']
        cur.close()

        return render_template('admin/siswa_selesai_pkl.html', data_siswa_selesai_pkl=data_siswa_selesai_pkl, jumlah_siswa_selesai_pkl=jumlah_siswa_selesai_pkl)

    except Exception as e:
        print(f"Error saat mengambil data siswa selesai PKL: {e}")
        flash('Terjadi kesalahan saat mengambil data siswa selesai PKL.', 'danger')
        return redirect(url_for('admin'))
