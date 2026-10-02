# TradingAgents — bàn giao 2026-09-27, tiếp nối 2026-10-02

## Cập nhật đang triển khai · 2026-10-01

**Bilingual supervised gate 2026-10-02:** source
`97b110d02596e8d57be6b0dd0b21f581c1e1b83b` chạy native graph đủ 14 stage qua
spawn ở English, Vietnamese và English + Vietnamese bằng fixture model. Giữ
canonical và horizon 3–6; presentation EN/VI trả về cha đúng nội dung. Fixture
tự thêm 25% bị từ chối sau một repair, không có decision payload hợp lệ và có
`report_translation_unavailable`. Full Python **1.640 + 88 subtests PASS**,
20 skips, 108,29 s; Ruff/diff/templates PASS. Chỉ test/docs, không đổi runtime,
prompt, provider hay frontend; không dùng quota AI. Đây không phải live MT/
financial acceptance. Tiếp theo ưu tiên fingerprinted graph recovery; các lỗi
live và NQ=F BLOCKED vẫn giữ nguyên, không tự chạy paid replay.

**Native/crash acceptance 2026-10-02:** source
`c4414a67a1c2d3b28169a0b201211457d635f626`. Native LangGraph thật qua spawn với
model giả lập chạy đủ 14 stage đúng thứ tự, giữ structured gate/600s SDK timeout/
retry 1 và không chạm CLI tool/memory/checkpoint/writes. Tiếng Anh-only: không
coi là bilingual/live finance proof. Process cha bị kill trong fixture: guard
dừng process con, không còn executing orphan trên macOS; zombie terminal không
được mô tả là process đã reaped. Full Python **1.637 + 88 subtests PASS**, 20 skips,
107,29 s; Ruff/diff/templates PASS. Không thay runtime production hay frontend,
không gọi vendor/model thật. Còn mở: bilingual supervised path, OS khác,
fingerprinted resume và live financial/translation acceptance. Xem receipt mới.

**Bridge concurrency follow-up:** runtime source hiện tại
`e1af4c35957918ae72debef3417ef24d2a1a767f` khóa cặp send/ack để callback threads
không xen frame hay lấy nhầm reply. Regression Python 1.634 + 88 subtests PASS,
20 skips, 109,11 s; một test concurrency bổ sung riêng PASS (thêm sau collection,
không gọi tổng thành một full run 1.635). Ruff/diff PASS; không đổi frontend.
Các gate native supervised graph/crash/resume/live của checkpoint dưới vẫn mở.

**Checkpoint process supervision 2026-10-02:** source
`be2149864ec0ffb91b7f8c3d79d88bd06087992c`. Default worker snapshot jobs chạy
graph trong process spawn, cha giữ observer/DB/lease/publication. Deadline,
cancellation và lease failure dừng/join process con, gồm SDK bị block, slow-read
hay retry/backoff; pipe reader riêng không chặn luồng kiểm tra allowance.
Usage/reader text được chuyển qua bridge, không gửi raw messages/reasoning;
nháp vẫn unvalidated, failure không tạo decision hay blind paid replay.
Full Python **1.634 + 88 subtests PASS**, 20 skips, 114,07 s; Ruff PASS; Web 137,
type/lint/build PASS. SDK tests dùng localhost/synthetic key, không vendor thật.
CLI/legacy live-tool và explicit injected engines giữ contract cũ. API chỉ công
bố default worker mode, không xác nhận worker đang chạy đã được nâng cấp.
Receipt 2026-10-02 ghi scope: native full graph qua spawn, crash/orphan và các OS
khác chưa nghiệm thu; graph resume/live quality còn mở. Chưa restart worker hay
chạy thêm AI trả phí. Tiếp theo nghiệm thu các gate này trước paid live mới.

