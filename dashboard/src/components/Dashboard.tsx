// ── Static mock data ─────────────────────────────────────────────────────────

const kpis = [
  {
    label: "총 수집 건수",
    value: "12,480",
    sub: "+8.2% (7일)",
    tone: "text-emerald-400",
  },
  {
    label: "오늘 신규",
    value: "342",
    sub: "목표 300 초과",
    tone: "text-emerald-400",
  },
  {
    label: "활성 소스",
    value: "18",
    sub: "전체 20개 중",
    tone: "text-slate-400",
  },
  {
    label: "실패/에러",
    value: "7",
    sub: "재시도 필요 3건",
    tone: "text-amber-400",
  },
];

const trendBars = [35, 50, 42, 68, 58, 74, 86];
const trendLabels = ["월", "화", "수", "목", "금", "토", "일"];

const sources = [
  {
    name: "Source A",
    lastSuccess: "2분 전",
    successRate: "98.2%",
    latency: "420ms",
    status: "ok",
  },
  {
    name: "Source B",
    lastSuccess: "5분 전",
    successRate: "95.1%",
    latency: "610ms",
    status: "warn",
  },
  {
    name: "Source C",
    lastSuccess: "11분 전",
    successRate: "99.0%",
    latency: "390ms",
    status: "ok",
  },
  {
    name: "Source D",
    lastSuccess: "1시간 전",
    successRate: "72.4%",
    latency: "1.2s",
    status: "error",
  },
];

const logs = [
  {
    msg: "Timeout on Source B /page/12",
    time: "14:28",
    level: "warn" as const,
  },
  {
    msg: "429 Rate limit on Source D",
    time: "13:51",
    level: "warn" as const,
  },
  {
    msg: "Parser mismatch on Source F",
    time: "11:07",
    level: "error" as const,
  },
];

// ── Sub-components ────────────────────────────────────────────────────────────

interface KpiCardProps {
  label: string;
  value: string;
  sub: string;
  tone: string;
}

function KpiCard({ label, value, sub, tone }: KpiCardProps) {
  return (
    <div className="rounded-2xl border border-slate-700 bg-slate-800 p-5">
      <p className="text-xs font-medium text-slate-400">{label}</p>
      <p className="mt-2 text-3xl font-bold text-white">{value}</p>
      <p className={`mt-1 text-xs ${tone}`}>{sub}</p>
    </div>
  );
}

function TrendChart() {
  return (
    <div className="rounded-2xl border border-slate-700 bg-slate-800 p-5">
      <h3 className="mb-4 text-sm font-semibold text-slate-300">
        수집 추이 (최근 7일)
      </h3>
      <div className="flex h-40 items-end gap-2">
        {trendBars.map((h, i) => (
          <div key={i} className="flex flex-1 flex-col items-center gap-1">
            <div
              className="w-full rounded-t-md bg-indigo-500 opacity-90 transition-all hover:opacity-100"
              style={{ height: `${h}%` }}
            />
            <span className="text-[10px] text-slate-500">{trendLabels[i]}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

const statusBadge: Record<string, string> = {
  ok: "bg-emerald-900 text-emerald-400",
  warn: "bg-amber-900 text-amber-400",
  error: "bg-red-900 text-red-400",
};

const statusLabel: Record<string, string> = {
  ok: "정상",
  warn: "경고",
  error: "오류",
};

function SourceTable() {
  return (
    <div className="rounded-2xl border border-slate-700 bg-slate-800 p-5">
      <h3 className="mb-4 text-sm font-semibold text-slate-300">
        소스별 현황
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-slate-700 text-xs text-slate-500">
              <th className="pb-2 pr-4 font-medium">소스명</th>
              <th className="pb-2 pr-4 font-medium">마지막 성공</th>
              <th className="pb-2 pr-4 font-medium">성공률</th>
              <th className="pb-2 pr-4 font-medium">응답시간</th>
              <th className="pb-2 font-medium">상태</th>
            </tr>
          </thead>
          <tbody>
            {sources.map((s) => (
              <tr
                key={s.name}
                className="border-b border-slate-700/50 last:border-0"
              >
                <td className="py-3 pr-4 font-medium text-white">{s.name}</td>
                <td className="py-3 pr-4 text-slate-400">{s.lastSuccess}</td>
                <td className="py-3 pr-4 text-slate-300">{s.successRate}</td>
                <td className="py-3 pr-4 text-slate-300">{s.latency}</td>
                <td className="py-3">
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${statusBadge[s.status]}`}
                  >
                    {statusLabel[s.status]}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const logStyle: Record<
  "warn" | "error",
  { dot: string; text: string }
> = {
  warn: { dot: "bg-amber-400", text: "text-amber-400" },
  error: { dot: "bg-red-400", text: "text-red-400" },
};

function ErrorLogPanel() {
  return (
    <div className="rounded-2xl border border-slate-700 bg-slate-800 p-5">
      <h3 className="mb-4 text-sm font-semibold text-slate-300">
        최근 에러 로그
      </h3>
      <ul className="space-y-3">
        {logs.map((log, i) => (
          <li
            key={i}
            className="flex items-start justify-between gap-3 rounded-xl border border-slate-700 bg-slate-900 p-3"
          >
            <div className="flex items-start gap-2">
              <span
                className={`mt-1 h-2 w-2 shrink-0 rounded-full ${logStyle[log.level].dot}`}
              />
              <span className="text-sm text-slate-300">{log.msg}</span>
            </div>
            <div className="flex shrink-0 flex-col items-end gap-1">
              <span className="text-xs text-slate-500">{log.time}</span>
              <button className="rounded-lg bg-slate-700 px-2 py-0.5 text-xs text-slate-300 hover:bg-slate-600">
                재시도
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

// ── Main Dashboard ────────────────────────────────────────────────────────────

export default function Dashboard() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 to-slate-950 p-6 font-sans text-white">
      {/* Header */}
      <header className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">
            NEET Content Collector
          </h1>
          <p className="mt-1 text-sm text-slate-400">
            마지막 수집: 2026-07-21 14:32 &middot; 상태:{" "}
            <span className="text-emerald-400">정상</span>
          </p>
        </div>
        <button className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-500 active:scale-95 transition-transform">
          수집 실행
        </button>
      </header>

      {/* KPI Cards */}
      <section className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        {kpis.map((k) => (
          <KpiCard key={k.label} {...k} />
        ))}
      </section>

      {/* Trend Chart + Error Log */}
      <section className="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <TrendChart />
        </div>
        <ErrorLogPanel />
      </section>

      {/* Source Status Table */}
      <section>
        <SourceTable />
      </section>
    </div>
  );
}
