import { useMemo, useState } from "react";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const MIN_PROCESSING_MS = 550;

function App() {
  const [screen, setScreen] = useState("upload");
  const [statementFile, setStatementFile] = useState(null);
  const [statementResult, setStatementResult] = useState(null);
  const [statementQuestion, setStatementQuestion] = useState("");
  const [statementAnswer, setStatementAnswer] = useState("");
  const [statementUploadError, setStatementUploadError] = useState("");
  const [statementQaError, setStatementQaError] = useState("");
  const [loading, setLoading] = useState(false);
  const [processingMs, setProcessingMs] = useState(null);

  const summaryItems = useMemo(() => {
    if (!statementResult?.analysis) return [];

    return [
      ["Transactions", statementResult.analysis.transaction_count],
      ["Total Debit", statementResult.analysis.total_debit],
      ["Total Credit", statementResult.analysis.total_credit],
      ["Opening Balance", statementResult.analysis.opening_balance],
      ["Closing Balance", statementResult.analysis.closing_balance],
    ];
  }, [statementResult]);

  async function analyzeStatement() {
    if (!statementFile) {
      setStatementUploadError("Please select a CSV statement first.");
      return;
    }

    setStatementUploadError("");
    setStatementQaError("");
    setStatementAnswer("");
    setLoading(true);
    setScreen("processing");

    const startedAt = performance.now();

    try {
      const formData = new FormData();
      formData.append("file", statementFile);

      const response = await fetch(`${API_BASE}/statement/upload`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Could not analyze statement.");
      }

      const requestFinishedAt = performance.now();
      const elapsed = requestFinishedAt - startedAt;
      const remainingVisualTime = Math.max(0, MIN_PROCESSING_MS - elapsed);

      if (remainingVisualTime > 0) {
        await new Promise((resolve) => setTimeout(resolve, remainingVisualTime));
      }

      setStatementResult(data);
      setProcessingMs(Math.round(elapsed));
      setScreen("workspace");
    } catch (err) {
      setStatementUploadError(err.message);
      setScreen("upload");
    } finally {
      setLoading(false);
    }
  }

  async function askStatementQuestion() {
    if (!statementResult) {
      setStatementQaError("Analyze a statement before asking questions.");
      return;
    }

    if (!statementQuestion.trim()) {
      setStatementQaError("Please enter a statement question.");
      return;
    }

    setLoading(true);
    setStatementQaError("");
    setStatementAnswer("");

    try {
      const response = await fetch(`${API_BASE}/statement/ask`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: statementQuestion,
          statement_data: statementResult.transactions,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        if (response.status === 502) {
          throw new Error(
            "The Statement Agent is temporarily unavailable or rate-limited. Please try again shortly."
          );
        }

        throw new Error(
          data.detail || "Could not answer statement question."
        );
      }

      setStatementAnswer(data.answer);
    } catch (err) {
      setStatementQaError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function resetWorkspace() {
    setScreen("upload");
    setStatementFile(null);
    setStatementResult(null);
    setStatementQuestion("");
    setStatementAnswer("");
    setStatementUploadError("");
    setStatementQaError("");
    setProcessingMs(null);
  }

  return (
    <div className="min-h-screen bg-[#f4f7fb] text-slate-900">
      <TopBar />

      {screen === "upload" && (
        <UploadScreen
          file={statementFile}
          error={statementUploadError}
          loading={loading}
          onFileChange={(file) => {
            setStatementFile(file);
            setStatementUploadError("");
          }}
          onAnalyze={analyzeStatement}
        />
      )}

      {screen === "processing" && (
        <ProcessingScreen filename={statementFile?.name} />
      )}

      {screen === "workspace" && statementResult && (
        <Workspace
          result={statementResult}
          summaryItems={summaryItems}
          processingMs={processingMs}
          question={statementQuestion}
          answer={statementAnswer}
          error={statementQaError}
          loading={loading}
          onQuestionChange={(value) => {
            setStatementQuestion(value);
            setStatementQaError("");
          }}
          onAsk={askStatementQuestion}
          onReset={resetWorkspace}
        />
      )}
    </div>
  );
}

function TopBar() {
  return (
    <>
      <div className="bg-[#f58220] text-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-2 text-[11px] font-semibold tracking-[0.16em] sm:px-6">
          <span>INTERNSHIP PROTOTYPE • SYNTHETIC DATA DEMO</span>
          <span className="hidden sm:inline">BANKING INTELLIGENCE WORKSPACE</span>
        </div>
      </div>

      <header className="border-b border-white/10 bg-[#063b6f] text-white shadow-[0_8px_30px_rgba(4,48,89,0.18)]">
        <div className="mx-auto flex min-h-[82px] max-w-7xl items-center gap-4 px-5 sm:px-6">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-white/10 text-sm font-black shadow-sm">
            AI
          </div>
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-blue-200">
              Student Internship Project • Banking AI Demo
            </p>
            <h1 className="mt-1 text-lg font-bold sm:text-2xl">
              Customer Statement Intelligence Suite
            </h1>
          </div>
        </div>
      </header>
    </>
  );
}

function UploadScreen({
  file,
  error,
  loading,
  onFileChange,
  onAnalyze,
}) {
  return (
    <main className="screen-enter mx-auto max-w-6xl px-5 py-8 sm:px-6 sm:py-12">
      <PrototypeNotice />

      <section className="relative overflow-hidden rounded-[30px] bg-[#063b6f] px-6 py-10 text-white shadow-[0_20px_60px_rgba(4,48,89,0.18)] sm:px-10 sm:py-14">
        <div className="pointer-events-none absolute -right-20 -top-20 h-64 w-64 rounded-full border-[46px] border-white/5" />
        <div className="relative max-w-3xl">
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-[#ffad64]">
            Start a new analysis
          </p>
          <h2 className="mt-3 text-3xl font-black leading-tight sm:text-5xl">
            Turn a synthetic statement into an intelligence workspace.
          </h2>
          <p className="mt-5 max-w-2xl text-sm leading-7 text-blue-100 sm:text-base">
            Upload one CSV statement. The application will validate the file,
            calculate verified financial metrics and prepare the workspace for
            grounded statement analysis.
          </p>
        </div>
      </section>

      <section className="mt-7 rounded-[26px] border border-slate-200 bg-white p-6 shadow-[0_14px_45px_rgba(15,23,42,0.07)] sm:p-8">
        <div className="grid gap-7 lg:grid-cols-[1fr_0.55fr] lg:items-center">
          <div>
            <label className="group block cursor-pointer rounded-2xl border-2 border-dashed border-blue-200 bg-[#f8fbff] p-8 text-center transition hover:border-[#0a5fa8] hover:bg-blue-50/40">
              <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-white text-sm font-black text-[#063b6f] shadow-sm ring-1 ring-slate-200">
                CSV
              </span>
              <span className="mt-4 block text-lg font-extrabold text-[#063b6f]">
                Choose synthetic statement
              </span>
              <span className="mt-2 block text-sm text-slate-500">
                CSV only • synthetic/demo data • maximum 2 MiB
              </span>
              <input
                type="file"
                accept=".csv"
                className="hidden"
                onChange={(event) => onFileChange(event.target.files[0] || null)}
              />
            </label>

            {file && (
              <div className="mt-4 flex items-center justify-between gap-3 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
                <div className="min-w-0">
                  <p className="text-xs font-bold uppercase tracking-[0.12em] text-slate-400">
                    Selected file
                  </p>
                  <p className="mt-1 truncate text-sm font-bold text-slate-700">
                    {file.name}
                  </p>
                </div>
                <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-700">
                  Ready
                </span>
              </div>
            )}

            {error && <ErrorMessage message={error} />}

            <button
              onClick={onAnalyze}
              disabled={loading}
              className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-[#f58220] px-6 py-3.5 text-sm font-extrabold text-white shadow-[0_8px_20px_rgba(245,130,32,0.24)] transition hover:-translate-y-0.5 hover:bg-[#df7117] disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto"
            >
              Analyze Statement
              <span aria-hidden="true">→</span>
            </button>
          </div>

          <div className="grid gap-3">
            <JourneyStep
              number="01"
              title="Upload once"
              text="The selected statement becomes the active analysis context."
            />
            <JourneyStep
              number="02"
              title="Verified processing"
              text="Financial totals are calculated by deterministic backend logic."
            />
            <JourneyStep
              number="03"
              title="Enter workspace"
              text="Review transactions and continue into statement intelligence."
            />
          </div>
        </div>
      </section>
    </main>
  );
}

function ProcessingScreen({ filename }) {
  return (
    <main className="screen-enter flex min-h-[calc(100vh-116px)] items-center justify-center px-5 py-10 sm:px-6">
      <section className="w-full max-w-2xl rounded-[30px] border border-slate-200 bg-white px-6 py-10 text-center shadow-[0_20px_65px_rgba(15,23,42,0.10)] sm:px-10 sm:py-14">
        <div className="processing-orbit mx-auto">
          <div className="processing-core">AI</div>
        </div>

        <p className="mt-8 text-xs font-bold uppercase tracking-[0.18em] text-[#f58220]">
          Preparing intelligence workspace
        </p>
        <h2 className="mt-3 text-2xl font-black text-[#063b6f] sm:text-3xl">
          Analyzing your synthetic statement
        </h2>
        <p className="mx-auto mt-4 max-w-xl text-sm leading-7 text-slate-500">
          Validating the CSV, reading transactions and calculating verified
          statement metrics.
        </p>

        <div className="mx-auto mt-7 max-w-md rounded-xl bg-slate-50 px-4 py-3 text-sm font-semibold text-slate-600">
          {filename || "Selected statement"}
        </div>

        <div className="mx-auto mt-6 h-1.5 max-w-md overflow-hidden rounded-full bg-slate-100">
          <div className="processing-bar h-full rounded-full bg-[#f58220]" />
        </div>

        <p className="mt-5 text-xs text-slate-400">
          The workspace opens as soon as verified processing completes.
        </p>
      </section>
    </main>
  );
}

function Workspace({
  result,
  summaryItems,
  processingMs,
  question,
  answer,
  error,
  loading,
  onQuestionChange,
  onAsk,
  onReset,
}) {
  return (
    <main className="screen-enter mx-auto max-w-7xl px-5 py-7 sm:px-6 sm:py-9">
      <PrototypeNotice />

      <section className="rounded-[26px] border border-slate-200 bg-white shadow-[0_14px_45px_rgba(15,23,42,0.07)]">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 px-6 py-5 sm:px-8">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.15em] text-[#f58220]">
              Active statement
            </p>
            <h2 className="mt-1 text-xl font-black text-[#063b6f] sm:text-2xl">
              Intelligence Workspace
            </h2>
            <p className="mt-1 text-sm text-slate-500">{result.filename}</p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {processingMs !== null && (
              <span className="rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-bold text-emerald-700">
                Processed in {processingMs} ms
              </span>
            )}
            <button
              onClick={onReset}
              className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-bold text-[#063b6f] transition hover:border-blue-300 hover:bg-blue-50"
            >
              Replace Statement
            </button>
          </div>
        </div>

        <div className="p-6 sm:p-8">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
            {summaryItems.map(([label, value], index) => (
              <SummaryCard
                key={label}
                label={label}
                value={formatMetric(value)}
                accent={String(index + 1).padStart(2, "0")}
              />
            ))}
          </div>

          <TransactionTable transactions={result.transactions || []} />

          <section className="mt-8 rounded-2xl border border-blue-100 bg-[#f7fbff] p-5 sm:p-6">
            <div className="flex items-start gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#063b6f] text-sm font-black text-white">
                AI
              </div>
              <div>
                <h3 className="font-extrabold text-[#063b6f]">
                  Statement Intelligence
                </h3>
                <p className="mt-1 text-sm leading-6 text-slate-500">
                  This is the current statement Q&A capability. Multi-turn
                  conversation will be added in the next milestone.
                </p>
              </div>
            </div>

            <textarea
              value={question}
              onChange={(event) => onQuestionChange(event.target.value)}
              rows="3"
              placeholder="Example: Compare my monthly spending and tell me what stands out."
              className="abl-input mt-5"
            />

            <button
              onClick={onAsk}
              disabled={loading}
              className="mt-4 inline-flex items-center justify-center gap-2 rounded-xl bg-[#f58220] px-6 py-3 text-sm font-extrabold text-white shadow-[0_8px_20px_rgba(245,130,32,0.22)] transition hover:-translate-y-0.5 hover:bg-[#df7117] disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "Analyzing..." : "Ask about this statement"}
              {!loading && <span aria-hidden="true">→</span>}
            </button>

            {error && <ErrorMessage message={error} />}

            {answer && (
              <div className="mt-5 rounded-2xl border border-blue-100 bg-white p-5 text-sm leading-7 text-slate-700 shadow-sm">
                <p className="mb-3 text-xs font-bold uppercase tracking-[0.12em] text-[#0a5fa8]">
                  Grounded response
                </p>
                <RichText text={answer} />
              </div>
            )}
          </section>
        </div>
      </section>
    </main>
  );
}

function PrototypeNotice() {
  return (
    <section className="mb-6 rounded-2xl border border-amber-300 bg-amber-50 px-5 py-4 text-sm leading-6 text-amber-950 shadow-sm">
      <p className="font-extrabold">
        Internship prototype — not an official Allied Bank customer website.
      </p>
      <p className="mt-1">
        This independent student project uses synthetic data for demonstration.
        Do not upload real customer statements, credentials or confidential
        information.
      </p>
    </section>
  );
}

function JourneyStep({ number, title, text }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
      <div className="flex gap-3">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-orange-50 text-xs font-black text-[#f58220]">
          {number}
        </span>
        <div>
          <h3 className="font-extrabold text-[#063b6f]">{title}</h3>
          <p className="mt-1 text-sm leading-6 text-slate-500">{text}</p>
        </div>
      </div>
    </div>
  );
}

function TransactionTable({ transactions }) {
  return (
    <section className="mt-8">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.14em] text-[#f58220]">
            Statement activity
          </p>
          <h3 className="mt-1 text-xl font-extrabold text-[#063b6f]">
            Transactions
          </h3>
        </div>
        <span className="rounded-full bg-slate-100 px-3 py-1.5 text-xs font-bold text-slate-500">
          {transactions.length} rows
        </span>
      </div>

      <div className="mt-4 overflow-hidden rounded-2xl border border-slate-200">
        <div className="max-h-[420px] overflow-auto">
          <table className="min-w-[760px] w-full border-collapse text-left text-sm">
            <thead className="sticky top-0 z-10 bg-[#063b6f] text-white">
              <tr>
                <TableHeader>Date</TableHeader>
                <TableHeader>Description</TableHeader>
                <TableHeader align="right">Debit</TableHeader>
                <TableHeader align="right">Credit</TableHeader>
                <TableHeader align="right">Balance</TableHeader>
              </tr>
            </thead>
            <tbody>
              {transactions.map((transaction, index) => (
                <tr
                  key={`${transaction.date}-${index}`}
                  className="border-t border-slate-100 bg-white transition hover:bg-blue-50/40"
                >
                  <TableCell>{transaction.date}</TableCell>
                  <TableCell strong>{transaction.description || "—"}</TableCell>
                  <TableCell align="right">
                    {formatMetric(transaction.debit)}
                  </TableCell>
                  <TableCell align="right">
                    {formatMetric(transaction.credit)}
                  </TableCell>
                  <TableCell align="right" strong>
                    {formatMetric(transaction.balance)}
                  </TableCell>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

function TableHeader({ children, align = "left" }) {
  return (
    <th
      className={`px-4 py-3 text-xs font-bold uppercase tracking-[0.10em] ${
        align === "right" ? "text-right" : "text-left"
      }`}
    >
      {children}
    </th>
  );
}

function TableCell({ children, align = "left", strong = false }) {
  return (
    <td
      className={`px-4 py-3 text-slate-600 ${
        align === "right" ? "text-right tabular-nums" : "text-left"
      } ${strong ? "font-bold text-slate-800" : ""}`}
    >
      {children}
    </td>
  );
}

function SummaryCard({ label, value, accent }) {
  return (
    <div className="relative overflow-hidden rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <span className="absolute right-4 top-4 text-[10px] font-black tracking-[0.12em] text-[#f58220]">
        {accent}
      </span>
      <p className="pr-8 text-xs font-bold uppercase tracking-[0.08em] text-slate-400">
        {label}
      </p>
      <p className="mt-3 break-words text-2xl font-black tracking-tight text-[#063b6f]">
        {value}
      </p>
      <div className="mt-4 h-1 w-10 rounded-full bg-[#f58220]" />
    </div>
  );
}

function ErrorMessage({ message }) {
  return (
    <div
      className="mt-5 flex items-start gap-3 rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700 shadow-sm"
      role="alert"
    >
      <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-red-100 font-bold">
        !
      </span>
      <span>{message}</span>
    </div>
  );
}

function RichText({ text }) {
  if (!text) return null;

  return (
    <div className="space-y-2">
      {text.split("\n").map((line, index) => {
        const trimmed = line.trim();

        if (!trimmed) {
          return <div key={index} className="h-1" />;
        }

        const isBullet =
          trimmed.startsWith("* ") ||
          trimmed.startsWith("- ") ||
          trimmed.startsWith("• ");

        if (isBullet) {
          return (
            <div key={index} className="flex gap-3">
              <span className="mt-[2px] font-black text-[#f58220]">•</span>
              <p>{renderInline(trimmed.slice(2))}</p>
            </div>
          );
        }

        return <p key={index}>{renderInline(line)}</p>;
      })}
    </div>
  );
}

function renderInline(text) {
  const pieces = text.split(/(\*\*[^*]+\*\*)/g);

  return pieces.map((piece, index) => {
    if (piece.startsWith("**") && piece.endsWith("**")) {
      return (
        <strong key={index} className="font-extrabold text-[#063b6f]">
          {piece.slice(2, -2)}
        </strong>
      );
    }

    return <span key={index}>{piece}</span>;
  });
}

function formatMetric(value) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  if (typeof value === "number") {
    return value.toLocaleString(undefined, {
      maximumFractionDigits: 2,
    });
  }

  return value;
}

export default App;
