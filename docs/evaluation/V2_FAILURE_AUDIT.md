# Audit kỹ thuật 19 lỗi baseline V2

Ngày rà soát: 16/11/2026. Người thực hiện rà soát: AI hỗ trợ phát triển.
Trạng thái nhãn: **chưa có human/expert legal review**. Đây là đối chiếu câu hỏi,
source/rule và nội dung corpus đang lưu; không phải xác nhận pháp lý hoặc đánh
giá hiệu lực văn bản.

## Nguồn và cách đếm

- Câu hỏi/nhãn gốc: `data/evaluation/candidate_questions_v2_blind.json`.
- Kết quả gốc: `data/evaluation/system_behavior_v2_blind_extractive.json`.
- Corpus đối chiếu: `data/processed/legal_chunks.json`, VBHN 133/VBHN-VPQH.
- Rewrite baseline: `app/agent/query_understanding.py` tại `73d3a14`.
- Baseline là `73d3a14` với fingerprint/worktree được ghi trong artifact gốc;
  không coi artifact đó là một lần chạy clean checkout.

Có **19 câu riêng biệt**: 12 câu answer trượt Hit@1, trong đó 5 câu trượt cả
Hit@k, cộng 7 câu refuse bị trả `success`. Không cộng 12 + 5 + 7 thành 24.

Danh sách `A → B` bên dưới là thứ tự **Điều khác nhau theo lần xuất hiện đầu**
trong citation gốc. Evaluator gốc đã bỏ citation trùng Điều; artifact không lưu
chunk ID, dense/lexical score hoặc toàn bộ thứ hạng chunk. Vì vậy danh sách có
thể ngắn hơn 5 và không được xem là raw top-5 chunks. Không suy ra score/margin
hoặc nguyên nhân định lượng từ phần dữ liệu chưa được lưu.

Kết luận nguyên nhân là chẩn đoán kỹ thuật để thiết kế thí nghiệm. Riêng các
nhận định nhãn đúng/sai hoặc nhiều Điều hợp lý đều cần người duyệt trước khi
thay nhãn. Audit này **không thay đổi dataset/manifest gốc, không tạo V2.1**.
Khi dùng các câu này để sửa rule, V2 phải được ghi nhận là development set đã
quan sát; kết quả sau sửa không còn là một phép đo độc lập.

## Tổng hợp phân loại

| Nhóm chính | Số câu | ID |
|---|---:|---|
| Điều kỳ vọng có trong kết quả nhưng bị xếp sau | 5 | 013, 017, 026, 029, 031 |
| Không truy hồi được Điều trực tiếp theo nhãn; có khoảng trống từ vựng | 3 | 021, 028, 032 |
| Câu/nhãn còn mơ hồ, đồng thời thiếu Điều kỳ vọng | 1 | 030 |
| False refusal vì corpus-gap rule quá rộng | 1 | 037 |
| Nhiều cấu phần; evidence thiếu đa dạng và rank đầu là quy định chung | 2 | 040, 046 |
| Thiếu dữ kiện/khái niệm hành vi hoặc yêu cầu bảo đảm kết quả vụ việc | 6 | 051, 052, 053, 054, 055, 058 |
| Cần dữ liệu giá hiện hành theo địa điểm nhưng chưa có nguồn/vị trí | 1 | 060 |

Không tìm thấy trường hợp nào trong 7 lỗi refuse là “đã từ chối nhưng evaluator
không nhận status”: cả bảy có `status=success`. Tuy nhiên artifact chỉ chứng
minh routing/status; không lưu toàn văn answer để xác nhận hệ thống đã đưa ra
kết luận sai nội dung cụ thể nào.

## 12 câu answer trượt hạng 1

### V2Q013 — rank sai giữa “trường hợp” và “thẩm quyền”

- Câu hỏi: “Những trường hợp chuyển mục đích sử dụng đất nào phải được cơ quan
  nhà nước có thẩm quyền cho phép?”
- Rewrite baseline: giữ nguyên.
- Nhãn kỳ vọng: `[121]` — Chuyển mục đích sử dụng đất.
- Điều trả về: `123 → 121 → 227 → 122 → 116`.
- Điều đầu: 123 — Thẩm quyền giao đất, cho thuê đất, cho phép chuyển mục đích
  sử dụng đất. Điều kỳ vọng ở vị trí thứ hai.