**Checkpoint budget accounting 2026-10-02:** source
`fc6a8812cc4cde979c8aa72432b98966abf2ae50` reserve model starts atomically,
thêm remaining allowance dùng cùng monotonic clock và cancellation precedence.
Usage phân biệt logical LangChain calls với số request SDK không quan sát được
(`provider_request_attempts=null`); giữ usage trả muộn, không cho bắt đầu call mới.
Full Python **1.623 + 88 subtests PASS**, 20 skips, 46,66 s; Ruff PASS; Web 137,
type/lint/build PASS. Chưa hard-interrupt request, chưa resume hay paid live mới.
Tiếp theo phải supervise blocking request gồm retries/backoff/slow reads,
không dùng thread timeout rồi để request chạy ngầm, không cắt graph.

**Checkpoint UI allowance 2026-10-02:** source
`a2a0b6f6db38bc08102af853da889f874515a2a6` thêm chọn 30/60 phút trước consent,
đổi lựa chọn phải xác nhận lại và dùng request identity mới. Processing hiển thị
allowance đã lưu, không gán mặc định cho lịch sử thiếu trường. Web **137 tests**,
typecheck/lint/build PASS; built-app synthetic 1280×900/390×900 PASS, mỗi viewport
một POST giả lập, không gọi worker/provider, không lỗi console/page hay overflow.
Đây không phải hard deadline, cost cap hay graph resume; chưa paid live mới.
Skill React giữ state trong form và không thêm fetch/provider từ component.
Receipt 2026-10-02 ghi exact source và scope; goal/PR vẫn mở.

**Checkpoint allowance mới 2026-10-02:** source
`648fa183ee90eed1e353b3e06cbcc2c249aebb82` đã bind allowance rõ ràng cho API
snapshot run → manifest/config hash/job → worker observer. Mặc định 1800s/128
calls giữ nguyên; omission legacy không đổi hash/payload cũ. Full Python
**1.619 + 88 subtests PASS**, 20 skips, 59,09 s; Web 134, type/lint/build PASS.
Mode vẫn `cooperative_boundaries`, không phải ngắt cứng request. UI lựa chọn,
deadline transport và graph resume chưa có; chưa chạy paid BTC/AAPL mới.

**Checkpoint replay fencing trước, 2026-10-02:** runtime source
`93e797576b9179e088f6ff809761bddd34cc3df6` ghi dấu mốc trước engine và chặn
replay toàn-run sau lỗi execution/lease không rõ chi phí. Giữ retry hoàn tất
report/decision đã commit mà không gọi model; nếu outputs không còn đọc được,
không quay lại engine. Full Python **1.608 + 88 subtests PASS**, 20 skips,
50,14 s; Ruff/diff/templates PASS. Không tăng allowance hay đổi SDK retry/timeout.
Graph checkpoint resume vẫn chưa có; không lấy bản sửa này làm live acceptance.
Receipt 2026-10-02 ghi cả regression FAIL tại checkpoint trước và bản sửa.

Tiếp nối **2026-10-02**, source `1a01f21455fa351017319ad6283bb8307defe0ee`:
web đã tách bản nháp khỏi báo cáo hoàn chỉnh, chỉ tải khi mở đọc, cảnh báo
chưa kiểm chứng/không thể phê duyệt; đổi EN/VI không dịch nội dung gốc hay gọi AI.
134 Web tests, typecheck/lint/build PASS; built-browser synthetic 1280×900 và
390×900 PASS, zero console/page error/overflow/mutation, một note GET. Xem
[receipt 2026-10-02](docs/platform/research-acceptance-20261002.md). Đây không
phải live model/financial acceptance. Allowance/timeout và graph resume vẫn dở;
goal/PR vẫn mở, không tự chạy paid retry.

**Checkpoint retention trước:** code `ecbb7d3f25ac0d64defdc9231afabe8dea59edb0` lưu bản nháp
nghiên cứu bất biến sau khi từng vai trò trả kết quả, chỉ giữ reader text đã
allowlist và ràng buộc owner/run/source/config. Cancellation và lease chặn worker
cũ xuất thêm nội dung. Bản nháp luôn unvalidated, không đủ điều kiện phê duyệt;
không phải checkpoint để resume graph. Full Python **1.600 + 88 subtests PASS**
(20 skips), Ruff PASS; Web 122 tests, lint/typecheck/build PASS. Chưa live-test
code mới ở checkpoint đó; UI đọc bản nháp đã có tại 1a01f21 nhưng graph resume
vẫn chưa hoàn thành. Các sửa
SEC/translation tại `af5349d` vẫn được giữ.

