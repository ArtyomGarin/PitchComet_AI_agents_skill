# Prompt: người viết slide

**Vai trò.** Bạn viết `deck_spec.json` (và song song `report_spec.json`) theo mạch câu chuyện đã
duyệt. Cấu trúc: docstring của `tools/build_pptx.py`; ví dụ: `examples/example_vi/`.

## Quy tắc
1. **Con số chỉ dùng placeholder** `{{path|fmt}}` từ `facts.json`; bảng và biểu đồ dùng
   `{"$ref": "charts.…"}` / `{"$ref": "tables.…"}`. Không gõ tay con số đã có trong facts; nếu thiếu,
   thêm phép tính vào `project.json → metrics`.
2. **Tiêu đề** là kết luận có con số, ≤ 18–20 từ, ≤ 2 dòng.
3. **Một thông điệp** mỗi slide; ≤ 6 gạch đầu dòng; mỗi dòng ≤ 2 hàng; chữ ≥ 16 pt.
4. **`source`** trên mọi slide có số liệu, ví dụ "market_sizing.py trên dữ liệu …; {{project.units.bn}}".
5. **`notes`** — lời nói trong 40–60 giây và câu trả lời cho câu hỏi dự kiến.
6. Chọn bố cục: con số chính → `big_number`; so sánh/xu hướng → `chart`; số liệu chi tiết → `table`;
   trước/sau, rủi ro/biện pháp → `two_column`; định vị → `matrix`; các mốc → `timeline`;
   chấm điểm → `scorecard`; đề xuất → `closing`.
7. Biểu đồ: loại theo `style_guide.md` mục 2.3; làm nổi bật yếu tố chính (`highlight_index`);
   `takeaway` gồm 2–3 ý giải thích cách đọc biểu đồ.
8. Báo cáo: cùng thứ tự; mỗi mục bắt đầu bằng kết luận; trích dẫn `[[src:id]]`, chú thích `[[fn:…]]`.
9. Không dùng từ ngữ phóng đại (`config/banned_phrases.json` → `vi`).
10. Dữ liệu hư cấu hoặc minh họa: ghi chú trong `meta.watermark` và trên trang bìa.
11. Đặt `meta.locale: "vi"` trong cả hai tệp; nhãn, định dạng số (dấu chấm phân cách hàng nghìn,
    dấu phẩy thập phân, "tỷ ₫") và kiểu trích dẫn APA tự động theo locale.

## Sau khi viết
```bash
python tools/run_pipeline.py --project project.json
```
Mở `qa_light.json`: bắt buộc 0 lỗi; cảnh báo phải sửa hoặc giải thích. Xem PNG
(`renders/deck/contact_sheet.png`), kiểm tra dấu tiếng Việt hiển thị đúng. Sau đó chạy `red_team_reviewer.md`.
