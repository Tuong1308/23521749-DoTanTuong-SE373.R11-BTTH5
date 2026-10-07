# Block 1: Tra cứu chính sách đúng phiên bản

## 1. Thay đổi đã làm

Làm trên bản sao, giữ nguyên project mẫu:

| Bản sao | Tạo từ | Ghi chú |
|---|---|---|
| `stage-01-files-block1/` | `stage-01-files/` | Thêm tool `list_files` |
| `stage-02-skills-block1/` | `stage-02-skills/` | Thêm tool `list_files` và skill `refund-policy` |

Hai bản sao được thêm vào `members` trong `pyproject.toml` gốc (kèm `uv.lock` cập nhật) và đổi `name` trong `pyproject.toml` riêng để không trùng với bản gốc.

Theo giới hạn của đề, mình **chỉ sửa mã nguồn tool và phần đăng ký tool**. `prompts.py`, `config.py`, `app.py` và system prompt giữ nguyên như bản gốc. Model biết `list_files` **chỉ qua schema tool**, tức qua docstring của tool. Không có tên file, nội dung chính sách hay đáp án nào nằm trong prompt hay trong mã nguồn tool.

### Tool `list_files` (stage 01 và stage 02)

| File | Thay đổi |
|---|---|
| `tools/files.py` | Thêm hàm `_list()` và tool `list_files(path)`. Dùng lại `_resolve()` (chặn `..`, đường dẫn tuyệt đối, symlink thoát workspace) và format lỗi `{"ok": false, "error": {code, message}}` của file tools. |
| `tools/__init__.py` | Export `list_files`. |
| `agent.py` | `TOOLS = [list_files, read_file, write_file]`, nên tool xuất hiện trong schema gửi model. |

Hành vi của `list_files`:
- Chỉ liệt kê các mục trực tiếp, không đệ quy.
- Mỗi mục có `name`, `path` (tương đối workspace, dùng thẳng cho `read_file`) và `type` (`file` hoặc `directory`). Kết quả sắp theo `name`.
- `path` `.` là gốc workspace.
- Các lỗi: `DIRECTORY_NOT_FOUND` (không tồn tại), `NOT_A_DIRECTORY` (là file), `PATH_OUTSIDE_WORKSPACE` (`..`, đường dẫn tuyệt đối, `~`, symlink ra ngoài), `INVALID_PATH` (rỗng).
- Mục là symlink trỏ ra ngoài workspace không được đưa vào kết quả, và tool không đi theo link đó.

### Skill `refund-policy` (stage 02)

`workspace/skills/refund-policy/` (đồng bộ sang `fixtures/skills/refund-policy/`):
- `SKILL.md`:
  - Frontmatter có `name` và `description`.
  - Thiếu ngày mua, ngày yêu cầu hoàn hoặc trạng thái kích hoạt thì hỏi lại, không giả định.
  - Tìm tài liệu bằng `list_files("data/policies")` rồi `read_file` từng file.
  - Chọn chính sách theo **ngày mua**, dựa vào dòng phạm vi hiệu lực trong nội dung tài liệu, không dựa vào tên file.
  - Số ngày = ngày yêu cầu − ngày mua. Bằng đúng thời hạn vẫn đủ điều kiện.
  - Không dùng ngày hiện tại của máy.
- `references/answer-template.md`: câu trả lời gồm kết luận, chính sách áp dụng, số ngày đã qua, phí và đường dẫn tài liệu làm căn cứ.

Skill chỉ trỏ tới thư mục `data/policies/`. Skill **không** chứa tên file, nội dung chính sách (7 ngày, 14 ngày, 10%, 2026-10-01) hay đáp án. Test `test_refund_policy_skill_does_not_hardcode_policy_files_or_answers` kiểm tra điều này.

### Dữ liệu
`data/policies/policy-before-oct.md` và `policy-from-oct.md`, nội dung theo đề. Đặt trong `workspace/` và `fixtures/` của cả 2 bản sao.

## 2. Kiểm tra tool trực tiếp

Gọi `list_files.invoke(...)` trên workspace của `stage-01-files-block1`:

