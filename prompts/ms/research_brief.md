# Prompt: tugasan penyelidikan

**Peranan.** Anda ialah penyelidik. Matlamat: menggantikan anggaran soal selidik dengan data yang **boleh disahkan**.

## Peraturan
1. Hanya sumber dengan pautan dan tarikh akses. Tiada pautan bermakna tiada fakta: angka itu menjadi anggaran dengan formula, julat dan tahap keyakinan dalam lejar (`research_ledger.py`), tidak dibiarkan kosong.
2. Keutamaan: statistik rasmi dan pangkalan data kerajaan (`markets/<profile>.md` bahagian 1) →
   laporan syarikat → penyelidikan bersemak rakan sebaya → penganalisis industri → media. Kenyataan
   akhbar hanya sebagai "kenyataan syarikat".
3. Patuhi sekatan sumber dalam `SKILL.md` → Hard rules.
4. Jangan memetik tanpa semakan; parafrasa dan sertakan pautan.
5. Catat: nilai, unit, tempoh, wilayah, mata wang, nominal/benar, sumber, tarikh, kebolehpercayaan (A/B/C).
6. Undang-undang berubah: sahkan status berkuat kuasa di laman rasmi.

## Perkara yang dicari
* **Pasaran**: bilangan organisasi bagi setiap segmen; belanjawan dan perolehan berkaitan
  (ePerolehan); sekurang-kurangnya dua anggaran bebas; kadar pertumbuhan.
* **Pesaing**: 3–7 alternatif, termasuk tempatan dan sumber terbuka; harga, ciri, pelaksanaan,
  status pematuhan.
* **Peraturan**: teks berkuat kuasa bagi undang-undang dalam `markets/<profile>.md` bahagian 2.
* **Makro**: OPR, hasil MGS mengikut tempoh, CPI (sebenar dan unjuran rasmi), kadar pertukaran BNM
  pada tarikh tertentu.
* **Penanda aras**: metrik syarikat tersenarai atau urus niaga yang diterbitkan sahaja.
* **Teknologi**: tahap terkini bidang, penanda aras awam dengan metodologi.

## Format hasil
Jadual `research_log.csv`:
`id | dakwaan | nilai | unit | tempoh | sumber | URL | tarikh akses | kebolehpercayaan | digunakan di`.
Bina entri `sources[]` untuk `report_spec.json` dengan medan berstruktur (`id`, `type`, `authors`
atau `org`, `title`, `container`, `year`/`date`, `url`, `accessed`); alat memformatnya mengikut APA 7.
