import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from './context/AuthContext';

import personBankFirst from './assets/person_bank_first.png';
import personWorkSmarter from './assets/person_work_smarter.png';
import personNoHassle from './assets/person_no_hassle.png';
import flexicardRender from './assets/flexicard_render.png';
import heroPromoAiyah from './assets/hero_promo_aiyah.png';

/* ========================================
   GXS Bank Clone — Main App Component
   ======================================== */

// Intersection Observer hook for scroll animations
function useInView(options = {}) {
  const ref = useRef(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
        }
      },
      { threshold: 0.15, ...options }
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  return [ref, isVisible];
}

// ======= HEADER =======
function Header() {
  const [scrolled, setScrolled] = useState(false);
  let authState = { isAuthenticated: false, isEmployee: false };
  try { authState = useAuth(); } catch(e) {}
  const { isAuthenticated, isEmployee } = authState;

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 50);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <header className="header" style={scrolled ? { background: 'rgba(12,6,23,0.97)' } : {}}>
      <div className="header-inner">
        <Link to="/" className="logo" id="gxs-logo">
          <span className="logo-g">G</span>
          <span className="logo-x" style={{ fontSize: '22px' }}>x</span>
          <span className="logo-s">S</span>
        </Link>
        <nav>
          <ul className="nav-links">
            <li><a href="#" className="nav-link" id="nav-home">Home</a></li>
            <li><a href="#savings" className="nav-link" id="nav-account">Account</a></li>
            <li><a href="#flexicard" className="nav-link" id="nav-cards">Cards</a></li>
            <li><a href="#flexiloan" className="nav-link" id="nav-loans">Loans</a></li>
            <li><a href="#" className="nav-link" id="nav-invest">Invest</a></li>
            <li><a href="#" className="nav-link" id="nav-help">Help Centre</a></li>
            <li><a href="#" className="nav-link" id="nav-betterzine">Betterzine</a></li>
            <li><a href="#" className="nav-link" id="nav-business">Business Banking</a></li>
          </ul>
        </nav>
        {isAuthenticated ? (
          <Link to={isEmployee ? '/employee/dashboard' : '/dashboard'} className="btn-download-nav" id="btn-dashboard-header">Dashboard</Link>
        ) : (
          <Link to="/login" className="btn-download-nav" id="btn-login-header">Log In</Link>
        )}
      </div>
      <div className="gradient-line" />
    </header>
  );
}

// ======= HERO =======
function HeroSection() {
  const [ref, visible] = useInView();

  return (
    <section className="hero-section" id="hero">
      <div className="hero-inner" ref={ref}>
        <div className={`hero-content ${visible ? 'fade-in-left visible' : 'fade-in-left'}`}>
          <h1>For the <em>aiyah</em><br />moments in life</h1>
          <p>
            Plot twist, no problem! Get fast cash at our lowest rates from 1.08% p.a.
            (EIR 2.02% p.a.), with no fees and interest rebate of 1.8% in cashback.
          </p>
          <p style={{ fontSize: '15px', color: '#b8a9cc', marginBottom: '32px' }}>
            Sign up for a GXS FlexiLoan account, take an Instalment Loan of min. S$10,000
            and name your loan "AIYAH" to be eligible.
          </p>
          <button className="btn-primary" id="btn-hero-apply">Apply now</button>
          <div className="hero-promo-tag" style={{ marginTop: '24px' }}>
            For promotion terms & conditions, visit here.
          </div>
          <p style={{ fontSize: '12px', color: 'rgba(184,169,204,0.6)', lineHeight: 1.5 }}>
            Offer is valid from 19 January to 31 March 2026. Min. loan tenure of 12 months required.
            Ensure you have a GXS Savings Account open by 31 March 2026 to receive your cashback.
          </p>
        </div>
        <div className={`hero-image-container ${visible ? 'fade-in-right visible' : 'fade-in-right'}`}>
          <img src={heroPromoAiyah} alt="GXS FlexiLoan Aiyah Promotion" className="hero-image" />
          <div className="hero-rate-badge">
            <span className="label">From</span>
            <div className="rate">1.08% p.a.</div>
            <span className="subrate">(EIR 2.02% p.a.)</span>
          </div>
        </div>
      </div>
    </section>
  );
}