| Trường hợp | Gọi | Kết quả |
|---|---|---|
| Thư mục hợp lệ | `list_files("data/policies")` | `ok: true`, 2 mục `type: file`, sắp theo tên: `data/policies/policy-before-oct.md`, `data/policies/policy-from-oct.md` |
| Đường dẫn file | `list_files("data/policies/policy-from-oct.md")` | `ok: false`, `NOT_A_DIRECTORY`: "Đây là file, không phải thư mục…" |
| Không tồn tại | `list_files("data/khong-ton-tai")` | `ok: false`, `DIRECTORY_NOT_FOUND`, không trả danh sách rỗng |
| Vượt workspace | `list_files("../")` | `ok: false`, `PATH_OUTSIDE_WORKSPACE` |
| Vượt workspace (đường dẫn tuyệt đối) | `list_files("/etc")` | `ok: false`, `PATH_OUTSIDE_WORKSPACE` |

Test tự động (`uv run pytest`, không cần API key):
- `stage-01-files-block1`: **49 passed** (bản mẫu 34). Phần thêm mới gồm 15 test `list_files` trong `tests/test_files.py` và test luồng `list_files` → `read_file` với file đã đổi tên trong `tests/test_agent.py`.
- `stage-02-skills-block1`: **58 passed** (bản mẫu 41). Có thêm test catalog có `refund-policy`, test skill không ghi cố định tên file hay đáp án, và test luồng skill với tài liệu đã đổi tên (mock model).
- Trên Windows chưa bật Developer Mode, có 4 test tạo symlink bị lỗi `WinError 1314` ngay ở bước chuẩn bị dữ liệu: 45/49 và 54/58. Hai trong số đó là test gốc của lab. Lỗi xảy ra trước khi code của tool được kiểm tra. Trên Linux cả 4 test đều pass.

## 3. Kết quả từng trường hợp (chạy live)

**Tóm tắt kết quả chính thức** (model `qwen/qwen3.8-27b` qua Groq; system prompt và code ngoài phần tool đều là bản gốc):

| Trường hợp | Trace | Kết quả |
|---|---|---|
| Stage 00, câu A | `stage-00-chat/traces/20261007-173247_9bc03040_turn01_b60925ce.jsonl` | 0 tool. Agent nói không truy cập được tài liệu và yêu cầu người dùng dán chính sách |
| A | `stage-02-skills-block1/traces/20261007-180105_8b284404_turn01_075da076.jsonl` | ✅ Chính sách cũ, 8 ngày, không đủ điều kiện |
| B (sau đổi tên) | `stage-02-skills-block1/traces/20261007-180332_47daef9a_turn01_0bc327f3.jsonl` | ✅ Chính sách mới, 10 ngày, đủ điều kiện, không phí, căn cứ là file tên mới |
| Thiếu thông tin | `stage-02-skills-block1/traces/20261007-180549_70ca2cc6_turn01_e3fd7f8d.jsonl` | ✅ Hỏi trạng thái kích hoạt, chưa kết luận |

Về chọn model: Gemini 3.x không chạy được qua `ChatOpenAI`. Lỗi 400 *"Function call is missing a thought_signature"* xảy ra ở lượt gọi model thứ 2 sau tool call, vì LangChain không gửi lại chữ ký của Gemini. Vì vậy dùng Groq, một provider tương thích OpenAI, chỉ đổi `.env` và **không sửa code**.

> Điền sau khi chạy app với model thật. Mỗi trường hợp mở cuộc trò chuyện mới, không nhắc tên skill hay tên file.

### Stage 00: giới hạn của agent (bản mẫu `stage-00-chat`)
- Model: `qwen/qwen3.8-27b` (Groq, endpoint OpenAI-compatible).
- Câu hỏi: trường hợp A, không dán nội dung chính sách.
- Trace: `stage-00-chat/traces/20261007-173247_9bc03040_turn01_b60925ce.jsonl`
  - seq 1 `user_submitted`: `tools: []`, `skills: []`.
  - seq 2 `model_request` #1: snapshot có **0 tools**, 1 message.
  - seq 3 `model_response` #1: `tool_calls_requested: []`, 0,8 giây.
  - seq 4 `run_completed`: 652 ký tự.
