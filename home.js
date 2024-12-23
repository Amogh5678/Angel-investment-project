// Importing React and CSS
import React from 'react';
import './App.css';

// Header Component
const Header = () => {
  return (
    <header className="header">
      <div className="logo">Angel Investments</div>
      <nav className="nav">
        <ul>
          <li><a href="#home">Home</a></li>
          <li><a href="#about">About Us</a></li>
          <li><a href="#contact">Contact Us</a></li>
          <li><a href="#login" className="login">Login/Sign Up</a></li>
        </ul>
      </nav>
    </header>
  );
};

// Footer Component
const Footer = () => {
  return (
    <footer className="footer">
      <div className="footer-links">
        <a href="#privacy">Privacy Policy</a>
        <a href="#terms">Terms of Service</a>
        <a href="#faq">FAQ</a>
      </div>
      <div className="social-media">
        <a href="https://facebook.com" target="_blank" rel="noreferrer">Facebook</a>
        <a href="https://twitter.com" target="_blank" rel="noreferrer">Twitter</a>
        <a href="https://linkedin.com" target="_blank" rel="noreferrer">LinkedIn</a>
      </div>
      <div className="contact-info">
        <p>Email: support@angelinvestments.com</p>
        <p>Phone: +1 (555) 123-4567</p>
      </div>
    </footer>
  );
};

// App Component
const App = () => {
  return (
    <div className="app">
      <Header />
      <main className="main">
        <section id="home">
          <h1>Welcome to Angel Investments</h1>
          <p>Empowering Innovations, Connecting Visionaries.</p>
        </section>
        <section id="about">
          <h2>About Us</h2>
          <p>Angel Investments is a platform where entrepreneurs pitch ideas and investors find opportunities.</p>
        </section>
        <section id="contact">
          <h2>Contact Us</h2>
          <p>Have questions? Reach out to us through our contact information below.</p>
        </section>
      </main>
      <Footer />
    </div>
  );
};

export default App;
