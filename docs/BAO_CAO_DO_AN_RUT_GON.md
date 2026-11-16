# BÁO CÁO ĐỒ ÁN MÔN KỸ NĂNG LÀM VIỆC TẠI DOANH NGHIỆP

## Xây dựng trợ lý tra cứu pháp luật đất đai Việt Nam cho Công ty Minh Long

> **Sinh viên:** [CẦN NGƯỜI DÙNG BỔ SUNG: họ tên, MSSV, lớp]
>
> **Giảng viên hướng dẫn:** [CẦN NGƯỜI DÙNG BỔ SUNG]
>
> **Doanh nghiệp/đơn vị phối hợp:** Công ty Minh Long
>
> **Hình thức thực hiện:** Freelance cá nhân — [CẦN NGƯỜI DÙNG XÁC NHẬN]
>
> **Thời gian thực hiện:** [CẦN NGƯỜI DÙNG BỔ SUNG: từ ngày/tháng/năm đến ngày/tháng/năm]
>
> **Ngày cập nhật bản thảo:** 16/11/2026

---

## Lưu ý sử dụng bản thảo

Bản thảo này ưu tiên quá trình làm việc, quyết định, ràng buộc và bài học thay
vì trình bày toàn bộ chi tiết kỹ thuật. Những chỗ có nhãn
`[CẦN NGƯỜI DÙNG BỔ SUNG]` không thể suy ra từ repository và phải được điền từ
trải nghiệm freelance thực tế. Không tự tạo tên người phụ trách, cuộc họp, phản
hồi, deadline, số người dùng hoặc kết quả nghiệm thu.

Báo cáo kỹ thuật đầy đủ được lưu tại
`docs/BAO_CAO_PHAN_TICH_DU_AN_HIEN_TAI.md`. Bản nộp chính nên giữ nội dung dưới
đây ở khoảng 20–30 trang; source code, bảng kiểm thử dài và artifact đưa vào phụ
lục hoặc liên kết repository.

---

# 1. Tóm tắt đề tài

Đề tài xây dựng một trợ lý tra cứu pháp luật đất đai Việt Nam cho Công ty Minh
Long theo kiến trúc Retrieval-Augmented Generation (RAG). Người dùng nhập câu
hỏi bằng tiếng Việt; hệ thống chuẩn hóa câu hỏi, tìm các đoạn luật có liên quan,
tạo trích dẫn Điều–Khoản–Điểm, kiểm tra mức độ bằng chứng và trả kết quả kèm
cảnh báo giới hạn sử dụng.

Sản phẩm hiện đạt mức demo/nghiên cứu. Hệ thống không được mô tả là dịch vụ tư
vấn pháp lý chuyên nghiệp, không thay thế luật sư hoặc cơ quan nhà nước và chưa
phải kho pháp luật đầy đủ. Corpus production hiện dùng Văn bản hợp nhất số
133/VBHN-VPQH; artifact có 260 Điều, 441 legal chunks, 441 embedding 384 chiều
và FAISS `IndexFlatIP` gồm 441 vector.

Quá trình thực hiện tập trung vào ba yêu cầu chất lượng:

1. căn cứ phải truy vết được về cấu trúc pháp lý;
2. artifact dữ liệu phải đồng bộ và có provenance;
3. hệ thống phải từ chối hoặc giới hạn câu trả lời khi thiếu nguồn.

Kết quả kiểm thử đầy đủ gần nhất là 70 test đạt. Kết quả retrieval Hit@1
`0,9667`, Recall@3/5 `1,0` và MRR `0,9778` chỉ áp dụng cho bộ 30 câu phát triển
nội bộ, chưa phải held-out evaluation và chưa chứng minh độ chính xác pháp lý
tổng quát. Một bộ 60 câu V2 đã được tạo và đóng băng sau baseline để giảm nguy
cơ tune ngược, nhưng đây vẫn là tập ứng viên do AI tạo, chờ người đánh giá duyệt;
không được gọi là independent/expert-held-out evaluation.

---

# 2. Bối cảnh doanh nghiệp và hình thức làm việc

## 2.1. Giới thiệu đơn vị

**Thông tin đã xác minh trong phạm vi dự án:** chủ thể được người phụ trách dự án
xác nhận là Công ty Minh Long. Repository không có hồ sơ pháp nhân, mô tả ngành
nghề, sơ đồ tổ chức hoặc người đại diện doanh nghiệp.