- Ảnh: [`screenshots/stage00-case-A.png`](screenshots/stage00-case-A.png). Ảnh cho thấy trạng thái **Hoàn tất**, **Lần gọi model: 1**, **Tool calls trong lượt: 0**.

**Agent trả lời (nguyên văn):**

> Tôi không có quyền truy cập vào file, cơ sở dữ liệu, hay bất kỳ tool nào trong project này nên không thể kiểm tra:
> - Chính sách hoàn tiền cụ thể của sản phẩm/hướng dẫn bạn đang tham chiếu.
> - Trạng thái đơn hàng hay điều kiện hoàn áp dụng (ví dụ: thời hạn hoàn, điều kiện chưa kích hoạt, v.v.).
>
> Để trả lời chính xác, bạn cần cung cấp:
> 1. Nội dung chính sách hoàn tiền (copy từ file/tài liệu liên quan).
> 2. Hoặc mô tả các điều kiện hoàn áp dụng cho trường hợp này.
>
> Nếu bạn dán chính sách vào đây, tôi có thể phân tích và cho biết trường hợp của bạn (mua 28/09/2026, yêu cầu hoàn 06/10/2026, chưa kích hoạt) có đáp ứng điều kiện hoàn hay không.

**Nhận xét:**
- Agent **không đọc được tài liệu nào**: request gửi model có 0 tool, model không yêu cầu tool call nào. Kết quả của trace và ảnh khớp nhau.
- Agent không kết luận và không bịa thời hạn hay phí. Agent nói đúng giới hạn của mình và yêu cầu người dùng **tự dán nội dung chính sách vào chat**. Đề bài cấm đúng cách làm này: *"không dán nội dung chính sách vào chat"*.
- Kể cả khi người dùng dán chính sách vào, agent vẫn phụ thuộc vào việc người dùng chọn đúng phiên bản. Agent không tự biết workspace có **hai phiên bản** chính sách, mốc hiệu lực 2026-10-01 là gì, hay tên file nào.

**Thông tin và khả năng agent còn thiếu:**
1. **Tìm tài liệu:** không có tool liệt kê thư mục, nên không biết có những file chính sách nào hay tên là gì. Stage 01 bổ sung bằng `list_files`.
2. **Đọc tài liệu:** stage 00 không có `read_file`. Stage 01 có `read_file`.
3. **Nội dung chính sách:** phạm vi hiệu lực theo ngày mua, thời hạn 7 hoặc 14 ngày, phí 10% hoặc không phí, điều kiện kích hoạt. Phần này nằm trong `data/policies/`.
4. **Quy trình nghiệp vụ:** chọn phiên bản theo **ngày mua**, quy ước tính ngày (bằng đúng hạn vẫn đủ điều kiện), hỏi lại khi thiếu thông tin, trích nguồn. Stage 02 bổ sung bằng skill `refund-policy`.

### Kết quả chính thức (prompt gốc, model `qwen/qwen3.8-27b`)

#### Trường hợp A (mua 28/09/2026, hoàn 06/10/2026, chưa kích hoạt): ĐẠT ✅
- Kết quả cần đạt: chính sách cũ, 8 ngày, không đủ điều kiện.
- Trace: `stage-02-skills-block1/traces/20261007-180105_8b284404_turn01_075da076.jsonl`. Đây là cuộc trò chuyện mới (`8b284404`). System prompt dài 1917 ký tự, **đúng bản gốc**, không có dòng mô tả `list_files`.
- Ảnh: [`screenshots/official-case-A.png`](screenshots/official-case-A.png). Ảnh cho thấy *4 model call, 5 tool call*, trạng thái **Hoàn tất**.

