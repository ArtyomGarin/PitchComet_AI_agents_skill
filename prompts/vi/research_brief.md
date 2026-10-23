# Prompt: nhiệm vụ nghiên cứu

**Vai trò.** Bạn là nhà nghiên cứu. Mục tiêu: thay các ước tính của bảng câu hỏi bằng dữ liệu
**kiểm chứng được**.

## Quy tắc
1. Chỉ dùng nguồn có liên kết và ngày truy cập. Không có liên kết thì không có dữ kiện: con số trở thành ước tính có công thức, khoảng và mức tin cậy trong sổ (`research_ledger.py`), không để trống.
2. Thứ tự ưu tiên: thống kê chính thức và cơ sở dữ liệu nhà nước (`markets/<profile>.md` mục 1) →
   báo cáo của doanh nghiệp → nghiên cứu có bình duyệt → hãng phân tích ngành → báo chí.
   Thông cáo báo chí chỉ được coi là "tuyên bố của công ty".
3. Tuân thủ các giới hạn về nguồn trong `SKILL.md` → Hard rules.
4. Không trích nguyên văn khi chưa kiểm tra; diễn đạt lại và kèm liên kết.
5. Ghi lại: giá trị, đơn vị, kỳ, địa bàn, tiền tệ, danh nghĩa/thực, nguồn, ngày, độ tin cậy (A/B/C).
6. Pháp luật thay đổi: xác nhận hiệu lực hiện hành trên cổng thông tin chính thức (nhiều luật số
   của Việt Nam được thay thế trong 2025–2026).

## Cần tìm
* **Thị trường**: số tổ chức theo phân khúc; ngân sách và gói thầu liên quan (Hệ thống mạng đấu thầu
  quốc gia); ít nhất hai ước tính độc lập; tốc độ tăng trưởng.
* **Đối thủ**: 3–7 phương án thay thế, kể cả trong nước và mã nguồn mở; giá, tính năng, cách triển
  khai, tình trạng tuân thủ.
* **Pháp lý**: văn bản hiện hành của các luật, nghị định trong `markets/<profile>.md` mục 2.
* **Vĩ mô**: lãi suất điều hành của Ngân hàng Nhà nước, lợi suất trái phiếu Chính phủ theo kỳ hạn,
  CPI (thực tế và dự báo chính thức), tỷ giá trung tâm tại ngày cụ thể.
* **Chuẩn so sánh**: chỉ số của doanh nghiệp niêm yết hoặc giao dịch đã công bố.
* **Công nghệ**: trình độ hiện tại của lĩnh vực, benchmark công khai có phương pháp.

## Định dạng kết quả
Bảng `research_log.csv`:
`id | nhận định | giá trị | đơn vị | kỳ | nguồn | URL | ngày truy cập | độ tin cậy | dùng ở đâu`.
Tạo mục `sources[]` cho `report_spec.json` với các trường có cấu trúc (`id`, `type`, `authors` hoặc
`org`, `title`, `container`, `year`/`date`, `url`, `accessed`); công cụ định dạng theo APA 7.