- Đối chiếu: chunk `art121_chunk001`, khoản 1 liệt kê các trường hợp phải được
  cho phép; 123 xác định cơ quan có thẩm quyền. Nhãn 121 có tương ứng văn bản
  trực tiếp; 123 liên quan nhưng trả lời khía cạnh khác.
- Phân loại: **ranking**. Cụm “thẩm quyền” có thể làm title boost ưu tiên 123;
  đây là giả thuyết, chưa có score ablation để khẳng định.
- Hành động: thử scoring phân biệt câu hỏi “trường hợp nào” với “ai cho phép”,
  có positive controls cho cả hai; chưa đổi nhãn.

### V2Q017 — phủ định bị lấn bởi cụm trùng title

- Câu hỏi: “Hộ gia đình sử dụng đất ổn định, không có giấy tờ, không vi phạm
  và không được giao trái thẩm quyền được xem xét cấp Giấy chứng nhận theo quy
  định nào?”
- Rewrite baseline: giữ nguyên.
- Nhãn kỳ vọng: `[138]` — Cấp Giấy chứng nhận cho trường hợp không giấy tờ,
  không vi phạm, không thuộc giao đất không đúng thẩm quyền.
- Điều trả về: `140 → 138`.
- Điều đầu: 140 — Cấp Giấy chứng nhận cho đất được giao không đúng thẩm quyền.
- Đối chiếu: `art138_chunk001` nêu các điều kiện loại trừ tương ứng; 140 là
  trường hợp mà câu hỏi đang phủ định. Cả title 138 và 140 chứa nhiều từ giống
  nhau, nên overlap đơn thuần không biểu diễn được phủ định.
- Phân loại: **ranking/negation**; không thấy rewrite làm mất chữ “không”.
- Hành động: thí nghiệm lexical/query handling có ngữ cảnh phủ định; test cặp
  “được giao trái thẩm quyền” và “không được giao trái thẩm quyền”.

### V2Q021 — “ghi sai” chưa nối tới “đính chính”

- Câu hỏi: “Sổ đỏ nhà tôi bị ghi sai tên và sai thông tin thửa đất thì xử lý
  kiểu gì?”
- Rewrite baseline: “Giấy chứng nhận quyền sử dụng đất nhà tôi bị ghi sai tên
  và sai thông tin thửa đất thì xử lý kiểu gì?”
- Nhãn kỳ vọng: `[152]` — Đính chính, thu hồi, hủy giấy chứng nhận đã cấp.
- Điều trả về: `135 → 148 → 134 → 146`; không có 152.
- Điều đầu: 135 — Nguyên tắc cấp Giấy chứng nhận.
- Đối chiếu: `art152_chunk001`, khoản 1 điểm a/b có sai sót thông tin người được
  cấp và thông tin thửa đất. Nhãn có tương ứng trực tiếp trong corpus.
- Phân loại: **candidate recall + khoảng trống rewrite/từ vựng**. Rewrite “sổ
  đỏ” đúng hướng nhưng không mở rộng “ghi sai” thành thuật ngữ đính chính.
- Hành động: thử expansion có giới hạn cho sai thông tin giấy chứng nhận;
  không đồng nhất mọi lỗi giấy tờ với thu hồi/hủy.

### V2Q026 — ruộng bị nhầm với đất ở

- Câu hỏi: “Ruộng của hộ gia đình bị thu hồi thì thường được đền bằng đất,
  tiền hay nhà?”
- Rewrite baseline: giữ nguyên.
- Nhãn kỳ vọng: `[96]` — Bồi thường đất nông nghiệp của hộ gia đình, cá nhân.
- Điều trả về: `98 → 96 → 99 → 109 → 101`.
- Điều đầu: 98 — Bồi thường đất ở.
- Đối chiếu: `art096_chunk001`, khoản 1 chứa các hình thức đất/tiền/nhà mà câu
  hỏi nêu; 98 cũng có các hình thức tương tự nhưng loại đất khác.
- Phân loại: **ranking + khoảng trống từ vựng “ruộng/đền”**.
- Hành động: expansion loại đất nông nghiệp và từ “bồi thường” trong ngữ cảnh
  thu hồi; test để không đổi nhầm các từ “đền” không liên quan.

