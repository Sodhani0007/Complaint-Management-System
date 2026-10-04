import { useEffect, useState } from "react";
import { enterDemo, extractErrorMessage, getAuthConfig, login, logout, setSessionToken } from "./api/client";
import type { Session } from "./api/client";
import { useAppDispatch } from "./hooks/reduxHooks";
import { ComplaintIntakePage } from "./pages/ComplaintIntakePage";
import { ComplaintInbox } from "./pages/ComplaintInbox";
import { resetForm } from "./store/slices/complaintSlice";
import { resetExtraction } from "./store/slices/extractionSlice";
import "./styles/demo.css";

function App() {
  const dispatch = useAppDispatch();
  const [session, setSession] = useState<Session | null>(null);
  const [config, setConfig] = useState<{ demo_enabled: boolean; live_ai_enabled: boolean } | null>(null);
  const [busy, setBusy] = useState(false);
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [tab, setTab] = useState<"intake" | "inbox">("intake");

  const clearSession = () => {
    setSessionToken(null); setSession(null);
    dispatch(resetForm()); dispatch(resetExtraction()); setTab("intake");
  };
  useEffect(() => {
    const expire = () => { clearSession(); setError("Your session ended. Please sign in again."); };
    window.addEventListener("session-expired", expire);
    const timer = session ? window.setTimeout(expire, session.expires_in * 1000) : undefined;
    return () => { window.removeEventListener("session-expired", expire); window.clearTimeout(timer); };
  }, [session]);
  const checkServer = async () => {
    setChecking(true); setError("");
    try { setConfig(await getAuthConfig()); }
    catch (err) { setError(extractErrorMessage(err)); }
    finally { setChecking(false); }
  };
  useEffect(() => { void checkServer(); }, []);
  const signIn = async (demo: boolean) => {
    setBusy(true); setError("");
    try {
      const result = demo ? await enterDemo() : await login(email, password);
      setSessionToken(result.access_token); setSession(result); setPassword("");
    } catch (err) { setError(extractErrorMessage(err)); }
    finally { setBusy(false); }
  };

  if (!session) return (
    <main className="demo-landing">
      <div className="demo-brand">COMPLAINT DESK <span>ENGINEERING DEMO</span></div>
      <div className="demo-hero">
        <section>
          <p className="demo-eyebrow">AI-ASSISTED QUALITY OPERATIONS</p>
          <h1>Every complaint deserves a clear next step.</h1>
          <p className="demo-intro">Turn unstructured reports into reviewed, structured records.
            Extract the details, check the assessment, and keep a record of your decision.</p>
          <ol className="demo-steps">
            <li><strong>Capture</strong><span>Upload a document or start with a synthetic sample.</span></li>
            <li><strong>Review</strong><span>Check and correct every field before saving.</span></li>
            <li><strong>Explore</strong><span>Reopen saved complaints and see repeat-batch escalation.</span></li>
          </ol>
          <a href="https://github.com/Sodhani0007/Complaint-Management-System" target="_blank" rel="noreferrer">
            Explore the source code ↗
          </a>
        </section>
        <section className="demo-login" aria-label="Sign in">
          <h2>Try the shared demo</h2>
          <p>Use synthetic information only. Saved complaints are visible to everyone using this demo.</p>
          {checking && <p role="status">Starting demo server… Free hosting can take about a minute to wake.</p>}
          {!checking && !config && <button onClick={checkServer}>Retry connection</button>}
          {config?.demo_enabled && <button className="demo-primary" disabled={busy} onClick={() => signIn(true)}>
            {busy ? "Signing in…" : "Enter demo"}
          </button>}
          {config && !config.demo_enabled && <p>Public demo access is disabled. Sign in with your owner account.</p>}
          <details>
            <summary>Owner sign-in</summary>
            <form onSubmit={(event) => { event.preventDefault(); void signIn(false); }}>
              <label>Email<input type="email" required autoComplete="username" value={email}
                onChange={(event) => setEmail(event.target.value)} /></label>
              <label>Password<input type="password" required autoComplete="current-password" value={password}
                onChange={(event) => setPassword(event.target.value)} /></label>
              <button type="submit" disabled={busy || checking}>Sign in</button>
            </form>
          </details>
          {error && <p className="demo-error" role="alert">{error}</p>}
          <p className="demo-footnote">Sessions expire after one hour with the default configuration.
            Refreshing the page signs you out. This portfolio demo is not a validated clinical or regulatory system.</p>
        </section>
      </div>
    </main>
  );

  return <>
    <header className="demo-header">
      <strong>Complaint Desk</strong>
      <nav aria-label="Main navigation">
        <button aria-current={tab === "intake" ? "page" : undefined} onClick={() => setTab("intake")}>New complaint</button>
        <button aria-current={tab === "inbox" ? "page" : undefined} onClick={() => setTab("inbox")}>Saved complaints</button>
        <button disabled={busy} onClick={async () => {
          setBusy(true);
          try { await logout(); clearSession(); }
          catch (err) { setError(extractErrorMessage(err)); }
          finally { setBusy(false); }
        }}>Sign out</button>
      </nav>
    </header>
    {config?.demo_enabled && <p className="demo-notice">Shared demo · Synthetic data only · Daily usage is limited.
      {!config.live_ai_enabled && " Live AI is unavailable; use Load synthetic sample or fill in the form."}</p>}
    {error && <p className="demo-error" role="alert">{error}</p>}
    {tab === "intake" ? <ComplaintIntakePage /> : <ComplaintInbox />}
  </>;
}

export default App;