[CẦN NGƯỜI DÙNG BỔ SUNG]

- Tên pháp lý đầy đủ của công ty nếu được phép công bố.
- Lĩnh vực hoạt động của Minh Long.
- Bộ phận hoặc cá nhân làm đầu mối cho dự án.
- Lý do doanh nghiệp quan tâm đến công cụ tra cứu pháp luật đất đai.

## 2.2. Hình thức cộng tác

[CẦN NGƯỜI DÙNG BỔ SUNG VÀ XÁC NHẬN]

Có thể trình bày theo mẫu sau nếu đúng với trải nghiệm thực tế:

> Dự án được thực hiện theo hình thức freelance cá nhân. Tôi tiếp nhận yêu cầu,
> làm rõ phạm vi, đề xuất giải pháp, phát triển, kiểm thử và báo cáo kết quả cho
> đầu mối phía Minh Long. Việc trao đổi được thực hiện qua [kênh thực tế] trong
> thời gian [mốc thực tế].

Không ghi Scrum, sprint, daily meeting hoặc phân công nhóm nếu không có bằng
chứng thực tế.

## 2.3. Vai trò và trách nhiệm cá nhân

[CẦN NGƯỜI DÙNG BỔ SUNG]

- Vai trò được thỏa thuận với công ty.
- Công việc thực sự đã đảm nhận: phân tích yêu cầu, dữ liệu, backend, AI/RAG,
  kiểm thử, giao diện, báo cáo hoặc demo.
- Công việc nằm ngoài trách nhiệm.
- Mức độ tự chủ và các quyết định cần xin ý kiến phía doanh nghiệp.

---

# 3. Yêu cầu, phạm vi và ràng buộc

## 3.1. Yêu cầu ban đầu từ doanh nghiệp

[CẦN NGƯỜI DÙNG BỔ SUNG]

- Bài toán ban đầu được Minh Long mô tả như thế nào?
- Người dùng mục tiêu dự kiến là ai?
- Doanh nghiệp muốn một bản demo, công cụ nội bộ hay sản phẩm triển khai thật?
- Đầu ra bàn giao ban đầu gồm những gì?

Nếu không có tài liệu yêu cầu chính thức, cần ghi rõ đây là nội dung được thuật
lại từ trao đổi thực tế, không trình bày như biên bản đã ký.

## 3.2. Phạm vi kỹ thuật đã xác minh

- Tra cứu pháp luật đất đai bằng câu hỏi tiếng Việt.
- Truy hồi căn cứ trước khi sinh câu trả lời.
- Giữ metadata Chương–Mục–Điều–Khoản–Điểm.
- Citation có thể truy ngược về document và vị trí pháp lý.
- Chạy local bằng extractive provider, không bắt buộc API key.
- Có Gemini và Qwen tùy chọn; Qwen mới được kiểm thử bằng mock HTTP, chưa live
  test do repository không chứa API key.
- API FastAPI và giao diện web chat tĩnh.

## 3.3. Ràng buộc thực tế

**Đã xác minh từ source và tài liệu:**

- nguồn luật phải có provenance và hash;
- không commit API key, hồ sơ cá nhân hoặc dữ liệu nhạy cảm;
- citation kỹ thuật không đồng nghĩa quy định còn hiệu lực;
- corpus hiện chưa bao phủ nghị định, thông tư và quy định địa phương đầy đủ;
- sản phẩm chỉ dùng cho demo/nghiên cứu.

[CẦN NGƯỜI DÙNG BỔ SUNG]

- Deadline và các mốc demo.
- Ngân sách hoặc giới hạn chi phí API.
- Thiết bị/môi trường doanh nghiệp yêu cầu hỗ trợ.
- Yêu cầu bảo mật hoặc không gửi dữ liệu ra ngoài.
- Những tính năng phía Minh Long ưu tiên hoặc tạm hoãn.

---

# 4. Quy trình làm việc và các giai đoạn phát triển

## 4.1. Giai đoạn khởi tạo

Ngày 06/07/2026, repository được khởi tạo qua hai commit tạo project tối thiểu
và cấu trúc thư mục. Giai đoạn này xác định các lớp chính: source ứng dụng,
scripts, dữ liệu, tài liệu và kiểm thử.

