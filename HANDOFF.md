# TradingAgents — bàn giao 2026-09-27, tiếp nối 2026-10-01

## Cập nhật đang triển khai · 2026-10-01

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
- Code đã full-test gần nhất: `50dd0df7e3ddfbfc166f1f6fbb84c97f7989f515`.
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
[bằng chứng mới nhất](docs/platform/research-acceptance-20260927.md).
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
- UI đã được cải thiện; browser nghiệm thu cuối vẫn chưa thực hiện được do tool
  từ chối truy cập vì không xác minh được chính sách admin trên máy cũ.
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
NQ chưa live-test; còn cần phân biệt `NQ=F` reference futures và `^NDX` cash index
trước khi coi một mã là nghiệm thu cho yêu cầu NQ. Không tự thay bằng ETF.

## Công việc tiếp theo có thứ tự

1. News service và prepare-news đã có local test, browser synthetic, một lượt
   Yahoo AAPL trực tiếp; còn cần live API/snapshot/run acceptance và kiểm soát
   coverage theo từng nguồn. Không coi một feed gần đây là lịch sử tin tức.
2. Hoàn thiện nguồn fundamentals, social, macro phù hợp từng asset và hợp đồng
   evidence/number tương ứng; giữ nguyên provider hiện có.
3. Xử lý semantic evidence và tiếng Việt từ các lỗi live đã lưu. Tránh tiếp tục
   chỉ thêm blacklist từng câu hoặc dùng numeric parity để chứng nhận ý nghĩa.
4. Hoàn thiện flow chuẩn bị → nghiên cứu → kiểm tra → đọc quyết định; tổng kết,
   luận điểm đối lập, rủi ro, invalidation và coverage cần dễ đọc trên desktop/mobile.
5. Chạy scope-appropriate local gates; sau khi có sửa đáng kể mới làm live BTC,
   AAPL, NQ nghiệm thu. Ghi SHA/input/coverage/usage/kết quả manual. Không replay
   tốn phí tự động chỉ vì clone repo hoặc đọc tài liệu bàn giao.
6. Chỉ complete khi acceptance toàn bộ đạt. Giữ PR draft đến khi đủ bằng chứng.

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
> chốt. Bắt đầu review/test NewsSnapshotService đang dở, rồi hoàn thiện ingestion
> ngoài giá, semantic quality và UI/process theo backlog. Kiểm tra trạng thái Git
> và bằng chứng mới trước khi hành động. Dùng local tests; không CI, không tự merge,
> không sửa lịch sử, không đổi model/provider hay mở paid runs từ riêng prompt
> bàn giao này. Báo cáo rõ mọi acceptance chưa đạt, đừng gọi toàn bộ goal complete.
