# Bảo mật và quyền riêng tư

- Không commit `.env`, `GEMINI_API_KEY`, token hoặc credential.
- Mặc định `LLM_PROVIDER=none`; chỉ gửi dữ liệu sang provider hosted khi người dùng đã cấu hình có chủ đích.
- Không ghi nguyên câu hỏi chứa thông tin cá nhân vào log production nếu chưa có cơ chế tối thiểu hóa/redaction và retention policy.
- Không đưa hồ sơ vụ việc, giấy tờ tùy thân hoặc dữ liệu nhạy cảm vào ground truth công khai.
- Guardrail prompt injection hiện là lớp giảm thiểu, không phải sandbox bảo mật.
- Static UI và API chưa được mô tả có authentication/authorization; không triển khai công khai như dịch vụ production nếu chưa bổ sung kiểm soát truy cập, rate limit, CORS và quản lý log.
- Thông báo giới hạn sử dụng và yêu cầu đối chiếu văn bản hiệu lực phải được giữ trong trải nghiệm người dùng.
- Context làm rõ chỉ nằm trong bộ nhớ tab và request/response, không session
  server hay event log. Mỗi phần được coi là input không tin cậy; giới hạn tối
  đa 3 câu bổ sung, 2000 ký tự mỗi phần và 6000 ký tự tổng. Khi chọn hosted
  provider, câu hỏi/context được dùng để tạo prompt như input thông thường;
  không gửi hồ sơ cá nhân nhạy cảm qua demo.
- Quote integrity và exact-extractive validation không chứng minh hiệu lực hoặc
  legal entailment. Hosted output chỉ qua kiểm tra cấu trúc/integrity và có
  metadata semantic_support_verified=false; không mô tả thành human review.