**Kết quả:** có nền tảng quản lý mã nguồn nhưng chưa có sản phẩm end-to-end.

## 4.2. Giai đoạn MVP RAG

Ngày 14/07/2026, commit `868ad8d` bổ sung pipeline xử lý văn bản, legal-aware
chunking, embedding, FAISS, retrieval, query understanding, citation,
guardrails, provider, API, UI, evaluation và test.

**Kết quả:** hình thành baseline chạy xuyên suốt từ nguồn luật đến giao diện.

**Bài học:** một chatbot pháp lý không nên gửi thẳng câu hỏi vào LLM. Việc tìm
căn cứ và kiểm tra citation phải nằm trước và sau bước generation.

## 4.3. Thử nghiệm và chuyển corpus

Ngày 08/08/2026, corpus Văn bản hợp nhất 133 được xây trong khu vực experiment,
qua quality gate rồi mới promotion sang production. Pipeline thử nghiệm không
được ghi trực tiếp vào `data/processed/` hoặc `data/vector_db/`; script promotion
yêu cầu xác nhận và tạo backup.

**Kết quả:** production chuyển sang corpus hợp nhất với 260 Điều và 441 chunks.

**Bài học về kỹ năng làm việc:** thay đổi dữ liệu lõi cần thử nghiệm tách biệt,
tiêu chí chấp nhận, backup và khả năng truy vết; không nên ghi đè production chỉ
vì một phiên bản mới có vẻ tốt hơn.

## 4.4. Quality hardening

Ngày 15/11/2026, nhánh `codex/quality-hardening` bổ sung Qwen provider tương
thích OpenAI, fallback có phân loại lỗi, giới hạn token/retry, diagnostic câu âm,
framework human review, corpus-gap routing và đồng bộ nhận diện Minh Long.

Số test tăng từ baseline 38 lên 54 ở giai đoạn quality hardening, rồi lên 70 sau
khi bổ sung dataset freezing, system-behavior evaluation và provider comparison
harness. Đây là timeline phát triển, không phải các kết quả hiện hành mâu thuẫn.

**Kết quả calibration:** ngưỡng dense `0,55` đạt balanced accuracy `0,5` trên
nhóm answerable so với missing-source. Ngưỡng in-sample `0,890138` đạt balanced
accuracy `0,9` nhưng từ chối nhầm 20% câu dương. Vì dữ liệu nhỏ và chưa có đánh
giá độc lập, production không tự động nâng threshold. Hệ thống dùng corpus-gap
routing cho các yêu cầu rõ ràng cần nguồn thuế, thủ tục, hồ sơ thửa hoặc quy
định địa phương.

**Bài học:** không thay đổi tham số chỉ vì một metric in-sample đẹp; phải xem
chi phí false positive/false refusal và mức tin cậy của nhãn.

## 4.5. Đóng băng evaluation V2 sau baseline

Sau khi baseline quality hardening được cố định tại commit
`73d3a141e51c7348763ead7379bf56bf36b54586`, metadata/protocol ghi nhận một tập
60 câu V2 được tạo mà không xem bộ 30 câu cũ, retrieval report,
query-understanding rule hoặc retriever implementation. Repository xác minh
được commit, thời điểm và SHA, nhưng tự nó không chứng minh được mọi nội dung
người tạo đã hoặc chưa xem. Dataset gồm 50 câu kỳ vọng trả lời và 10 câu kỳ vọng
từ chối/làm rõ. Toàn bộ nhãn mang trạng thái
`ai_generated_candidate_pending_human_review`.

Dataset được đóng băng với SHA-256:

```text
fc892269eae03256ce8a2808c444c89a98af7ac3a16d62a97fabb452e8bef363
```

Việc đóng băng giúp phát hiện thay đổi trái phép và ngăn sửa dataset âm thầm sau
khi xem kết quả. Tuy nhiên, nó không biến tập do AI tạo thành đánh giá độc lập
hoặc nhãn pháp lý do chuyên gia xác nhận. Chính sách hiện tại là không tune
retrieval/query rule trực tiếp theo kết quả V2; mọi chỉnh nhãn phải tạo version
và manifest mới.