### V2Q028 — danh mục hỗ trợ bị xếp thành chi trả tiền bồi thường

- Câu hỏi: “Ngoài tiền bồi thường, người bị lấy đất còn có thể được hỗ trợ
  những khoản gì?”
- Rewrite baseline: giữ nguyên.
- Nhãn kỳ vọng: `[108]` — Hỗ trợ khi Nhà nước thu hồi đất.
- Điều trả về: `94 → 91 → 92 → 98 → 254`; không có 108.
- Điều đầu: 94 — Kinh phí và chi trả tiền bồi thường, hỗ trợ, tái định cư.
- Đối chiếu: `art108_chunk001`, khoản 1 có danh sách các loại hỗ trợ; 94 tập
  trung chi trả/kinh phí, không phải danh mục mà câu hỏi yêu cầu.
- Phân loại: **candidate recall + từ vựng/intent**. “Bị lấy đất” không được
  rewrite thành thu hồi đất; các từ tiền/bồi thường có thể lấn mục đích hỏi.
- Hành động: thí nghiệm expansion giữ trọng tâm “hỗ trợ những khoản gì”.

### V2Q029 — câu hỏi thời hạn thông báo bị lấn bởi chủ đề bồi thường

- Câu hỏi: “Nhà nước định thu hồi ruộng hoặc đất ở thì phải báo cho dân trước
  bao lâu?”
- Rewrite baseline: giữ nguyên.
- Nhãn kỳ vọng: `[85]` — Thông báo thu hồi đất và chấp hành quyết định thu hồi.
- Điều trả về: `108 → 98 → 101 → 85 → 91`.
- Điều đầu: 108 — Hỗ trợ khi Nhà nước thu hồi đất; 85 ở vị trí thứ tư.
- Đối chiếu: `art085_chunk001`, khoản 1 chứa thời hạn thông báo theo nhóm đất.
- Phân loại: **ranking + paraphrase** (“báo trước bao lâu” so với “thông báo”).
- Hành động: thử signal về thời hạn thông báo; kiểm tra riêng câu hỏi mức bồi
  thường để không tăng 85 cho mọi câu thu hồi.

### V2Q030 — candidate miss nhưng nhãn cần duyệt

- Câu hỏi: “Gia đình ở ổn định lâu rồi nhưng chẳng còn giấy tờ đất, cũng không
  lấn chiếm, vậy quy định cấp sổ nằm ở đâu?”
- Rewrite baseline: giữ nguyên.
- Nhãn kỳ vọng: `[138]` — Trường hợp không có giấy tờ, không vi phạm.
- Điều trả về: `137`; không có 138.
- Đối chiếu: title/đoạn đầu 138 phù hợp nếu ý là không có các giấy tờ về quyền
  sử dụng đất. Nhưng “chẳng còn” cũng có thể là giấy gốc bị thất lạc;
  `art137_chunk007`, khoản 7 đề cập bản sao khi bản gốc thất lạc. Câu không nêu
  có bản sao hay chưa từng có giấy; cũng chưa loại trừ giao trái thẩm quyền.
- Phân loại: **nhãn/câu mơ hồ + candidate recall**; chưa đủ căn cứ gọi 137 hoàn
  toàn sai hoặc tự đổi nhãn sang 137.
- Hành động: người duyệt chọn làm rõ câu hỏi, cho tập nhãn chấp nhận có điều kiện,
  hoặc kỳ vọng clarification. Nếu sửa thì tạo V2.1 riêng, giữ label pending.

### V2Q031 — điều kiện chọn hình thức trả tiền bị xếp sau quy định cho thuê

- Câu hỏi: “Đang thuê đất của Nhà nước và trả tiền từng năm, tôi có được đổi
  sang trả một lần cho thời gian còn lại không?”
- Rewrite baseline: giữ nguyên.
- Nhãn kỳ vọng: `[30]` — Quyền lựa chọn hình thức trả tiền thuê đất.
- Điều trả về: `120 → 30 → 33 → 155 → 156`.
- Điều đầu: 120 — Cho thuê đất; 30 ở vị trí thứ hai.
- Đối chiếu: `art030_chunk001`, khoản 1 có chuyển từ trả hằng năm sang một lần
  cho thời gian còn lại cùng điều kiện kèm theo. 120 là căn cứ liên quan đến
  hình thức thuê, nhưng 30 khớp mục đích hỏi trực tiếp hơn.
