import { useEffect, useRef, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const MAX_HISTORY_MESSAGES = 8;

const STARTER_PROMPTS_WITH_STATEMENT = [
  "How much did I spend?",
  "Find recurring payments.",
  "What was my largest debit?",
  "Summarize my statement.",
];

const STARTER_PROMPTS_WITHOUT_STATEMENT = [
  "What documents are required to claim an unclaimed deposit?",
  "What does the Financial Consumer Protection Framework cover?",
];

function App() {
  // upload      -> Statement abhi load nahi hui.
  // processing  -> CSV backend par validate/analyze ho rahi hai.
  // workspace   -> Statement load ho chuki hai aur assistant ke paas context hai.
  const [screen, setScreen] = useState("upload");

  const [statementFile, setStatementFile] = useState(null);
  const [statementResult, setStatementResult] = useState(null);

  // ONE ASSISTANT:
  //
  // Ab statement Q&A, recurring-payment questions aur policy questions
  // aik hi conversation surface use karte hain.
  const [assistantQuestion, setAssistantQuestion] = useState("");
  const [assistantMessages, setAssistantMessages] = useState([]);

  const [loading, setLoading] = useState(false);
  const [statementUploadError, setStatementUploadError] = useState("");
  const [assistantError, setAssistantError] = useState("");

  const [showTransactions, setShowTransactions] = useState(false);

  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "nearest",
    });
  }, [assistantMessages, loading]);

  const hasStatement = Boolean(statementResult);

  const starterPrompts = hasStatement
    ? STARTER_PROMPTS_WITH_STATEMENT
    : STARTER_PROMPTS_WITHOUT_STATEMENT;

  async function analyzeStatement(fileOverride = null) {
    const fileToAnalyze = fileOverride ?? statementFile;

    if (!fileToAnalyze) {
      setStatementUploadError("Please choose a synthetic CSV statement first.");
      return;
    }

    setLoading(true);
    setStatementUploadError("");
    setAssistantError("");
    setStatementResult(null);
    setAssistantMessages([]);
    setShowTransactions(false);
    setScreen("processing");

    try {
      const formData = new FormData();
      formData.append("file", fileToAnalyze);

      const startedAt = performance.now();

      const response = await fetch(`${API_BASE}/statement/upload`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          extractApiError(data, "Could not analyze the statement."),
        );
      }

      const elapsed = performance.now() - startedAt;

      console.log(`Statement processing: ${Math.round(elapsed)} ms`);

      // Transition ko deliberate feel dene ke liye minimum short delay.
      const minimumProcessingDuration = 600;

      const remainingProcessingTime = Math.max(
        0,
        minimumProcessingDuration - elapsed,
      );

      if (remainingProcessingTime > 0) {
        await new Promise((resolve) =>
          setTimeout(resolve, remainingProcessingTime),
        );
      }

      setStatementResult(data);
      setScreen("workspace");
    } catch (err) {
      setStatementUploadError(err.message);
      setScreen("upload");
    } finally {
      setLoading(false);
    }
  }

  async function useFreshDemoStatement() {
    // Har click par browser runtime par nayi synthetic CSV banti hai.
    // Koi static demo file reuse nahi hoti.
    const demoFile = generateRuntimeDemoStatement();

    setStatementFile(demoFile);
    setStatementUploadError("");

    // Reviewer ko extra Browse -> Analyze steps na karne paren.
    await analyzeStatement(demoFile);
  }

  function resetStatement() {
    setStatementFile(null);
    setStatementResult(null);
    setAssistantQuestion("");
    setAssistantMessages([]);
    setStatementUploadError("");
    setAssistantError("");
    setShowTransactions(false);
    setScreen("upload");
  }

  async function askAssistantQuestion(promptOverride = null) {
    const userQuestion = (promptOverride ?? assistantQuestion).trim();

    if (!userQuestion) {
      setAssistantError("Please enter a question.");
      return;
    }

    setLoading(true);
    setAssistantError("");

    // Current question request.question mein separately jaati hai.
    // History mein sirf previous user/assistant turns bhejte hain.
    const conversationHistory = assistantMessages
      .slice(-MAX_HISTORY_MESSAGES)
      .map((message) => ({
        role: message.role,
        content: message.content,
      }));

    setAssistantMessages((currentMessages) => [
      ...currentMessages,
      {
        role: "user",
        content: userQuestion,
      },
    ]);

    setAssistantQuestion("");

    try {
      const response = await fetch(`${API_BASE}/assistant/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: userQuestion,
          statement_data: statementResult?.transactions ?? [],
          conversation_history: conversationHistory,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          extractApiError(
            data,
            "The banking assistant could not answer that question.",
          ),
        );
      }

      // Backend metadata ko message ke saath preserve karte hain.
      // UI isi metadata se evidence/provenance explain karegi.
      setAssistantMessages((currentMessages) => [
        ...currentMessages,
        {
          role: "assistant",
          content: data.answer,
          capability: data.capability,
          method: data.method,
          sources: data.sources ?? [],
          structuredData: data.structured_data ?? null,
        },
      ]);
    } catch (err) {
      setAssistantError(err.message);
    } finally {
      setLoading(false);
    }
  }

  if (screen === "processing") {
    return (
      <div className="min-h-screen bg-[#f4f7fb] text-slate-900">
        <CompactHeader />

        <main className="mx-auto flex min-h-[calc(100vh-72px)] max-w-7xl items-center justify-center px-5 py-10 sm:px-6">
          <section
            className="w-full max-w-lg rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-[0_20px_60px_rgba(15,23,42,0.10)] sm:p-10"
            aria-live="polite"
            aria-busy="true"
          >
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50">
              <div className="h-7 w-7 animate-spin rounded-full border-4 border-blue-100 border-t-[#063b6f]" />
            </div>

            <p className="mt-6 text-xs font-bold uppercase tracking-[0.16em] text-[#f58220]">
              Verified statement processing
            </p>

            <h1 className="mt-2 text-2xl font-black tracking-tight text-[#063b6f]">
              Preparing your workspace
            </h1>

            <p className="mx-auto mt-3 max-w-md text-sm leading-6 text-slate-600">
              The synthetic CSV is being validated, parsed and analyzed with
              deterministic backend calculations.
            </p>
          </section>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f4f7fb] text-slate-900">
      <CompactHeader />

      <main className="mx-auto max-w-7xl px-5 py-5 sm:px-6 sm:py-6">
        {screen === "upload" ? (
          <LandingWorkspace
            statementFile={statementFile}
            setStatementFile={(file) => {
              setStatementFile(file);
              setStatementUploadError("");
            }}
            statementUploadError={statementUploadError}
            analyzeStatement={analyzeStatement}
            useFreshDemoStatement={useFreshDemoStatement}
            loading={loading}
            assistantQuestion={assistantQuestion}
            setAssistantQuestion={(value) => {
              setAssistantQuestion(value);
              setAssistantError("");
            }}
            assistantMessages={assistantMessages}
            assistantError={assistantError}
            askAssistantQuestion={askAssistantQuestion}
            starterPrompts={starterPrompts}
            chatEndRef={chatEndRef}
          />
        ) : (
          <StatementWorkspace
            statementResult={statementResult}
            resetStatement={resetStatement}
            showTransactions={showTransactions}
            setShowTransactions={setShowTransactions}
            assistantQuestion={assistantQuestion}
            setAssistantQuestion={(value) => {
              setAssistantQuestion(value);
              setAssistantError("");
            }}
            assistantMessages={assistantMessages}
            assistantError={assistantError}
            askAssistantQuestion={askAssistantQuestion}
            starterPrompts={starterPrompts}
            loading={loading}
            chatEndRef={chatEndRef}
          />
        )}

        <PrototypeNotice />
      </main>

      <Footer />
    </div>
  );
}

function CompactHeader() {
  return (
    <header className="border-b border-white/10 bg-[#063b6f] text-white shadow-[0_6px_24px_rgba(4,48,89,0.16)]">
      <div className="mx-auto flex min-h-[72px] max-w-7xl items-center justify-between gap-4 px-5 sm:px-6">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white/10 text-xs font-black">
            AI
          </div>

          <div className="min-w-0">
            <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-blue-200">
              Banking Intelligence Assistant
            </p>

            <h1 className="truncate text-base font-extrabold sm:text-xl">
              Customer Statement Intelligence Suite
            </h1>
          </div>
        </div>

        <div className="hidden shrink-0 items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3 py-2 text-xs font-semibold text-blue-100 sm:flex">
          <span className="h-2 w-2 rounded-full bg-[#f58220]" />
          Internship Prototype
        </div>
      </div>
    </header>
  );
}

function LandingWorkspace({
  statementFile,
  setStatementFile,
  statementUploadError,
  analyzeStatement,
  useFreshDemoStatement,
  loading,
  assistantQuestion,
  setAssistantQuestion,
  assistantMessages,
  assistantError,
  askAssistantQuestion,
  starterPrompts,
  chatEndRef,
}) {
  return (
    <section className="grid gap-5 lg:grid-cols-[0.88fr_1.12fr]">
      <div className="rounded-[24px] border border-slate-200 bg-white p-5 shadow-[0_12px_38px_rgba(15,23,42,0.07)] sm:p-6">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.14em] text-[#f58220]">
              Start here
            </p>

            <h2 className="mt-1 text-2xl font-black tracking-tight text-[#063b6f] sm:text-3xl">
              Upload. Ask. Follow up.
            </h2>
          </div>

          <span className="rounded-full bg-blue-50 px-3 py-1.5 text-xs font-bold text-[#063b6f]">
            Synthetic data only
          </span>
        </div>

        <p className="mt-3 max-w-xl text-sm leading-6 text-slate-600">
          Upload a synthetic bank statement, then use one assistant for verified
          statement calculations, recurring-payment detection and grounded
          public-policy questions.
        </p>

        <div className="mt-5 grid grid-cols-3 gap-2">
          <StepCard number="1" title="Upload" text="Choose CSV" />
          <StepCard number="2" title="Ask" text="Use plain English" />
          <StepCard number="3" title="Follow up" text="Keep chatting" />
        </div>

        <div className="mt-5 rounded-2xl border-2 border-dashed border-blue-200 bg-[#f8fbff] p-5 transition hover:border-[#0a5fa8]">
          <div className="flex items-center gap-4">
            <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-white text-xs font-black text-[#063b6f] shadow-sm ring-1 ring-slate-200">
              CSV
            </span>

            <span className="min-w-0 flex-1">
              <span className="block font-extrabold text-[#063b6f]">
                Choose synthetic statement
              </span>

              <span className="mt-0.5 block truncate text-xs text-slate-500">
                {statementFile ? statementFile.name : "No file selected"}
              </span>
            </span>

            <label className="cursor-pointer rounded-lg bg-white px-3 py-2 text-xs font-bold text-[#0a5fa8] shadow-sm ring-1 ring-slate-200 transition hover:bg-blue-50">
              Browse
              <input
                type="file"
                accept=".csv"
                onChange={(event) =>
                  setStatementFile(event.target.files[0] ?? null)
                }
                className="hidden"
              />
            </label>
          </div>

          <div className="mt-4 grid gap-2 sm:grid-cols-2">
            <button
              type="button"
              onClick={() => analyzeStatement()}
              disabled={loading}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#f58220] px-5 py-3 text-sm font-extrabold text-white shadow-[0_8px_20px_rgba(245,130,32,0.22)] transition hover:bg-[#df7117] disabled:cursor-not-allowed disabled:opacity-50"
            >
              Analyze Selected CSV
              <span aria-hidden="true">→</span>
            </button>

            <button
              type="button"
              onClick={useFreshDemoStatement}
              disabled={loading}
              className="inline-flex items-center justify-center gap-2 rounded-xl border border-blue-200 bg-white px-5 py-3 text-sm font-extrabold text-[#063b6f] shadow-sm transition hover:border-[#0a5fa8] hover:bg-blue-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Use Fresh Demo
              <span aria-hidden="true">↻</span>
            </button>
          </div>

          <p className="mt-2 text-center text-[11px] leading-4 text-slate-400">
            Fresh demo creates a new synthetic multi-month CSV in your browser
            every time.
          </p>
        </div>

        {statementUploadError && (
          <ErrorMessage message={statementUploadError} className="mt-3" />
        )}

        <div className="mt-5 flex flex-wrap gap-2">
          <CapabilityPill label="Statement calculations" enabled={false} />
          <CapabilityPill label="Recurring patterns" enabled={false} />
          <CapabilityPill label="Public policy" enabled />
        </div>

        <p className="mt-3 text-xs leading-5 text-slate-500">
          Public-policy questions work immediately. Uploading a statement
          unlocks statement calculations and recurring pattern detection.
        </p>
      </div>

      <AssistantPanel
        title="Ask the banking assistant"
        subtitle="No statement loaded yet — public-policy questions are available now."
        assistantQuestion={assistantQuestion}
        setAssistantQuestion={setAssistantQuestion}
        assistantMessages={assistantMessages}
        assistantError={assistantError}
        askAssistantQuestion={askAssistantQuestion}
        starterPrompts={starterPrompts}
        loading={loading}
        chatEndRef={chatEndRef}
        hasStatement={false}
      />
    </section>
  );
}

function StatementWorkspace({
  statementResult,
  resetStatement,
  showTransactions,
  setShowTransactions,
  assistantQuestion,
  setAssistantQuestion,
  assistantMessages,
  assistantError,
  askAssistantQuestion,
  starterPrompts,
  loading,
  chatEndRef,
}) {
  return (
    <>
      <section className="mb-5 flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-blue-100 bg-white px-5 py-4 shadow-sm">
        <div className="flex min-w-0 items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#063b6f] text-sm font-black text-white">
            ✓
          </div>

          <div className="min-w-0">
            <p className="text-xs font-bold uppercase tracking-[0.12em] text-[#f58220]">
              Statement context active
            </p>

            <p className="truncate font-extrabold text-[#063b6f]">
              {statementResult.filename}
            </p>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <CapabilityPill label="Statement calculations" enabled />
          <CapabilityPill label="Recurring patterns" enabled />
          <CapabilityPill label="Public policy" enabled />

          <button
            type="button"
            onClick={resetStatement}
            className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-bold text-slate-600 transition hover:border-blue-200 hover:bg-blue-50 hover:text-[#063b6f]"
          >
            Change statement
          </button>
        </div>
      </section>

      <section className="grid items-start gap-5 lg:grid-cols-[0.82fr_1.18fr]">
        <div className="space-y-5">
          <div className="rounded-[24px] border border-slate-200 bg-white p-5 shadow-[0_12px_38px_rgba(15,23,42,0.07)] sm:p-6">
            <div className="flex items-end justify-between gap-3">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.14em] text-[#f58220]">
                  Verified snapshot
                </p>

                <h2 className="mt-1 text-xl font-black text-[#063b6f]">
                  Statement Summary
                </h2>
              </div>

              <span className="rounded-full bg-slate-100 px-3 py-1.5 text-xs font-semibold text-slate-500">
                {statementResult.transactions.length} rows
              </span>
            </div>

            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              <MetricCard
                label="Total Debit"
                value={statementResult.analysis.total_debit}
              />
              <MetricCard
                label="Total Credit"
                value={statementResult.analysis.total_credit}
              />
              <MetricCard
                label="Opening Balance"
                value={statementResult.analysis.opening_balance}
              />
              <MetricCard
                label="Closing Balance"
                value={statementResult.analysis.closing_balance}
              />
            </div>

            <div className="mt-3 rounded-xl bg-[#f8fafc] px-4 py-3 text-sm text-slate-600">
              <span className="font-bold text-[#063b6f]">Transactions:</span>{" "}
              {statementResult.analysis.transaction_count}
            </div>

            <button
              type="button"
              onClick={() => setShowTransactions((current) => !current)}
              className="mt-4 inline-flex w-full items-center justify-between rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-bold text-[#063b6f] transition hover:border-blue-200 hover:bg-blue-50"
            >
              <span>
                {showTransactions ? "Hide" : "View"} transaction evidence
              </span>

              <span aria-hidden="true">{showTransactions ? "↑" : "↓"}</span>
            </button>
          </div>
        </div>

        <AssistantPanel
          title="Banking Intelligence Assistant"
          subtitle="Ask about this statement, recurring patterns, or public Allied Bank policy."
          assistantQuestion={assistantQuestion}
          setAssistantQuestion={setAssistantQuestion}
          assistantMessages={assistantMessages}
          assistantError={assistantError}
          askAssistantQuestion={askAssistantQuestion}
          starterPrompts={starterPrompts}
          loading={loading}
          chatEndRef={chatEndRef}
          hasStatement
        />
      </section>

      {showTransactions && (
        <TransactionTable transactions={statementResult.transactions} />
      )}
    </>
  );
}

function AssistantPanel({
  title,
  subtitle,
  assistantQuestion,
  setAssistantQuestion,
  assistantMessages,
  assistantError,
  askAssistantQuestion,
  starterPrompts,
  loading,
  chatEndRef,
  hasStatement,
}) {
  return (
    <div className="rounded-[24px] border border-slate-200 bg-white shadow-[0_12px_38px_rgba(15,23,42,0.07)]">
      <div className="flex items-start gap-3 border-b border-slate-100 px-5 py-4 sm:px-6">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#063b6f] text-xs font-black text-white">
          AI
        </div>

        <div>
          <p className="text-xs font-bold uppercase tracking-[0.14em] text-[#f58220]">
            Banking Intelligence Assistant
          </p>

          <h2 className="mt-0.5 text-lg font-extrabold text-[#063b6f]">
            {title}
          </h2>

          <p className="mt-1 text-[11px] font-semibold text-slate-400">
            Verified calculations • recurring patterns • grounded policy
          </p>

          <p className="mt-0.5 text-xs leading-5 text-slate-500">{subtitle}</p>
        </div>
      </div>

      <div className="max-h-[310px] min-h-[185px] space-y-4 overflow-y-auto bg-[#f8fafc] px-5 py-5 sm:px-6">
        {assistantMessages.length === 0 ? (
          <div>
            <p className="text-sm font-bold text-slate-700">
              Try one of these:
            </p>

            <div className="mt-2 flex flex-wrap gap-1.5">
              {starterPrompts.map((prompt) => (
                <PromptChip
                  key={prompt}
                  text={prompt}
                  onClick={() => askAssistantQuestion(prompt)}
                  disabled={loading}
                />
              ))}
            </div>

            {!hasStatement && (
              <div className="mt-4 rounded-xl border border-blue-100 bg-white px-4 py-3 text-xs leading-5 text-slate-500">
                Upload a statement to unlock verified financial calculations and
                recurring-payment detection.
              </div>
            )}
          </div>
        ) : (
          assistantMessages.map((message, index) => (
            <ConversationMessage
              key={`${message.role}-${index}`}
              message={message}
            />
          ))
        )}

        {loading && (
          <div className="flex justify-start">
            <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
              <p className="text-[11px] font-bold uppercase tracking-[0.1em] text-[#f58220]">
                Banking Assistant
              </p>

              <p className="mt-1 text-sm text-slate-500">
                Checking the relevant evidence mode...
              </p>
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      <div className="border-t border-slate-100 px-5 py-4 sm:px-6">
        <textarea
          value={assistantQuestion}
          onChange={(event) => setAssistantQuestion(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey && !loading) {
              event.preventDefault();
              askAssistantQuestion();
            }
          }}
          rows="2"
          maxLength={1000}
          placeholder={
            hasStatement
              ? "Ask about your statement, recurring payments, or public policy..."
              : "Ask an Allied Bank public-policy question..."
          }
          className="abl-input"
          disabled={loading}
        />

        <div className="mt-2 flex items-center justify-between gap-3">
          <p className="text-xs text-slate-400">
            {assistantQuestion.length}/1000
          </p>

          <p className="text-xs text-slate-400">
            Enter to send • Shift+Enter for new line
          </p>
        </div>

        <button
          type="button"
          onClick={() => askAssistantQuestion()}
          disabled={loading}
          className="mt-3 inline-flex items-center justify-center gap-2 rounded-xl bg-[#f58220] px-5 py-2.5 text-sm font-extrabold text-white shadow-[0_8px_20px_rgba(245,130,32,0.22)] transition hover:bg-[#df7117] disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? "Working..." : "Ask Assistant"}
          {!loading && <span aria-hidden="true">→</span>}
        </button>

        {assistantError && (
          <ErrorMessage message={assistantError} className="mt-3" />
        )}
      </div>
    </div>
  );
}

function ConversationMessage({ message }) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[88%] rounded-2xl rounded-br-md bg-[#063b6f] px-4 py-3 text-white sm:max-w-[78%]">
          <p className="mb-1 text-[10px] font-bold uppercase tracking-[0.1em] text-blue-100">
            You
          </p>

          <p className="whitespace-pre-wrap text-sm leading-6">
            {message.content}
          </p>
        </div>
      </div>
    );
  }

  const provenance = getProvenanceMeta(message.method);

  return (
    <div className="flex justify-start">
      <div className="max-w-[94%] rounded-2xl rounded-bl-md border border-slate-200 bg-white px-4 py-3 text-slate-700 shadow-sm sm:max-w-[86%]">
        <p className="mb-2 text-[10px] font-bold uppercase tracking-[0.1em] text-[#f58220]">
          Banking Assistant
        </p>

        <RichText text={message.content} />

        {provenance && (
          <div className="mt-3 inline-flex items-center gap-2 rounded-full bg-blue-50 px-3 py-1.5 text-[11px] font-bold text-[#063b6f]">
            <span>{provenance.icon}</span>
            <span>{provenance.label}</span>
          </div>
        )}

        <RecurringStructuredData structuredData={message.structuredData} />
        <PolicySources sources={message.sources} />
      </div>
    </div>
  );
}

function RecurringStructuredData({ structuredData }) {
  const payments = structuredData?.recurring_payments ?? [];

  if (!payments.length) {
    return null;
  }

  return (
    <div className="mt-4 grid gap-2">
      {payments.map((payment, index) => (
        <div
          key={`${payment.description}-${index}`}
          className="rounded-xl border border-slate-200 bg-[#f8fafc] px-4 py-3"
        >
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="font-extrabold text-[#063b6f]">
              {payment.description}
            </p>

            <span className="rounded-full bg-orange-50 px-2.5 py-1 text-[11px] font-bold text-[#d9690f]">
              {payment.occurrences} occurrences
            </span>
          </div>

          <div className="mt-2 grid gap-1 text-xs leading-5 text-slate-500 sm:grid-cols-2">
            <p>
              <span className="font-bold text-slate-700">Amounts:</span>{" "}
              {payment.amounts.join(", ")}
            </p>

            <p>
              <span className="font-bold text-slate-700">Dates:</span>{" "}
              {payment.dates.join(", ")}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}

function PolicySources({ sources }) {
  if (!sources?.length) {
    return null;
  }

  return (
    <div className="mt-4 border-t border-slate-100 pt-3">
      <p className="text-xs font-extrabold text-[#063b6f]">Public sources</p>

      <ul className="mt-2 grid gap-1.5">
        {sources.map((source, index) => (
          <li key={`${source.url}-${index}`}>
            <a
              href={source.url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 text-xs font-semibold text-[#0a5fa8] underline decoration-blue-200 underline-offset-4 transition hover:text-[#f58220]"
            >
              <span className="text-[#f58220]">↗</span>
              {source.title}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}

function TransactionTable({ transactions }) {
  return (
    <section className="mt-5 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 bg-[#f8fafc] px-5 py-4 sm:px-6">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.14em] text-[#f58220]">
            Transaction evidence
          </p>

          <h3 className="mt-1 text-lg font-extrabold text-[#063b6f]">
            Parsed statement rows
          </h3>
        </div>

        <span className="rounded-full bg-blue-50 px-3 py-1.5 text-xs font-bold text-[#063b6f]">
          {transactions.length} rows
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-[#063b6f] text-white">
            <tr>
              <TableHeading>Date</TableHeading>
              <TableHeading>Description</TableHeading>
              <TableHeading align="right">Debit</TableHeading>
              <TableHeading align="right">Credit</TableHeading>
              <TableHeading align="right">Balance</TableHeading>
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-100">
            {transactions.map((transaction, index) => (
              <tr
                key={`${transaction.date}-${transaction.description}-${index}`}
                className="transition hover:bg-blue-50/50"
              >
                <td className="whitespace-nowrap px-5 py-4 font-medium text-slate-600">
                  {transaction.date}
                </td>

                <td className="min-w-[220px] px-5 py-4 font-semibold text-slate-800">
                  {transaction.description || "—"}
                </td>

                <td className="whitespace-nowrap px-5 py-4 text-right font-semibold text-slate-700">
                  {transaction.debit ?? "—"}
                </td>

                <td className="whitespace-nowrap px-5 py-4 text-right font-semibold text-slate-700">
                  {transaction.credit ?? "—"}
                </td>

                <td className="whitespace-nowrap px-5 py-4 text-right font-extrabold text-[#063b6f]">
                  {transaction.balance}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function TableHeading({ children, align = "left" }) {
  return (
    <th
      className={`whitespace-nowrap px-5 py-3.5 text-xs font-bold uppercase tracking-[0.08em] ${
        align === "right" ? "text-right" : "text-left"
      }`}
    >
      {children}
    </th>
  );
}

function StepCard({ number, title, text }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-[#f8fafc] px-3 py-3">
      <div className="flex h-6 w-6 items-center justify-center rounded-full bg-[#f58220] text-[11px] font-black text-white">
        {number}
      </div>

      <p className="mt-2 text-sm font-extrabold text-[#063b6f]">{title}</p>

      <p className="mt-0.5 text-[11px] leading-4 text-slate-500">{text}</p>
    </div>
  );
}

function CapabilityPill({ label, enabled }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[11px] font-bold ${
        enabled
          ? "bg-emerald-50 text-emerald-700"
          : "bg-slate-100 text-slate-400"
      }`}
    >
      <span>{enabled ? "✓" : "○"}</span>
      {label}
    </span>
  );
}