Evaluator kiểm tra SHA/path với manifest và lưu commit, cấu hình cùng fingerprint
code/corpus/index. Artifact cũng ghi rõ worktree lúc chạy còn dirty do chính các
file evaluator/config đang được bổ sung; vì vậy có thể kiểm toán nội dung đã
chạy nhưng chưa được gọi là tái lập từ clean checkout độc lập.

## 4.6. Phản hồi và thay đổi từ Minh Long

[CẦN NGƯỜI DÙNG BỔ SUNG]

Nên lập bảng từ trải nghiệm thật:

| Thời điểm | Phản hồi/yêu cầu thực tế | Cách phân tích | Thay đổi đã làm | Kết quả được xác nhận |
|---|---|---|---|---|
| [Bổ sung] | [Bổ sung] | [Bổ sung] | [Bổ sung] | [Bổ sung] |

Chỉ ghi “được chấp nhận/nghiệm thu” khi có xác nhận thật.

---

# 5. Các quyết định kỹ thuật tiêu biểu

## 5.1. Dùng nguồn Công báo Word thay cho PDF nhiễu

**Vấn đề:** PDF của VBHN 133 có trang scan và chú thích hợp nhất gây nhiễu
parser.

**Quyết định:** sử dụng ba phần Công báo Word chính thức, lưu DOCX dẫn xuất cùng
provenance về file DOC nguồn.

**Kết quả:** quality gate đạt 260 Điều, 441 chunks, không còn boilerplate Công
báo trong artifact production.

**Giới hạn:** đây là lựa chọn nguồn tốt hơn, chưa phải giải pháp OCR tổng quát
cho mọi PDF scan.

## 5.2. Legal-aware chunking thay vì chỉ cắt theo ký tự

**Vấn đề:** character chunking có thể cắt qua Điều–Khoản–Điểm, làm mất ngữ cảnh
và citation.

**Quyết định:** duy trì character chunker làm baseline và dùng legal-aware
chunker cho production.

**Kết quả:** mỗi chunk có metadata pháp lý và giới hạn độ dài; retrieval có thể
trả citation theo Điều–Khoản–Điểm.

## 5.3. Tách experiment và production

**Vấn đề:** thử corpus mới trực tiếp trên production có thể làm lệch chunk,
embedding, metadata và FAISS.

**Quyết định:** experiment nằm trong `data/experiments/`; promotion có quality
gate, `--confirm`, validation và backup.

**Kết quả:** corpus mới được so sánh và promotion bằng commit riêng, giữ được
khả năng truy vết thay đổi.

## 5.4. Không nâng evidence threshold theo kết quả in-sample

**Vấn đề:** threshold `0,55` quá thấp trên diagnostic nhưng threshold cao hơn
làm tăng từ chối nhầm.

**Quyết định:** giữ nguyên threshold production, ghi rõ hạn chế và bổ sung
corpus-gap routing cho các lớp câu hỏi chắc chắn cần nguồn chưa có.

**Kết quả:** hệ thống giảm một số câu trả lời vượt phạm vi mà không tuyên bố đã
giải quyết hoàn toàn evidence calibration.

---

# 6. Kết quả đạt được

## 6.1. Kết quả sản phẩm

- Pipeline nguồn → chuẩn hóa → legal tree → chunks → embedding → FAISS.
- Hybrid retrieval và query rewriting tiếng Việt.
- Citation Điều–Khoản–Điểm.
- Guardrails cho input, evidence và output citation.
- Extractive provider mặc định; Gemini và Qwen tùy chọn.
- FastAPI, web chat, health endpoint và JSONL event log.
- Quy trình experiment/promotion corpus có quality gate.

## 6.2. Kết quả kiểm thử

Lần chạy full suite gần nhất:

```text
70 passed, 1 warning
```

Cảnh báo liên quan quyền ghi `.pytest_cache`, không phải test failure. Trước khi
nộp báo cáo chính thức, cần chạy lại lệnh dưới đây và chụp output có ngày giờ:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## 6.3. Kết quả retrieval và cách diễn giải

| Chỉ số | Kết quả trên bộ 30 câu nội bộ |
|---|---:|
| Hit@1 | 0,9667 |
| Recall@3 | 1,0000 |
| Recall@5 | 1,0000 |
| MRR | 0,9778 |

Bộ câu hỏi và các rule retrieval xuất hiện cùng giai đoạn MVP; Git không đủ
bằng chứng để xác định dataset được viết trước hay sau khi tune rule. Vì vậy số
liệu trên phải được gọi là **development-set baseline**, không gọi là held-out
accuracy và không dùng làm trọng tâm chứng minh chất lượng pháp lý.

