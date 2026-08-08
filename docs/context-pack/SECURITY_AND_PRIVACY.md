# Bảo mật và quyền riêng tư

- Không commit `.env`, `GEMINI_API_KEY`, token hoặc credential.
- Mặc định `LLM_PROVIDER=none`; chỉ gửi dữ liệu sang provider hosted khi người dùng đã cấu hình có chủ đích.
- Không ghi nguyên câu hỏi chứa thông tin cá nhân vào log production nếu chưa có cơ chế tối thiểu hóa/redaction và retention policy.
- Không đưa hồ sơ vụ việc, giấy tờ tùy thân hoặc dữ liệu nhạy cảm vào ground truth công khai.
- Guardrail prompt injection hiện là lớp giảm thiểu, không phải sandbox bảo mật.
- Static UI và API chưa được mô tả có authentication/authorization; không triển khai công khai như dịch vụ production nếu chưa bổ sung kiểm soát truy cập, rate limit, CORS và quản lý log.
- Thông báo giới hạn sử dụng và yêu cầu đối chiếu văn bản hiệu lực phải được giữ trong trải nghiệm người dùng.
