from flask import Blueprint, render_template, session, redirect, url_for, flash
import MySQLdb

data_tempat_pkl_view = Blueprint('data_tempat_pkl_view', __name__)
mysql = None

def init_data_tempat_pkl_view(mysql_instance):
    global mysql
    mysql = mysql_instance

# @data_tempat_pkl_view.route('/admin')
# def admin():
#     if session.get('role') != 'admin':
#         flash('Anda tidak memiliki akses ke halaman ini.', 'danger')
#         return redirect(url_for('auth.login'))

#     cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
#     cursor.execute("""
#         SELECT tp.*, m.nama_perusahaan 
#         FROM tempat_pkl tp
#         JOIN mitra m ON tp.mitra_id = m.id
#     """)
#     data_tempat_pkl = cursor.fetchall()
#     cursor.close()

#     return render_template('admin/admin.html', data_tempat_pkl=data_tempat_pkl)



@data_tempat_pkl_view.route('/admin')
def admin():
    if session.get('role') != 'admin':
        flash('Anda tidak memiliki akses ke halaman ini.', 'danger')
        return redirect(url_for('auth.login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    # Query untuk menghitung jumlah tempat PKL
    cursor.execute("SELECT COUNT(*) AS total_tempat_pkl FROM tempat_pkl")
    total_tempat_pkl = cursor.fetchone()['total_tempat_pkl']
    
    # Query untuk menghitung jumlah siswa PKL yang aktif
    cursor.execute("SELECT COUNT(*) AS total_siswa_pkl FROM lamaran_pkl WHERE status_pkl = 'aktif'")
    total_siswa_pkl = cursor.fetchone()['total_siswa_pkl']
    
    # Query untuk menghitung jumlah siswa PKL yang selesai
    cursor.execute("SELECT COUNT(*) AS total_siswa_selesai_pkl FROM lamaran_pkl WHERE status_pkl = 'selesai'")
    total_siswa_selesai_pkl = cursor.fetchone()['total_siswa_selesai_pkl']
    
    cursor.execute("""
        SELECT tp.*, m.nama_perusahaan 
        FROM tempat_pkl tp
        JOIN mitra m ON tp.mitra_id = m.id
    """)
    data_tempat_pkl = cursor.fetchall()
    cursor.close()

    return render_template('admin/admin.html', 
                           data_tempat_pkl=data_tempat_pkl,
                           total_tempat_pkl=total_tempat_pkl,
                           total_siswa_pkl=total_siswa_pkl,
                           total_siswa_selesai_pkl=total_siswa_selesai_pkl)




@data_tempat_pkl_view.route('/hapus_tempat_pkl/<int:id>', methods=['POST'])
def hapus_tempat_pkl(id):
    if session.get('role') != 'admin':
        flash('Anda tidak memiliki akses ke halaman ini.', 'danger')
        return redirect(url_for('auth.login'))

    try:
        cursor = mysql.connection.cursor()
        cursor.execute("DELETE FROM tempat_pkl WHERE id = %s", (id,))
        mysql.connection.commit()
        cursor.close()
        flash('Data tempat PKL berhasil dihapus.', 'success')
    except Exception as e:
        flash(f'Terjadi kesalahan saat menghapus: {str(e)}', 'danger')

    return redirect(url_for('data_tempat_pkl_view.admin'))