## 6.4. Baseline hành vi trên bộ V2 đã đóng băng

Bộ V2 được chạy bằng `extractive` offline trên baseline commit `73d3a14`. Kết
quả artifact tại `data/evaluation/system_behavior_v2_blind_extractive.json`:

| Chỉ số | Kết quả | Cách hiểu đúng |
|---|---:|---|
| Answer success rate | 98% (49/50) | Provider trả về trạng thái thành công |
| Expected-article Hit@1 | 76% (38/50) | Điều kỳ vọng đứng đầu danh sách citation |
| Expected-article Hit@k | 90% (45/50) | Điều kỳ vọng xuất hiện ở một vị trí trong top-k |
| Article MRR | 0,825 | Thứ hạng trung bình nghịch đảo của Điều kỳ vọng |
| Refusal correctness | 30% (3/10) | Chỉ 3/10 câu kỳ vọng refuse được xử lý đúng hành vi |
| Grounded behavior | 68,33% (41/60) | Answer yêu cầu success + Hit@1; refuse yêu cầu đúng routing |

Hit@k không được diễn giải thành độ đúng của câu trả lời: provider extractive
chỉ dùng evidence `[1]`, nên grounded behavior dùng Hit@1. Kết quả hữu ích để
chỉ ra cả điểm yếu xếp hạng và refusal, nhưng chưa phải độ chính xác pháp lý.
Nhãn do AI tạo đang chờ human/legal review; vì vậy không dùng các lỗi V2 để tune
trực tiếp hệ thống và không công bố đây là independent/expert-held-out benchmark.

## 6.5. Provider comparison và kết quả chưa có

Repository đã có provider comparison harness để chạy cùng một dataset qua
extractive, Gemini và Qwen, đồng thời ghi trạng thái, latency, token usage,
citation và fallback mà không lưu API key. Harness mặc định chỉ dùng dữ liệu
tổng hợp và không lưu nguyên câu hỏi/câu trả lời vào report.

- Chưa có Qwen/Gemini live comparison vì chưa cấu hình key cục bộ cho lần đo.
- Chưa có independent/expert-held-out evaluation; bộ V2 chỉ là candidate đã
  đóng băng, chờ human/legal review.
- Chưa có chuyên gia pháp lý duyệt nhãn.
- Chưa có metric citation correctness, faithfulness, completeness từ human
  review.
- Chưa có bằng chứng người dùng thật hoặc hiệu quả kinh doanh.

---

# 7. Khó khăn, cách xử lý và hạn chế còn lại

| Khó khăn | Cách xử lý | Kết quả | Hạn chế còn lại |
|---|---|---|---|
| PDF scan/chú thích gây nhiễu | Chọn Công báo Word chính thức, lưu provenance | Corpus vượt quality gate | Chưa có OCR tổng quát |
| Chunk dễ mất cấu trúc pháp lý | Legal-aware chunker + validator | 441 chunks có metadata | Điều dài vẫn cần chia nhiều chunk |
| Artifact có thể lệch phiên bản | Manifest, hash, count, dimension checks | 441 chunks/embedding/vector đồng bộ | Cần kiểm tra portability trên CI/Linux |
| LLM có thể trả lời thiếu căn cứ | Evidence/output guardrail + extractive fallback | Hosted output lỗi không làm chat sập | Chưa đo faithfulness trên tập được duyệt |
| Corpus chỉ có một văn bản lõi | Corpus-gap routing và disclaimer | Giảm một số trả lời vượt phạm vi | Thiếu nghị định, thông tư, địa phương |
| Threshold khó phân tách | Diagnostic câu âm, không nâng ngưỡng máy móc | Có số liệu trung thực về trade-off | Chưa có held-out calibration |
| Cold start/model CPU | Giữ model local và ghi nhận runtime | Demo chạy được | Lần đầu từng đo khoảng 18–30 giây; có rủi ro bộ nhớ |

---

# 8. Kỹ năng làm việc tại doanh nghiệp

## 8.1. Tiếp nhận và làm rõ yêu cầu

[CẦN NGƯỜI DÙNG BỔ SUNG: một ví dụ thật về yêu cầu ban đầu còn mơ hồ, câu hỏi
đã dùng để làm rõ và kết quả thống nhất với Minh Long.]

