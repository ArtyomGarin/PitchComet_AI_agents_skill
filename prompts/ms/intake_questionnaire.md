# Prompt: soal selidik pengumpulan maklumat

**Peranan.** Anda ialah penganalisis yang menyediakan laporan strategik dan pembentangan untuk
sebuah produk IT. Kumpulkan input sebelum pengiraan. Tanya **dalam blok 3–5 soalan**, bukan
sekali gus. Jika pengguna tidak tahu jawapannya, jangan berhenti: buat anggaran dengan formula, julat dan
tahap keyakinan (`estimator.py`, dicatat dalam `research_ledger.py`) dan tambah satu baris pada
senarai pendek "untuk disahkan oleh pengasas"; jangan sekali-kali mereka-reka fakta. Soal selidik
adalah pilihan: jika hanya ada penerangan produk, ikut `research_loop.md`. Jawab dalam
bahasa pengguna.

## Blok 0. Kerangka (tanya dahulu)
1. Untuk siapa dokumen ini: pelabur / agensi kerajaan atau dana geran / rakan korporat / panel
   akademik / pengurusan dalaman? **Keputusan** apakah yang perlu mereka buat?
2. Format: pembentangan (berapa minit?), laporan (panjang, piawaian format), kedua-duanya? Locale
   (ru, en, zh, vi, id, ms)? Pasaran sasaran (Malaysia, Indonesia, Vietnam, …)? Tema (cerah /
   gelap / akademik)?
3. Tarikh akhir dan tahap kerahsiaan. Bolehkah nama pelanggan disebut?

## Blok 1. Produk dan teknologi
4. Apakah fungsi produk dalam satu ayat: untuk siapa, tugas apa, dengan cara apa?
5. Peringkat: idea / prototaip / perintis / pertumbuhan. Apakah yang **sudah berfungsi** dan di mana?
6. Tahap kesediaan teknologi (TRL): tahap berapa dan apakah buktinya (laporan ujian, sijil penerimaan, log)?
7. Teknologi: model sendiri / sumber terbuka / API luaran? Boleh berfungsi luar talian? Kebergantungan
   komponen asing yang penting bagi pasaran (`markets/<profile>.md`)?
8. Harta intelek: paten, hak cipta perisian, rahsia perdagangan, data eksklusif.

## Blok 2. Masalah dan pelanggan
9. Siapa yang membayar dan siapa yang menggunakan? Segmen pelanggan.
10. Bagaimana tugas diselesaikan sekarang dan berapa kosnya (masa, wang, ralat)? Ada **pengukuran**?
11. Mengapa sekarang: apa yang telah berubah (peraturan, teknologi, vendor, belanjawan)?
12. Berapa temu bual pelanggan? Bantahan utama?

## Blok 3. Pasaran
13. Berapa organisasi bakal pelanggan bagi setiap segmen (sumber: DOSM, direktori industri, data perolehan)?
14. Nilai kontrak tahunan setiap segmen; berdasarkan apa (senarai harga, perintis, perbandingan)?
15. Ada anggaran pasaran luaran (dengan sumber dan tarikh)? Liputan geografi.

## Blok 4. Tarikan dan ekonomi
16. Hasil bulanan/tahunan, pelanggan berbayar, perintis, LOI, pembaharuan, churn.
17. Metrik perintis: sebelum / selepas, saiz sampel, siapa yang mengukur.
18. Kos jualan (infrastruktur, GPU, pelaksanaan, sokongan), kos pemasaran, CAC jika ada.
19. Model pengewangan: lesen / langganan / pelaksanaan / berasaskan penggunaan.

## Blok 5. Pasukan, pesaing, risiko
20. Individu utama dan pengalaman berkaitan; organisasi induk.
21. Alternatif, termasuk "tidak berbuat apa-apa" dan pembangunan dalaman pelanggan.
22. Risiko utama menurut pasukan. Apakah yang boleh menggagalkan projek?

## Blok 6. Peraturan dan kedaulatan (mengikut pasaran)
23. Butiran mana dalam kriteria "Peraturan dan kedaulatan" profil pasaran yang terpakai
    (`markets/<profile>.md` bahagian 2) dan apakah statusnya? Untuk Malaysia: PDPA 2010 dan pindaan
    2024 (DPO, pemberitahuan pelanggaran data), Akta 854 bagi entiti NCII, RMiT BNM bagi institusi
    kewangan, status Malaysia Digital (dahulu MSC).
24. Data peribadi, infrastruktur kritikal, peraturan sektor (kewangan, kesihatan, kerajaan) — yang mana terpakai?

## Blok 7. Kewangan dan permintaan
25. Tunai, perbelanjaan bulanan, dana yang telah diperoleh, geran.
26. Berapa yang diperlukan, untuk apa, berapa lama, pencapaian apa? Syarat (ekuiti, geran, dana padanan)?
27. Kadar diskaun / keperluan pelabur atau dana, tempoh.

## Hasil
Simpan jawapan dalam `intake.json` (atau terus dalam `*_input.json` daripada `templates/ms/`),
tandakan asal setiap medan: `client` (kenyataan), `measured` (pengukuran), `public` (pautan),
`assumption` (andaian). Serahkan senarai medan yang menggunakan anggaran kepada `research_brief.md` / `research_loop.md`.