// ======= VALUES SECTION =======
function ValuesSection() {
  const [ref, visible] = useInView();

  const values = [
    {
      image: personBankFirst,
      title: 'A bank\nthat puts\nyou first.',
      desc: 'We make the good stuff like credit, interest & rewards accessible to everyone, and take away the fees.',
    },
    {
      image: personWorkSmarter,
      title: 'Work\nsmarter.\nNot harder.',
      desc: 'We use technology to create smart solutions that help you do more with your money. And keep it secure.',
    },
    {
      image: personNoHassle,
      title: 'No Queues.\nNo Branches.\nNo Hassle.',
      desc: 'Get all your banking done in just a few taps.',
    },
  ];

  return (
    <section className="values-section" id="values">
      <div className="values-inner" ref={ref}>
        {values.map((val, i) => (
          <div
            key={i}
            className={`value-card ${visible ? 'fade-in visible' : 'fade-in'}`}
            style={{ transitionDelay: `${i * 0.2}s` }}
          >
            <div className="value-image-container">
              <img src={val.image} alt={val.title} className="value-image" />
            </div>
            <h3 style={{ whiteSpace: 'pre-line' }}>{val.title}</h3>
            <p>{val.desc}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

// ======= BETTER SECTION =======
function BetterSection() {
  const labels = ['UX', 'service', 'security', 'savings', 'rewards', 'payments', 'interest', 'insights', 'control', 'banking'];
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setIndex((prev) => (prev + 1) % labels.length);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <section className="better-section" id="better">
      <div className="better-inner">
        <div className="better-word">
          better
          <span className="better-label" key={index}>
            {labels[index]}
          </span>
        </div>
      </div>
    </section>
  );
}

// ======= SAVINGS SECTION =======
function SavingsSection() {
  const [ref, visible] = useInView();

  return (
    <section className="savings-section" id="savings">
      <div className="savings-inner" ref={ref}>
        <div className={visible ? 'fade-in visible' : 'fade-in'}>
          <span className="section-badge">GXS Savings Account</span>
          <h2>Daily interest.<br />Daily rewards.</h2>
          <p>
            See your money grow with daily interest credited to your account
            and track your transactions in one place with GXS Savings Account.
          </p>
          <button className="btn-outline" id="btn-savings">GXS Savings Account</button>
        </div>
      </div>
    </section>
  );
}

// ======= FLEXICARD SECTION =======
function FlexiCardSection() {
  const [ref, visible] = useInView();

  return (
    <section className="flexicard-section" id="flexicard">
      <div className="flexicard-inner" ref={ref}>
        <div className={`flexicard-content ${visible ? 'fade-in-left visible' : 'fade-in-left'}`}>
          <span className="section-badge">GXS FlexiCard</span>
          <h2>The starter<br />credit card.</h2>
          <p>
            A no-interest credit card with unlimited instant rewards
            and no minimum income requirement.
          </p>
          <button className="btn-outline" id="btn-flexicard">GXS FlexiCard</button>
          <p className="note">Please ensure you have the latest version of the GXS Bank app.</p>
        </div>
        <div className={`flexicard-image-container ${visible ? 'fade-in-right visible' : 'fade-in-right'}`}>
          <img src={flexicardRender} alt="GXS FlexiCard" className="flexicard-image" />
        </div>
      </div>
    </section>
  );
}

// ======= FLEXILOAN SECTION =======
function FlexiLoanSection() {
  const [ref, visible] = useInView();

  return (
    <section className="flexiloan-section" id="flexiloan">
      <div className="flexiloan-inner" ref={ref}>
        <div className={`flexiloan-content ${visible ? 'fade-in-left visible' : 'fade-in-left'}`}>
          <span className="section-badge">Loans</span>
          <h2>Instant cash<br />with GXS<br />FlexiLoan.</h2>
          <p>
            Get an instant cash boost with GXS FlexiLoan. Enjoy 0% interest rate with
            Balance transfer or no additional fees with our Instalment loan.
          </p>
          <button className="btn-outline" id="btn-flexiloan">GXS FlexiLoan</button>
        </div>
        <div className={`flex-text-container ${visible ? 'fade-in-right visible' : 'fade-in-right'}`}>
          <span className="flex-giant-text">FLEX</span>
        </div>
      </div>
    </section>
  );
}

// ======= CTA SECTION =======
function CTASection() {
  const [ref, visible] = useInView();

  return (
    <section className="cta-section" id="cta">
      <div className="cta-inner" ref={ref}>
        <div className={visible ? 'fade-in visible' : 'fade-in'}>
          <p className="cta-ready">READY?</p>
          <h2>Banking made better.<br />Sign up now on the GXS app.</h2>
          <p>Ready to join the fun? Hit the button below to get started.</p>
          <button className="btn-gradient" id="btn-cta-download">Download GXS Bank app</button>
        </div>

        <div className={`cta-help ${visible ? 'fade-in visible' : 'fade-in'}`} style={{ transitionDelay: '0.3s' }}>
          <h3>Got questions? We got answers.</h3>
          <p>
            Visit our Help Centre for answers to commonly asked questions
            or chat with us through the app. We're online all day, every day.
          </p>
          <a href="#" id="link-help-centre">Find help here →</a>
        </div>
      </div>
    </section>
  );
}

// ======= FOOTER =======
function Footer() {
  return (
    <footer className="footer" id="footer">
      <div className="footer-inner">
        <div className="footer-top">
          <div className="footer-brand">
            <h3>A new era of digital banking is here.</h3>
            <p>
              Banking is just banking, right? Well, we think it can be made better so you can
              do more with your money. More than you've ever imagined.
              And the cherry on top? It's accessible from both your Grab and Singtel apps.
            </p>
          </div>
          <div className="footer-column">
            <h4>About GXS</h4>
            <ul>
              <li><a href="#">About us</a></li>
              <li><a href="#">Newsroom</a></li>
              <li><a href="#">Leadership</a></li>
              <li><a href="#">Corporate governance</a></li>
              <li><a href="#">Refer and earn</a></li>
              <li><a href="#">Travel with GXS</a></li>
              <li><a href="#">GXS Odyssey</a></li>
            </ul>
          </div>
          <div className="footer-column">
            <h4>Support</h4>
            <ul>
              <li><a href="#">Security tips</a></li>
              <li><a href="#">Help Centre</a></li>
              <li><a href="#">Contact us</a></li>
            </ul>
          </div>
          <div className="footer-column">
            <h4>Important Info</h4>
            <ul>
              <li><a href="#">Terms and conditions</a></li>
              <li><a href="#">Data privacy policy</a></li>
              <li><a href="#">Terms of use</a></li>
              <li><a href="#">Acceptable use policy</a></li>
              <li><a href="#">Whistleblowing policy</a></li>
              <li><a href="#">Notices</a></li>
              <li><a href="#">E-Payments Guidelines</a></li>
              <li><a href="#">Third party policy</a></li>
            </ul>
          </div>
        </div>
        <div className="footer-bottom">
          <p className="footer-notice">
            Insured up to S$100K by SDIC. Terms apply. This advertisement has not been
            reviewed by the Monetary Authority of Singapore.
          </p>
          <div className="footer-sdic">
            🛡️ SDIC Insured
          </div>
        </div>
        <p className="footer-copyright">
          © {new Date().getFullYear()} GXS Bank Pte. Ltd. All rights reserved.
        </p>
      </div>
    </footer>
  );
}

// ======= COOKIE BANNER =======
function CookieBanner() {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  return (
    <div className="cookie-banner" id="cookie-banner">
      <button className="cookie-close" onClick={() => setDismissed(true)} id="btn-cookie-close">✕</button>
      <p>
        We use <a href="#">cookies</a> to operate and track the use of our site,
        and improve your experience with GXS Bank.
      </p>
    </div>
  );
}

// ======= MAIN APP =======
export default function App() {
  return (
    <>
      <Header />
      <main>
        <HeroSection />
        <ValuesSection />
        <BetterSection />
        <SavingsSection />
        <FlexiCardSection />
        <FlexiLoanSection />
        <CTASection />
      </main>
      <Footer />
      <CookieBanner />
    </>
  );
}