function PromptChip({ text, onClick, disabled }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="rounded-full border border-blue-100 bg-white px-3 py-1.5 text-left text-[11px] font-semibold text-[#063b6f] shadow-sm transition hover:border-blue-200 hover:bg-blue-50 disabled:cursor-not-allowed disabled:opacity-50"
    >
      {text}
    </button>
  );
}

function MetricCard({ label, value }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-[#f8fafc] px-4 py-3">
      <p className="text-[10px] font-bold uppercase tracking-[0.1em] text-slate-400">
        {label}
      </p>

      <p className="mt-1 text-lg font-black text-[#063b6f]">{value ?? "N/A"}</p>
    </div>
  );
}

function PrototypeNotice() {
  return (
    <section className="mt-5 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs leading-5 text-amber-950">
      <p className="font-extrabold">
        Internship prototype — not an official Allied Bank customer website.
      </p>

      <p>
        This independent student project is a synthetic-data demonstration
        created for educational and internship purposes. Do not upload real
        customer statements, credentials, or confidential information.
      </p>
    </section>
  );
}

function Footer() {
  return (
    <footer className="mt-6 border-t-4 border-[#f58220] bg-[#052f59] text-white">
      <div className="mx-auto grid max-w-7xl gap-6 px-5 py-6 sm:px-6 md:grid-cols-[1fr_auto] md:items-center">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.14em] text-blue-200">
            Allied Bank Internship Program
          </p>

          <p className="mt-1 text-sm text-blue-100/80">
            Synthetic statement data and public policy information only.
          </p>
        </div>

        <div className="developer-signature">
          <div className="developer-info">
            <span>Developed by</span>
            <strong>Daniyal Saqib</strong>
            <small>IT Intern • ABIP</small>
          </div>

          <img
            src="/daniyal-signature.png"
            alt="Daniyal Saqib signature"
            className="signature-image"
          />
        </div>
      </div>
    </footer>
  );
}

