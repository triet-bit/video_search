import { useState, useEffect, useRef, useCallback } from "react";

const API_BASE = "https://hypergamous-somewhat-hiroko.ngrok-free.dev";

function useDebounce(fn, delay) {
  const timer = useRef(null);
  return useCallback((...args) => {
    clearTimeout(timer.current);
    timer.current = setTimeout(() => fn(...args), delay);
  }, [fn, delay]);
}

async function translateQuery(text) {
  try {
    const res = await fetch(`${API_BASE}/translate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (res.ok) {
      const d = await res.json();
      return d.translated || d.text || text;
    }
  } catch (_) {}
  try {
    const res = await fetch(`${API_BASE}/search/vector`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: text, top_k: 1 }),
    });
    if (res.ok) {
      const d = await res.json();
      if (d.translated_query && d.translated_query !== text) return d.translated_query;
    }
  } catch (_) {}
  return text;
}

// ── Netflix-style design tokens ─────────────────────────────
const NF = {
  red: "#E50914",
  redHover: "#F40612",
  redDim: "rgba(229,9,20,0.15)",
  redBorder: "rgba(229,9,20,0.35)",
  bg: "#141414",
  bgCard: "#1F1F1F",
  bgInput: "#2A2A2A",
  bgHover: "#262626",
  border: "rgba(255,255,255,0.1)",
  borderHover: "rgba(255,255,255,0.2)",
  text: "#FFFFFF",
  textMuted: "#A3A3A3",
  textDim: "#6B6B6B",
  teal: "#46D369",
  tealDim: "rgba(70,211,105,0.12)",
  tealBorder: "rgba(70,211,105,0.3)",
  purple: "#8B5CF6",
  purpleDim: "rgba(139,92,246,0.12)",
  purpleBorder: "rgba(139,92,246,0.3)",
};

const S = {
  app: {
    background: NF.bg,
    color: NF.text,
    minHeight: "100vh",
    fontFamily: "'Netflix Sans','Helvetica Neue',Helvetica,Arial,sans-serif",
    fontSize: 14,
    display: "flex",
    flexDirection: "column",
  },
  header: {
    position: "sticky", top: 0, zIndex: 50,
    background: "linear-gradient(to bottom, #000000 0%, rgba(0,0,0,0.85) 100%)",
    backdropFilter: "blur(10px)",
    borderBottom: `1px solid ${NF.border}`,
    padding: "0 36px",
    height: 56,
    display: "flex", alignItems: "center", justifyContent: "space-between",
  },
  logo: {
    fontFamily: "'Arial Black','Arial',sans-serif",
    fontSize: 22, fontWeight: 900,
    letterSpacing: -1, color: NF.red,
    textTransform: "uppercase",
    userSelect: "none",
  },
  logoSub: {
    fontSize: 11, color: NF.textDim,
    letterSpacing: "0.18em", textTransform: "uppercase",
    marginLeft: 2,
  },
  headerTag: {
    fontSize: 10, color: NF.textDim,
    letterSpacing: "0.12em", textTransform: "uppercase",
    border: `1px solid ${NF.border}`,
    borderRadius: 3, padding: "3px 10px",
  },
  main: { flex: 1, padding: "32px 36px", maxWidth: 1140, margin: "0 auto", width: "100%" },

  tabs: {
    display: "flex", gap: 0,
    borderBottom: `2px solid ${NF.border}`,
    marginBottom: 28,
  },
  tabBtn: (active) => ({
    background: "transparent",
    border: "none",
    borderBottom: active ? `2px solid ${NF.red}` : "2px solid transparent",
    marginBottom: -2,
    color: active ? NF.text : NF.textMuted,
    fontFamily: "inherit", fontSize: 13,
    fontWeight: active ? 600 : 400,
    padding: "10px 22px",
    cursor: "pointer",
    transition: "all 0.2s",
    letterSpacing: "0.04em",
    textTransform: "uppercase",
  }),

  field: { marginBottom: 14 },
  label: {
    display: "block", fontSize: 10,
    letterSpacing: "0.12em", textTransform: "uppercase",
    color: NF.textDim, marginBottom: 6, fontWeight: 500,
  },
  input: {
    width: "100%",
    background: NF.bgInput,
    border: `1px solid ${NF.border}`,
    borderRadius: 4,
    color: NF.text,
    fontFamily: "inherit", fontSize: 14,
    padding: "9px 13px",
    outline: "none",
    transition: "border-color 0.2s, background 0.2s",
    boxSizing: "border-box",
  },
  textarea: {
    width: "100%",
    background: NF.bgInput,
    border: `1px solid ${NF.border}`,
    borderRadius: 4,
    color: NF.text,
    fontFamily: "inherit", fontSize: 14,
    padding: "9px 13px",
    outline: "none",
    resize: "vertical",
    minHeight: 88,
    boxSizing: "border-box",
  },

  translatedRow: {
    display: "flex", alignItems: "flex-start", gap: 8,
    background: "rgba(70,211,105,0.05)",
    border: `1px solid ${NF.tealBorder}`,
    borderRadius: 4,
    padding: "7px 12px",
    marginBottom: 14,
  },
  translatedBadge: {
    fontSize: 9, letterSpacing: "0.1em",
    textTransform: "uppercase", color: NF.teal,
    background: NF.tealDim,
    border: `1px solid ${NF.tealBorder}`,
    borderRadius: 3, padding: "2px 7px",
    flexShrink: 0, marginTop: 1,
  },
  translatedInput: {
    flex: 1, background: "transparent",
    border: "none", outline: "none",
    color: NF.textMuted, fontFamily: "inherit",
    fontSize: 13, padding: 0,
  },
  translatingDot: { color: NF.textDim, fontSize: 12, marginTop: 2 },

  row: { display: "flex", gap: 12, alignItems: "flex-end" },
  smlInput: { width: 90 },

  submitBtn: (loading) => ({
    background: loading ? "#4A0000" : NF.red,
    color: loading ? NF.textDim : NF.text,
    border: "none", borderRadius: 4,
    fontFamily: "inherit", fontSize: 13,
    fontWeight: 600, letterSpacing: "0.06em",
    padding: "9px 24px", cursor: loading ? "not-allowed" : "pointer",
    transition: "background 0.2s, transform 0.1s",
    whiteSpace: "nowrap",
    textTransform: "uppercase",
  }),

  eventRow: { display: "flex", gap: 8, alignItems: "center", marginBottom: 8 },
  eventIdx: { fontSize: 10, color: NF.textDim, width: 18, textAlign: "right", flexShrink: 0 },
  rmBtn: {
    background: "transparent", border: `1px solid ${NF.border}`,
    color: NF.textDim, borderRadius: 4,
    width: 30, height: 30, cursor: "pointer",
    fontSize: 14, display: "flex", alignItems: "center", justifyContent: "center",
    flexShrink: 0, transition: "border-color 0.15s, color 0.15s",
  },
  addBtn: {
    background: "transparent", border: `1px dashed ${NF.border}`,
    color: NF.textMuted, fontFamily: "inherit", fontSize: 12,
    padding: "7px 16px", borderRadius: 4,
    cursor: "pointer", marginBottom: 14, display: "block",
    transition: "border-color 0.15s",
    letterSpacing: "0.04em",
  },

  statusBar: {
    display: "flex", alignItems: "center", gap: 10,
    marginTop: 22, marginBottom: 18,
    padding: "10px 14px",
    border: `1px solid ${NF.border}`,
    borderRadius: 4, background: NF.bgCard,
    fontSize: 13, minHeight: 42,
  },
  statusDot: (state) => ({
    width: 7, height: 7, borderRadius: "50%", flexShrink: 0,
    background: state === "ok" ? NF.teal
      : state === "err" ? NF.red
      : state === "loading" ? NF.purple
      : NF.textDim,
    animation: state === "loading" ? "nfPulse 1s infinite" : "none",
    boxShadow: state === "ok" ? `0 0 6px ${NF.teal}`
      : state === "err" ? `0 0 6px ${NF.red}`
      : state === "loading" ? `0 0 6px ${NF.purple}`
      : "none",
  }),
  statusText: { color: NF.textMuted, flex: 1 },
  statusMeta: { color: NF.textDim, fontSize: 12 },

  chunkBadge: {
    fontSize: 11, background: NF.purpleDim,
    border: `1px solid ${NF.purpleBorder}`,
    color: NF.purple, borderRadius: 4,
    padding: "3px 10px",
  },

  sectionTitle: {
    fontSize: 10, fontWeight: 600,
    letterSpacing: "0.14em", textTransform: "uppercase",
    color: NF.textDim, marginBottom: 12,
  },

  resultsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(215px, 1fr))",
    gap: 12,
  },

  frameCard: {
    background: NF.bgCard,
    border: `1px solid ${NF.border}`,
    borderRadius: 6,
    overflow: "hidden",
    cursor: "pointer",
    transition: "border-color 0.2s, transform 0.2s, box-shadow 0.2s",
  },
  frameInfo: { padding: "9px 12px" },
  frameVideo: { fontSize: 12, color: NF.teal, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", marginBottom: 3 },
  frameMeta: { fontSize: 11, color: NF.textDim },
  frameScore: { fontSize: 11, color: NF.purple, float: "right" },

  trakeCard: {
    background: NF.bgCard,
    border: `1px solid ${NF.border}`,
    borderRadius: 6, marginBottom: 14, overflow: "hidden",
  },
  trakeHeader: {
    display: "flex", alignItems: "center", justifyContent: "space-between",
    padding: "10px 14px", borderBottom: `1px solid ${NF.border}`,
    background: "rgba(229,9,20,0.04)",
  },
  trakeVideoName: { fontSize: 13, fontWeight: 600, color: NF.text },
  trakeScore: { fontSize: 11, color: NF.purple },
  trakeFrames: { display: "flex", gap: 10, padding: 12, overflowX: "auto" },
  trakeEvent: { flexShrink: 0, width: 185 },
  trakeEventQuery: { fontSize: 10, color: NF.textDim, marginTop: 5, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" },

  modalOverlay: {
    position: "fixed", inset: 0, zIndex: 200,
    background: "rgba(0,0,0,0.88)",
    backdropFilter: "blur(8px)",
    display: "flex", alignItems: "center", justifyContent: "center",
  },
  modal: {
    background: "#1A1A1A",
    border: `1px solid ${NF.border}`,
    borderRadius: 8, width: "90%", maxWidth: 800,
    maxHeight: "90vh", overflowY: "auto",
    padding: 26, position: "relative",
  },
  modalClose: {
    position: "absolute", top: 12, right: 14,
    background: "transparent", border: "none",
    color: NF.textMuted, fontSize: 22, cursor: "pointer",
    transition: "color 0.15s",
  },
  modalMeta: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px 24px" },
  metaRow: { display: "flex", justifyContent: "space-between", fontSize: 12 },
  metaKey: { color: NF.textDim },
  metaVal: { color: NF.text },

  empty: { textAlign: "center", padding: "56px 0", color: NF.textDim, fontSize: 13 },
  footer: {
    borderTop: `1px solid ${NF.border}`,
    padding: "14px 36px", fontSize: 11,
    color: NF.textDim,
    display: "flex", justifyContent: "space-between",
  },
};

// ── NumericInput: fix cho top-k, không bị kẹt số 0 ─────────
function NumericInput({ value, onChange, min = 1, max, style, ...rest }) {
  const [raw, setRaw] = useState(String(value));

  useEffect(() => {
    setRaw(String(value));
  }, [value]);

  const handleChange = (e) => {
    const s = e.target.value;
    setRaw(s);
    const n = parseInt(s, 10);
    if (!isNaN(n) && n >= min && (max == null || n <= max)) {
      onChange(n);
    }
  };

  const handleBlur = () => {
    const n = parseInt(raw, 10);
    if (isNaN(n) || n < min) {
      setRaw(String(min));
      onChange(min);
    } else if (max != null && n > max) {
      setRaw(String(max));
      onChange(max);
    } else {
      setRaw(String(n));
      onChange(n);
    }
  };

  return (
    <input
      {...rest}
      type="text"
      inputMode="numeric"
      pattern="[0-9]*"
      value={raw}
      onChange={handleChange}
      onBlur={handleBlur}
      style={{ ...S.input, ...style }}
    />
  );
}

// ── FrameImage ─────────────────────────────────────────────
function FrameImage({ path, alt, style }) {
  const [err, setErr] = useState(false);
  const src = path
    ? (path.startsWith("http") ? path : `/data/${path.replace(/^\//, "")}`)
    : null;
  if (!src || err) {
    return (
      <div style={{ ...style, background: "#2A2A2A", display: "flex", alignItems: "center", justifyContent: "center", color: NF.textDim, fontSize: 22 }}>
        🎞
      </div>
    );
  }
  return <img src={src} alt={alt || "frame"} style={style} onError={() => setErr(true)} />;
}

function TranslatedInput({ value, onChange, translating }) {
  return (
    <div style={S.translatedRow}>
      <span style={S.translatedBadge}>EN</span>
      {translating
        ? <span style={S.translatingDot}>···</span>
        : <input
            style={S.translatedInput}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder="bản dịch tiếng Anh (có thể chỉnh)"
          />
      }
    </div>
  );
}

function FrameModal({ frame, onClose }) {
  if (!frame) return null;
  return (
    <div style={S.modalOverlay} onClick={onClose}>
      <div style={S.modal} onClick={(e) => e.stopPropagation()}>
        <button style={S.modalClose} onClick={onClose}>×</button>
        <FrameImage
          path={frame.frame_webp_path}
          style={{ width: "100%", borderRadius: 5, marginBottom: 18, aspectRatio: "16/9", objectFit: "cover" }}
        />
        <div style={S.modalMeta}>
          {[
            ["Video", frame.video_name],
            ["Score", frame.score != null ? frame.score.toFixed(4) : "—"],
            ["Frame file", frame.frame_filename],
            ["Frame order", frame.frame_order],
            ["PTS time", frame.pts_time != null ? `${frame.pts_time.toFixed(3)}s` : "—"],
            ["FPS", frame.fps],
            ["Global idx", frame.global_frame_index],
            ["Qdrant ID", frame.qdrant_id],
          ].map(([k, v]) => (
            <div key={k} style={S.metaRow}>
              <span style={S.metaKey}>{k}</span>
              <span style={{ ...S.metaVal, maxWidth: 270, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{String(v ?? "—")}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── VectorPanel ────────────────────────────────────────────
function VectorPanel({ onResult, onStatus }) {
  const [query, setQuery] = useState("");
  const [translated, setTranslated] = useState("");
  const [translating, setTranslating] = useState(false);
  const [topK, setTopK] = useState(10);
  const [videoName, setVideoName] = useState("");
  const [loading, setLoading] = useState(false);

  const doTranslate = useCallback(async (text) => {
    if (!text.trim()) { setTranslated(""); return; }
    setTranslating(true);
    const t = await translateQuery(text);
    setTranslated(t);
    setTranslating(false);
  }, []);

  const debouncedTranslate = useDebounce(doTranslate, 700);

  const handleQueryChange = (val) => {
    setQuery(val);
    debouncedTranslate(val);
  };

  const submit = async () => {
    if (!query.trim()) return;
    setLoading(true);
    onStatus("loading", "Đang tìm kiếm…");
    const t0 = performance.now();
    try {
      const res = await fetch(`${API_BASE}/search/vector`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: translated || query, top_k: topK, video_name: videoName || null }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      onResult({ type: "vector", data });
      onStatus("ok", `${data.total} kết quả`, `${Math.round(performance.now() - t0)} ms · ${data.translated_query}`);
    } catch (e) {
      onStatus("err", "Lỗi kết nối", e.message);
      onResult(null);
    } finally { setLoading(false); }
  };

  return (
    <div>
      <div style={S.field}>
        <label style={S.label}>Query</label>
        <input
          style={S.input}
          value={query}
          onChange={(e) => handleQueryChange(e.target.value)}
          placeholder="vd: người đi xe máy trên đường phố…"
          onKeyDown={(e) => e.key === "Enter" && submit()}
        />
      </div>
      {(query || translating) && (
        <TranslatedInput value={translated} onChange={setTranslated} translating={translating} />
      )}
      <div style={S.row}>
        <div style={S.field}>
          <label style={S.label}>Top K</label>
          <NumericInput min={1} max={100} value={topK} onChange={setTopK} style={{ width: 90 }} />
        </div>
        <div style={{ ...S.field, flex: 2 }}>
          <label style={S.label}>Video filter <span style={{ opacity: 0.4 }}>(tuỳ chọn)</span></label>
          <input style={S.input} value={videoName} onChange={(e) => setVideoName(e.target.value)} placeholder="tên video…" />
        </div>
        <div style={S.field}>
          <label style={{ ...S.label, visibility: "hidden" }}>_</label>
          <button
            style={S.submitBtn(loading)}
            onClick={submit}
            disabled={loading}
            onMouseEnter={(e) => { if (!loading) e.currentTarget.style.background = NF.redHover; }}
            onMouseLeave={(e) => { if (!loading) e.currentTarget.style.background = NF.red; }}
          >
            {loading ? "Searching…" : "Search"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── TrakePanel ─────────────────────────────────────────────
function TrakePanel({ onResult, onStatus }) {
  const [events, setEvents] = useState(["", ""]);
  const [translatedEvents, setTranslatedEvents] = useState(["", ""]);
  const [translatingIdx, setTranslatingIdx] = useState(-1);
  const [topK, setTopK] = useState(5);
  const [cands, setCands] = useState(50);
  const [lambda, setLambda] = useState(0.0001);
  const [loading, setLoading] = useState(false);

  const translateEvent = useCallback(async (idx, text) => {
    if (!text.trim()) { setTranslatedEvents(p => { const n = [...p]; n[idx] = ""; return n; }); return; }
    setTranslatingIdx(idx);
    const t = await translateQuery(text);
    setTranslatedEvents(p => { const n = [...p]; n[idx] = t; return n; });
    setTranslatingIdx(-1);
  }, []);

  const setEvent = (idx, val) => {
    setEvents(p => { const n = [...p]; n[idx] = val; return n; });
  };

  const addEvent = () => {
    setEvents(p => [...p, ""]);
    setTranslatedEvents(p => [...p, ""]);
  };

  const removeEvent = (idx) => {
    if (events.length <= 2) return;
    setEvents(p => p.filter((_, i) => i !== idx));
    setTranslatedEvents(p => p.filter((_, i) => i !== idx));
  };

  const submit = async () => {
    const filled = events.filter(Boolean);
    if (filled.length < 2) { alert("Cần ít nhất 2 sự kiện"); return; }
    const queries = events.map((e, i) => translatedEvents[i] || e).filter(Boolean);
    setLoading(true);
    onStatus("loading", "Đang chạy DANTE…");
    const t0 = performance.now();
    try {
      const res = await fetch(`${API_BASE}/search/trake`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ queries, top_k: topK, top_k_candidates: cands, lambda_penalty: lambda }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      onResult({ type: "trake", data });
      onStatus("ok", `${data.total} video`, `${Math.round(performance.now() - t0)} ms`);
    } catch (e) {
      onStatus("err", "Lỗi kết nối", e.message);
      onResult(null);
    } finally { setLoading(false); }
  };

  return (
    <div>
      <label style={S.label}>Chuỗi sự kiện <span style={{ opacity: 0.4 }}>(tối thiểu 2, theo thứ tự thời gian)</span></label>
      {events.map((ev, i) => (
        <EventRow
          key={i} idx={i} value={ev}
          translated={translatedEvents[i]}
          translating={translatingIdx === i}
          onChange={(val) => setEvent(i, val)}
          onBlurTranslate={() => translateEvent(i, ev)}
          onTranslatedChange={(val) => setTranslatedEvents(p => { const n = [...p]; n[i] = val; return n; })}
          onRemove={() => removeEvent(i)}
          canRemove={events.length > 2}
        />
      ))}
      <button style={S.addBtn} onClick={addEvent}>+ Thêm sự kiện</button>
      <div style={S.row}>
        <div style={S.field}>
          <label style={S.label}>Top K</label>
          <NumericInput min={1} max={20} value={topK} onChange={setTopK} style={{ width: 80 }} />
        </div>
        <div style={S.field}>
          <label style={S.label}>Candidates</label>
          <NumericInput min={10} max={200} value={cands} onChange={setCands} style={{ width: 95 }} />
        </div>
        <div style={S.field}>
          <label style={S.label}>λ penalty</label>
          <input
            style={{ ...S.input, width: 105 }}
            type="number"
            step={0.0001} min={0} max={1}
            value={lambda}
            onChange={(e) => setLambda(parseFloat(e.target.value))}
          />
        </div>
        <div style={S.field}>
          <label style={{ ...S.label, visibility: "hidden" }}>_</label>
          <button
            style={S.submitBtn(loading)}
            onClick={submit}
            disabled={loading}
            onMouseEnter={(e) => { if (!loading) e.currentTarget.style.background = NF.redHover; }}
            onMouseLeave={(e) => { if (!loading) e.currentTarget.style.background = NF.red; }}
          >
            {loading ? "Running…" : "Search"}
          </button>
        </div>
      </div>
    </div>
  );
}

function EventRow({ idx, value, translated, translating, onChange, onBlurTranslate, onTranslatedChange, onRemove, canRemove }) {
  return (
    <div style={{ marginBottom: 6 }}>
      <div style={S.eventRow}>
        <span style={S.eventIdx}>{idx + 1}</span>
        <input
          style={{ ...S.input, flex: 1 }}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onBlur={onBlurTranslate}
          placeholder={`Sự kiện ${idx + 1}…`}
        />
        <button
          style={{ ...S.rmBtn, color: canRemove ? NF.textMuted : NF.textDim, cursor: canRemove ? "pointer" : "not-allowed" }}
          onClick={onRemove}
          disabled={!canRemove}
        >×</button>
      </div>
      {value && (
        <div style={{ paddingLeft: 28 }}>
          <TranslatedInput value={translated} onChange={onTranslatedChange} translating={translating} />
        </div>
      )}
    </div>
  );
}

// ── LLMPanel ───────────────────────────────────────────────
function LLMPanel({ onResult, onStatus }) {
  const [query, setQuery] = useState("");
  const [translated, setTranslated] = useState("");
  const [translating, setTranslating] = useState(false);
  const [topK, setTopK] = useState(10);
  const [videoName, setVideoName] = useState("");
  const [loading, setLoading] = useState(false);

  const doTranslate = useCallback(async (text) => {
    if (!text.trim()) { setTranslated(""); return; }
    setTranslating(true);
    const t = await translateQuery(text);
    setTranslated(t);
    setTranslating(false);
  }, []);

  const debouncedTranslate = useDebounce(doTranslate, 900);

  const submit = async () => {
    if (!query.trim()) return;
    setLoading(true);
    onStatus("loading", "LLM đang phân tích…");
    const t0 = performance.now();
    try {
      const res = await fetch(`${API_BASE}/search/llm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: translated || query, top_k: topK, video_name: videoName || null }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      onResult({ type: "llm", data });
      onStatus("ok", `${data.total} kết quả`, `${Math.round(performance.now() - t0)} ms`);
    } catch (e) {
      onStatus("err", "Lỗi kết nối", e.message);
      onResult(null);
    } finally { setLoading(false); }
  };

  return (
    <div>
      <div style={S.field}>
        <label style={S.label}>Query dài / phức tạp</label>
        <textarea
          style={S.textarea}
          value={query}
          onChange={(e) => { setQuery(e.target.value); debouncedTranslate(e.target.value); }}
          placeholder="Mô tả chi tiết cảnh bạn muốn tìm…"
        />
      </div>
      {(query || translating) && (
        <TranslatedInput value={translated} onChange={setTranslated} translating={translating} />
      )}
      <div style={S.row}>
        <div style={S.field}>
          <label style={S.label}>Top K</label>
          <NumericInput min={1} max={100} value={topK} onChange={setTopK} style={{ width: 90 }} />
        </div>
        <div style={{ ...S.field, flex: 2 }}>
          <label style={S.label}>Video filter <span style={{ opacity: 0.4 }}>(tuỳ chọn)</span></label>
          <input style={S.input} value={videoName} onChange={(e) => setVideoName(e.target.value)} placeholder="tên video…" />
        </div>
        <div style={S.field}>
          <label style={{ ...S.label, visibility: "hidden" }}>_</label>
          <button
            style={S.submitBtn(loading)}
            onClick={submit}
            disabled={loading}
            onMouseEnter={(e) => { if (!loading) e.currentTarget.style.background = NF.redHover; }}
            onMouseLeave={(e) => { if (!loading) e.currentTarget.style.background = NF.red; }}
          >
            {loading ? "Searching…" : "Search"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Results ────────────────────────────────────────────────
function VectorResults({ data, onFrameClick }) {
  if (!data.results?.length) return <div style={S.empty}>Không có kết quả</div>;
  return (
    <div style={S.resultsGrid}>
      {data.results.map((f, i) => (
        <div
          key={f.qdrant_id}
          style={S.frameCard}
          onClick={() => onFrameClick(f)}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = NF.redBorder;
            e.currentTarget.style.transform = "translateY(-3px) scale(1.01)";
            e.currentTarget.style.boxShadow = `0 8px 24px rgba(229,9,20,0.2)`;
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = NF.border;
            e.currentTarget.style.transform = "none";
            e.currentTarget.style.boxShadow = "none";
          }}
        >
          <FrameImage
            path={f.frame_webp_path}
            style={{ width: "100%", aspectRatio: "16/9", objectFit: "cover", display: "block" }}
          />
          <div style={S.frameInfo}>
            <div style={S.frameVideo}>{f.video_name}</div>
            <div style={S.frameMeta}>
              {f.score != null && <span style={S.frameScore}>{f.score.toFixed(3)}</span>}
              #{f.global_frame_index} · {f.pts_time != null ? `${f.pts_time.toFixed(1)}s` : ""}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function TrakeResults({ data, onFrameClick }) {
  if (!data.results?.length) return <div style={S.empty}>Không có kết quả</div>;
  return (
    <div>
      {data.results.map((vid) => (
        <div key={vid.video_name} style={S.trakeCard}>
          <div style={S.trakeHeader}>
            <span style={S.trakeVideoName}>{vid.video_name}</span>
            <span style={S.trakeScore}>score {vid.dante_score.toFixed(4)}</span>
          </div>
          <div style={S.trakeFrames}>
            {vid.event_frames.map((ef, i) => (
              <div key={i} style={S.trakeEvent}
                onClick={() => onFrameClick({ ...ef, video_name: vid.video_name, qdrant_id: ef.global_frame_index })}
              >
                <FrameImage
                  path={ef.frame_webp_path}
                  style={{ width: 185, aspectRatio: "16/9", objectFit: "cover", borderRadius: 4, display: "block", cursor: "pointer" }}
                />
                <div style={S.trakeEventQuery}>{ef.query}</div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function LLMResults({ data, onFrameClick }) {
  return (
    <div>
      {data.chunks?.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <div style={S.sectionTitle}>Chunks được tách</div>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            {data.chunks.map((c, i) => <span key={i} style={S.chunkBadge}>{c}</span>)}
          </div>
        </div>
      )}
      <VectorResults data={data} onFrameClick={onFrameClick} />
    </div>
  );
}

// ── Main App ───────────────────────────────────────────────
export default function VideoSearch() {
  const [tab, setTab] = useState("vector");
  const [status, setStatus] = useState({ state: "", text: "Sẵn sàng", meta: "" });
  const [result, setResult] = useState(null);
  const [modal, setModal] = useState(null);

  const handleStatus = (state, text, meta = "") => setStatus({ state, text, meta });
  const handleResult = (r) => setResult(r);

  const tabs = [
    { id: "vector", label: "Vector" },
    { id: "trake",  label: "Trake" },
    { id: "llm",    label: "LLM" },
  ];

  return (
    <>
      <style>{`
        @keyframes nfPulse { 0%,100%{opacity:1} 50%{opacity:0.25} }
        * { box-sizing: border-box; }
        input:focus { border-color: rgba(229,9,20,0.5) !important; }
        textarea:focus { border-color: rgba(229,9,20,0.5) !important; }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #1A1A1A; }
        ::-webkit-scrollbar-thumb { background: #3A3A3A; border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: #E50914; }
        ::placeholder { color: #555; }
      `}</style>

      <div style={S.app}>
        <header style={S.header}>
          <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
            <div style={S.logo}>TRIETDEPTRAI</div>
            <div style={S.logoSub}>Video Retrieval</div>
          </div>
          <div style={S.headerTag}>Search System</div>
        </header>

        <main style={S.main}>
          <div style={S.tabs}>
            {tabs.map((t) => (
              <button key={t.id} style={S.tabBtn(tab === t.id)}
                onClick={() => { setTab(t.id); setResult(null); setStatus({ state: "", text: "Sẵn sàng", meta: "" }); }}>
                {t.label}
              </button>
            ))}
          </div>

          {tab === "vector" && <VectorPanel onResult={handleResult} onStatus={handleStatus} />}
          {tab === "trake"  && <TrakePanel  onResult={handleResult} onStatus={handleStatus} />}
          {tab === "llm"    && <LLMPanel    onResult={handleResult} onStatus={handleStatus} />}

          <div style={S.statusBar}>
            <div style={S.statusDot(status.state)} />
            <div style={S.statusText}>{status.text}</div>
            <div style={S.statusMeta}>{status.meta}</div>
          </div>

          {result?.type === "vector" && <VectorResults data={result.data} onFrameClick={setModal} />}
          {result?.type === "trake"  && <TrakeResults  data={result.data} onFrameClick={setModal} />}
          {result?.type === "llm"    && <LLMResults    data={result.data} onFrameClick={setModal} />}

          {!result && status.state === "" && (
            <div style={S.empty}>Nhập query và nhấn Search để bắt đầu</div>
          )}
        </main>

        <footer style={S.footer}>
          <span>HCMAI Video Search</span>
          <span style={{ color: NF.textDim }}>API: {API_BASE}</span>
        </footer>
      </div>

      {modal && <FrameModal frame={modal} onClose={() => setModal(null)} />}
    </>
  );
}