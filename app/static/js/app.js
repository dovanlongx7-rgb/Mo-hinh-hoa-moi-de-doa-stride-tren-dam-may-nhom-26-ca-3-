"use strict";

// 1. API là mặc định. Demo chỉ để xem trước, không phải kiểm soát bảo mật thật.
const page = document.body.dataset.page;
const mode = document.body.dataset.mode || "api";
const sessionKey = mode === "demo" ? "stride_demo_session" : "bank_token";
const message = document.getElementById("message");
const demoPassword = "Demo@2026!";
const samplePeople = [
  { id: "U_A", username: "van_a", full_name: "Nguyễn Văn A", account: "ACC_A", initial: 1000000 },
  { id: "U_B", username: "van_b", full_name: "Nguyễn Văn B", account: "ACC_B", initial: 500000 },
  { id: "U_C", username: "van_c", full_name: "Nguyễn Văn C", account: "ACC_C", initial: 200000 }
];
const errors = {
  AUTH_REQUIRED: "Bạn cần đăng nhập.", INVALID_SESSION: "Phiên đăng nhập không còn hợp lệ.",
  INVALID_CREDENTIALS: "Tên đăng nhập hoặc mật khẩu không đúng.", ACCOUNT_ACCESS_DENIED: "Bạn không có quyền truy cập tài khoản này.",
  REAUTH_PASSWORD_INVALID: "Mật khẩu xác nhận không đúng.", REAUTH_REQUIRED: "Cần xác thực lại giao dịch.",
  REAUTH_INVALID: "Xác nhận không còn hợp lệ. Vui lòng nhập lại mật khẩu.", INSUFFICIENT_FUNDS: "Số dư không đủ.",
  PER_TRANSFER_LIMIT: "Hạn mức mỗi giao dịch là 300.000 đ.", DAILY_LIMIT: "Giao dịch vượt hạn mức 600.000 đ trong ngày UTC.",
  RATE_LIMITED: "Bạn gửi yêu cầu quá nhanh. Vui lòng thử lại sau.", IDEMPOTENCY_CONFLICT: "Nội dung không khớp giao dịch trước.",
  SAME_ACCOUNT: "Tài khoản nguồn và nhận phải khác nhau.", TARGET_INVALID: "Tài khoản nhận không hợp lệ.",
  INVALID_INPUT: "Thông tin nhập chưa hợp lệ.", INTERNAL_ERROR: "Chưa xác nhận được kết quả. Vui lòng gửi lại cùng yêu cầu.",
  ROLE_DENIED: "Bạn không có quyền thực hiện thao tác này."
};
class BankError extends Error {
  constructor(code, status = 0) { super(errors[code] || code); this.code = code; this.status = status; }
}
const token = () => sessionStorage.getItem(sessionKey);
const money = value => `${new Intl.NumberFormat("vi-VN").format(value)} đ`;
const personName = account => samplePeople.find(p => p.account === account)?.full_name || account;
const fingerprint = intent => JSON.stringify([intent.source_account_id, intent.target_account_id, intent.amount]);
function node(tag, className, text) {
  const e = document.createElement(tag);
  if (className) e.className = className;
  if (text !== undefined) e.textContent = text; // Không chèn dữ liệu người dùng qua innerHTML.
  return e;
}
function notice(text = "", isError = false) { message.textContent = text; message.className = `message${isError ? " error" : ""}`; }
function busy(button, state, text) { button.disabled = state; button.textContent = text; }