function ErrorMessage({ message, className = "mt-4" }) {
  return (
    <div
      className={`${className} flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700`}
      role="alert"
    >
      <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-red-100 text-xs font-black">
        !
      </span>

      <span>{message}</span>
    </div>
  );
}

function RichText({ text }) {
  if (!text) {
    return null;
  }

  return (
    <div className="space-y-2 text-sm leading-6">
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
            <div key={index} className="flex gap-2">
              <span className="font-black text-[#f58220]">•</span>
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

function getProvenanceMeta(method) {
  if (method === "verified_statement_intelligence") {
    return {
      icon: "✓",
      label: "Verified Statement Intelligence",
    };
  }

  if (method === "deterministic_recurring_rules") {
    return {
      icon: "✓",
      label: "Deterministic Pattern Detection",
    };
  }

  if (method === "policy_rag") {
    return {
      icon: "↗",
      label: "Grounded Public Policy",
    };
  }

  return null;
}

function generateRuntimeDemoStatement() {
  // Last three COMPLETE months use karte hain.
  // September runtime => June, July, August.
  const now = new Date();

  const monthStarts = [3, 2, 1].map((monthsBack) => {
    return new Date(now.getFullYear(), now.getMonth() - monthsBack, 1);
  });

  const randomAmount = (min, max) => {
    const value = min + Math.random() * (max - min);
    return Math.round(value * 100) / 100;
  };

  const pad = (value) => String(value).padStart(2, "0");

  const dateText = (date, day) =>
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(day)}`;

  const rows = [];
  let balance = randomAmount(65000, 95000);

  rows.push({
    date: dateText(monthStarts[0], 1),
    description: "Opening Balance",
    debit: "",
    credit: "",
    balance,
  });

  monthStarts.forEach((monthDate, index) => {
    const salary = randomAmount(85000, 120000);
    balance += salary;

    rows.push({
      date: dateText(monthDate, 2),
      description: "Salary Credit",
      debit: "",
      credit: salary,
      balance,
    });

    // Same descriptions intentionally create recurring candidates.
    const netflix = randomAmount(1400, 1800);
    balance -= netflix;
    rows.push({
      date: dateText(monthDate, 5),
      description: "Netflix",
      debit: netflix,
      credit: "",
      balance,
    });

    const internet = randomAmount(2800, 4200);
    balance -= internet;
    rows.push({
      date: dateText(monthDate, 9),
      description: "PTCL Internet Bill",
      debit: internet,
      credit: "",
      balance,
    });

    const groceries = randomAmount(4500 + index * 500, 9500 + index * 700);
    balance -= groceries;
    rows.push({
      date: dateText(monthDate, 15),
      description: "Grocery Store",
      debit: groceries,
      credit: "",
      balance,
    });

    const atm = randomAmount(3000, 9000);
    balance -= atm;
    rows.push({
      date: dateText(monthDate, 21),
      description: `ATM Withdrawal ${index + 1}`,
      debit: atm,
      credit: "",
      balance,
    });
  });

  const money = (value) => {
    if (value === "") {
      return "";
    }
    return Number(value).toFixed(2);
  };

  const csvLines = [
    "date,description,debit,credit,balance",
    ...rows.map((row) =>
      [
        row.date,
        row.description,
        money(row.debit),
        money(row.credit),
        money(row.balance),
      ].join(","),
    ),
  ];

  const stamp = new Date().toISOString().replace(/[:.]/g, "-");

  return new File([csvLines.join("\n")], `runtime_demo_${stamp}.csv`, {
    type: "text/csv",
  });
}

function extractApiError(data, fallback) {
  if (!data) {
    return fallback;
  }

  if (typeof data.detail === "string") {
    return data.detail;
  }

  if (Array.isArray(data.detail)) {
    return data.detail
      .map((item) => item?.msg)
      .filter(Boolean)
      .join(" ");
  }

  return fallback;
}

export default App;
