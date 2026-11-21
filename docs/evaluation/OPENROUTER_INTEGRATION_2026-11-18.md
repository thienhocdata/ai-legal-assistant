# Kết nối OpenRouter / ERNIE — 18/11/2026

## Phạm vi thay đổi

- Thêm `LLM_PROVIDER=openrouter`, dùng key riêng `OPENROUTER_API_KEY` và
  `OPENROUTER_MODEL=baidu/ernie-5.5-flash-preview:free`.
- Tái sử dụng adapter chat-completions, semantic router và luồng RAG hiện có;
  không thay corpus, retrieval, citation hoặc ngưỡng bằng chứng.
- Endpoint cố định `https://openrouter.ai/api/v1`. Adapter chỉ chấp nhận model
  `:free` hoặc `openrouter/free`, gửi giới hạn giá prompt/completion/request bằng
  0, không thêm model fallback trả phí hoặc plugin. Khi lỗi vẫn fallback local.
- API trả model thực tế được phục vụ; giữ model yêu cầu trong metadata adapter.
  Từ chối cả lỗi HTTP200 và phản hồi kết thúc bằng `finish_reason=error/length`.
- Key chỉ ở `.env` cục bộ đã gitignore; không nằm trong tài liệu hoặc artifact.

## Vấn đề phát hiện khi gọi thật

1. ERNIE trả HTTP400 khi gửi `reasoning.enabled=false`, với thông báo suy luận
   bắt buộc. Đã bỏ tùy chọn tắt suy luận.
2. Lượt sinh câu trả lời luật với ngân sách cũ 800 token rơi về local do
   `ProviderResponseError`. Chưa lưu được finish reason của lượt đó, nên không
   khẳng định nguyên nhân chính xác chỉ từ loại lỗi.
3. Lần chẩn đoán với 4096 token kết thúc `stop`, dùng 4051 completion token,
   gồm 2513 reasoning token. Cấu hình OpenRouter demo dùng trần 8192 để chừa
   chỗ cho cả suy luận và câu trả lời; đây không phải yêu cầu trả lời dài.

## Kết quả có bằng chứng

- Full suite sau thay đổi: **457 passed**, một warning deprecation hiện có của
  Starlette TestClient/HTTPX. Test offline/mock không tiêu quota hosted.
- Local readiness kiểm tra cấu hình OpenRouter và tính toàn vẹn 441 chunks /
  441 vectors / 384 chiều thành công; không dùng kết quả này để chứng minh API.
- POST `/api/chat`, câu hội thoại tổng hợp: HTTP200, `status=smalltalk`,
  `provider=openrouter`, đúng model ERNIE, `usage.cost=0`.
- POST `/api/chat`, câu thử tổng hợp “Điều kiện để người sử dụng đất chuyển
  nhượng quyền sử dụng đất là gì?”: HTTP200, `status=success`,
  `provider=openrouter`, đúng model, `generation_fallback_reason=null`,
  `usage.cost=0`, citation labels `[1,2]`. Lượt đo mất khoảng 17,9 giây trên
  máy hiện tại, không phải benchmark độ trễ.
- Trên giao diện `/`, đã thử lời đề nghị nói dễ hiểu, câu hỏi về đất đang có
  tranh chấp và câu nối tiếp “Nói lại ý chính trong 2 câu thôi nha.”. Giao diện
  nhận đủ phản hồi; lượt nối tiếp giữ được chủ đề và trả lời bằng hai câu có
  citation. Đây vẫn là các tình huống do AI chọn, chưa phải human acceptance.
- Artifact cục bộ không chứa key: `data/evaluation/runs/` có
  `openrouter_ernie_web_smoke_20261118.json` (thử đầu thất bại),
  `openrouter_ernie_web_smoke_20261118_recheck.json`,
  `openrouter_ernie_generation_4096_20261118.json` và
  `openrouter_ernie_web_verified_20261118.json`. Giữ riêng lần lỗi và lần đạt.

## Giới hạn diễn giải

Đây là kiểm tra tích hợp bằng câu hỏi do AI chuẩn bị, không phải đánh giá độc
lập hoặc kiểm định pháp lý. Output luật mới qua kiểm tra nhãn citation và quote
integrity (`semantic_support_verified=false`); chưa chứng minh từng nhận định
được nguồn hỗ trợ hoặc đầy đủ điều kiện. Không nâng các metric V2 nhờ lượt thử này.

Tài khoản được API xác nhận hạn mức 50 lượt gọi miễn phí/ngày lúc kiểm tra.
Một lượt hỏi luật thường gọi hai lần (routing và generation); không diễn giải
thành 50 câu chat. Nguồn miễn phí, model preview và độ sẵn sàng có thể thay đổi.

Tài liệu nhà cung cấp đã đối chiếu:
[model ERNIE](https://openrouter.ai/baidu/ernie-5.5-flash-preview:free),
[giới hạn](https://openrouter.ai/docs/api_reference/limits),
[kiểm soát giá provider](https://openrouter.ai/docs/guides/routing/provider-selection).