// 2. Adapter dữ liệu giả trong sessionStorage. Không gọi mạng hoặc SQLite.
function readDemo() {
  let data;
  try { data = JSON.parse(sessionStorage.getItem("stride_demo_db_v1")); } catch (_) { data = null; }
  return data || { accounts: samplePeople.map(p => ({ id: p.account, user_id: p.id, balance: p.initial })),
    transfers: [], proofs: {}, idempotency: {}, spent: {}, day: new Date().toISOString().slice(0, 10) };
}
function writeDemo(data) { sessionStorage.setItem("stride_demo_db_v1", JSON.stringify(data)); }
async function demoApi(path, options = {}) {
  const data = readDemo();
  const payload = options.body ? JSON.parse(options.body) : {};
  if (path === "/api/auth/login") {
    const user = samplePeople.find(p => p.username === payload.username);
    if (!user || payload.password !== demoPassword) throw new BankError("INVALID_CREDENTIALS", 401);
    return { access_token: `demo:${user.id}`, user: { id: user.id, username: user.username, full_name: user.full_name, role: "customer" } };
  }
  const user = samplePeople.find(p => token() === `demo:${p.id}`);
  if (!user) throw new BankError("INVALID_SESSION", 401);
  const accounts = data.accounts.filter(a => a.user_id === user.id);
  if (path === "/api/auth/logout") return { message: "Đã đăng xuất." };
  if (path === "/api/auth/me") return { id: user.id, username: user.username, full_name: user.full_name, role: "customer" };
  if (path === "/api/accounts") return accounts;
  if (path.startsWith("/api/accounts/")) {
    const id = decodeURIComponent(path.split("/")[3]);
    const account = accounts.find(a => a.id === id);
    if (!account) throw new BankError("ACCOUNT_ACCESS_DENIED", 403);
    if (path.endsWith("/history")) return data.transfers.filter(t => t.source_account_id === id || t.target_account_id === id).slice().reverse().slice(0, 100);
    return account;
  }
  const source = accounts.find(a => a.id === payload.source_account_id);
  if (!source) throw new BankError("ACCOUNT_ACCESS_DENIED", 403);
  if (path === "/api/transfers/reauth") {
    if (payload.password !== demoPassword) throw new BankError("REAUTH_PASSWORD_INVALID", 401);
    const proof = crypto.randomUUID();
    data.proofs[proof] = { user_id: user.id, fingerprint: fingerprint(payload), expires: Date.now() + 180000, consumed: false };
    writeDemo(data); return { reauth_proof: proof, expires_in: 180 };
  }
  if (path === "/api/transfers") {
    const key = `${user.id}:${options.headers["Idempotency-Key"]}`;
    const previous = data.idempotency[key];
    if (previous) {
      if (previous.fingerprint !== fingerprint(payload)) throw new BankError("IDEMPOTENCY_CONFLICT", 409);
      return { transaction: previous.transaction, replayed: true };
    }
    const proof = data.proofs[payload.reauth_proof];
    if (!proof || proof.user_id !== user.id || proof.consumed || proof.expires <= Date.now() || proof.fingerprint !== fingerprint(payload)) throw new BankError("REAUTH_INVALID", 403);
    if (!Number.isSafeInteger(payload.amount) || payload.amount <= 0) throw new BankError("INVALID_INPUT", 422);
    if (payload.source_account_id === payload.target_account_id) throw new BankError("SAME_ACCOUNT", 422);
    const target = data.accounts.find(a => a.id === payload.target_account_id);
    if (!target) throw new BankError("TARGET_INVALID", 422);
    if (payload.amount > 300000) throw new BankError("PER_TRANSFER_LIMIT", 422);
    const day = new Date().toISOString().slice(0, 10);
    if (day !== data.day) { data.spent = {}; data.day = day; }
    if ((data.spent[user.id] || 0) + payload.amount > 600000) throw new BankError("DAILY_LIMIT", 422);
    if (source.balance < payload.amount) throw new BankError("INSUFFICIENT_FUNDS", 422);
    source.balance -= payload.amount; target.balance += payload.amount;
    data.spent[user.id] = (data.spent[user.id] || 0) + payload.amount; proof.consumed = true;
    const transaction = { id: crypto.randomUUID(), user_id: user.id, source_account_id: source.id,
      target_account_id: target.id, amount: payload.amount, created_at: new Date().toISOString(), day_utc: day };
    data.transfers.push(transaction); data.idempotency[key] = { fingerprint: fingerprint(payload), transaction };
    writeDemo(data); return { transaction, replayed: false };
  }
  throw new BankError("Không tìm thấy chức năng trong chế độ xem trước.", 404);
}

// 3. API thật: giữ nguyên endpoint và data contract của backend hiện có.
async function api(path, options = {}) {
  try {
    if (mode === "demo") return await demoApi(path, options);
    const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
    if (token()) headers.Authorization = `Bearer ${token()}`;
    const controller = new AbortController(); const timer = setTimeout(() => controller.abort(), 10000);
    try {
      const response = await fetch(path, { ...options, headers, signal: controller.signal });
      const result = await response.json();
      if (!response.ok) throw new BankError(result.error || "Không thực hiện được yêu cầu.", response.status);
      return result;
    } finally { clearTimeout(timer); }
  } catch (error) {
    if (error instanceof BankError) {
      if (error.status === 401 && page !== "login" && error.code !== "REAUTH_PASSWORD_INVALID") {
        sessionStorage.removeItem(sessionKey); location.assign("/");
      }
      throw error;
    }
    throw new BankError("Chưa nhận được phản hồi. Kiểm tra kết nối và gửi lại cùng yêu cầu.", 0);
  }
}