Lượt BTC market+news tại `f73d1a9` **FAIL**: 37m38s / 539.339 token / 13 calls,
`RESEARCH_BUDGET_EXHAUSTED`, attempt 1/1, không xuất report/decision. Đã xong
chín stage trước Portfolio Manager; chưa chạy Financial validation/Report
presentation. Trần 30 phút hiện là kiểm tra giữa các bước, không ngắt request
model đang chạy. Không dùng sự kiện tiến trình để coi nội dung đã nghiệm thu.

Tiếp theo ưu tiên R08: allowance hiện rõ, tương thích request timeout và graph
recovery có fingerprint đầy đủ,
giữ source/config/model/prompt/owner/lease và toàn bộ vai trò. Không tự tăng trần
hay replay paid BTC; cần chủ repo duyệt lượt mới
sau khi sửa flow. AAPL full graph chưa chạy ở candidate mới; SEC source đã PASS.
NQ=F giữ BLOCKED theo quyết định chủ repo, không thêm provider. Xem phần cuối
receipt 2026-10-01 để có exact SHA và trạng thái. Goal và Draft PR #7 vẫn mở.

### Nhật ký các checkpoint trước

Goal R01–R14 vẫn **chưa hoàn thành**; Draft PR #7 chưa được merge. Nhánh
`fix/TA-R01-research-quality` nay có bước news hiện tại ngoài price: thu Yahoo
trong subprocess 45 giây, lưu snapshot bất biến và owner-scoped, xác minh
publication/retrieval/cutoff/hash/identity, endpoint `prepare-news` có auth/CSRF,
UI Anh–Việt cho phép chọn news tùy chọn trước consent AI. Feed bảy ngày là
`recent_feed_not_exhaustive`, không phải lịch sử đầy đủ hay nguồn social/
fundamentals/macro. Synthetic QA chặn mọi vendor/model.

PASS local tại worktree trước commit: Ruff toàn repo; Python **1.495 tests +
88 subtests**, 20 skips; Web **117 tests/21 files**, lint/typecheck/build; UI
synthetic desktop 1280px và mobile 390px có thao tác news lỗi, không gọi AI,
không tràn ngang, không pageerror. Direct Yahoo AAPL news smoke trả
`OK`, 100 bài trong khoảng 2,68 giây; chứng minh đúng **một lượt đọc nguồn**
trên máy này, không chứng minh toàn bộ flow live. Xem receipt mới nhất
[2026-10-01](docs/platform/research-acceptance-20261001.md) sau khi commit.

Còn mở: acquisition và hợp đồng evidence cho fundamentals/social/macro theo
asset, semantic finance và chất lượng dịch đã FAIL live, UI research/review
chưa nghiệm thu vận hành, live full-graph BTC/AAPL/NQ chưa chạy trên candidate
mới. NQ cần chọn rõ reference `NQ=F` hay `^NDX` trước khi coi là acceptance.
Không lấy kết quả local/synthetic/news smoke để nâng thành release approval.

Tiếp nối: chủ repo đã chọn `NQ=F` reference-only. Không thay bằng `^NDX` hay
QQQ. Yahoo continuous không có metadata active/next contract và rollover mà
pipeline futures yêu cầu, nên live NQ vẫn BLOCKED đến khi có nguồn hợp lệ.
Commit `cd033dd` thêm cảnh báo song ngữ bắt buộc cho news feed không đầy đủ;
1.496 Python tests + 88 subtests PASS, 20 skips. Chưa chạy thêm AI; xem
receipt 2026-10-01 để phân biệt gate đã/chưa nghiệm thu.