- Phân loại: **ranking**. Câu có thể trả quy định chung có điều kiện, không nên
  chỉ vì dùng đại từ “tôi” mà từ chối toàn bộ tra cứu.

### V2Q032 — hợp thửa chưa được nhận diện qua khẩu ngữ

- Câu hỏi: “Hai mảnh sát nhau muốn gộp thành một thửa thì cần cùng mục đích và
  cùng thời hạn sử dụng không?”
- Rewrite baseline: giữ nguyên.
- Nhãn kỳ vọng: `[220]` — Tách thửa đất, hợp thửa đất.
- Điều trả về: `172 → 173 → 121 → 218 → 156`; không có 220.
- Điều đầu: 172 — Đất sử dụng có thời hạn.
- Đối chiếu: `art220_chunk001`, khoản 3 nêu các điều kiện mục đích/thời hạn/hình
  thức trả tiền thuê khi hợp thửa. Từ khóa thời hạn/mục đích đang dẫn retrieval
  sang chủ đề liên quan nhưng không đủ trực tiếp.
- Phân loại: **candidate recall + paraphrase**. Rule “gộp sổ” chưa bao phủ
  “gộp thành một thửa”.
- Hành động: expansion có ngữ cảnh hợp thửa; giữ câu hỏi sử dụng nhiều mục đích
  khác với câu hỏi gộp các thửa.

### V2Q037 — false refusal của câu hỏi quy định chung

- Câu hỏi: “Bảng giá đất của tỉnh được đem ra tính những khoản nào?”
- Rewrite baseline: giữ nguyên.
- Nhãn kỳ vọng: `[159]` — Bảng giá đất.
- Kết quả: `insufficient_coverage`, không có citation.
- Đối chiếu: `art159_chunk001`, khoản 1 liệt kê các trường hợp áp dụng bảng
  giá đất. Câu không yêu cầu đơn giá của địa phương hiện tại.
- Nguyên nhân source: `CORPUS_GAP_PATTERNS` bắt `bảng giá đất` cùng `tỉnh` rồi
  chuyển thẳng sang insufficient coverage.
- Phân loại: **false corpus-gap routing**, không phải bằng chứng retrieval
  không tìm thấy Điều 159 vì retrieval chưa được gọi.
- Hành động: phân biệt “bảng giá dùng làm gì/theo nguyên tắc nào” với “giá hiện
  tại ở địa điểm này là bao nhiêu”.

### V2Q040 — multi-condition, top-k chưa bao phủ đủ cấu phần

- Câu hỏi: “Một hộ đủ điều kiện bồi thường bị thu hồi toàn bộ đất ở, căn nhà
  phải phá dỡ và gia đình phải chuyển chỗ ở thì cần đối chiếu quy định nào về bồi
  thường đất, bồi thường nhà và bố trí tái định cư?”
- Rewrite baseline: giữ nguyên.
- Nhãn kỳ vọng: `[98, 102, 111]` — đất ở, nhà/công trình, bố trí tái định cư.
- Điều trả về: `91 → 111`; đầu là 91 — Nguyên tắc bồi thường, hỗ trợ, tái định cư.
- Đối chiếu: 98/102/111 tương ứng ba phần câu hỏi. 91 cũng liên quan về nguyên
  tắc nhưng không thay cho ba nội dung chi tiết. 111 có 12 chunks trong corpus;
  chỉ có 2 Điều khác nhau trong các citations cho thấy evidence thiếu đa dạng.
- Phân loại: **multi-evidence coverage + ranking**. Nhãn nhiều Điều có lý do
  văn bản; top1-hit hoặc any-hit riêng lẻ không chấm được đầy đủ câu này.
- Hành động: đo recall của toàn bộ tập Điều kỳ vọng; thí nghiệm article
  diversification/query decomposition và extractive nhiều evidence có giới hạn.

### V2Q046 — nguyên tắc chung lấn căn cứ, thông báo và thủ tục

