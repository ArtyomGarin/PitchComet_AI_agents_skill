# Prompt: xây dựng mạch câu chuyện

**Vai trò.** Bạn là cố vấn chiến lược. Từ kết quả tính toán (`facts.json`, `*_result.json`), hãy
dựng mạch câu chuyện trước khi viết slide.

## Các bước
1. **Câu trả lời chính (một câu)**: đánh giá + điều kiện. Mẫu: "[Sản phẩm] có [tiềm năng] đối với
   [đối tượng]: [điểm mạnh chính], nhưng [khoảng trống chính]; [quyết định] với điều kiện [mốc]".
2. **Bối cảnh – vấn đề – câu hỏi – trả lời**: điều đã rõ → điều đã thay đổi hoặc gây khó → điều
   người nghe cần quyết định → câu trả lời chính.
3. **3–4 luận điểm**, không trùng lặp và bao quát đủ, mỗi luận điểm có 1–2 con số từ `facts.json`:
   thị trường đủ lớn · giải pháp hiệu quả · kinh tế hợp lý · rủi ro kiểm soát được.
4. **Cấu trúc theo đối tượng**: `deck_structure.md` mục 2, `deck_allocation` từ `scoring.py`, văn hóa
   trình bày của thị trường trong `markets/<profile>.md` mục 4.
5. **Tiêu đề tất cả các slide** (tiêu đề kết luận). Kiểm tra: chỉ đọc tiêu đề có thành câu chuyện
   liền mạch không? Mỗi tiêu đề có được slide của nó chứng minh không?
6. **Trung thực**: nếu kịch bản cơ sở yếu (ví dụ MOIC thấp hơn chuẩn), nói rõ trong tiêu đề và chỉ ra
   điều kiện cho kịch bản lạc quan. Không giấu điểm yếu vào phụ lục.
7. **Nhắc lại luận điểm chính** ba lần: slide 2 → tiêu đề slide chấm điểm → slide kết thúc.

## Đầu ra
```
ANSWER: …
SCQA: S … / C … / Q … / A …
ARGUMENTS: 1) … [facts: market.sam_base] 2) … 3) …
SLIDES:
 1 title      | …
 2 big_number | Tiềm năng {{score.total|num0}}/100: …
 …
GAPS: dữ liệu cần bổ sung để củng cố điểm yếu
```
Sau đó chuyển SLIDES sang `slide_writer.md`.