## 8.2. Giao tiếp và phản hồi

[CẦN NGƯỜI DÙNG BỔ SUNG: kênh trao đổi, tần suất, một phản hồi cụ thể và cách
phản hồi đó làm thay đổi sản phẩm.]

## 8.3. Quản lý phạm vi

Điểm có bằng chứng kỹ thuật là sản phẩm được giới hạn thành trợ lý tra cứu đất
đai phục vụ demo/nghiên cứu; chưa triển khai kho luật đầy đủ hoặc tư vấn pháp lý
chuyên nghiệp. Việc tách phần UI exploration khỏi production và giữ Qwen ở chế
độ opt-in thể hiện cách tránh mở rộng phạm vi khi chưa đủ bằng chứng chất lượng.

[CẦN NGƯỜI DÙNG BỔ SUNG: quyết định phạm vi nào đã được trao đổi với công ty.]

## 8.4. Quản lý thay đổi và rủi ro

- Dùng Git để lưu mốc phát triển.
- Tách corpus experiment khỏi production.
- Promotion có validation và backup.
- Không commit API key hoặc hồ sơ cá nhân.
- Không công bố calibration in-sample như production accuracy.

## 8.5. Tự học và giải quyết vấn đề

Quá trình thực hiện yêu cầu kết hợp xử lý tài liệu, NLP, vector search, backend,
kiểm thử và giao diện. Bài học quan trọng là model mạnh hơn không tự giải quyết
được nguồn luật thiếu, hiệu lực pháp lý hoặc evaluation chưa độc lập.

[CẦN NGƯỜI DÙNG BỔ SUNG: công nghệ mới đã tự học, cách học và khó khăn cá nhân.]

## 8.6. Trách nhiệm nghề nghiệp

Trong lĩnh vực pháp lý, báo cáo cần phân biệt rõ điều đã kiểm chứng với suy luận.
Hệ thống giữ disclaimer, từ chối khi thiếu nguồn rõ ràng và không tự mô tả là tư
vấn chuyên nghiệp. Đây là yêu cầu đạo đức và quản lý rủi ro, không chỉ là chi
tiết kỹ thuật.

---

# 9. Bài học kinh nghiệm

1. **Nguồn dữ liệu quan trọng hơn giao diện đẹp.** Một citation tốt phải truy
   ngược được về văn bản và cấu trúc pháp lý.
2. **Metric cao cần được đặt trong bối cảnh.** Kết quả trên development set nhỏ
   không thay thế held-out test hoặc chuyên gia duyệt.
3. **Không sửa production trực tiếp.** Experiment, quality gate, backup và
   promotion giúp giảm rủi ro thay đổi dữ liệu.
4. **Fallback phải có giới hạn.** Chỉ lỗi provider dự kiến được fallback; lỗi
   lập trình không nên bị che giấu.
5. **Biết từ chối là một chức năng.** Với corpus hẹp, câu trả lời trung thực về
   giới hạn tốt hơn một câu trả lời trôi chảy nhưng thiếu căn cứ.
6. **Tài liệu doanh nghiệp cần bằng chứng ngoài repository.** Vai trò, phản hồi,
   deadline và nghiệm thu phải đến từ trải nghiệm thật, không suy ra từ code.

---

# 10. Hướng phát triển

Theo thứ tự ưu tiên:

1. nhờ người độc lập/chuyên gia rà soát bộ V2 đã đóng băng; nếu phải sửa nhãn,
   tạo version và manifest mới thay vì sửa âm thầm hoặc tune trực tiếp theo V2;
2. chấm citation correctness, faithfulness, completeness và refusal trên một
   tập nhỏ bằng human review;
3. dùng provider comparison harness để chạy Qwen/Gemini/extractive trên cùng
   evidence và ghi token, latency, citation, fallback khi có key cục bộ;
4. ingest văn bản hướng dẫn chính cùng metadata hiệu lực;
5. bổ sung session/query condensation nếu cần hội thoại nhiều lượt;
6. hoàn thiện auth, rate limit, CORS, retention và monitoring chỉ khi có yêu cầu
   triển khai ngoài local.

---

# 11. Kết luận

