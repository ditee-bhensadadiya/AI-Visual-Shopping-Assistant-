import { useState } from "react";
import { BrowserRouter, NavLink, Route, Routes } from "react-router-dom";
import { useHealth } from "./hooks/useHealth";
import UploadPage from "./UploadPage";

function ApiIndicator() {
  const health = useHealth();
  const connected = health.state === "connected";
  const label = health.state === "loading"
    ? "Checking API"
    : connected
      ? "API connected"
      : "API unavailable";

  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-semibold ${
        connected
          ? "border-emerald-200 bg-emerald-50 text-emerald-800"
          : health.state === "disconnected"
            ? "border-amber-200 bg-amber-50 text-amber-900"
            : "border-stone-200 bg-white text-stone-600"
      }`}
      role="status"
    >
      <span className={`h-2 w-2 rounded-full ${connected ? "bg-emerald-500" : "bg-amber-400"}`} />
      {label}
    </span>
  );
}

function HomePage() {
  const health = useHealth();
  const [activeTab, setActiveTab] = useState<"image" | "video">("image");

  return (
    <main className="mx-auto grid w-full max-w-6xl flex-1 gap-10 px-5 py-12 sm:px-8 lg:grid-cols-[1.05fr_0.95fr] lg:items-center lg:py-20">
      <section className="max-w-xl">
        <p className="mb-5 inline-flex items-center gap-2 rounded-full bg-orange-100 px-3 py-1.5 text-xs font-bold uppercase tracking-[0.16em] text-orange-900">
          <span aria-hidden="true">✦</span> Visual discovery
        </p>
        <h1 className="text-4xl font-semibold leading-tight tracking-tight text-stone-950 sm:text-6xl">
          Find the pieces
          <span className="block font-serif font-normal italic text-emerald-800">behind the look.</span>
        </h1>
        <p className="mt-6 max-w-lg text-base leading-7 text-stone-600 sm:text-lg">
          A visual shopping assistant that will help turn inspiration into product matches and price comparisons.
        </p>
        <div className="mt-8 flex flex-wrap items-center gap-4">
          <NavLink to="/upload" className="rounded-full bg-stone-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-emerald-900 focus:outline-none focus:ring-2 focus:ring-emerald-700 focus:ring-offset-2">Upload an image</NavLink>
          <ApiIndicator />
        </div>
        {health.state === "disconnected" && (
          <p className="mt-4 max-w-md text-sm text-amber-900">
            Start the backend at <code className="rounded bg-amber-100 px-1">127.0.0.1:8000</code> to see its connection status.
          </p>
        )}
      </section>

      <section aria-label="Workflow preview" className="rounded-[2rem] border border-stone-200 bg-white p-5 shadow-[0_24px_80px_-48px_rgba(28,25,23,0.35)] sm:p-7">
        <div className="flex items-center justify-between border-b border-stone-100 pb-5">
          <div>
            <p className="text-sm font-semibold text-stone-900">A simpler way to shop</p>
            <p className="mt-1 text-xs text-stone-500">Upload an inspiration image to begin</p>
          </div>
          <span className="rounded-full bg-stone-100 px-3 py-1 text-xs font-medium text-stone-600">Phase 3</span>
        </div>

        <div className="mt-5 flex gap-2" role="tablist" aria-label="Workflow type">
          {(["image", "video"] as const).map((tab) => (
            <button
              key={tab}
              type="button"
              role="tab"
              aria-selected={activeTab === tab}
              onClick={() => setActiveTab(tab)}
              className={`rounded-full px-4 py-2 text-sm font-medium capitalize transition ${
                activeTab === tab ? "bg-emerald-900 text-white" : "bg-stone-100 text-stone-600 hover:bg-stone-200"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        <div className="mt-6 space-y-3" id="how-it-works">
          {(activeTab === "image"
            ? ["Add an image", "Identify products", "Compare offers"]
            : ["Add a video", "Sample useful frames", "Review product matches"]
          ).map((step, index) => (
            <div key={step} className="flex items-center gap-4 rounded-2xl bg-[#f7f8f4] p-4">
              <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-white text-sm font-semibold text-emerald-900 shadow-sm">
                0{index + 1}
              </span>
              <span className="text-sm font-medium text-stone-700">{step}</span>
              <span className="ml-auto text-stone-400" aria-hidden="true">↗</span>
            </div>
          ))}
        </div>
        <p className="mt-5 text-xs leading-5 text-stone-500">
          Images are stored privately. Product detection and matching arrive in later phases.
        </p>
      </section>
    </main>
  );
}