// 4. Điều hướng và đăng nhập.
document.querySelectorAll("[data-nav]").forEach(link => {
  const selected = link.dataset.nav === page; link.classList.toggle("active", selected);
  if (selected) link.setAttribute("aria-current", "page");
});
document.getElementById("logout").addEventListener("click", async event => {
  event.currentTarget.disabled = true;
  try { if (token()) await api("/api/auth/logout", { method: "POST" }); }
  catch (_) { /* Không ghi thông tin xác thực ra console. */ }
  finally { sessionStorage.removeItem(sessionKey); location.assign("/"); }
});
if (page !== "login" && !token()) location.replace("/");
if (page === "login") {
  document.getElementById("login-form").addEventListener("submit", async event => {
    event.preventDefault(); const button = event.target.querySelector("button");
    busy(button, true, "Đang đăng nhập…"); notice();
    try {
      const data = await api("/api/auth/login", { method: "POST", body: JSON.stringify({
        username: document.getElementById("username").value.trim(), password: document.getElementById("password").value }) });
      sessionStorage.setItem(sessionKey, data.access_token); document.getElementById("password").value = "";
      location.assign("/account");
    } catch (error) { notice(error.message, true); }
    finally { busy(button, false, "Đăng nhập"); }
  });
}

// 5. Tài khoản: trạng thái tải, số dư và chủ sở hữu.
async function loadAccount() {
  const [user, accounts] = await Promise.all([api("/api/auth/me"), api("/api/accounts")]);
  document.getElementById("welcome").textContent = `Xin chào, ${user.full_name}`;
  const container = document.getElementById("accounts"); container.replaceChildren();
  for (const account of accounts) {
    const content = document.getElementById("account-card").content.cloneNode(true);
    content.querySelector('[data-role="balance"]').textContent = money(account.balance);
    content.querySelector('[data-role="account-id"]').textContent = account.id;
    content.querySelector('[data-role="owner"]').textContent = user.full_name;
    container.append(content);
  }
  if (!accounts.length) container.append(node("p", "empty-state", "Bạn chưa có tài khoản."));
  container.setAttribute("aria-busy", "false");
}