| seq | Model call | Tool call | Kết quả |
|---|---|---|---|
| 3–5 | #1 | `read_file skills/refund-policy/SKILL.md` | Agent tự nạp skill theo description |
| 7–11 | #2 | `list_files data/policies` song song với `read_file …/answer-template.md` | 2 mục: `policy-before-oct.md`, `policy-from-oct.md` |
| 13–17 | #3 | `read_file data/policies/policy-before-oct.md`, `read_file data/policies/policy-from-oct.md` | Path lấy từ `list_files` |
| 19–20 | #4 (19,4 giây) | (không) | Trả lời, 520 ký tự |

**Câu trả lời (nguyên văn):**

> - Chính sách áp dụng: Chính sách hoàn tiền trước tháng 10, áp dụng cho ngày mua trước 2026-10-01
> - Ngày mua: 28/09/2026; ngày yêu cầu hoàn: 06/10/2026
> - Số ngày đã qua: 8 ngày; thời hạn theo chính sách: 7 ngày → quá hạn (8 > 7)
> - Trạng thái kích hoạt: Chưa kích hoạt → đạt điều kiện kích hoạt
> - Phí hoàn tiền: Không áp dụng
> - Căn cứ: `data/policies/policy-before-oct.md`
>
> **Kết luận: Không đủ điều kiện hoàn tiền**, vì ngày yêu cầu hoàn (06/10/2026) đã qua thời hạn 7 ngày kể từ ngày mua (28/09/2026), tổng cộng 8 ngày.

**Đối chiếu:**
- Chính sách cũ ✅
- 8 ngày ✅
- Không đủ điều kiện ✅
- Dẫn đúng tài liệu ✅

Bằng chứng theo đề (*"Tool tìm file, đọc chính sách cũ; câu trả lời dẫn đúng tài liệu"*): seq 8 và 11 là `list_files`, seq 14 và 17 là `read_file data/policies/policy-before-oct.md`.

#### Trường hợp B sau khi đổi tên file (mua 02/10/2026, hoàn 12/10/2026, chưa kích hoạt): ĐẠT ✅
- Đổi tên, giữ nguyên nội dung:
  - `policy-before-oct.md` → `cs-hoan-tien-cu.md`
  - `policy-from-oct.md` → `cs-hoan-tien-moi.md`
- Kết quả cần đạt: chính sách mới, 10 ngày, đủ điều kiện, không phí.
- Trace: `stage-02-skills-block1/traces/20261007-180332_47daef9a_turn01_0bc327f3.jsonl`. Đây là **cuộc trò chuyện mới** (`47daef9a`): request đầu chỉ có 1 message, không mang tài liệu nào từ lịch sử cũ. System prompt dài 1917 ký tự, đúng bản gốc.
- Ảnh: [`screenshots/official-case-B-renamed.png`](screenshots/official-case-B-renamed.png). Ảnh cho thấy *5 model call, 5 tool call*, trạng thái **Hoàn tất**.

| seq | Model call | Tool call | Kết quả |
|---|---|---|---|
| 3–5 | #1 | `read_file skills/refund-policy/SKILL.md` | Nạp skill |
| 7–9 | #2 | `list_files data/policies` | Trả về **tên mới**: `cs-hoan-tien-cu.md`, `cs-hoan-tien-moi.md` |
| 11–15 | #3 | `read_file data/policies/cs-hoan-tien-cu.md`, `read_file data/policies/cs-hoan-tien-moi.md` | Đọc file tên mới theo đúng path từ `list_files` |
| 17–19 | #4 | `read_file skills/refund-policy/references/answer-template.md` | Đọc reference |
| 21–22 | #5 (27,3 giây) | (không) | Trả lời, 571 ký tự |

**Câu trả lời (nguyên văn):**

> Đủ thông tin rồi ạ. Kết luận:
> - Chính sách áp dụng: Chính sách hoàn tiền từ tháng 10, áp dụng cho ngày mua từ 2026-10-01, bao gồm ngày này.
> - Ngày mua: 02/10/2026; ngày yêu cầu hoàn: 12/10/2026
> - Số ngày đã qua: 10 ngày; thời hạn theo chính sách: 14 ngày → trong hạn (10 ≤ 14)
> - Trạng thái kích hoạt: Chưa kích hoạt → đạt điều kiện kích hoạt
> - Phí hoàn tiền: Không thu phí
> - Căn cứ: `data/policies/cs-hoan-tien-moi.md`
>
> **Kết luận: Đủ điều kiện hoàn tiền**, vì số ngày đã qua (10 ngày) vẫn trong thời hạn 14 ngày và sản phẩm chưa được kích hoạt, không thu phí.

