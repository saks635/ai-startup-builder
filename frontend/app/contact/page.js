import Link from "next/link";

export default function ContactPage() {
  return (
    <main className="container site-wrap">
      <header className="site-navbar fade-up">
        <div className="nav-inner">
          <Link className="brand" href="/login">
            Saksham Nilajkar
          </Link>
          <nav className="nav-links">
            <Link href="/contact">Contact</Link>
            <Link href="/dashboard">Dashboard</Link>
            <Link href="/login">App Login</Link>
          </nav>
        </div>
      </header>

      <section className="contact-layout fade-up delay-1">
        <article className="glass-card card-pad">
          <p className="eyebrow">Contact</p>
          <h1 className="title">Let&apos;s Connect</h1>
          <p className="subtitle">
            For startup collaboration, frontend improvements, or product consulting, reach out through any channel
            below.
          </p>
          <div className="contact-list">
            <p className="contact-item">
              <span>Email</span>
              <a href="mailto:sakshamnilajkar18@gmail.com">sakshamnilajkar18@gmail.com</a>
            </p>
            <p className="contact-item">
              <span>Phone</span>
              <a href="tel:+919423251087">9423251087</a>
            </p>
            <p className="contact-item">
              <span>LinkedIn</span>
              <a href="https://www.linkedin.com/in/saksham-nilajkar-090865290/" rel="noreferrer" target="_blank">
                linkedin.com/in/saksham-nilajkar-090865290
              </a>
            </p>
          </div>
          <div className="cta-row">
            <Link className="button" href="/login">
              Back to Login
            </Link>
            <Link className="button secondary" href="/dashboard">
              Open Dashboard
            </Link>
          </div>
        </article>

        <aside className="glass-card card-pad contact-side">
          <h2 className="section-title">Availability</h2>
          <p className="text-muted">
            Open to product discussions, UI revamps, and startup-focused web development work.
          </p>
          <h3 className="section-title" style={{ marginTop: "1.1rem" }}>
            Quick Notes
          </h3>
          <ul className="list">
            <li>Best for focused, high-impact UI improvements.</li>
            <li>Clean, structured layouts with strong readability.</li>
            <li>Consistent branding and professional interaction flow.</li>
          </ul>
        </aside>
      </section>
    </main>
  );
}
