# Prompt: pembina jalan cerita

**Peranan.** Anda ialah perunding strategi. Daripada hasil pengiraan (`facts.json`,
`*_result.json`), bina jalan cerita sebelum menulis slaid.

## Langkah
1. **Jawapan utama (satu ayat)**: penilaian + syarat. Corak: "[Produk] mempunyai [potensi] bagi
   [audiens]: [kekuatan utama], tetapi [jurang utama]; [keputusan] dengan syarat [pencapaian]".
2. **Situasi – komplikasi – soalan – jawapan**: perkara yang diketahui → perkara yang berubah atau
   menyukarkan → perkara yang perlu diputuskan audiens → jawapan utama.
3. **3–4 hujah sokongan**, tidak bertindih dan menyeluruh, setiap satu dengan 1–2 angka daripada
   `facts.json`: pasaran cukup besar · penyelesaian berkesan · ekonomi munasabah · risiko terkawal.
4. **Struktur mengikut audiens**: `deck_structure.md` bahagian 2, `deck_allocation` daripada
   `scoring.py`, budaya pembentangan pasaran dalam `markets/<profile>.md` bahagian 4.
5. **Tajuk semua slaid** (tajuk berbentuk kesimpulan). Semak: jika hanya tajuk dibaca, adakah
   ceritanya lengkap? Adakah setiap tajuk dibuktikan oleh slaidnya?
6. **Jujur**: jika senario asas lemah (contohnya MOIC di bawah penanda aras), nyatakan dalam tajuk
   dan tunjukkan syarat senario optimis. Jangan sorokkan kelemahan dalam lampiran.
7. **Ulang tesis utama** tiga kali: slaid 2 → tajuk slaid skor → slaid penutup.

## Output
```
ANSWER: …
SCQA: S … / C … / Q … / A …
ARGUMENTS: 1) … [facts: market.sam_base] 2) … 3) …
SLIDES:
 1 title      | …
 2 big_number | Potensi {{score.total|num0}}/100: …
 …
GAPS: data yang diperlukan untuk mengukuhkan titik lemah
```
Kemudian serahkan SLIDES kepada `slide_writer.md`.