Tiếp nối tại `f69e329`: chủ repo đã duyệt dùng SEC EDGAR hiện có riêng cho
AAPL web, không đổi CLI default. Có collector filed-date-aware, snapshot bất
biến, endpoint/UI tùy chọn, fact-ID cho kiểm chứng số và bố cục báo cáo song
ngữ dễ đọc hơn. Local PASS 1.505 Python tests + 88 subtests (20 skips), 121
Web tests, build/lint/typecheck; browser synthetic desktop/mobile PASS cho SEC
unavailable, chưa phải live SEC. `SEC_EDGAR_USER_AGENT` chưa có trong worktree
ở lúc kiểm tra; không dùng contact mẫu. Social/macro vẫn chưa acquisition;
semantic finance/translation và live BTC/AAPL chưa được nghiệm thu. NQ=F chủ
repo chọn giữ BLOCKED, chưa thêm provider; không thay bằng ^NDX/QQQ.

Tiếp nối tại `2547669`: đã sửa layout để báo cáo hiện trước sau khi hoàn tất,
tiến trình được giữ trong mục mở rộng; active/error vẫn hiển thị trực tiếp.
Fixture song ngữ đi qua compiler/validation/worker/API thật với đầu ra synthetic
được ghi nhãn rõ. Browser desktop 1280×900/mobile 390×844 PASS các tab và chuyển
EN/VI, giữ nguyên số, không tạo run mới khi đọc, không tràn ngang/pageerror;
trang quyết định liên kết giữ phê duyệt disabled khi không có portfolio/risk.
Full Python 1.506 + 88 subtests PASS (20 skips), Web 122 tests PASS,
typecheck/lint/build PASS. Đây là UI/integration proof, không phải live model
hay translation acceptance. Kiểm tra tiếp đã tìm thấy contact SEC hợp lệ trong
`.env` ignored ở checkout gốc: AAPL API live SEC PASS 1.159 facts, zero invalid,
latest filing 2026-07-31. BTC API giá/news PASS và bind hai snapshot; chưa phải
full graph. Worktree chưa tự nạp root env, nên QA phải nạp rõ file gốc và assert
MiniMax-M3; initial QA default-OpenAI run đã cancel trước model call. Các gate
live finance/translation vẫn mở.

Yêu cầu mới nhất của chủ repo: lưu toàn bộ code, phần dở và ngữ cảnh lên GitHub
để có thể tiếp tục từ máy khác hoặc Claude. Đây là checkpoint công việc, chưa
nghiệm thu sản phẩm và chưa merge PR.

## Checkout đúng nhánh

```sh
git clone --branch fix/TA-R01-research-quality https://github.com/phankietit/TradingAgents.git
cd TradingAgents
git status --short
git rev-parse HEAD
```

- Nhánh tiếp tục: `fix/TA-R01-research-quality`.
- Draft PR: https://github.com/phankietit/TradingAgents/pull/7 (base `main`).
- `origin/main` được kiểm tra tại `7dfec4d20709a702b130f3ba5813f097a930ffe6`.
- Baseline trước checkpoint: `0696141fddb8b5b7bde7cbde21aa408015716e58`.
- Candidate đã full-test gần nhất: `97b110d02596e8d57be6b0dd0b21f581c1e1b83b`.
  Runtime production của supervisor giữ nguyên từ `e1af4c3`; candidate này bổ
  sung test và cập nhật chỉ dẫn, không phải một lượt phân tích live mới.
- PR #7 đã chứa code prerequisite của PR #5 (bilingual) và #6 (data flow).
  Không cherry-pick lại hoặc merge các PR này chỉ để phục hồi checkpoint.
- Nhánh `chore/governance-bootstrap` lưu nguyên bộ governance từ checkout gốc.
  Nhánh sản phẩm này cũng chứa các rules cần để tiếp tục độc lập.
- Nhánh `fix/TA-M4-model-env` lưu commit riêng `d5eecfe`; đây là nhánh lưu trữ,
  không phải bước bắt buộc để khởi động. Đối chiếu diff trước khi tích hợp vì
  nhánh sản phẩm đã có xử lý model env.
