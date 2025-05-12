-- phpMyAdmin SQL Dump
-- version 5.2.0
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: May 12, 2025 at 06:58 AM
-- Server version: 8.0.30
-- PHP Version: 8.1.10

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `db_sistem_pkl`
--

-- --------------------------------------------------------

--
-- Table structure for table `admin`
--

CREATE TABLE `admin` (
  `id` int NOT NULL,
  `nama` varchar(100) COLLATE utf8mb4_general_ci NOT NULL,
  `email` varchar(100) COLLATE utf8mb4_general_ci NOT NULL,
  `no_hp` varchar(20) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `password` varchar(100) COLLATE utf8mb4_general_ci NOT NULL,
  `foto` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `admin`
--

INSERT INTO `admin` (`id`, `nama`, `email`, `no_hp`, `password`, `foto`, `created_at`) VALUES
(2, 'admin1', 'admin@gmail.com', '1287853673', '$2b$12$Zgbov3IKp7DBAbTUnenB6uS43U..bJgw4/gTT9dEP6W45tQLLTN.y', 'aliando.jpg', '2025-04-20 10:30:26');

-- --------------------------------------------------------

--
-- Table structure for table `lamaran_pkl`
--

CREATE TABLE `lamaran_pkl` (
  `id` int NOT NULL,
  `siswa_id` int NOT NULL,
  `tempat_pkl_id` int NOT NULL,
  `surat_pengantar` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `kartu_pelajar` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `cv` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `status` enum('Menunggu','Diterima','Ditolak') COLLATE utf8mb4_general_ci DEFAULT 'Menunggu',
  `tanggal_lamaran` datetime DEFAULT CURRENT_TIMESTAMP,
  `status_pkl` enum('Aktif','Selesai') COLLATE utf8mb4_general_ci DEFAULT NULL,
  `konfirmasi` varchar(10) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `tanggal_diterima` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `lamaran_pkl`
--

INSERT INTO `lamaran_pkl` (`id`, `siswa_id`, `tempat_pkl_id`, `surat_pengantar`, `kartu_pelajar`, `cv`, `status`, `tanggal_lamaran`, `status_pkl`, `konfirmasi`, `tanggal_diterima`) VALUES
(22, 9, 39, 'Peserta_Seminar_Proposal_KAMIS_27_FEBRUARI_2025.pdf', 'aliando.jpg', 'Peserta_Seminar_Proposal_KAMIS_27_FEBRUARI_2025.pdf', 'Ditolak', '2025-04-23 20:15:53', NULL, NULL, '2025-04-27 13:25:17'),
(23, 9, 40, 'Peserta_Seminar_Proposal_KAMIS_27_FEBRUARI_2025.pdf', 'dilan.jpg', 'Peserta_Seminar_Proposal_KAMIS_12_DESEMBER_2024.pdf', 'Diterima', '2025-04-23 23:12:16', 'Selesai', 'ambil', '2025-04-27 13:29:01'),
(26, 9, 39, 'cupuzdefault.groups.name.managerconvert.pdf', 'removed.png', '245-1748-1-PB_1.pdf', 'Diterima', '2025-05-03 13:27:03', 'Selesai', 'ambil', '2025-05-03 13:27:18'),
(27, 11, 55, 'adminJurnalMoch.NurAdiwana.pdf', 'MAULIDA-Alur_Penelitian.drawio.png', 'ARTIKELFISLING_CINDYASAPUTRI_230210102051UP.pdf', 'Menunggu', '2025-05-09 05:49:55', NULL, NULL, NULL);

-- --------------------------------------------------------

--
-- Table structure for table `mitra`
--

CREATE TABLE `mitra` (
  `id` int NOT NULL,
  `nama_perusahaan` varchar(100) COLLATE utf8mb4_general_ci NOT NULL,
  `institusi` enum('Pemerintah','Swasta') COLLATE utf8mb4_general_ci DEFAULT NULL,
  `alamat` text COLLATE utf8mb4_general_ci NOT NULL,
  `no_hp` varchar(20) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `email` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `password` varchar(100) COLLATE utf8mb4_general_ci NOT NULL,
  `foto` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `mitra`
--

INSERT INTO `mitra` (`id`, `nama_perusahaan`, `institusi`, `alamat`, `no_hp`, `email`, `password`, `foto`, `created_at`) VALUES
(2, 'Unit Smk Muhammadiyah 18', 'Swasta', 'Pangkalan Berandan', '08986525441', 'mitra@gmail.com', '$2b$12$oYtajk1Vh/lWoUmsqmMghu7xdPng4JSBG9SdAexESZ5aWWCdXI0Y2', 'logo_smk.png', '2025-04-20 07:50:08'),
(7, 'Telkom Pangkalan Berandan', 'Pemerintah', 'Pangkalan Berandan', NULL, 'mitra2@gmail.com', '$2b$12$oYtajk1Vh/lWoUmsqmMghu7xdPng4JSBG9SdAexESZ5aWWCdXI0Y2', NULL, '2025-04-27 06:26:52'),
(8, 'Malikussaleh University', 'Pemerintah', 'Lhoksuemawe', '082165443677', 'aji@gmail.com', '$2b$12$oYtajk1Vh/lWoUmsqmMghu7xdPng4JSBG9SdAexESZ5aWWCdXI0Y2', NULL, '2025-05-08 23:00:27');

-- --------------------------------------------------------

--
-- Table structure for table `siswa`
--

CREATE TABLE `siswa` (
  `id` int NOT NULL,
  `nama_siswa` varchar(100) COLLATE utf8mb4_general_ci NOT NULL,
  `nis` varchar(20) COLLATE utf8mb4_general_ci NOT NULL,
  `jurusan` varchar(50) COLLATE utf8mb4_general_ci NOT NULL,
  `kelas` varchar(20) COLLATE utf8mb4_general_ci NOT NULL,
  `email` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `password` varchar(100) COLLATE utf8mb4_general_ci NOT NULL,
  `no_hp` varchar(20) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `foto` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `siswa`
--

INSERT INTO `siswa` (`id`, `nama_siswa`, `nis`, `jurusan`, `kelas`, `email`, `password`, `no_hp`, `foto`, `created_at`) VALUES
(2, 'jalol', '82653272', 'Teknik Komputer Jaringan', '', 'siswa@gmail.com', '$2b$12$dUFvi2T5kUuuQeR/A2ngcexoobIqaYLoETF04HH9wLhdAZ2q0ZpK2', NULL, 'dilan.jpg', '2025-04-20 05:18:11'),
(9, 'M.Rizky', '7635263', 'Teknik Jaringan Jaringan', '', 'kygaming@gmail.com', '$2b$12$Zz59bIkez9Kb5Mut97Qg8eZ61SR196MDaDiYlFsuhZdZ06SEfQGvu', 'None', 'foto_rikzy.jpg', '2025-04-23 13:04:45'),
(11, 'Khairul Huda', '1234567890', 'Teknik Kimia', 'XI IPS 1', 'khairulhuda242@gmail.com', '$2b$12$Zgbov3IKp7DBAbTUnenB6uS43U..bJgw4/gTT9dEP6W45tQLLTN.y', NULL, NULL, '2025-05-08 22:47:25');

-- --------------------------------------------------------

--
-- Table structure for table `tempat_pkl`
--

CREATE TABLE `tempat_pkl` (
  `id` int NOT NULL,
  `foto` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `nama_tempat` varchar(100) COLLATE utf8mb4_general_ci NOT NULL,
  `institusi` enum('Pemerintah','Swasta') COLLATE utf8mb4_general_ci NOT NULL,
  `bidang_pekerjaan` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `fasilitas` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `durasi` enum('2 Bulan, 3x Seminggu','2 Bulan, 4x Seminggu','2 Bulan, 5x Seminggu','2 Bulan, 6x Seminggu') COLLATE utf8mb4_general_ci NOT NULL,
  `kuota` int NOT NULL,
  `alamat` varchar(255) COLLATE utf8mb4_general_ci NOT NULL,
  `deskripsi` text COLLATE utf8mb4_general_ci NOT NULL,
  `mitra_id` int DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `jarak` decimal(10,2) DEFAULT NULL,
  `label_durasi` varchar(20) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `label_fasilitas` varchar(20) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `label_kuota` varchar(20) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `label_jarak` varchar(20) COLLATE utf8mb4_general_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `tempat_pkl`
--

INSERT INTO `tempat_pkl` (`id`, `foto`, `nama_tempat`, `institusi`, `bidang_pekerjaan`, `fasilitas`, `durasi`, `kuota`, `alamat`, `deskripsi`, `mitra_id`, `created_at`, `jarak`, `label_durasi`, `label_fasilitas`, `label_kuota`, `label_jarak`) VALUES
(39, 'telkom_brandan.jpg', 'Telkom Pangkalan Berandan', 'Pemerintah', 'Jaringan', 'Komputer, internet, Perangkat Jaringan, Printer, Scanner', '2 Bulan, 5x Seminggu', 5, 'Pangkalan Berandan', 'Bagus', 2, '2025-04-23 13:10:57', '0.28', 'Panjang', 'Sangat Lengkap', 'Sedang', 'Dekat'),
(40, 'telkom_binjai.jpg', 'Telkom Kendati Binjai', 'Pemerintah', 'Jaringan', 'Komputer, internet, Perangkat Jaringan, Printer, Scanner', '2 Bulan, 5x Seminggu', 5, 'Binjai', 'mantap', 2, '2025-04-23 15:17:51', '60.00', 'Panjang', 'Sangat Lengkap', 'Sedang', NULL),
(41, 'samsat_brandan.jpg', 'Samsat Pangkalan Berandan', 'Pemerintah', 'Multimedia', 'Komputer, internet, Printer, Scanner', '2 Bulan, 5x Seminggu', 4, 'Pangkalan Berandan', '4', 2, '2025-04-24 04:33:49', NULL, 'Panjang', 'Sedang', 'Sedang', NULL),
(42, 'smp_bangun_mulia.jpg', 'SMP Swasta Bangun Mulia', 'Pemerintah', 'Administrasi', 'Komputer, internet, Printer', '2 Bulan, 6x Seminggu', 2, 'Pangkalan Berandan', ' Bagus', 2, '2025-04-27 03:22:50', '2.00', 'Panjang', 'Sedang', 'Sedikit', 'Dekat'),
(43, 'kantor_pos.jpg', 'Kantor POS Pangkalan Berandan', 'Pemerintah', 'Administrasi, Multimedia', 'Komputer, Printer', '2 Bulan, 5x Seminggu', 3, 'Pangkalan Berandan', ' Bagus', 2, '2025-04-27 03:28:57', '0.55', 'Panjang', 'Kurang', 'Sedikit', 'Dekat'),
(44, 'Pertagas_pangkalan_susu.jpg', 'Pertagas Pangkalan Susu', 'Pemerintah', 'Jaringan', 'Komputer, internet, Perangkat Jaringan, Printer', '2 Bulan, 5x Seminggu', 2, 'Pangkalan Susu', ' Bagus', 2, '2025-04-27 03:38:02', '0.40', 'Panjang', 'Sedang', 'Sedikit', 'Dekat'),
(45, 'aneka_digital_studi.jpg', 'Aneka Digital Studio', 'Swasta', 'Jaringan', 'Komputer, internet, Perangkat Jaringan, Printer, Scanner', '2 Bulan, 3x Seminggu', 10, 'Pangkalan Berandan', 'Bagus ', 2, '2025-04-27 03:43:28', '25.00', 'Pendek', 'Sangat Lengkap', 'Banyak', 'Jauh'),
(46, 'Pltu_susu.jpg', 'PLTU Pangkalan Susu', 'Pemerintah', 'Jaringan', 'Komputer, internet, Perangkat Jaringan, Printer, Scanner', '2 Bulan, 5x Seminggu', 2, 'Pangkalan Susu', 'Bagus ', 2, '2025-04-27 03:49:02', '25.00', 'Panjang', 'Sangat Lengkap', 'Sedikit', 'Jauh'),
(47, 'Lkp_Tifa.jpg', 'LKP Tifa Karya', 'Swasta', 'Jaringan', 'Komputer, internet, Perangkat_Jaringan, Printer', '2 Bulan, 3x Seminggu', 13, 'Pangkalan Berandan', ' Bagus', 2, '2025-04-27 03:56:06', '0.35', 'Pendek', 'Sedang', 'Banyak', 'Dekat'),
(48, 'Smk_Muhammadiyah.jpg', 'Unit Produksi SMK Muhammdiyah 18', 'Swasta', 'Jaringan', 'Komputer, internet, Perangkat Jaringan, Printer', '2 Bulan, 6x Seminggu', 15, 'Pangkalan Berandan', 'Bagus ', 2, '2025-04-27 03:58:16', '0.05', 'Panjang', 'Sedang', 'Banyak', 'Dekat'),
(49, 'Rs_pertamina.jpg', 'RS Pertamina P.Berandan', 'Swasta', 'Jaringan', 'Komputer, internet, Perangkat Jaringan, Printer, Scanner', '2 Bulan, 6x Seminggu', 4, 'Pangkalan Berandan', ' Bagus', 2, '2025-04-27 04:01:17', '0.80', 'Panjang', 'Sangat Lengkap', 'Sedang', 'Dekat'),
(50, 'Camat_babaln.jpg', 'Kantor Kecamatan Babalan', 'Pemerintah', 'Administrasi', 'Komputer, internet, Printer, Scanner', '2 Bulan, 5x Seminggu', 3, 'Pangkalan Berandan', 'Bagus ', 2, '2025-04-27 04:07:03', '4.00', 'Panjang', 'Sedang', 'Sedikit', 'Dekat'),
(51, 'camat_seilepan.jpg', 'Kantor Kecamatan Sei Lepan', 'Pemerintah', 'Administrasi', 'Komputer, internet, Printer, Scanner', '2 Bulan, 5x Seminggu', 2, 'Tangkahan Durian', ' Bagus', 2, '2025-04-27 04:12:26', '5.00', 'Panjang', 'Sedang', 'Sedikit', 'Sedang'),
(52, 'paluh_manis.jpg', 'Kantor Desa Paluh Manis', 'Pemerintah', 'Administrasi', 'Komputer, internet, Printer', '2 Bulan, 5x Seminggu', 2, 'Gebang', ' Bagus', 2, '2025-04-27 04:13:47', '8.00', 'Panjang', 'Sedang', 'Sedikit', 'Sedang'),
(53, 'curai.jpg', 'Kantor Desa Securai Utara', 'Pemerintah', 'Administrasi', 'Komputer, Printer', '2 Bulan, 5x Seminggu', 2, 'Curai Utara', ' Bagus', 2, '2025-04-27 04:19:33', '4.00', 'Panjang', 'Kurang', 'Sedikit', 'Dekat'),
(54, 'Pln_brandan.jpg', 'Kantor PLN P.Berandan', 'Pemerintah', 'Administrasi', 'Komputer, internet, Printer, Scanner', '2 Bulan, 5x Seminggu', 3, 'Pangkalan Berandan', 'Bagus ', 2, '2025-04-27 04:28:17', '0.30', 'Panjang', 'Sedang', 'Sedikit', 'Dekat'),
(55, 'smp_n1.jpg', 'SMP Negri 1 Babalan', 'Pemerintah', 'Administrasi', 'Komputer, internet, Printer', '2 Bulan, 6x Seminggu', 2, 'Pangkalan Berandan', ' Bagus', 2, '2025-04-27 04:31:16', '0.75', 'Panjang', 'Sedang', 'Sedikit', 'Dekat'),
(56, 'negri_2.jpg', 'SMP Negri 2 Babalan', 'Pemerintah', 'Administrasi, Multimedia', 'Komputer, internet, Printer', '2 Bulan, 6x Seminggu', 3, 'Pangkalan Berandan', ' Bagus', 2, '2025-04-27 04:41:05', '0.75', 'Panjang', 'Sedang', 'Sedikit', 'Dekat');

--
-- Triggers `tempat_pkl`
--
DELIMITER $$
CREATE TRIGGER `trigger_label_tempat_pkl` BEFORE INSERT ON `tempat_pkl` FOR EACH ROW BEGIN
  -- Label Durasi
  SET NEW.label_durasi = CASE
    WHEN NEW.durasi LIKE '%3x%' THEN 'Pendek'
    WHEN NEW.durasi LIKE '%4x%' THEN 'Sedang'
    WHEN NEW.durasi LIKE '%5x%' OR NEW.durasi LIKE '%6x%' THEN 'Panjang'
    ELSE NULL
  END;

  -- Label Kuota
  SET NEW.label_kuota = CASE
    WHEN NEW.kuota <= 3 THEN 'Sedikit'
    WHEN NEW.kuota BETWEEN 4 AND 7 THEN 'Sedang'
    WHEN NEW.kuota >= 8 THEN 'Banyak'
    ELSE NULL
  END;

  -- Label Jarak
  SET NEW.label_jarak = CASE
    WHEN NEW.jarak < 5 THEN 'Dekat'
    WHEN NEW.jarak BETWEEN 5 AND 10 THEN 'Sedang'
    WHEN NEW.jarak > 10 THEN 'Jauh'
    ELSE NULL
  END;

  -- Label Fasilitas (jumlah koma + 1)
  SET @jumlah_fasilitas = LENGTH(NEW.fasilitas) - LENGTH(REPLACE(NEW.fasilitas, ',', '')) + 1;
  SET NEW.label_fasilitas = CASE
    WHEN @jumlah_fasilitas <= 2 THEN 'Kurang'
    WHEN @jumlah_fasilitas BETWEEN 3 AND 4 THEN 'Sedang'
    WHEN @jumlah_fasilitas >= 5 THEN 'Sangat Lengkap'
    ELSE NULL
  END;
END
$$
DELIMITER ;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `admin`
--
ALTER TABLE `admin`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- Indexes for table `lamaran_pkl`
--
ALTER TABLE `lamaran_pkl`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_lamaran_tempat` (`tempat_pkl_id`),
  ADD KEY `lamaran_pkl_ibfk_1` (`siswa_id`);

--
-- Indexes for table `mitra`
--
ALTER TABLE `mitra`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `siswa`
--
ALTER TABLE `siswa`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `tempat_pkl`
--
ALTER TABLE `tempat_pkl`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_mitra` (`mitra_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `admin`
--
ALTER TABLE `admin`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `lamaran_pkl`
--
ALTER TABLE `lamaran_pkl`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=28;

--
-- AUTO_INCREMENT for table `mitra`
--
ALTER TABLE `mitra`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT for table `siswa`
--
ALTER TABLE `siswa`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT for table `tempat_pkl`
--
ALTER TABLE `tempat_pkl`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=60;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `lamaran_pkl`
--
ALTER TABLE `lamaran_pkl`
  ADD CONSTRAINT `fk_lamaran_tempat` FOREIGN KEY (`tempat_pkl_id`) REFERENCES `tempat_pkl` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `lamaran_pkl_ibfk_1` FOREIGN KEY (`siswa_id`) REFERENCES `siswa` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `lamaran_pkl_ibfk_2` FOREIGN KEY (`tempat_pkl_id`) REFERENCES `tempat_pkl` (`id`);

--
-- Constraints for table `tempat_pkl`
--
ALTER TABLE `tempat_pkl`
  ADD CONSTRAINT `fk_mitra` FOREIGN KEY (`mitra_id`) REFERENCES `mitra` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