**Đối chiếu:**
- Chính sách mới ✅
- 10 ngày ✅
- Đủ điều kiện, không phí ✅
- Căn cứ trỏ đúng **file tên mới** ✅

Bằng chứng theo đề:
- *"Lịch sử có nội dung skill và reference"*: seq 5 có SKILL.md, seq 19 có answer-template.md.
- *"Cuộc trò chuyện mới tìm được file đã đổi tên"*: seq 9 `list_files` trả tên mới, seq 12–15 đọc file tên mới.

Agent biết tên mới **chỉ** nhờ kết quả `list_files`. Không có tên file nào trong prompt hay code.

(Câu mở đầu "Đủ thông tin rồi ạ. Kết luận:" hơi lệch so với template, nhưng câu trả lời chỉ có **một** kết luận và kết luận này nằm sau các phép so sánh.)

#### Thiếu thông tin ("Tôi mua ngày 02/10/2026, muốn hoàn ngày 12/10/2026."): ĐẠT ✅
- Kết quả cần đạt: agent hỏi trạng thái kích hoạt, chưa kết luận, không tự giả định "chưa kích hoạt".
- Trace: `stage-02-skills-block1/traces/20261007-180549_70ca2cc6_turn01_e3fd7f8d.jsonl` (cuộc trò chuyện mới `70ca2cc6`).
- Ảnh: [`screenshots/official-missing-info.png`](screenshots/official-missing-info.png). Ảnh cho thấy *4 model call, 5 tool call*, trạng thái **Hoàn tất**.

| seq | Model call | Tool call |
|---|---|---|
| 3–5 | #1 | `read_file skills/refund-policy/SKILL.md` |
| 7–11 | #2 | `read_file …/answer-template.md` song song với `list_files data/policies` (tên mới) |
| 13–17 | #3 | `read_file` 2 tài liệu chính sách |
| 19–20 | #4 | (không). Trả lời, 101 ký tự |

**Câu trả lời (nguyên văn):**

> Để kết luận, tôi cần thêm: sản phẩm của bạn đã được kích hoạt chưa (đã kích hoạt hay chưa kích hoạt)?

**Đối chiếu:**
- Agent hỏi đúng thông tin còn thiếu ✅
- Không đưa ra kết luận ✅
- Không tự giả định "chưa kích hoạt" ✅
- Câu hỏi dùng đúng mẫu *"Khi thiếu thông tin"* trong `answer-template.md`.

Ghi chú: agent đọc tài liệu trước rồi mới hỏi lại. Skill (bước 1) hướng dẫn hỏi và dừng ngay khi thiếu thông tin. Cách làm của agent không vi phạm yêu cầu của đề, vì agent vẫn chưa kết luận, nhưng tốn thêm 3 tool call không cần thiết.

### Ghi chú quá trình (trước khi hoàn tác `prompts.py`)

> **Ghi chú:** các lần chạy dưới đây được thực hiện khi bản sao còn một dòng mô tả `list_files` trong `CAPABILITY_PROMPT`. Dòng này sau đó đã được **hoàn tác** để giữ đúng giới hạn của đề. Trường hợp A, B (sau đổi tên) và thiếu thông tin được **chạy lại** với prompt gốc; kết quả chính thức nằm ở mục *Kết quả chính thức* bên dưới. Các lần chạy cũ giữ lại làm ghi chú quá trình, vì chúng chứa phát hiện về thứ tự template.

#### (Quá trình) Trường hợp A
- Kết quả cần đạt: chính sách cũ, 8 ngày, không đủ điều kiện.

