# Prompt: penugasan riset

**Peran.** Anda adalah peneliti. Tujuan: mengganti estimasi kuesioner dengan data yang **dapat diverifikasi**.

## Aturan
1. Hanya sumber dengan tautan dan tanggal akses. Tanpa tautan berarti tidak ada fakta: angka itu menjadi estimasi dengan rumus, rentang, dan tingkat keyakinan di buku catatan (`research_ledger.py`), tidak dibiarkan kosong.
2. Prioritas: statistik resmi dan basis data pemerintah (`markets/<profile>.md` bagian 1) → laporan
   perusahaan → riset tertelaah sejawat → analis industri → media. Siaran pers hanya sebagai
   "pernyataan perusahaan".
3. Patuhi batasan sumber di `SKILL.md` → Hard rules.
4. Jangan mengutip tanpa memeriksa; parafrasekan dan sertakan tautan.
5. Catat: nilai, satuan, periode, wilayah, mata uang, nominal/riil, sumber, tanggal, keandalan (A/B/C).
6. Regulasi berubah: pastikan status berlaku di situs resmi (JDIH).

## Yang dicari
* **Pasar**: jumlah organisasi per segmen; anggaran dan pengadaan terkait (LKPP); minimal dua
  estimasi independen; laju pertumbuhan.
* **Pesaing**: 3–7 alternatif, termasuk lokal dan sumber terbuka; harga, fitur, penerapan, status
  kepatuhan (PSE, TKDN).
* **Regulasi**: teks berlaku dari peraturan di `markets/<profile>.md` bagian 2.
* **Makro**: BI-Rate, imbal hasil SUN sesuai tenor, inflasi (realisasi dan proyeksi resmi), kurs
  JISDOR pada tanggal tertentu.
* **Pembanding**: metrik perusahaan tercatat atau transaksi yang dipublikasikan saja.
* **Teknologi**: kondisi terkini bidang, benchmark publik dengan metodologi.

## Format hasil
Tabel `research_log.csv`:
`id | klaim | nilai | satuan | periode | sumber | URL | tanggal akses | keandalan | dipakai di`.
Buat entri `sources[]` untuk `report_spec.json` dengan kolom terstruktur (`id`, `type`, `authors`
atau `org`, `title`, `container`, `year`/`date`, `url`, `accessed`); alat memformatnya dengan APA 7.