- Các milestone cũ: `feature/TA-018-observability-baseline` và
  `feature/TA-027-data-health-engine` đã ở origin; cả hai worktree local sạch.

Đọc tiếp: [AGENTS](AGENTS.md), [routing](docs/ops/agent-map.md),
[backlog R01–R14](docs/platform/research-remediation.md),
[bằng chứng mới nhất](docs/platform/research-acceptance-20261002.md).
Receipt milestone cũ chỉ chứng minh SHA ghi trong receipt, không chứng minh HEAD.

## Mục tiêu và yêu cầu đã chốt

Nền tảng hỗ trợ quyết định đầu tư cá nhân, giao diện web Anh–Việt hiện đại,
phong cách tài chính sạch, dễ đọc cho người không chuyên kỹ thuật. Nhóm tài sản:
US large caps, ETF/chỉ số tham khảo, BTC/ETH. NQ/ES chỉ tham khảo, không thực thi
futures. Không broker, không thay risk limits hay provider, không sửa lịch sử.
LLM viết nghiên cứu; tính toán danh mục/policy phải xác định và có human approval.

Giữ toàn bộ LangGraph: analyst theo phạm vi nguồn, Bull/Bear, Research Manager,
Trader, Aggressive/Conservative/Neutral, Portfolio Manager, Financial validation,
Report presentation. Không bỏ vai trò hay lấy dữ liệu hiện tại bù lịch sử để
ép kết quả đạt. MiniMax hiện dùng cho cả model nhanh/chậm. Thiết kế bằng code,
không ImageGen. Test local/manual; GitHub CI đã được disable trong checkpoint.

## Đang có và đang dở

- Python/CLI + FastAPI, durable worker, immutable artifact store, auth owner,
  React/Vite UI, progress/retry/cancel/usage, tách research/portfolio approval.
- Snapshot giá có session/cutoff và full-history indicator/return xác định;
  analyst truy vấn snapshot đã khóa. Dữ liệu thiếu không được biến thành trung tính.
- Strict MiniMax JSON parser, một lần format repair, kiểm tra số liệu/provenance,
  percentage statements EN/VI xác định, dịch theo block với protected quantities.
- UI đã có browser synthetic desktop/mobile receipts; các lỗi browser tool ở
  checkpoint cũ không còn là mô tả trạng thái mới nhất. Chất lượng tài chính và
  vận hành live vẫn chưa được nghiệm thu; không lấy screenshot làm finance proof.
- `tradingagents/dataflows/platform_news.py` đã commit/test: collector Yahoo news
  có publication/retrieval time, nhận diện asset và trạng thái lỗi/phạm vi nguồn.
- Tại checkpoint 2026-09-27, `NewsSnapshotService` mới là WIP chưa test hoặc
  nối API/UI. Bản tiếp nối 2026-10-01 đã xử lý phần này; xem cập nhật trên.
- Web `prepare-data` vẫn chỉ persist giá; `prepare-news` là bước riêng. Có
  reader social/fundamentals không đồng nghĩa có ingestion. R04 chưa hoàn tất.

## Kết quả kiểm chứng và lỗi phải xử lý

Full regression ở `50dd0df`: **1.482 tests + 88 subtests PASS**, 20 skip, 39.94s;
Ruff PASS. 20 skip gồm 18 PostgreSQL, optional Bedrock và live DeepSeek. Không
chuyển kết quả này sang file WIP hoặc HEAD mới một cách mặc định.

Live BTC ở `5bbbdee` chạy đủ 11 stage, 14 model calls, **480.325 token**.
Automatic validation không báo lỗi và tạo Hold research, nhưng **manual FAIL**:
nhận định xác suất mean reversion/tax-driven exits chưa có bằng chứng tương ứng;
dịch “preserve optionality” thành “duy trì quyền chọn” sai nghĩa. Đây là snapshot
market-only, không phải full-source/fresh-data/queue/browser acceptance.