- Câu hỏi: “Đối với dự án công cộng dự kiến thu hồi đất, cần kiểm tra đồng thời
  căn cứ và điều kiện thu hồi, thời hạn thông báo cho người dân, cùng trình tự
  bồi thường, hỗ trợ, tái định cư ở những điều nào?”
- Rewrite baseline: giữ nguyên.
- Nhãn kỳ vọng: `[80, 85, 87]` — căn cứ/điều kiện, thông báo, trình tự.
- Điều trả về: `91 → 87 → 93`; đầu là 91 — Nguyên tắc bồi thường, hỗ trợ, tái
  định cư. 87 trong kết quả nhưng 80/85 vắng.
- Đối chiếu: title 80/85/87 tách đúng các khía cạnh của câu. Điều 91/93 có liên
  quan bối cảnh, không bao phủ các khía cạnh đã nêu. 87 có 9 chunks.
- Phân loại: **multi-evidence coverage + ranking**. Any-hit ở 87 không chứng
  minh answer đầy đủ ba phần.
- Hành động: đo set recall và tác động chunks trùng Điều trước khi giữ phương
  án article diversification; chưa đổi nhãn tự động.

## 7 câu refuse bị trả success

### V2Q051 — thiếu dữ kiện cấp giấy chứng nhận

- Câu hỏi: “Miếng đất này có làm sổ được không?”
- Rewrite baseline: giữ nguyên; nhãn Điều kỳ vọng: `[]`.
- Điều trả về: `187 → 120 → 9 → 185 → 10`; đầu 187 — Đất làm muối.
- Kết quả: `success`. Câu không nêu nguồn gốc, loại đất, giấy tờ, thời điểm,
  vi phạm/tranh chấp hoặc chủ thể. Từ “làm sổ” không được hiểu như eligibility
  cấp giấy, còn “làm” có thể tạo tương đồng không phù hợp với “đất làm muối”.
- Phân loại: **needs_clarification**; không phải ngoài miền đất đai.
- Hành động: hỏi dữ kiện trọng yếu, có thể đề nghị tra quy định chung; không
  tuyên bố thửa đất cụ thể chắc chắn đủ/không đủ điều kiện.

### V2Q052 — đòi số tiền cho vụ việc chưa có dữ kiện

- Câu hỏi: “Nhà nước thu đất của tôi thì đền bao nhiêu tiền?”
- Rewrite baseline: giữ nguyên; nhãn Điều kỳ vọng: `[]`.
- Điều trả về: `119 → 98 → 118 → 108 → 33`; đầu 119 — Giao đất có thu tiền sử
  dụng đất.
- Kết quả: `success`. Cần loại đất, vị trí/diện tích, phương án/quyết định và
  tình trạng pháp lý; mức tiền cụ thể cần nguồn giá/quyết định tương ứng.
- Phân loại: **needs_clarification + local/current source gap**.
- Hành động: ưu tiên hỏi dữ kiện và nêu giới hạn tính tiền; không vì thiếu giá
  mà chặn câu hỏi chung về nguyên tắc bồi thường.

### V2Q053 — hành vi “chuyển đất” chưa xác định

- Câu hỏi: “Tôi có được chuyển đất không?”
- Rewrite baseline: giữ nguyên; nhãn Điều kỳ vọng: `[]`.
- Điều trả về: `121 → 255 → 174`; đầu 121 — Chuyển mục đích sử dụng đất.
- Kết quả: `success`. “Chuyển đất” có thể là chuyển nhượng/chuyển đổi/chuyển
  mục đích; câu chưa chọn một hành vi.
- Phân loại: **needs_clarification/ambiguous action**.
- Hành động: hỏi loại giao dịch/hành vi trước, tránh rewrite tự quyết một ý.

### V2Q054 — chưa biết lỗi của giấy tờ là gì

- Câu hỏi: “Sổ đất của tôi có vấn đề, cơ quan nào phải chịu trách nhiệm?”
- Rewrite baseline: giữ nguyên; nhãn Điều kỳ vọng: `[]`.
- Điều trả về: `7 → 6 → 69 → 217 → 226`; đầu 7 — Người chịu trách nhiệm trước
  Nhà nước đối với đất được giao quản lý.
- Kết quả: `success`. Chưa phân biệt sai thông tin/cấp sai/mất giấy, tranh
  chấp, chậm thủ tục hoặc trách nhiệm của một hành vi cụ thể.
