import { useState } from "react";

const API_BASE = "http://127.0.0.1:8000";

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

  // Shared UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

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
      setError("Please select a CSV statement first.");
      return;
    }

    setLoading(true);
    setError("");
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
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  // -------------------------------------------------------
  // STATEMENT Q&A
  // -------------------------------------------------------

  async function askStatementQuestion() {
    if (!statementResult) {
      setError("Analyze a statement before asking questions.");
      return;
    }

    if (!statementQuestion.trim()) {
      setError("Please enter a statement question.");
      return;
    }

    setLoading(true);
    setError("");
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
        throw new Error(
          data.detail || "Could not answer statement question."
        );
      }

      setStatementAnswer(data.answer);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  // -------------------------------------------------------
  // RECURRING PAYMENTS
  // -------------------------------------------------------

  async function detectSubscriptions() {
    if (!subscriptionFile) {
      setError("Please select a CSV statement first.");
      return;
    }

    setLoading(true);
    setError("");
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
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  // -------------------------------------------------------
  // POLICY RAG
  // -------------------------------------------------------

  async function askPolicyQuestion() {
    if (!policyQuestion.trim()) {
      setError("Please enter a policy question.");
      return;
    }

    setLoading(true);
    setError("");
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
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      {/* HEADER */}
      <header className="bg-emerald-800 text-white shadow-lg">
        <div className="mx-auto max-w-7xl px-6 py-5">
          <div className="flex items-center justify-between gap-6">
            <div>
              <p className="text-sm font-semibold tracking-widest text-emerald-200">
                ALLIED BANK LIMITED
              </p>

              <h1 className="mt-1 text-2xl font-bold">
                Customer Statement Intelligence Suite
              </h1>
            </div>

            <div className="shrink-0 rounded-full bg-emerald-700 px-4 py-2 text-sm">
              Agentic AI
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-10">
        {/* INTRODUCTION */}
        <section className="mb-8">
          <h2 className="text-3xl font-bold">AI Banking Intelligence</h2>

          <p className="mt-2 max-w-3xl text-slate-600">
            Analyze synthetic account statements, identify recurring
            transactions and retrieve information from Allied Bank&apos;s
            public policy documents.
          </p>
        </section>

        {/* MODULE SELECTOR */}
        <section className="grid gap-5 md:grid-cols-3">
          {modules.map((module) => (
            <button
              key={module.id}
              onClick={() => {
                setActiveModule(module.id);
                setError("");
              }}
              className={`rounded-xl border p-6 text-left shadow-sm transition hover:-translate-y-1 hover:shadow-md ${
                activeModule === module.id
                  ? "border-emerald-600 bg-emerald-50"
                  : "border-slate-200 bg-white"
              }`}
            >
              <h3 className="text-lg font-bold">{module.title}</h3>

              <p className="mt-2 text-sm text-slate-600">
                {module.description}
              </p>
            </button>
          ))}
        </section>

        {/* ERROR MESSAGE */}
        {error && (
          <div className="mt-6 rounded-lg border border-red-200 bg-red-50 p-4 text-red-700">
            {error}
          </div>
        )}

        {/* MAIN WORKSPACE */}
        <section className="mt-8 rounded-xl border border-slate-200 bg-white p-8 shadow-sm">
          {/* =====================================================
              STATEMENT INTELLIGENCE
          ===================================================== */}

          {activeModule === "statement" && (
            <div>
              <h2 className="text-2xl font-bold">
                Statement Intelligence
              </h2>

              <p className="mt-2 text-slate-600">
                Upload a synthetic CSV account statement to analyze
                transactions and ask questions about the statement.
              </p>

              {/* Custom file selector */}
              <div className="mt-6 rounded-lg border-2 border-dashed border-slate-300 p-10 text-center">
                <label className="inline-flex cursor-pointer flex-col items-center gap-3">
                  <span className="rounded-lg bg-slate-100 px-6 py-3 font-semibold text-slate-700 transition hover:bg-slate-200">
                    Choose CSV File
                  </span>

                  <input
                    type="file"
                    accept=".csv"
                    onChange={(e) => {
                      setStatementFile(e.target.files[0]);
                      setStatementResult(null);
                      setStatementAnswer("");
                      setError("");
                    }}
                    className="hidden"
                  />

                  <span className="text-sm text-slate-500">
                    {statementFile
                      ? statementFile.name
                      : "No file selected"}
                  </span>
                </label>

                <div>
                  <button
                    onClick={analyzeStatement}
                    disabled={loading}
                    className="mt-5 rounded-lg bg-emerald-700 px-6 py-3 font-semibold text-white transition hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {loading ? "Processing..." : "Analyze Statement"}
                  </button>
                </div>
              </div>

              {/* Statement summary */}
              {statementResult && (
                <>
                  <div className="mt-8">
                    <h3 className="text-lg font-bold">
                      Statement Summary
                    </h3>

                    <p className="mt-1 text-sm text-slate-500">
                      {statementResult.filename}
                    </p>
                  </div>

                  <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
                    <SummaryCard
                      label="Transactions"
                      value={statementResult.analysis.transaction_count}
                    />

                    <SummaryCard
                      label="Total Debit"
                      value={statementResult.analysis.total_debit}
                    />

                    <SummaryCard
                      label="Total Credit"
                      value={statementResult.analysis.total_credit}
                    />

                    <SummaryCard
                      label="Opening Balance"
                      value={statementResult.analysis.opening_balance}
                    />

                    <SummaryCard
                      label="Closing Balance"
                      value={statementResult.analysis.closing_balance}
                    />
                  </div>

                  {/* Statement Q&A */}
                  <div className="mt-8 border-t border-slate-200 pt-8">
                    <h3 className="text-lg font-bold">
                      Ask about this statement
                    </h3>

                    <p className="mt-1 text-sm text-slate-500">
                      Ask the AI agent a question using the uploaded
                      statement data.
                    </p>

                    <textarea
                      value={statementQuestion}
                      onChange={(e) =>
                        setStatementQuestion(e.target.value)
                      }
                      rows="3"
                      placeholder="Example: How much did I spend in total?"
                      className="mt-4 w-full rounded-lg border border-slate-300 p-4 outline-none focus:border-emerald-600"
                    />

                    <button
                      onClick={askStatementQuestion}
                      disabled={loading}
                      className="mt-3 rounded-lg bg-emerald-700 px-6 py-3 font-semibold text-white transition hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {loading
                        ? "Processing..."
                        : "Ask Statement Agent"}
                    </button>

                    {statementAnswer && (
                      <div className="mt-5 rounded-lg border border-emerald-100 bg-emerald-50 p-5">
                        <p className="font-semibold text-emerald-900">
                          AI Answer
                        </p>

                        <p className="mt-2 whitespace-pre-line text-slate-700">
                          {statementAnswer}
                        </p>
                      </div>
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
              <h2 className="text-2xl font-bold">
                Recurring Payment Analysis
              </h2>

              <p className="mt-2 text-slate-600">
                Upload a synthetic statement to identify repeated
                outgoing payment patterns.
              </p>

              {/* Custom file selector */}
              <div className="mt-6 rounded-lg border-2 border-dashed border-slate-300 p-10 text-center">
                <label className="inline-flex cursor-pointer flex-col items-center gap-3">
                  <span className="rounded-lg bg-slate-100 px-6 py-3 font-semibold text-slate-700 transition hover:bg-slate-200">
                    Choose CSV File
                  </span>

                  <input
                    type="file"
                    accept=".csv"
                    onChange={(e) => {
                      setSubscriptionFile(e.target.files[0]);
                      setSubscriptionResult(null);
                      setError("");
                    }}
                    className="hidden"
                  />

                  <span className="text-sm text-slate-500">
                    {subscriptionFile
                      ? subscriptionFile.name
                      : "No file selected"}
                  </span>
                </label>

                <div>
                  <button
                    onClick={detectSubscriptions}
                    disabled={loading}
                    className="mt-5 rounded-lg bg-emerald-700 px-6 py-3 font-semibold text-white transition hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {loading
                      ? "Processing..."
                      : "Detect Recurring Payments"}
                  </button>
                </div>
              </div>

              {/* Recurring payment results */}
              {subscriptionResult && (
                <div className="mt-8">
                  <h3 className="text-lg font-bold">
                    Recurring Payment Candidates
                  </h3>

                  <p className="mt-1 text-slate-600">
                    Found{" "}
                    <span className="font-semibold">
                      {subscriptionResult.recurring_payment_count}
                    </span>{" "}
                    recurring payment candidates.
                  </p>

                  {subscriptionResult.recurring_payments.length === 0 ? (
                    <div className="mt-5 rounded-lg bg-slate-100 p-5 text-slate-600">
                      No recurring payment candidates were detected.
                    </div>
                  ) : (
                    <div className="mt-5 grid gap-4">
                      {subscriptionResult.recurring_payments.map(
                        (payment, index) => (
                          <div
                            key={index}
                            className="rounded-lg border border-slate-200 bg-slate-50 p-5"
                          >
                            <div className="flex flex-wrap items-center justify-between gap-3">
                              <h4 className="font-bold">
                                {payment.description}
                              </h4>

                              <span className="rounded-full bg-emerald-100 px-3 py-1 text-sm font-semibold text-emerald-800">
                                {payment.occurrences} occurrences
                              </span>
                            </div>

                            <p className="mt-3 text-sm text-slate-600">
                              <span className="font-semibold">
                                Amounts:
                              </span>{" "}
                              {payment.amounts.join(", ")}
                            </p>

                            <p className="mt-1 text-sm text-slate-600">
                              <span className="font-semibold">
                                Dates:
                              </span>{" "}
                              {payment.dates.join(", ")}
                            </p>
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
              <h2 className="text-2xl font-bold">
                ABL Policy Assistant
              </h2>

              <p className="mt-2 text-slate-600">
                Ask questions using the available public Allied Bank
                policy knowledge base.
              </p>

              <div className="mt-6">
                <label className="font-semibold text-slate-700">
                  Your Question
                </label>

                <textarea
                  value={policyQuestion}
                  onChange={(e) => {
                    setPolicyQuestion(e.target.value);
                    setError("");
                  }}
                  rows="5"
                  placeholder="Example: What documents are required to claim an unclaimed deposit?"
                  className="mt-2 w-full rounded-lg border border-slate-300 p-4 outline-none focus:border-emerald-600"
                />

                <button
                  onClick={askPolicyQuestion}
                  disabled={loading}
                  className="mt-4 rounded-lg bg-emerald-700 px-6 py-3 font-semibold text-white transition hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {loading
                    ? "Searching..."
                    : "Ask Policy Assistant"}
                </button>
              </div>

              {/* Policy answer */}
              {policyResult && (
                <div className="mt-6 rounded-lg border border-emerald-100 bg-emerald-50 p-6">
                  <p className="font-semibold text-emerald-900">
                    Policy Answer
                  </p>

                  <p className="mt-3 whitespace-pre-line leading-7 text-slate-700">
                    {policyResult.answer}
                  </p>

                  {policyResult.sources?.length > 0 && (
                    <div className="mt-6 border-t border-emerald-200 pt-4">
                      <p className="font-semibold text-slate-800">
                        Sources
                      </p>

                      <ul className="mt-3 space-y-2">
                        {policyResult.sources.map((source, index) => (
                          <li key={index}>
                            <a
                              href={source.url}
                              target="_blank"
                              rel="noreferrer"
                              className="font-medium text-emerald-700 underline hover:text-emerald-900"
                            >
                              {source.title}
                            </a>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </section>

        {/* FOOTER */}
        <footer className="mt-10 border-t border-slate-200 py-6 text-sm text-slate-500">
          Developed for the Allied Bank Internship Program • Synthetic
          statement data and public policy information only
        </footer>
      </main>
    </div>
  );
}

function SummaryCard({ label, value }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
      <p className="text-sm text-slate-500">{label}</p>

      <p className="mt-1 break-words text-xl font-bold">
        {value ?? "N/A"}
      </p>
    </div>
  );
}

export default App;