'use client';

import React from 'react';
import Nav from './Nav';
import Hero from './Hero';
import Demo from './Demo';
import Problem from './Problem';
import HowItWorks from './HowItWorks';
import Developer from './Developer';
import Footer from './Footer';
import { Reveal } from './ui';

export default function LandingPage({ authed = false }: { authed?: boolean }) {
  return (
    <div style={{ background: 'var(--surface-ground)' }}>
      <Nav authed={authed} />
      <main>
        <Hero authed={authed} />
        <Reveal><Demo /></Reveal>
        <Reveal><Problem /></Reveal>
        <Reveal><HowItWorks /></Reveal>
        <Reveal><Developer /></Reveal>
      </main>
      <Footer />
    </div>
  );
}