// 6. Chuyển tiền: giữ key xuyên reload nếu kết quả chưa rõ; không lưu mật khẩu.
async function loadTransfer() {
  const [user, accounts] = await Promise.all([api("/api/auth/me"), api("/api/accounts")]);
  const form = document.getElementById("transfer-form"), source = document.getElementById("source"),
    target = document.getElementById("target"), amount = document.getElementById("amount"),
    password = document.getElementById("confirm-password"), button = document.getElementById("transfer-submit"),
    newButton = document.getElementById("new-transfer"), result = document.getElementById("transfer-result");
  const pendingKey = `bank_pending:${mode}:${user.id}`;
  source.replaceChildren();
  for (const account of accounts) {
    const option = node("option", "", `${account.id} · ${money(account.balance)}`); option.value = account.id; source.append(option);
  }
  if (!accounts.length) { notice("Bạn chưa có tài khoản để chuyển tiền.", true); return; }
  source.disabled = false; button.disabled = false;
  let pending;
  try { pending = JSON.parse(sessionStorage.getItem(pendingKey)); } catch (_) { pending = null; }
  function remember() {
    if (pending) sessionStorage.setItem(pendingKey, JSON.stringify(pending)); else sessionStorage.removeItem(pendingKey);
  }
  function lockIntent(locked) {
    for (const field of [source, target, amount]) field.disabled = locked;
    password.required = !locked; password.disabled = locked;
    newButton.disabled = Boolean(pending && pending.status === "pending");
  }
  if (pending) {
    source.value = pending.intent.source_account_id; target.value = pending.intent.target_account_id; amount.value = pending.intent.amount;
    lockIntent(true); button.textContent = "Gửi lại cùng yêu cầu";
    notice("Có yêu cầu trước đó. Gửi lại cùng yêu cầu để xác nhận kết quả mà không tạo giao dịch mới.");
  }
  newButton.addEventListener("click", () => {
    if (pending?.status === "pending") return;
    pending = null; remember(); lockIntent(false); password.value = "";
    result.hidden = true; result.replaceChildren(); button.textContent = "Xác nhận chuyển tiền";
    notice("Sẵn sàng tạo giao dịch mới.");
  });
  form.addEventListener("submit", async event => {
    event.preventDefault(); busy(button, true, "Đang xác nhận…"); notice();
    for (const field of [source, target, amount]) field.disabled = true;
    newButton.disabled = true;
    try {
      if (!pending) {
        const intent = { source_account_id: source.value, target_account_id: target.value, amount: Number(amount.value) };
        if (!Number.isSafeInteger(intent.amount) || intent.amount <= 0) throw new BankError("INVALID_INPUT", 422);
        if (intent.source_account_id === intent.target_account_id) throw new BankError("SAME_ACCOUNT", 422);
        const proof = await api("/api/transfers/reauth", { method: "POST", body: JSON.stringify({ ...intent, password: password.value }) });
        pending = { intent, key: crypto.randomUUID(), proof: proof.reauth_proof, status: "pending" };
        remember(); lockIntent(true); password.value = "";
      }
      const data = await api("/api/transfers", { method: "POST", headers: { "Idempotency-Key": pending.key },
        body: JSON.stringify({ ...pending.intent, reauth_proof: pending.proof }) });
      pending.status = "success"; remember(); lockIntent(true);
      if (!data.replayed) {
        const sourceAccount = accounts.find(a => a.id === data.transaction.source_account_id);
        const targetAccount = accounts.find(a => a.id === data.transaction.target_account_id);
        if (sourceAccount) sourceAccount.balance -= data.transaction.amount;
        if (targetAccount) targetAccount.balance += data.transaction.amount;
        for (const option of source.options) {
          const account = accounts.find(a => a.id === option.value);
          if (account) option.textContent = `${account.id} · ${money(account.balance)}`;
        }
      }
      result.replaceChildren(node("h2", "", data.replayed ? "Giao dịch đã được xử lý trước đó" : "Chuyển tiền thành công"),
        node("p", "", `${money(data.transaction.amount)} tới ${personName(data.transaction.target_account_id)}.`),
        node("p", "transaction-id", `Mã giao dịch: ${data.transaction.id}`));
      result.hidden = false;
      notice(data.replayed ? "Hệ thống trả lại kết quả trước, không trừ tiền thêm." : "Chọn Giao dịch mới nếu muốn thực hiện một lần chuyển khác.");
    } catch (error) {
      // Timeout/5xx có thể đã commit: giữ key để hỏi lại. 429 cũng giữ key.
      if (error.status >= 400 && error.status < 500 && error.status !== 429) { pending = null; remember(); lockIntent(false); }
      notice(error.message, true);
    } finally {
      lockIntent(Boolean(pending));
      busy(button, false, pending ? "Gửi lại cùng yêu cầu" : "Xác nhận chuyển tiền");
    }
  });
}

// 7. Lịch sử: trạng thái trống, tổng số dư, chống trùng các dòng hiển thị.
async function loadHistory() {
  const accounts = await api("/api/accounts");
  document.getElementById("history-caption").textContent = accounts.length === 1
    ? `Các giao dịch của tài khoản ${accounts[0].id}.` : "Các giao dịch thuộc tài khoản của bạn.";
  document.getElementById("history-balance").textContent = money(accounts.reduce((total, a) => total + a.balance, 0));
  const groups = await Promise.all(accounts.map(a => api(`/api/accounts/${encodeURIComponent(a.id)}/history`)));
  const unique = new Map(); for (const entry of groups.flat()) unique.set(entry.id, entry);
  const entries = [...unique.values()].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
  const body = document.getElementById("history"); body.replaceChildren();
  if (!entries.length) {
    const row = node("tr"), cell = node("td", "empty-state", "Chưa có giao dịch. Lịch sử sẽ xuất hiện sau lần chuyển tiền đầu tiên.");
    cell.colSpan = 4; row.append(cell); body.append(row);
  }
  for (const entry of entries) {
    const row = node("tr");
    for (const text of [new Date(entry.created_at).toLocaleString("vi-VN"), `${entry.source_account_id} → ${entry.target_account_id}`, money(entry.amount)]) row.append(node("td", "", text));
    const status = node("td"); status.append(node("span", "status-pill", "Hoàn tất")); row.append(status); body.append(row);
  }
  if (entries.length === 1) {
    document.getElementById("history-note").textContent = `Người nhận: ${personName(entries[0].target_account_id)}`;
    document.getElementById("history-note").hidden = false;
  }
}
if (page !== "login" && token()) {
  const loaders = { account: loadAccount, transfer: loadTransfer, history: loadHistory };
  loaders[page]?.().catch(error => notice(error.message, true));
}