Live AAPL full-graph ở `f70907f`: 15 calls, **430.934 token**, manual FAIL do diễn
giải phần trăm và tiếng Việt. Sau đó có sửa công thức và kiểm tra thành phần.
Translation replay ở `2cd2609`: 1 call, **21.417 token**, số liệu giữ nguyên,
nhưng manual FAIL vì mất qualifier “aggressive” và văn phong lặp. Prompt đã sửa
ở `5bbbdee`; sửa prompt không chứng minh khả năng dịch đúng một cách tổng quát.

Không có USD cost chính xác từ provider. Token usage không phải hóa đơn.
NQ chưa live-test: chủ repo đã chọn `NQ=F`, giữ BLOCKED do thiếu contract/roll
metadata. Không thay bằng `^NDX` hoặc ETF; đây không phải acceptance đã đạt.

## Công việc tiếp theo có thứ tự

1. R08 đã lưu reader text riêng tư bằng publication fence; chưa phải resume.
   UI đọc bản nháp/chọn allowance đã có synthetic proof, allowance bind API và
   default worker process supervision đã triển khai; supervised bilingual path
   đã có fixture proof. Hoàn thiện durable graph recovery trước
   paid acceptance mới; giữ tất cả analyst/debate/risk/validation/presentation,
   không tự nâng budget hoặc biến partial report thành decision. Kiểm tra bằng
   local fixtures trước. BTC mới cần duyệt; AAPL đã được duyệt nhưng chưa chạy.
2. News service và prepare-news đã có local test, browser synthetic, một lượt
   Yahoo AAPL trực tiếp; còn cần live API/snapshot/run acceptance và kiểm soát
   coverage theo từng nguồn. Không coi một feed gần đây là lịch sử tin tức.
3. Hoàn thiện nguồn fundamentals, social, macro phù hợp từng asset và hợp đồng
   evidence/number tương ứng; giữ nguyên provider hiện có.
4. Xử lý semantic evidence và tiếng Việt từ các lỗi live đã lưu. Tránh tiếp tục
   chỉ thêm blacklist từng câu hoặc dùng numeric parity để chứng nhận ý nghĩa.
5. Hoàn thiện flow chuẩn bị → nghiên cứu → kiểm tra → đọc quyết định; tổng kết,
   luận điểm đối lập, rủi ro, invalidation và coverage cần dễ đọc trên desktop/mobile.
6. Chạy scope-appropriate local gates; sau khi có sửa đáng kể mới làm live BTC,
   AAPL, NQ nghiệm thu. Ghi SHA/input/coverage/usage/kết quả manual. Không replay
   tốn phí tự động chỉ vì clone repo hoặc đọc tài liệu bàn giao.
7. Chỉ complete khi acceptance toàn bộ đạt. Giữ PR draft đến khi đủ bằng chứng.

## Chạy trên máy mới

Python baseline đã dùng: 3.14.7; Node 26.8.1/npm 11.19.0. Khả năng hỗ trợ version
khác theo `pyproject.toml`, cần kiểm tra môi trường mới.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev,platform]'
cd web
npm ci
npm run build
cd ..
bash scripts/verify-local.sh
```

Tạo `.env` từ tên biến trong `.env.example`, bổ sung secrets qua kênh riêng.
Cấu hình model không bí mật được kiểm tra lúc bàn giao:

```dotenv
TRADINGAGENTS_LLM_PROVIDER=minimax
TRADINGAGENTS_QUICK_THINK_LLM=MiniMax-M3
TRADINGAGENTS_DEEP_THINK_LLM=MiniMax-M3
TRADINGAGENTS_LLM_BACKEND_URL=https://api.minimax.io/v1
TRADINGAGENTS_OUTPUT_LANGUAGE=Vietnamese
TRADINGAGENTS_MAX_DEBATE_ROUNDS=1
TRADINGAGENTS_MAX_RISK_ROUNDS=1
```

Các QA replay đã override output language thành `English and Vietnamese`.
Không suy ra thinking/max_tokens khác từ env trống. API và worker cần cùng model
env/database/artifact root. FRED cần key; SEC cần user agent liên hệ; Yahoo giá/
news không cần API key. Xem `.env.example` và config cho đường nguồn thực tế.

Theo [local-web-startup](docs/platform/local-web-startup.md) để cấu hình đường
dẫn DB/artifact/web/dist theo máy mới, bootstrap **DB mới** và owner, rồi chạy
`tradingagents-api` và `tradingagents-worker` ở hai terminal. Worker có thể phát
sinh phí AI khi có job. Dùng loopback `http://127.0.0.1:8000`.
Không dùng bootstrap/reset/migration test lên DB chứa lịch sử người dùng.

