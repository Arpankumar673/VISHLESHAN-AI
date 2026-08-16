function App() {
  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <section className="mx-auto flex min-h-screen max-w-6xl flex-col items-center justify-center px-6 text-center">
        <div className="mb-6 rounded-full border border-cyan-400/30 bg-cyan-400/10 px-4 py-2 text-sm text-cyan-300">
          AI-Powered Company Intelligence
        </div>

        <h1 className="text-5xl font-bold tracking-tight sm:text-6xl">
          Vishleshan AI
        </h1>

        <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-300">
          Research, verify and analyze companies using evidence-backed
          intelligence, trust analysis and recruitment risk signals.
        </p>

        <div className="mt-10 flex flex-col gap-4 sm:flex-row">
          <button
            type="button"
            className="rounded-xl bg-cyan-400 px-6 py-3 font-semibold text-slate-950 transition hover:bg-cyan-300"
          >
            Research a Company
          </button>

          <button
            type="button"
            className="rounded-xl border border-slate-700 px-6 py-3 font-semibold text-slate-200 transition hover:bg-slate-800"
          >
            Explore Reports
          </button>
        </div>
      </section>
    </main>
  );
}

export default App;