Dự án đã hình thành một baseline RAG pháp luật có thể chạy end-to-end với nguồn
có provenance, legal-aware chunking, embedding/vector index, hybrid retrieval,
citation, guardrails, provider fallback, API/UI và kiểm thử tự động. Giá trị lớn
nhất không nằm ở một con số retrieval cao mà ở quá trình kiểm soát nguồn, tách
experiment/production và thừa nhận giới hạn evidence.

Để hoàn thiện đồ án môn Kỹ năng làm việc tại doanh nghiệp, phần còn thiếu quan
trọng nhất là bối cảnh freelance thật với Minh Long: yêu cầu, người phụ trách,
kênh trao đổi, phản hồi, deadline, bàn giao và vai trò cá nhân. Những nội dung
này phải được người thực hiện bổ sung từ trải nghiệm thật trước khi nộp.

---

# Phụ lục A. Bản đồ bằng chứng

| Nhận định | Nguồn bằng chứng | Mức sử dụng |
|---|---|---|
| Kiến trúc RAG và luồng trả lời | `app/services/legal_assistant.py`, `docs/context-pack/ARCHITECTURE_MAP.md` | Có thể khẳng định |
| Corpus production VBHN 133 | `data/processed/legal_embeddings_manifest.json`, metadata document | Có thể khẳng định về artifact; không tự khẳng định hiệu lực |
| 260 Điều, 441 chunks/vector, dimension 384 | manifests và `data/processed/legal_chunks.json` | Có thể khẳng định |
| Retrieval metrics trên 30 câu | `data/evaluation/retrieval_eval_hybrid_vbhn_133.json` | Chỉ gọi development-set baseline |
| Test tăng 38 → 54 → 70 | lịch sử tài liệu và output pytest | Trình bày theo timeline |
| Threshold `0,55` chưa hiệu quả | `data/evaluation/evidence_calibration_v1.json` | Chỉ in-sample diagnostic |
| Qwen integration | `app/llm_provider/openai_compatible_provider.py` và mock tests | Không gọi là live test |
| Bộ V2 gồm 60 câu, baseline và SHA | `candidate_questions_v2_blind_manifest.json` | Candidate post-baseline, chờ human review |
| V2 extractive: success 98%, Hit@1 76%, Hit@k 90%, MRR 0,825, refusal 30%, grounded 68,33% | `system_behavior_v2_blind_extractive.json` | Hành vi kỹ thuật, không phải độ chính xác pháp lý |
| Provider comparison harness | `scripts/compare_answer_providers.py`, `docs/evaluation/PROVIDER_COMPARISON.md` | Có harness; chưa có live Qwen/Gemini report |
| Phản hồi/đầu mối/deadline Minh Long | Không có trong repository | Người dùng phải bổ sung |
| Nghiệm thu và số người dùng thật | Chưa có bằng chứng | Không được tự khẳng định |

# Phụ lục B. Hồ sơ nên đính kèm khi nộp

- Ảnh output pytest chạy lại trước ngày nộp.
- Ảnh output retrieval evaluation kèm cảnh báo giới hạn.
- Sơ đồ kiến trúc rút gọn.
- Ảnh giao diện và citation mở rộng.
- Git log các mốc chính.
- [CẦN NGƯỜI DÙNG BỔ SUNG] ảnh/chứng cứ trao đổi với Minh Long đã được phép sử
  dụng và đã che thông tin nhạy cảm.
- [CẦN NGƯỜI DÙNG BỔ SUNG] xác nhận bàn giao/nghiệm thu nếu có.

# Phụ lục C. Câu hỏi cần người thực hiện trả lời

1. Thời gian freelance chính xác là khi nào?
2. Ai là đầu mối giao việc và chức vụ của họ, nếu được phép công bố?
3. Yêu cầu ban đầu được mô tả bằng lời nào?
4. Hai bên trao đổi qua kênh nào và bao lâu một lần?
5. Ba phản hồi quan trọng nhất từ Minh Long là gì?
6. Deadline, chi phí API và giới hạn thiết bị là gì?
7. Vai trò thực tế của người thực hiện gồm những công việc nào?
8. Sản phẩm đã được xem, bàn giao hoặc nghiệm thu ở mức nào?
9. Công ty cho phép sử dụng thông tin/hình ảnh nào trong báo cáo?
10. Bài học giao tiếp hoặc quản lý công việc đáng nhớ nhất là gì?
