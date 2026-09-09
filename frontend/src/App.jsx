import { useState } from "react";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const ABL_LOGO_URL =
  "https://upload.wikimedia.org/wikipedia/commons/f/f8/Allied_Bank_Limited_logo_%282022%29.png";

function App() {
  const [activeModule, setActiveModule] = useState("statement");

  // Statement Intelligence
  const [statementFile, setStatementFile] = useState(null);
  const [statementResult, setStatementResult] = useState(null);
  const [statementQuestion, setStatementQuestion] = useState("");
  const [statementAnswer, setStatementAnswer] = useState("");

  // Recurring Payments
  const [subscriptionFile, setSubscriptionFile] = useState(null);
  const [subscriptionResult, setSubscriptionResult] = useState(null);

  // Policy Assistant
  const [policyQuestion, setPolicyQuestion] = useState("");
  const [policyResult, setPolicyResult] = useState(null);

  // Shared loading state
  const [loading, setLoading] = useState(false);

  // Contextual error state
  const [statementUploadError, setStatementUploadError] = useState("");
  const [statementQaError, setStatementQaError] = useState("");
  const [subscriptionError, setSubscriptionError] = useState("");
  const [policyError, setPolicyError] = useState("");

  const modules = [
    {
      id: "statement",
      title: "Statement Intelligence",
      description: "Upload and analyze customer statements",
    },
    {
      id: "subscriptions",
      title: "Recurring Payments",
      description: "Detect recurring payment patterns",
    },
    {
      id: "policy",
      title: "ABL Policy Assistant",
      description: "Ask questions about public ABL policies",
    },
  ];

  // -------------------------------------------------------
  // STATEMENT ANALYSIS
  // -------------------------------------------------------

  async function analyzeStatement() {
    if (!statementFile) {
      setStatementUploadError("Please select a CSV statement first.");
      return;
    }

    setLoading(true);
    setStatementUploadError("");
    setStatementQaError("");
    setStatementResult(null);
    setStatementAnswer("");

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

      setStatementResult(data);
    } catch (err) {
      setStatementUploadError(err.message);
    } finally {
      setLoading(false);
    }
  }

  // -------------------------------------------------------
  // STATEMENT Q&A
  // -------------------------------------------------------

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

  // -------------------------------------------------------
  // RECURRING PAYMENTS
  // -------------------------------------------------------

  async function detectSubscriptions() {
    if (!subscriptionFile) {
      setSubscriptionError("Please select a CSV statement first.");
      return;
    }

    setLoading(true);
    setSubscriptionError("");
    setSubscriptionResult(null);

    try {
      const formData = new FormData();
      formData.append("file", subscriptionFile);

      const response = await fetch(`${API_BASE}/statement/subscriptions`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Could not detect recurring payments."
        );
      }

      setSubscriptionResult(data);
    } catch (err) {
      setSubscriptionError(err.message);
    } finally {
      setLoading(false);
    }
  }

  // -------------------------------------------------------
  // POLICY RAG
  // -------------------------------------------------------

  async function askPolicyQuestion() {
    if (!policyQuestion.trim()) {
      setPolicyError("Please enter a policy question.");
      return;
    }

    setLoading(true);
    setPolicyError("");
    setPolicyResult(null);

    try {
      const response = await fetch(`${API_BASE}/policy/ask`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: policyQuestion,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Could not answer policy question.");
      }

      setPolicyResult(data);
    } catch (err) {
      setPolicyError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#f4f7fb] text-slate-900">
      {/* ABL-STYLE UTILITY BAR */}
      <div className="bg-[#f58220] text-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-2 text-[11px] font-semibold tracking-[0.16em] sm:px-6">
          <span>ALLIED BANK LIMITED</span>
          <span className="hidden sm:inline">INTERNSHIP PROGRAM • AGENTIC AI</span>
        </div>
      </div>

      {/* BRAND HEADER */}
      <header className="border-b border-white/10 bg-[#063b6f] text-white shadow-[0_8px_30px_rgba(4,48,89,0.18)]">
        <div className="mx-auto max-w-7xl px-5 sm:px-6">
          <div className="flex min-h-[88px] items-center justify-between gap-5">
            <div className="flex min-w-0 items-center gap-4">
              <a
                href="https://www.abl.com/"
                target="_blank"
                rel="noreferrer"
                className="flex h-12 w-[150px] shrink-0 items-center justify-center rounded-xl bg-white px-3 py-2 shadow-sm sm:h-14 sm:w-[190px]"
                aria-label="Visit Allied Bank official website"
              >
                <img
                  src={ABL_LOGO_URL}
                  alt="Allied Bank Limited"
                  className="h-full w-full object-contain"
                />
              </a>

              <div className="min-w-0">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-blue-200">
                  Allied Bank • AI Banking
                </p>
                <h1 className="mt-1 truncate text-xl font-bold sm:text-2xl">
                  Customer Statement Intelligence Suite
                </h1>
              </div>
            </div>

            <div className="hidden shrink-0 items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm font-semibold sm:flex">
              <span className="h-2 w-2 rounded-full bg-[#f58220]" />
              Agentic AI
            </div>
          </div>
        </div>
      </header>

      {/* PRIMARY APP NAVIGATION */}
      <nav className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 shadow-sm backdrop-blur">
        <div className="mx-auto flex max-w-7xl gap-1 overflow-x-auto px-5 sm:px-6">
          {modules.map((module, index) => {
            const active = activeModule === module.id;

            return (
              <button
                key={module.id}
                onClick={() => {
                  setActiveModule(module.id);
                }}
                className={`group relative min-w-max px-4 py-4 text-left transition sm:px-5 ${
                  active
                    ? "text-[#063b6f]"
                    : "text-slate-500 hover:text-[#063b6f]"
                }`}
              >
                <div className="flex items-center gap-3">
                  <span
                    className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold ${
                      active
                        ? "bg-[#f58220] text-white"
                        : "bg-slate-100 text-slate-500 group-hover:bg-blue-50 group-hover:text-[#063b6f]"
                    }`}
                  >
                    0{index + 1}
                  </span>

                  <div>
                    <p className="text-sm font-bold">{module.title}</p>
                    <p className="hidden text-[11px] font-medium text-slate-400 md:block">
                      {module.description}
                    </p>
                  </div>
                </div>

                <span
                  className={`absolute inset-x-4 bottom-0 h-[3px] rounded-t-full transition ${
                    active ? "bg-[#f58220]" : "bg-transparent"
                  }`}
                />
              </button>
            );
          })}
        </div>
      </nav>

      <main className="mx-auto max-w-7xl px-5 py-8 sm:px-6 sm:py-10">
        {/* HERO */}
        <section className="relative overflow-hidden rounded-[28px] bg-[#063b6f] px-6 py-8 text-white shadow-[0_18px_55px_rgba(4,48,89,0.18)] sm:px-10 sm:py-10">
          <div className="pointer-events-none absolute -right-24 -top-24 h-64 w-64 rounded-full border-[44px] border-white/5" />
          <div className="pointer-events-none absolute -bottom-24 right-32 h-52 w-52 rounded-full bg-[#f58220]/10 blur-2xl" />

          <div className="relative grid items-end gap-8 lg:grid-cols-[1.4fr_0.6fr]">
            <div>
              <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-blue-300/30 bg-white/10 px-3 py-1.5 text-xs font-semibold text-blue-100">
                <span className="h-2 w-2 rounded-full bg-[#f58220]" />
                Secure synthetic-data demonstration
              </div>

              <h2 className="max-w-3xl text-3xl font-black leading-tight sm:text-4xl">
                Banking intelligence,
                <span className="text-[#ff9a3c]"> simplified.</span>
              </h2>

              <p className="mt-4 max-w-3xl text-sm leading-7 text-blue-100 sm:text-base">
                Analyze synthetic account statements, identify recurring
                payment patterns and retrieve grounded information from Allied
                Bank&apos;s public policy material — from one focused workspace.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3 lg:grid-cols-1">
              <HeroStat label="AI Modules" value="03" />
              <HeroStat label="Data Mode" value="Synthetic" />
            </div>
          </div>
        </section>


        {/* MAIN WORKSPACE */}
        <section className="mt-7 overflow-hidden rounded-[24px] border border-slate-200 bg-white shadow-[0_12px_40px_rgba(15,23,42,0.07)]">
          <div className="border-b border-slate-100 bg-gradient-to-r from-[#f8fbff] to-white px-6 py-5 sm:px-8">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.16em] text-[#f58220]">
                  Active Workspace
                </p>
                <h2 className="mt-1 text-xl font-extrabold text-[#063b6f] sm:text-2xl">
                  {modules.find((module) => module.id === activeModule)?.title}
                </h2>
              </div>

              <div className="rounded-full bg-blue-50 px-4 py-2 text-xs font-semibold text-[#063b6f]">
                ABL Intelligence Workspace
              </div>
            </div>
          </div>

          <div className="p-6 sm:p-8">
            {/* =====================================================
                STATEMENT INTELLIGENCE
            ===================================================== */}

            {activeModule === "statement" && (
              <div>
                <SectionIntro
                  eyebrow="Statement Intelligence"
                  title="Understand account activity at a glance"
                  description="Upload a synthetic CSV account statement to generate a structured summary and ask the statement agent questions grounded in the uploaded transactions."
                />

                <UploadPanel
                  file={statementFile}
                  onChange={(file) => {
                    setStatementFile(file);
                    setStatementResult(null);
                    setStatementAnswer("");
                    setStatementUploadError("");
                    setStatementQaError("");
                  }}
                  buttonText={loading ? "Processing..." : "Analyze Statement"}
                  onAction={analyzeStatement}
                  loading={loading}
                />

                {statementUploadError && (
                  <ErrorMessage message={statementUploadError} />
                )}

                {statementResult && (
                  <>
                    <div className="mt-10">
                      <div className="flex flex-wrap items-end justify-between gap-3">
                        <div>
                          <p className="text-xs font-bold uppercase tracking-[0.14em] text-[#f58220]">
                            Analysis Result
                          </p>
                          <h3 className="mt-1 text-xl font-extrabold text-[#063b6f]">
                            Statement Summary
                          </h3>
                        </div>

                        <span className="rounded-full bg-slate-100 px-3 py-1.5 text-xs font-semibold text-slate-500">
                          {statementResult.filename}
                        </span>
                      </div>
                    </div>

                    <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
                      <SummaryCard
                        label="Transactions"
                        value={statementResult.analysis.transaction_count}
                        accent="01"
                      />
                      <SummaryCard
                        label="Total Debit"
                        value={statementResult.analysis.total_debit}
                        accent="02"
                      />
                      <SummaryCard
                        label="Total Credit"
                        value={statementResult.analysis.total_credit}
                        accent="03"
                      />
                      <SummaryCard
                        label="Opening Balance"
                        value={statementResult.analysis.opening_balance}
                        accent="04"
                      />
                      <SummaryCard
                        label="Closing Balance"
                        value={statementResult.analysis.closing_balance}
                        accent="05"
                      />
                    </div>

                    <div className="mt-9 rounded-2xl border border-slate-200 bg-[#f8fafc] p-5 sm:p-6">
                      <div className="flex items-start gap-3">
                        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#063b6f] text-sm font-black text-white">
                          AI
                        </div>

                        <div>
                          <h3 className="font-extrabold text-[#063b6f]">
                            Ask about this statement
                          </h3>
                          <p className="mt-1 text-sm leading-6 text-slate-500">
                            Ask the agent a question using only the uploaded
                            statement data.
                          </p>
                        </div>
                      </div>

                      <textarea
                        value={statementQuestion}
                        onChange={(e) => {
                          setStatementQuestion(e.target.value);
                          setStatementQaError("");
                        }}
                        rows="3"
                        placeholder="Example: How much did I spend in total?"
                        className="abl-input mt-5"
                      />

                      <ActionButton
                        onClick={askStatementQuestion}
                        loading={loading}
                        text="Ask Statement Agent"
                        loadingText="Processing..."
                      />

                      {statementQaError && (
                        <ErrorMessage
                          message={statementQaError}
                          className="mt-4"
                        />
                      )}

                      {statementAnswer && (
                        <AnswerPanel title="AI Answer">
                          <RichText text={statementAnswer} />
                        </AnswerPanel>
                      )}
                    </div>
                  </>
                )}
              </div>
            )}

            {/* =====================================================
                RECURRING PAYMENTS
            ===================================================== */}

            {activeModule === "subscriptions" && (
              <div>
                <SectionIntro
                  eyebrow="Recurring Payments"
                  title="Spot repeated outgoing payment patterns"
                  description="Upload a synthetic statement to identify repeated merchant descriptions and recurring-payment candidates."
                />

                <UploadPanel
                  file={subscriptionFile}
                  onChange={(file) => {
                    setSubscriptionFile(file);
                    setSubscriptionResult(null);
                    setSubscriptionError("");
                  }}
                  buttonText={
                    loading ? "Processing..." : "Detect Recurring Payments"
                  }
                  onAction={detectSubscriptions}
                  loading={loading}
                />

                {subscriptionError && (
                  <ErrorMessage message={subscriptionError} />
                )}

                {subscriptionResult && (
                  <div className="mt-10">
                    <div className="flex flex-wrap items-end justify-between gap-4">
                      <div>
                        <p className="text-xs font-bold uppercase tracking-[0.14em] text-[#f58220]">
                          Pattern Detection
                        </p>
                        <h3 className="mt-1 text-xl font-extrabold text-[#063b6f]">
                          Recurring Payment Candidates
                        </h3>
                      </div>

                      <div className="rounded-xl bg-[#063b6f] px-4 py-3 text-white shadow-sm">
                        <span className="text-xs text-blue-200">Candidates</span>
                        <span className="ml-3 text-xl font-black">
                          {subscriptionResult.recurring_payment_count}
                        </span>
                      </div>
                    </div>

                    {subscriptionResult.recurring_payments.length === 0 ? (
                      <div className="mt-5 rounded-2xl border border-slate-200 bg-slate-50 p-5 text-sm text-slate-600">
                        No recurring payment candidates were detected.
                      </div>
                    ) : (
                      <div className="mt-5 grid gap-4">
                        {subscriptionResult.recurring_payments.map(
                          (payment, index) => (
                            <div
                              key={index}
                              className="group rounded-2xl border border-slate-200 bg-white p-5 transition hover:border-blue-200 hover:shadow-md"
                            >
                              <div className="flex flex-wrap items-center justify-between gap-3">
                                <div className="flex items-center gap-3">
                                  <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 text-sm font-black text-[#063b6f]">
                                    {String(index + 1).padStart(2, "0")}
                                  </span>
                                  <h4 className="font-extrabold text-slate-900">
                                    {payment.description}
                                  </h4>
                                </div>

                                <span className="rounded-full bg-orange-50 px-3 py-1.5 text-xs font-bold text-[#d9690f]">
                                  {payment.occurrences} occurrences
                                </span>
                              </div>

                              <div className="mt-4 grid gap-3 text-sm text-slate-600 sm:grid-cols-2">
                                <p className="rounded-xl bg-slate-50 px-4 py-3">
                                  <span className="font-bold text-slate-800">
                                    Amounts:
                                  </span>{" "}
                                  {payment.amounts.join(", ")}
                                </p>

                                <p className="rounded-xl bg-slate-50 px-4 py-3">
                                  <span className="font-bold text-slate-800">
                                    Dates:
                                  </span>{" "}
                                  {payment.dates.join(", ")}
                                </p>
                              </div>
                            </div>
                          )
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* =====================================================
                POLICY RAG ASSISTANT
            ===================================================== */}

            {activeModule === "policy" && (
              <div>
                <SectionIntro
                  eyebrow="Public Policy RAG"
                  title="Ask Allied Bank policy questions with sources"
                  description="Retrieve grounded answers from the available public Allied Bank policy knowledge base. Source references are returned with relevant answers."
                />

                <div className="mt-7 rounded-2xl border border-slate-200 bg-[#f8fafc] p-5 sm:p-6">
                  <label className="text-sm font-extrabold text-[#063b6f]">
                    Your Question
                  </label>

                  <textarea
                    value={policyQuestion}
                    onChange={(e) => {
                      setPolicyQuestion(e.target.value);
                      setPolicyError("");
                    }}
                    rows="5"
                    placeholder="Example: What documents are required to claim an unclaimed deposit?"
                    className="abl-input mt-3"
                  />

                  <ActionButton
                    onClick={askPolicyQuestion}
                    loading={loading}
                    text="Ask Policy Assistant"
                    loadingText="Searching..."
                  />

                  {policyError && (
                    <ErrorMessage
                      message={policyError}
                      className="mt-4"
                    />
                  )}
                </div>

                {policyResult && (
                  <AnswerPanel title="Policy Answer" className="mt-6">
                    <RichText text={policyResult.answer} />

                    {policyResult.sources?.length > 0 && (
                      <div className="mt-6 border-t border-blue-100 pt-5">
                        <p className="text-sm font-extrabold text-[#063b6f]">
                          Sources
                        </p>

                        <ul className="mt-3 grid gap-2">
                          {policyResult.sources.map((source, index) => (
                            <li key={index}>
                              <a
                                href={source.url}
                                target="_blank"
                                rel="noreferrer"
                                className="inline-flex items-center gap-2 rounded-lg text-sm font-semibold text-[#0a5fa8] underline decoration-blue-200 underline-offset-4 transition hover:text-[#f58220]"
                              >
                                <span className="text-[#f58220]">↗</span>
                                {source.title}
                              </a>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </AnswerPanel>
                )}
              </div>
            )}
          </div>
        </section>

        {/* INFORMATION STRIP */}
        <section className="mt-7 grid gap-4 md:grid-cols-3">
          <InfoCard
            number="01"
            title="Synthetic Data"
            text="Statement analysis is designed for synthetic/local demonstration data."
          />
          <InfoCard
            number="02"
            title="Grounded Policy Q&A"
            text="Policy answers are based on retrieved public Allied Bank material."
          />
          <InfoCard
            number="03"
            title="AI-Assisted"
            text="The suite combines structured analysis, semantic retrieval and generative AI."
          />
        </section>
      </main>

      {/* FOOTER + PERSONAL SIGNATURE */}
      <footer className="mt-8 border-t-4 border-[#f58220] bg-[#052f59] text-white">
        <div className="mx-auto grid max-w-7xl gap-8 px-5 py-8 sm:px-6 md:grid-cols-[1fr_auto] md:items-center">
          <div>
            <p className="text-sm font-bold uppercase tracking-[0.14em] text-blue-200">
              Allied Bank Internship Program
            </p>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-blue-100/80">
              Customer Statement Intelligence Suite • Synthetic statement data
              and public policy information only.
            </p>
            <p className="mt-3 text-xs text-blue-200/70">
              Demonstration application — not connected to live customer
              banking systems.
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
    </div>
  );
}

function SectionIntro({ eyebrow, title, description }) {
  return (
    <div className="max-w-3xl">
      <p className="text-xs font-bold uppercase tracking-[0.16em] text-[#f58220]">
        {eyebrow}
      </p>
      <h3 className="mt-2 text-2xl font-black tracking-tight text-[#063b6f] sm:text-3xl">
        {title}
      </h3>
      <p className="mt-3 text-sm leading-7 text-slate-600 sm:text-base">
        {description}
      </p>
    </div>
  );
}

function UploadPanel({ file, onChange, buttonText, onAction, loading }) {
  return (
    <div className="mt-7 rounded-2xl border-2 border-dashed border-blue-200 bg-[#f8fbff] p-7 text-center transition hover:border-[#0a5fa8] sm:p-9">
      <label className="inline-flex cursor-pointer flex-col items-center gap-3">
        <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white text-xl font-black text-[#063b6f] shadow-sm ring-1 ring-slate-200">
          CSV
        </span>

        <span className="font-extrabold text-[#063b6f]">
          Choose statement file
        </span>

        <span className="text-xs text-slate-500">
          Synthetic CSV statements only
        </span>

        <input
          type="file"
          accept=".csv"
          onChange={(e) => onChange(e.target.files[0])}
          className="hidden"
        />

        <span className="mt-1 rounded-full bg-white px-3 py-1.5 text-xs font-semibold text-slate-500 shadow-sm ring-1 ring-slate-200">
          {file ? file.name : "No file selected"}
        </span>
      </label>

      <div>
        <ActionButton
          onClick={onAction}
          loading={loading}
          text={buttonText}
          loadingText={buttonText}
          className="mt-5"
        />
      </div>
    </div>
  );
}

function ActionButton({
  onClick,
  loading,
  text,
  loadingText,
  className = "mt-4",
}) {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      className={`${className} inline-flex items-center justify-center gap-2 rounded-xl bg-[#f58220] px-6 py-3 text-sm font-extrabold text-white shadow-[0_8px_20px_rgba(245,130,32,0.24)] transition hover:-translate-y-0.5 hover:bg-[#df7117] hover:shadow-[0_10px_24px_rgba(245,130,32,0.3)] disabled:cursor-not-allowed disabled:opacity-50`}
    >
      {loading ? loadingText : text}
      {!loading && <span aria-hidden="true">→</span>}
    </button>
  );
}

function ErrorMessage({ message, className = "mt-5" }) {
  return (
    <div
      className={`${className} flex items-start gap-3 rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700 shadow-sm`}
      role="alert"
    >
      <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-red-100 font-bold">
        !
      </span>
      <span>{message}</span>
    </div>
  );
}


function AnswerPanel({ title, children, className = "mt-5" }) {
  return (
    <div
      className={`${className} overflow-hidden rounded-2xl border border-blue-100 bg-[#f3f8fd] shadow-sm`}
    >
      <div className="flex items-center gap-3 border-b border-blue-100 bg-white/60 px-5 py-4">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#063b6f] text-xs font-black text-white">
          AI
        </span>
        <p className="font-extrabold text-[#063b6f]">{title}</p>
      </div>

      <div className="p-5 text-sm leading-7 text-slate-700 sm:p-6">
        {children}
      </div>
    </div>
  );
}

function HeroStat({ label, value }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/10 px-5 py-4 backdrop-blur-sm">
      <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-blue-200">
        {label}
      </p>
      <p className="mt-1 text-xl font-black text-white">{value}</p>
    </div>
  );
}

function InfoCard({ number, title, text }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start gap-4">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-orange-50 text-xs font-black text-[#f58220]">
          {number}
        </span>
        <div>
          <h4 className="font-extrabold text-[#063b6f]">{title}</h4>
          <p className="mt-1 text-sm leading-6 text-slate-500">{text}</p>
        </div>
      </div>
    </div>
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
        {value ?? "N/A"}
      </p>

      <div className="mt-4 h-1 w-10 rounded-full bg-[#f58220]" />
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

export default App;