Frontend checks: `cd web && npm run typecheck && npm run lint && npm test && npm run build`.
PostgreSQL chỉ dùng DB test bỏ được và hướng dẫn `scripts/verify-postgres-local.sh`.
Trên máy cũ Colima bị lỗi và restart chưa được owner xác nhận; máy mới có thể
dùng môi trường local riêng. Không thay đổi VM đang dùng bởi tác vụ khác.

## Dữ liệu riêng không có trong clone public

GitHub repo này là **public**. Code, rules, kế hoạch và receipt đã ở Git. Các mục
sau không được đưa lên GitHub public: `.env`, API keys, owner DB/password/session,
raw reports/snapshots, portfolio/history, checkpoint/cache, logs và ảnh QA chứa
thông tin cá nhân. Clone mới đủ để tiếp tục phát triển, nhưng không tự phục hồi
dữ liệu phân tích/đăng nhập hiện có.

Để giữ đúng lịch sử: chuyển `.env` qua secret manager/kênh bảo mật; tạo backup
nhất quán của DB bằng công cụ DB phù hợp và chuyển **cả artifact store** qua kho
private mã hóa. DB và artifact store là một cặp; chỉ copy một bên không đủ.
Xác minh hash, ownership và đường dẫn sau restore. Không copy DB SQLite đang
ghi bằng thao tác file đơn giản; dùng SQLite backup hoặc dừng writer có kiểm soát.
Chưa tạo hoặc tải backup riêng trong checkpoint này vì chưa có đích private.

Vị trí cũ để tìm dữ liệu khi cần: env tại checkout gốc
`/Volumes/Data/Project/TradingAgents/.env`; runtime dưới
`/Volumes/Data/TradingAgents-runtime/trial/`. Giá trị đường dẫn DB/artifact chính
xác lấy từ env trên máy cũ, không đoán. Worktree code cũ:
`/Volumes/Data/codex/worktrees/ta-030-analysis-risk/TradingAgents`.

Các helper QA dùng trong phiên được lưu nguyên source text ở
`docs/handoff/qa-source/`. Chúng phụ thuộc DB/artifact private, đường dẫn máy cũ
và parent report IDs; chưa portable hoặc live-test trên máy mới. Sửa cấu hình
cho bản sao DB private và review script trước khi chạy. Không lưu output raw vào Git.
Các script này có thể gọi MiniMax và tiêu token; không có job tự chạy khi clone.

Ảnh giao diện cũ không thay thế kiểm tra UI HEAD. Style contract nằm ở
`docs/platform/research-remediation.md`; không cần truy cập máy cũ để hiểu layout.

## Prompt để bàn giao cho Claude/agent khác

> Đọc HANDOFF.md, CLAUDE.md, AGENTS.md và docs/ops/agent-map.md. Tiếp tục trên
> fix/TA-R01-research-quality, Draft PR #7. Giữ mục tiêu R01–R14 và các boundary đã
> chốt. Bắt đầu từ receipt mới nhất để kiểm tra supervision/recovery còn thiếu,
> rồi hoàn thiện ingestion ngoài giá, semantic quality và UI/process theo backlog.
> NewsSnapshotService đã có API/UI, không bắt đầu lại như một WIP chưa tích hợp.
> Kiểm tra trạng thái Git
> và bằng chứng mới trước khi hành động. Dùng local tests; không CI, không tự merge,
> không sửa lịch sử, không đổi model/provider hay mở paid runs từ riêng prompt
> bàn giao này. Báo cáo rõ mọi acceptance chưa đạt, đừng gọi toàn bộ goal complete.
