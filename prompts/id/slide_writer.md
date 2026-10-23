# Prompt: penulis slide

**Peran.** Anda menulis `deck_spec.json` (dan sekaligus `report_spec.json`) berdasarkan alur cerita
yang disetujui. Skema: docstring `tools/build_pptx.py`; contoh: `examples/example_id/`.

## Aturan
1. **Angka hanya sebagai placeholder** `{{path|fmt}}` dari `facts.json`; tabel dan grafik dengan
   `{"$ref": "charts.…"}` / `{"$ref": "tables.…"}`. Jangan mengetik angka yang ada di facts; jika
   belum ada, tambahkan perhitungan di `project.json → metrics`.
2. **Judul** = kesimpulan dengan angka, ≤ 18–20 kata, ≤ 2 baris.
3. **Satu pesan** per slide; ≤ 6 butir; butir ≤ 2 baris; teks ≥ 16 pt.
4. **`source`** di setiap slide berangka, misalnya "market_sizing.py atas data …; {{project.units.bn}}".
5. **`notes`** — naskah 40–60 detik dan jawaban atas pertanyaan yang diperkirakan.
6. Tata letak: angka utama → `big_number`; perbandingan/tren → `chart`; angka rinci → `table`;
   sebelum/sesudah, risiko/mitigasi → `two_column`; posisi → `matrix`; tonggak → `timeline`;
   skor → `scorecard`; permintaan → `closing`.
7. Grafik: jenis sesuai `style_guide.md` bagian 2.3; sorot elemen utama (`highlight_index`);
   `takeaway` berisi 2–3 butir cara membaca grafik.
8. Laporan: urutan sama; setiap bagian diawali kesimpulan; sitasi `[[src:id]]`, catatan kaki `[[fn:…]]`.
9. Tanpa kata berlebihan (`config/banned_phrases.json` → `id`).
10. Data fiktif atau ilustratif: tandai di `meta.watermark` dan halaman judul.
11. Atur `meta.locale: "id"` di kedua spesifikasi; label, format angka (titik ribuan, koma desimal,
    "Rp … miliar/triliun") dan gaya sitasi APA mengikuti locale.

## Setelah menulis
```bash
python tools/run_pipeline.py --project project.json
```
Buka `qa_light.json`: wajib 0 galat; peringatan diperbaiki atau dijelaskan. Periksa PNG
(`renders/deck/contact_sheet.png`). Lalu jalankan `red_team_reviewer.md`.
