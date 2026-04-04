import { useState, useEffect, useRef, useCallback } from "react";

const API_BASE = "https://hypergamous-somewhat-hiroko.ngrok-free.dev";

// ── tiny debounce ──────────────────────────────────────────
function useDebounce(fn, delay) {
  const timer = useRef(null);
  return useCallback((...args) => {
    clearTimeout(timer.current);
    timer.current = setTimeout(() => fn(...args), delay);
  }, [fn, delay]);
}

// ── translate helper (calls your API's translate endpoint or falls back) ──
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
  // fallback: hit vector search with top_k=1 just to get translated_query back
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

// ── styles ─────────────────────────────────────────────────
const S = {
  app: {
    background: "#09090b",
    color: "#e2e2e8",
    minHeight: "100vh",
    fontFamily: "'DM Mono', 'Fira Code', monospace",
    fontSize: 13,
    display: "flex",
    flexDirection: "column",
  },
  header: {
    position: "sticky", top: 0, zIndex: 50,
    background: "rgba(9,9,11,0.88)",
    backdropFilter: "blur(14px)",
    borderBottom: "1px solid #1d1d21",
    padding: "0 28px",
    height: 50,
    display: "flex", alignItems: "center", justifyContent: "space-between",
  },
  logo: {
    fontFamily: "'Syne','Segoe UI',sans-serif",
    fontSize: 15, fontWeight: 800,
    letterSpacing: -0.5, color: "#e2e2e8",
  },
  logoAccent: { color: "#6ee7b7" },
  headerTag: {
    fontSize: 10, color: "#52525b",
    letterSpacing: "0.1em", textTransform: "uppercase",
    border: "1px solid #27272a", borderRadius: 3,
    padding: "3px 8px",
  },
  main: { flex: 1, padding: "28px 32px", maxWidth: 1120, margin: "0 auto", width: "100%" },

  // tabs
  tabs: {
    display: "flex", gap: 2,
    border: "1px solid #1d1d21", borderRadius: 6,
    padding: 3, width: "fit-content", marginBottom: 24,
  },
  tabBtn: (active) => ({
    background: active ? "#27272a" : "transparent",
    border: "none",
    color: active ? "#6ee7b7" : "#52525b",
    fontFamily: "inherit", fontSize: 12,
    padding: "6px 18px", borderRadius: 4,
    cursor: "pointer", transition: "all 0.15s",
    letterSpacing: "0.03em",
  }),

  // form
  field: { marginBottom: 12 },
  label: {
    display: "block", fontSize: 10,
    letterSpacing: "0.1em", textTransform: "uppercase",
    color: "#52525b", marginBottom: 5,
  },
  input: {
    width: "100%",
    background: "#111113",
    border: "1px solid #1d1d21",
    borderRadius: 5,
    color: "#e2e2e8",
    fontFamily: "inherit", fontSize: 13,
    padding: "8px 11px",
    outline: "none",
    transition: "border-color 0.15s",
    boxSizing: "border-box",
  },
  inputFocus: { borderColor: "#3f3f46" },
  textarea: {
    width: "100%",
    background: "#111113",
    border: "1px solid #1d1d21",
    borderRadius: 5,
    color: "#e2e2e8",
    fontFamily: "inherit", fontSize: 13,
    padding: "8px 11px",
    outline: "none",
    resize: "vertical",
    minHeight: 80,
    boxSizing: "border-box",
  },

  // translated row
  translatedRow: {
    display: "flex", alignItems: "flex-start", gap: 8,
    background: "#0f0f12",
    border: "1px solid #1d1d21",
    borderRadius: 5,
    padding: "7px 11px",
    marginBottom: 14,
  },
  translatedBadge: {
    fontSize: 9, letterSpacing: "0.08em",
    textTransform: "uppercase", color: "#6ee7b7",
    background: "rgba(110,231,183,0.08)",
    border: "1px solid rgba(110,231,183,0.2)",
    borderRadius: 3, padding: "2px 6px",
    flexShrink: 0, marginTop: 1,
  },
  translatedInput: {
    flex: 1, background: "transparent",
    border: "none", outline: "none",
    color: "#a1a1aa", fontFamily: "inherit",
    fontSize: 13, padding: 0,
  },
  translatingDot: { color: "#52525b", fontSize: 12, marginTop: 2 },

  row: { display: "flex", gap: 10, alignItems: "flex-end" },
  smlInput: { width: 88 },

  submitBtn: (loading) => ({
    background: loading ? "#27272a" : "#6ee7b7",
    color: loading ? "#52525b" : "#09090b",
    border: "none", borderRadius: 5,
    fontFamily: "inherit", fontSize: 12,
    fontWeight: 500, letterSpacing: "0.05em",
    padding: "9px 22px", cursor: loading ? "not-allowed" : "pointer",
    transition: "opacity 0.15s, transform 0.1s",
    whiteSpace: "nowrap",
    opacity: loading ? 0.6 : 1,
  }),

  // trake events
  eventRow: { display: "flex", gap: 8, alignItems: "center", marginBottom: 8 },
  eventIdx: { fontSize: 10, color: "#52525b", width: 16, textAlign: "right", flexShrink: 0 },
  rmBtn: {
    background: "transparent", border: "1px solid #27272a",
    color: "#52525b", borderRadius: 4,
    width: 28, height: 28, cursor: "pointer",
    fontSize: 14, display: "flex", alignItems: "center", justifyContent: "center",
    flexShrink: 0,
  },
  addBtn: {
    background: "transparent", border: "1px dashed #27272a",
    color: "#52525b", fontFamily: "inherit", fontSize: 11,
    padding: "6px 14px", borderRadius: 5,
    cursor: "pointer", marginBottom: 14, display: "block",
  },

  // status
  statusBar: {
    display: "flex", alignItems: "center", gap: 10,
    marginTop: 20, marginBottom: 16,
    padding: "9px 13px",
    border: "1px solid #1d1d21",
    borderRadius: 5, background: "#111113",
    fontSize: 12, minHeight: 40,
  },
  statusDot: (state) => ({
    width: 6, height: 6, borderRadius: "50%", flexShrink: 0,
    background: state === "ok" ? "#6ee7b7"
      : state === "err" ? "#f87171"
      : state === "loading" ? "#818cf8"
      : "#3f3f46",
    animation: state === "loading" ? "pulse 1s infinite" : "none",
  }),
  statusText: { color: "#71717a", flex: 1 },
  statusMeta: { color: "#52525b", fontSize: 11 },

  // chunks
  chunkBadge: {
    fontSize: 11, background: "rgba(129,140,248,0.1)",
    border: "1px solid rgba(129,140,248,0.25)",
    color: "#818cf8", borderRadius: 4,
    padding: "3px 9px",
  },

  sectionTitle: {
    fontFamily: "'Syne','Segoe UI',sans-serif",
    fontSize: 10, fontWeight: 700,
    letterSpacing: "0.12em", textTransform: "uppercase",
    color: "#52525b", marginBottom: 12,
  },

  // grid
  resultsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(210px, 1fr))",
    gap: 11,
  },

  frameCard: {
    background: "#111113",
    border: "1px solid #1d1d21",
    borderRadius: 6,
    overflow: "hidden",
    cursor: "pointer",
    transition: "border-color 0.15s, transform 0.15s",
  },
  frameInfo: { padding: "9px 11px" },
  frameVideo: { fontSize: 11, color: "#6ee7b7", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", marginBottom: 3 },
  frameMeta: { fontSize: 10, color: "#52525b" },
  frameScore: { fontSize: 10, color: "#818cf8", float: "right" },

  // trake card
  trakeCard: {
    background: "#111113",
    border: "1px solid #1d1d21",
    borderRadius: 6, marginBottom: 12, overflow: "hidden",
  },
  trakeHeader: {
    display: "flex", alignItems: "center", justifyContent: "space-between",
    padding: "9px 13px", borderBottom: "1px solid #1d1d21",
  },
  trakeVideoName: { fontFamily: "'Syne',sans-serif", fontSize: 13, fontWeight: 600 },
  trakeScore: { fontSize: 11, color: "#818cf8" },
  trakeFrames: { display: "flex", gap: 8, padding: 12, overflowX: "auto" },
  trakeEvent: { flexShrink: 0, width: 180 },
  trakeEventQuery: { fontSize: 10, color: "#52525b", marginTop: 5, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" },

  // modal
  modalOverlay: {
    position: "fixed", inset: 0, zIndex: 200,
    background: "rgba(0,0,0,0.82)",
    backdropFilter: "blur(6px)",
    display: "flex", alignItems: "center", justifyContent: "center",
  },
  modal: {
    background: "#111113",
    border: "1px solid #27272a",
    borderRadius: 8, width: "90%", maxWidth: 780,
    maxHeight: "90vh", overflowY: "auto",
    padding: 24, position: "relative",
  },
  modalClose: {
    position: "absolute", top: 12, right: 14,
    background: "transparent", border: "none",
    color: "#52525b", fontSize: 20, cursor: "pointer",
  },
  modalMeta: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px 20px" },
  metaRow: { display: "flex", justifyContent: "space-between", fontSize: 12 },
  metaKey: { color: "#52525b" },
  metaVal: { color: "#e2e2e8" },

  empty: { textAlign: "center", padding: "48px 0", color: "#52525b", fontSize: 12 },
  footer: {
    borderTop: "1px solid #1d1d21",
    padding: "13px 28px", fontSize: 11,
    color: "#3f3f46",
    display: "flex", justifyContent: "space-between",
  },
};

// ── FrameImage ─────────────────────────────────────────────
function FrameImage({ path, alt, style, className }) {
  const [err, setErr] = useState(false);
  const src = path ? (path.startsWith("http") ? path : `${API_BASE}/${path.replace(/^\//, "")}`) : null;
  if (!src || err) {
    return (
      <div style={{ ...style, background: "#1d1d21", display: "flex", alignItems: "center", justifyContent: "center", color: "#3f3f46", fontSize: 20 }}>
        🎞
      </div>
    );
  }
  return <img src={src} alt={alt || "frame"} style={style} onError={() => setErr(true)} />;
}

// ── TranslatedInput ────────────────────────────────────────
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

// ── FrameModal ─────────────────────────────────────────────
function FrameModal({ frame, onClose }) {
  if (!frame) return null;
  return (
    <div style={S.modalOverlay} onClick={onClose}>
      <div style={S.modal} onClick={(e) => e.stopPropagation()}>
        <button style={S.modalClose} onClick={onClose}>×</button>
        <FrameImage
          path={frame.frame_webp_path}
          style={{ width: "100%", borderRadius: 5, marginBottom: 16, aspectRatio: "16/9", objectFit: "cover" }}
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
              <span style={{ ...S.metaVal, maxWidth: 260, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{String(v ?? "—")}</span>
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
          <input style={{ ...S.input, ...S.smlInput }} type="number" min={1} max={100} value={topK} onChange={(e) => setTopK(+e.target.value)} />
        </div>
        <div style={{ ...S.field, flex: 2 }}>
          <label style={S.label}>Video filter <span style={{ opacity: 0.4 }}>(tuỳ chọn)</span></label>
          <input style={S.input} value={videoName} onChange={(e) => setVideoName(e.target.value)} placeholder="tên video…" />
        </div>
        <div style={S.field}>
          <label style={{ ...S.label, visibility: "hidden" }}>_</label>
          <button style={S.submitBtn(loading)} onClick={submit} disabled={loading}>
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

  const makeDebounce = (idx) => useDebounce((text) => translateEvent(idx, text), 700);

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
          onChange={(val) => {
            setEvent(i, val);
          }}
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
          <input style={{ ...S.input, width: 80 }} type="number" min={1} max={20} value={topK} onChange={(e) => setTopK(+e.target.value)} />
        </div>
        <div style={S.field}>
          <label style={S.label}>Candidates</label>
          <input style={{ ...S.input, width: 90 }} type="number" min={10} max={200} value={cands} onChange={(e) => setCands(+e.target.value)} />
        </div>
        <div style={S.field}>
          <label style={S.label}>λ penalty</label>
          <input style={{ ...S.input, width: 100 }} type="number" step={0.0001} min={0} max={1} value={lambda} onChange={(e) => setLambda(parseFloat(e.target.value))} />
        </div>
        <div style={S.field}>
          <label style={{ ...S.label, visibility: "hidden" }}>_</label>
          <button style={S.submitBtn(loading)} onClick={submit} disabled={loading}>
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
        <button style={S.rmBtn} onClick={onRemove} disabled={!canRemove}>×</button>
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
          <input style={{ ...S.input, ...S.smlInput }} type="number" min={1} max={100} value={topK} onChange={(e) => setTopK(+e.target.value)} />
        </div>
        <div style={{ ...S.field, flex: 2 }}>
          <label style={S.label}>Video filter <span style={{ opacity: 0.4 }}>(tuỳ chọn)</span></label>
          <input style={S.input} value={videoName} onChange={(e) => setVideoName(e.target.value)} placeholder="tên video…" />
        </div>
        <div style={S.field}>
          <label style={{ ...S.label, visibility: "hidden" }}>_</label>
          <button style={S.submitBtn(loading)} onClick={submit} disabled={loading}>
            {loading ? "Searching…" : "Search"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Results renderers ──────────────────────────────────────
function VectorResults({ data, onFrameClick }) {
  if (!data.results?.length) return <div style={S.empty}>Không có kết quả</div>;
  return (
    <div style={S.resultsGrid}>
      {data.results.map((f, i) => (
        <div
          key={f.qdrant_id}
          style={{ ...S.frameCard, animationDelay: `${i * 30}ms` }}
          onClick={() => onFrameClick(f)}
          onMouseEnter={(e) => { e.currentTarget.style.borderColor = "#3f3f46"; e.currentTarget.style.transform = "translateY(-2px)"; }}
          onMouseLeave={(e) => { e.currentTarget.style.borderColor = "#1d1d21"; e.currentTarget.style.transform = "none"; }}
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
                  style={{ width: 180, aspectRatio: "16/9", objectFit: "cover", borderRadius: 4, display: "block", cursor: "pointer" }}
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
  const handleResult = (r) => { setResult(r); };

  const tabs = [
    { id: "vector", label: "Vector" },
    { id: "trake",  label: "Trake" },
    { id: "llm",    label: "LLM" },
  ];

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Syne:wght@700;800&display=swap');
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
        * { box-sizing: border-box; }
        input[type=number]::-webkit-inner-spin-button { opacity: 0.4; }
      `}</style>

      <div style={S.app}>
        <header style={S.header}>
          <div style={S.logo}>HCMAI<span style={S.logoAccent}>·</span>Search</div>
          <div style={S.headerTag}>Video Retrieval System</div>
        </header>

        <main style={S.main}>
          {/* Tabs */}
          <div style={S.tabs}>
            {tabs.map((t) => (
              <button key={t.id} style={S.tabBtn(tab === t.id)}
                onClick={() => { setTab(t.id); setResult(null); setStatus({ state: "", text: "Sẵn sàng", meta: "" }); }}>
                {t.label}
              </button>
            ))}
          </div>

          {/* Panels */}
          {tab === "vector" && <VectorPanel onResult={handleResult} onStatus={handleStatus} />}
          {tab === "trake"  && <TrakePanel  onResult={handleResult} onStatus={handleStatus} />}
          {tab === "llm"    && <LLMPanel    onResult={handleResult} onStatus={handleStatus} />}

          {/* Status bar */}
          <div style={S.statusBar}>
            <div style={S.statusDot(status.state)} />
            <div style={S.statusText}>{status.text}</div>
            <div style={S.statusMeta}>{status.meta}</div>
          </div>

          {/* Results */}
          {result?.type === "vector" && <VectorResults data={result.data} onFrameClick={setModal} />}
          {result?.type === "trake"  && <TrakeResults  data={result.data} onFrameClick={setModal} />}
          {result?.type === "llm"    && <LLMResults    data={result.data} onFrameClick={setModal} />}

          {!result && status.state === "" && (
            <div style={S.empty}>Nhập query và nhấn Search để bắt đầu</div>
          )}
        </main>

        <footer style={S.footer}>
          <span>HCMAI Video Search</span>
          <span>API: {API_BASE}</span>
        </footer>
      </div>

      {/* Modal */}
      {modal && <FrameModal frame={modal} onClose={() => setModal(null)} />}
    </>
  );
}