function StatusPage() {
  const health = useHealth();
  return (
    <main className="mx-auto w-full max-w-4xl flex-1 px-5 py-12 sm:px-8 sm:py-16">
      <p className="text-xs font-bold uppercase tracking-[0.16em] text-emerald-800">System status</p>
      <h1 className="mt-3 text-3xl font-semibold tracking-tight text-stone-950 sm:text-4xl">Application foundation</h1>
      <p className="mt-4 max-w-2xl leading-7 text-stone-600">
        The web app checks the FastAPI health endpoint through the Vite development proxy.
      </p>
      <div className="mt-8 rounded-3xl border border-stone-200 bg-white p-6 shadow-sm">
        <ApiIndicator />
        {health.state === "connected" && (
          <dl className="mt-6 grid gap-4 border-t border-stone-100 pt-5 sm:grid-cols-2">
            <div><dt className="text-xs uppercase tracking-wide text-stone-500">Service</dt><dd className="mt-1 font-medium text-stone-900">{health.health.service}</dd></div>
            <div><dt className="text-xs uppercase tracking-wide text-stone-500">Version</dt><dd className="mt-1 font-medium text-stone-900">{health.health.version}</dd></div>
          </dl>
        )}
        {health.state === "disconnected" && (
          <p className="mt-4 text-sm text-amber-900">{health.message}</p>
        )}
      </div>
    </main>
  );
}

function NotFoundPage() {
  return (
    <main className="mx-auto w-full max-w-4xl flex-1 px-5 py-16 sm:px-8">
      <p className="text-xs font-bold uppercase tracking-[0.16em] text-emerald-800">404</p>
      <h1 className="mt-3 text-3xl font-semibold text-stone-950">Page not found</h1>
      <p className="mt-3 text-stone-600">That page isn’t part of this application.</p>
      <NavLink className="mt-6 inline-block font-semibold text-emerald-900 underline" to="/">Return home</NavLink>
    </main>
  );
}

function AppLayout() {
  return (
    <div className="flex min-h-screen flex-col bg-[#f7f8f4]">
      <header className="border-b border-stone-200/80 bg-[#f7f8f4]/95">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-4 sm:px-8">
          <NavLink to="/" className="flex items-center gap-3" aria-label="Visual Shopping Assistant home">
            <span className="grid h-10 w-10 place-items-center rounded-2xl bg-emerald-900 text-lg text-white">V</span>
            <span className="text-sm font-semibold leading-tight text-stone-950">Visual Shopping<br />Assistant</span>
          </NavLink>
          <nav className="flex items-center gap-2 sm:gap-5" aria-label="Main navigation">
            <NavLink to="/" end className={({ isActive }) => `rounded-full px-3 py-2 text-sm font-medium ${isActive ? "text-stone-950" : "text-stone-500 hover:text-stone-900"}`}>Home</NavLink>
            <NavLink to="/upload" className={({ isActive }) => `rounded-full px-3 py-2 text-sm font-medium ${isActive ? "text-stone-950" : "text-stone-500 hover:text-stone-900"}`}>Upload</NavLink>
            <NavLink to="/status" className={({ isActive }) => `rounded-full px-3 py-2 text-sm font-medium ${isActive ? "text-stone-950" : "text-stone-500 hover:text-stone-900"}`}>Status</NavLink>
          </nav>
        </div>
      </header>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/status" element={<StatusPage />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
      <footer className="border-t border-stone-200/80 px-5 py-5 text-center text-xs text-stone-500">
        Built in phases · Visual Shopping Assistant
      </footer>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppLayout />
    </BrowserRouter>
  );
}