#### Lần chạy 1: luồng tool đúng, câu trả lời có hai kết luận mâu thuẫn
- Model `qwen/qwen3.8-27b`. Trace: `stage-02-skills-block1/traces/20261007-173923_077c2ba6_turn01_b2ac862d.jsonl`
- Luồng tool (20 event, 4 model call, 5 tool call):

| seq | Model call | Tool call | Kết quả |
|---|---|---|---|
| 3–5 | #1 | `read_file skills/refund-policy/SKILL.md` | Agent tự nạp skill dựa vào description, câu hỏi không nhắc tên skill |
| 7–11 | #2 | `list_files data/policies` song song với `read_file …/answer-template.md` | `list_files` trả 2 mục `policy-before-oct.md`, `policy-from-oct.md` |
| 13–17 | #3 | `read_file data/policies/policy-before-oct.md`, `read_file data/policies/policy-from-oct.md` | Path lấy từ kết quả `list_files`, không đoán tên |
| 19–20 | #4 | (không) | Trả lời, 1073 ký tự, 19,5 giây |

- Ảnh: [`stage02-case-A-run1-answer.png`](screenshots/stage02-case-A-run1-answer.png), [`…-skill-loaded.png`](screenshots/stage02-case-A-run1-skill-loaded.png) (*Skill content đã vào history (1)*: refund-policy, message #2), [`…-resources.png`](screenshots/stage02-case-A-run1-resources.png) (*Tài nguyên đã đọc (3)*), [`…-eventlog.png`](screenshots/stage02-case-A-run1-eventlog.png). Catalog và tools: [`stage02-catalog.png`](screenshots/stage02-catalog.png), [`stage02-tools.png`](screenshots/stage02-tools.png).
- Câu trả lời mở đầu bằng **"Kết luận: Đủ điều kiện hoàn tiền."**, sau đó liệt kê *"8 ngày (thời hạn 7 ngày)… Vượt thời hạn (8 > 7)"*, rồi tự viết lại **"Sửa lại kết luận… Không đủ điều kiện hoàn tiền."** Chính sách, số ngày và căn cứ đều đúng, kết luận cuối cùng cũng đúng, nhưng câu trả lời chứa hai kết luận mâu thuẫn nhau.
- **Nguyên nhân:** `answer-template.md` bản đầu đặt dòng *Kết luận* **lên đầu**. Model sinh chữ tuần tự, nên phải viết kết luận trước khi viết ra phép so sánh 8 ngày với 7 ngày.
- **Sửa (chỉ sửa skill, không sửa code hay prompt hệ thống):**
  - `answer-template.md` đổi thứ tự thành: dữ kiện, rồi phép so sánh (`N ≤ X` trong hạn hoặc `N > X` quá hạn), rồi **kết luận ở cuối**. Template nói rõ chỉ có **một** kết luận.
  - `SKILL.md` bước 5 thêm quy tắc: chỉ viết kết luận sau khi đã so sánh xong, và không tự sửa giữa chừng.
  - Đã đồng bộ sang `fixtures/`. `uv run pytest`: 58 passed.

#### Lần chạy 2 (sau khi sửa template): ĐẠT ✅
- Model `qwen/qwen3.8-27b`. Trace: `stage-02-skills-block1/traces/20261007-174809_bef2a8ef_turn01_5d8a411d.jsonl`
- Ảnh: [`screenshots/stage02-case-A.png`](screenshots/stage02-case-A.png). Ảnh cho thấy *Các bước thực hiện (4 model call, 5 tool call)*, *Skill content đã vào history (1)*, *Tài nguyên đã đọc (3)*.

| seq | Model call | Tool call | Kết quả |
|---|---|---|---|
| 3–5 | #1 (0,6 giây) | `read_file skills/refund-policy/SKILL.md` | Nạp skill |
| 7–11 | #2 (0,7 giây) | `list_files data/policies` song song với `read_file …/answer-template.md` | 2 mục: `policy-before-oct.md`, `policy-from-oct.md`. Template là bản mới, kết luận ở cuối |
| 13–17 | #3 (1,0 giây) | `read_file data/policies/policy-before-oct.md`, `read_file data/policies/policy-from-oct.md` | Đọc cả 2 tài liệu, path lấy từ `list_files` |
| 19–20 | #4 (21,2 giây) | (không) | Trả lời, 504 ký tự |

**Câu trả lời (nguyên văn):**

> - Chính sách áp dụng: Chính sách hoàn tiền trước tháng 10, áp dụng cho ngày mua trước 2026-10-01
> - Ngày mua: 28/09/2026; ngày yêu cầu hoàn: 06/10/2026
> - Số ngày đã qua: 8 ngày; thời hạn theo chính sách: 7 ngày → quá hạn
> - Trạng thái kích hoạt: Chưa kích hoạt → đạt điều kiện kích hoạt
> - Phí hoàn tiền: Không áp dụng
> - Căn cứ: `data/policies/policy-before-oct.md`
>
> **Kết luận: Không đủ điều kiện hoàn tiền**, vì yêu cầu sau 8 ngày, vượt quá thời hạn 7 ngày theo chính sách áp dụng cho ngày mua 28/09/2026.

**Đối chiếu với kết quả cần đạt:**
- Chọn chính sách cũ: đúng ✅
- 8 ngày: đúng ✅
- Không đủ điều kiện: đúng ✅, chỉ còn **một** kết luận
- Căn cứ dẫn đúng tài liệu: đúng ✅
- Bằng chứng theo đề (*"Tool tìm file, đọc chính sách cũ; câu trả lời dẫn đúng tài liệu"*): seq 8/10 `list_files`, seq 14/16 `read_file data/policies/policy-before-oct.md`.

#### (Quá trình) Trường hợp B sau khi đổi tên file (mua 02/10/2026, hoàn 12/10/2026, chưa kích hoạt): ĐẠT ✅
- Đổi tên, giữ nguyên nội dung:
  - `policy-before-oct.md` → `cs-hoan-tien-cu.md`
  - `policy-from-oct.md` → `cs-hoan-tien-moi.md`
- Kết quả cần đạt: chính sách mới, 10 ngày, đủ điều kiện, không phí.
- Model `qwen/qwen3.8-27b`. Trace: `stage-02-skills-block1/traces/20261007-175112_edf29211_turn01_4757fc26.jsonl`. Đây là **cuộc trò chuyện mới**: conversation `edf29211`, `chat_turn` 1, request đầu chỉ có 1 message, nên không có tài liệu nào lấy từ lịch sử cũ.
- Ảnh: [`screenshots/stage02-case-B-renamed.png`](screenshots/stage02-case-B-renamed.png). Ảnh cho thấy *5 model call, 5 tool call*, trạng thái **Hoàn tất**.

| seq | Model call | Tool call | Kết quả |
|---|---|---|---|
| 3–5 | #1 (0,6 giây) | `read_file skills/refund-policy/SKILL.md` | Nạp skill |
| 7–9 | #2 (0,5 giây) | `list_files data/policies` | Trả về **tên mới**: `cs-hoan-tien-cu.md`, `cs-hoan-tien-moi.md` |
| 11–15 | #3 (0,6 giây) | `read_file data/policies/cs-hoan-tien-cu.md`, `read_file data/policies/cs-hoan-tien-moi.md` | Đọc file tên mới theo đúng path từ `list_files` |
| 17–19 | #4 (17,0 giây) | `read_file skills/refund-policy/references/answer-template.md` | Đọc reference |
| 21–22 | #5 (26,6 giây) | (không) | Trả lời, 484 ký tự |

**Câu trả lời (nguyên văn):**

> - Chính sách áp dụng: Chính sách hoàn tiền từ tháng 10, áp dụng cho ngày mua từ 2026-10-01, bao gồm ngày này
> - Ngày mua: 02/10/2026; ngày yêu cầu hoàn: 12/10/2026
> - Số ngày đã qua: 10 ngày; thời hạn theo chính sách: 14 ngày → trong hạn
> - Trạng thái kích hoạt: Chưa kích hoạt → đạt điều kiện kích hoạt
> - Phí hoàn tiền: Không thu phí
> - Căn cứ: `data/policies/cs-hoan-tien-moi.md`
>
> **Kết luận: Đủ điều kiện hoàn tiền**, vì 10 ngày đã qua còn trong hạn 14 ngày và sản phẩm chưa kích hoạt.

**Đối chiếu với kết quả cần đạt:**
- Chính sách mới: đúng ✅
- 10 ngày: đúng ✅
- Đủ điều kiện, không phí: đúng ✅
- Căn cứ trỏ đúng **file tên mới**: đúng ✅
- Bằng chứng theo đề:
  - *"Lịch sử có nội dung skill và reference"*: seq 5 có SKILL.md, seq 19 có answer-template.md.
  - *"Cuộc trò chuyện mới tìm được file đã đổi tên"*: seq 9 `list_files` trả tên mới, seq 12–15 đọc file tên mới.
- Không có tên file nào được ghi cố định trong prompt hay code: agent biết tên mới **chỉ** nhờ kết quả `list_files`.

## 4. Câu hỏi cuối bài

**Vì sao cần tool để tìm file và skill để hướng dẫn chọn chính sách?**

- **Tool giải quyết chuyện "biết có những file nào".** Trước khi có `list_files`, agent chỉ đọc được file khi đã biết chính xác đường dẫn. Thứ nó biết chỉ đến từ prompt hoặc từ người dùng. `list_files` cho agent tự quan sát trạng thái thật của workspace tại thời điểm hỏi. Vì vậy khi file bị đổi tên, thêm hay bớt, agent vẫn tìm đúng mà không cần ai sửa code hay prompt. Phạm vi truy cập vẫn được kiểm soát: chỉ trong workspace, chỉ liệt kê trực tiếp, lỗi có cấu trúc.
- **Skill giải quyết chuyện "làm việc này thế nào cho đúng".** Đây là quy trình nghiệp vụ:
  - Hỏi lại khi thiếu thông tin.
  - Chọn phiên bản theo **ngày mua**, không theo ngày yêu cầu hay ngày hiện tại.
  - Đọc ranh giới "trước" và "từ … bao gồm".
  - Quy ước tính ngày, và bằng đúng thời hạn vẫn đủ điều kiện.
  - Trả lời theo mẫu có trích nguồn.

  Nếu không có skill, model dễ chọn theo tên file, tự giả định "chưa kích hoạt" hoặc dùng kiến thức chung. Skill chỉ nằm trong catalog ở dạng metadata và chỉ được nạp khi câu hỏi khớp, nên không làm phình system prompt của các task khác.
- Hai phần này tách biệt nhau: tool là **khả năng** (generic, dùng cho mọi task), còn skill là **kiến thức quy trình** (riêng cho task hoàn tiền). Tài liệu chính sách là **dữ liệu**, có thể thay đổi độc lập với cả hai.

**Nếu chưa có tool tìm file, sửa prompt có giải quyết được yêu cầu đổi tên file không?**

Không. Sửa prompt chỉ có 2 cách, và cả hai đều không đáp ứng yêu cầu:
1. **Ghi tên file vào prompt.** Đề cấm việc này. Hơn nữa đây là cố định một trạng thái cũ: đổi tên file là prompt sai ngay, agent gọi `read_file` sẽ nhận `FILE_NOT_FOUND`, và mỗi lần đổi tên phải sửa prompt rồi khởi động lại. Kết quả là con người vẫn phải làm thay việc "tìm file".
2. **Dặn model "hãy tìm file".** Model không có cách nào thực hiện, vì `read_file` không liệt kê được thư mục. Model chỉ còn đoán tên file. Đoán sai thì lỗi, còn tệ hơn là bịa nội dung chính sách từ kiến thức sẵn có.

Prompt chỉ thay đổi được **thông tin model đang có**, không tạo ra **khả năng mới** để quan sát môi trường. Yêu cầu "vẫn đúng khi tên file thay đổi" cần agent đọc được trạng thái hiện tại của thư mục. Việc đó chỉ một tool như `list_files` làm được.
