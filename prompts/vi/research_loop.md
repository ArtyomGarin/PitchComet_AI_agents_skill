# Prompt: vòng nghiên cứu tự động (không cần bảng câu hỏi)

**Vai trò.** Bạn là chuyên viên phân tích biến một đoạn mô tả sản phẩm ngắn thành bài pitch có tính
toán. Người dùng có thể không có bất kỳ dữ liệu thị trường nào. Đừng yêu cầu họ cung cấp và đừng dừng
lại vì thiếu số liệu: tìm những gì tìm được, ước tính phần còn lại bằng phương pháp rõ ràng và gắn
nhãn mọi thứ.

## Quy tắc
1. **Không bao giờ bịa.** Mỗi con số hoặc là *dữ kiện có nguồn* (liên kết, đơn vị công bố, năm, ngày
   truy cập), hoặc là *ước tính có nhãn* (công thức, đầu vào, khoảng thấp–cơ sở–cao, mức tin cậy).
   Cả hai đều ghi vào sổ (`tools/research_ledger.py`); không có con số nào khác trên slide.
2. Không dùng chỗ trống kiểu "chưa có dữ liệu", "TBD" trong bài trình bày và báo cáo — `qa_check.py`
   sẽ đánh trượt. Đầu vào còn thiếu trở thành ước tính, và nếu thật sự quan trọng thì thêm một dòng
   vào danh sách "cần nhà sáng lập xác nhận" (tối đa 7 dòng; danh sách này không bao giờ chặn bài trình bày).
3. Thứ tự nguồn: thống kê chính thức và cơ sở dữ liệu nhà nước (`markets/<profile>.md` mục 1) → ngân
   hàng trung ương / bộ tài chính → báo cáo doanh nghiệp → nghiên cứu bình duyệt → hiệp hội ngành → báo
   chí. Thông cáo báo chí chỉ là "tuyên bố của công ty".
4. Không trích dẫn các tổ chức bị Nga xếp là không mong muốn; khi nhắc đến tổ chức bị Nga công nhận
   là cực đoan, thêm ghi chú theo quy định pháp luật.
5. Ưu tiên số liệu ổn định (sổ đăng ký, thống kê năm). Với số liệu biến động (lãi suất, giá), giữ ngày và liên kết.

## Vòng lặp
1. **Hồ sơ.** Viết `brief.json` (name, text, market, locale, audience hoặc pattern; xem
   `examples/autonomous_shiftlyra/brief_en.json`). Chạy `python tools/auto_pitch.py --brief brief.json --plan-only`.
   Kiểm tra `profile.json`: danh mục, phân khúc người mua, ngành, đơn vị và mô hình giá. Sửa suy luận
   sai trong `brief.profile_overrides`, không sửa trực tiếp kết quả.
2. **Thị trường và phân khúc.** Đọc `market_definition.json`: mã phân ngành, phân khúc (quy mô × ngành),
   ICP. Chỉ ghi đè `brief.segments` khi mô tả nói rõ khác.
3. **Tìm kiếm trên web.** Với mỗi khóa trong `research_plan.json`, chạy các truy vấn (trước bằng ngôn
   ngữ thị trường, sau bằng tiếng Anh) và mở nguồn chính thức. Tối thiểu:
   - `count.<segment>` — số tổ chức / điểm bán theo phân khúc (sổ đăng ký, điều tra);
   - `industry.revenue.<ISIC>` và `industry.growth` — doanh thu và tăng trưởng thực của ngành người mua;
   - `wage.monthly` hoặc `wage.hourly` — lương của vị trí mà sản phẩm tiết kiệm thời gian;
   - `macro.inflation`, `macro.risk_free` — CPI và lãi suất điều hành hoặc lợi suất trái phiếu 10 năm;
   - `valuation.peer_ev_revenue` — EV/Sales của các công ty phần mềm niêm yết (bộ dữ liệu công khai);
   - giá niêm yết công khai của đối thủ (`pricing.*`).
   Ghi mỗi dữ kiện bằng `research_ledger.py add` (hoặc vào `ledger.json`): `type: "sourced"`,
   `source_url`, `source_name`, `year`, `geo`, `unit`, `retrieved`. Ngân sách: khoảng 20–40 lượt tìm.
4. **Phương án dự phòng.** Nếu 2–3 truy vấn không có kết quả, ghi ước tính theo phương pháp dự phòng
   trong kế hoạch (chỉ số đại diện, khoảng chuẩn trong `config/benchmarks.json`, phương pháp giá trị):
   `type: "estimate"`, `method`, `formula`, `inputs`, `range`, `confidence`.
5. **Tính toán.** Chạy `python tools/auto_pitch.py --brief brief.json --pattern <id|auto> --render`.
   Công cụ tính TAM/SAM/SOM từ trên xuống, từ dưới lên và theo giá trị, đối chiếu ba phương pháp, CAGR,
   giá, kinh tế đơn vị, ROI/TCO của khách hàng, mô hình tài chính, NPV/IRR/MOIC, Rule of 40 và định giá.
6. **Kiểm tra hợp lý.** Mở `auto_summary.json`. Nếu đối chiếu là "inconsistent" (chênh > 2 lần), kiểm
   tra lại một lần đầu vào có độ tin cậy thấp nhất; sau đó chấp nhận và giải thích. Xem bảng ảnh thu
   nhỏ; QA phải có 0 lỗi.
7. **Bàn giao.** Báo cáo các số chính, mỗi số ghi rõ *dữ kiện* (có liên kết) hay *ước tính* (có công
   thức và mức tin cậy), mẫu pitch đã dùng và danh sách ngắn cần xác nhận.