- Phân loại: **needs_clarification/vague document problem**.
- Hành động: hỏi vấn đề, cơ quan xử lý và giấy tờ/quyết định đang có; không gán
  “trách nhiệm sử dụng đất” chỉ vì cùng từ “chịu trách nhiệm”.

### V2Q055 — yêu cầu bảo đảm kết quả tranh chấp

- Câu hỏi: “Tranh chấp đất nhà tôi thì bên nào chắc chắn thắng?”
- Rewrite baseline: giữ nguyên; nhãn Điều kỳ vọng: `[]`.
- Điều trả về: `236 → 235 → 90 → 3 → 220`; đầu 236 — Thẩm quyền giải quyết
  tranh chấp đất đai.
- Kết quả: `success`. Quy định thẩm quyền/hòa giải không cho phép dự đoán bên
  thắng khi chưa có hồ sơ/chứng cứ.
- Phân loại: **không kết luận vụ việc/needs_clarification**. Có thể cung cấp
  thủ tục chung nếu người dùng chuyển mục đích hỏi.
- Hành động: nêu rõ không thể xác định kết quả, hỏi tình tiết và nhu cầu tra
  thủ tục; không chặn mọi câu hỏi có chữ “tranh chấp”.

### V2Q058 — yêu cầu bảo đảm sang tên chỉ từ năm và giấy viết tay

- Câu hỏi: “Tôi mua đất bằng giấy viết tay năm 2010 thì chắc chắn sang tên
  được chứ?”
- Rewrite baseline: “Tôi mua đất bằng giấy viết tay năm 2010 thì chắc chắn
  đăng ký biến động chuyển nhượng quyền sử dụng đất được chứ?”
- Nhãn Điều kỳ vọng: `[]`.
- Điều trả về: `133 → 45 → 27 → 35 → 28`; đầu 133 — Đăng ký biến động.
- Kết quả: `success`. Rewrite làm rõ thuật ngữ nhưng không bổ sung được nguồn
  gốc/giấy tờ/tình trạng đăng ký, tranh chấp hoặc hồ sơ giao dịch.
- Phân loại: **needs_clarification/case-specific certainty**.
- Hành động: không cam kết kết quả từ hai dữ kiện; hỏi hồ sơ cần đối chiếu.
  Không tự đổi mọi câu giấy viết tay thành từ chối: câu hỏi quy định chung
  vẫn có thể tra cứu với giới hạn thích hợp.

### V2Q060 — giá hiện hành nhưng thiếu địa điểm và nguồn

- Câu hỏi: “Giá đất năm nay ở đây là bao nhiêu một mét vuông?”
- Rewrite baseline: giữ nguyên; nhãn Điều kỳ vọng: `[]`.
- Điều trả về: `159 → 160 → 158`; đầu 159 — Bảng giá đất.
- Kết quả: `success`. 159/160/158 là quy định về giá, không chứa một đơn giá
  hiện hành cho “ở đây”. Câu còn thiếu địa điểm, loại/vị trí đất và mục đích giá.
- Phân loại: **local_current_source_gap + needs_clarification**.
- Hành động: hỏi địa phương/vị trí/loại đất, yêu cầu nguồn bảng giá/quyết định
  phù hợp, không tạo số tiền từ similarity score.

## Kết luận sửa nhãn và hướng xác minh

Audit không phát hiện căn cứ đủ chắc để tự sửa một nhãn gốc rồi công bố số
“sau duyệt”. V2Q030 cần người duyệt nhất vì câu có nhiều cách hiểu. V2Q040/046
cần metric đầy đủ nhiều Điều; không nên giảm nhãn xuống Điều mà hệ thống đã
tìm thấy để làm đẹp kết quả. V2Q037 cần sửa router trước khi quy lỗi cho retrieval.

Các thí nghiệm sau audit cần báo cáo riêng từng thay đổi, giữ positive controls
để đo false refusal và giữ bộ gốc như baseline lịch sử. AI audit này không làm
nhãn trở thành expert-reviewed; V3 độc lập vẫn cần quy trình tác giả/người duyệt
riêng và không được tự gọi một tập do cùng AI sinh là tập người độc lập viết.
