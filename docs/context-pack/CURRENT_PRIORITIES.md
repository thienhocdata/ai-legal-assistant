# Ưu tiên hiện tại

1. Clean baseline và audit kỹ thuật 19 lỗi đã xong. Ưu tiên người thật review
   mẫu khoảng 20 câu đa dạng, kiểm tra cả nhãn AI lẫn nhận định audit AI; ghi
   câu được duyệt và chuyên môn thật của người duyệt.
2. Ưu tiên paraphrase (11/18 Hit@1) và coverage evidence (35/50 khớp mọi nhãn),
   sau khi rà nhãn; tách thiếu ở retrieval khỏi thiếu ở bước chọn căn cứ. V1/V2
   là dev đã quan sát, sửa nhãn cần V2.1 và manifest mới, giữ baseline cũ.
3. Tổ chức V3 do người độc lập viết và duyệt theo giao thức đã ghi. Hiện chưa có
   V3 độc lập; không gọi số sau sửa trên V2 là phép đo held-out.
4. Dùng framework human review để đo citation correctness, faithfulness,
   completeness và loại refusal. Metric status/rank/marker hiện có chưa đo các
   khía cạnh này; Wilson cũng không loại bỏ thiên lệch nhãn AI.
5. Giữ hybrid mặc định trong khi thử phương án xếp hạng riêng. Article-diversity
   và RRF chưa được promote do có giảm điểm hoặc mất evidence; chỉ nhận thay đổi
   sau khi kiểm tra cả metric lẫn nội dung các chunk bị loại.
6. Cấu hình API key cục bộ hợp lệ để live-test Qwen/Gemini khi có điều kiện;
   hiện chưa có live comparison hoặc kết luận provider tốt hơn.
7. Bổ sung nguồn luật qua pipeline/quality gate: Luật 43/2024/QH15 và văn bản
   hướng dẫn cần thiết, đồng thời quản lý hiệu lực và quan hệ sửa đổi.
8. Hoàn thiện portability, đồng bộ metadata sau pipeline và bảo mật/riêng tư
   trước triển khai ngoài máy local.
