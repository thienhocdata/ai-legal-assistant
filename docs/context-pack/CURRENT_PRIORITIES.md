# Ưu tiên hiện tại

1. Tổ chức người độc lập/chuyên gia pháp lý rà soát nhãn cho candidate v2; sửa
   nhãn phải tạo dataset và manifest phiên bản mới, không ghi đè v2 đã khóa.
2. Cải thiện refusal trên một bộ phát triển khác: candidate v2 chỉ đạt `30%`
   refusal correctness và không được dùng làm tập tune sau khi đã xem kết quả.
3. Dùng framework human review để đo citation correctness, faithfulness,
   completeness và refusal; chưa công bố metric pháp lý cho đến khi có nhãn thật.
4. Tải và lưu bản gốc Luật 43/2024/QH15 để bảo toàn provenance của quan hệ sửa đổi.
5. Tự động đồng bộ trạng thái processing/index vào document metadata sau mỗi pipeline run.
6. Hoàn thiện bảo mật/riêng tư trước mọi triển khai ngoài máy local.
7. Sau khi người dùng duyệt, archive tài liệu giai đoạn cũ và hợp nhất requirements trùng lặp.
