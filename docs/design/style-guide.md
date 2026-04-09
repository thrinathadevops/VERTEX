# VAREX Design System & Graphic Styles Guide

This guide documents the core aesthetic styles, UI patterns, and prompt references to be used when generating new components or pages for the VAREX platform.

## 1. Core Aesthetics

### 1.1 Glassmorphism
**Use Case:** Modern SaaS landing pages, floating navbars, overlaid info cards.
**Implementation:** `backdrop-filter: blur(12px)` + `background: rgba(255,255,255,0.15)` + thin low-opacity border. Requires vibrant background.
**Prompt:** "Build a glassmorphism SaaS landing page. Use a vivid purple-to-blue gradient background (#667eea to #764ba2). Create 3 feature cards that look like frosted glass panels — each card should have background: rgba(255,255,255,0.15), a backdrop-filter blur of 12px, a white border at 30% opacity, and a subtle drop shadow. Text should be white. Add a glass-style navbar at the top."

### 1.2 Neumorphism (Soft UI)
**Use Case:** Dashboards, media players, control panels. Use sparingly (low contrast).
**Implementation:** Dual box-shadows. The background color and element color MUST match perfectly (e.g., `#e0e5ec`).
**Prompt:** "Create a neumorphism dashboard on a #e0e5ec background. Build raised circular buttons using dual box-shadows: box-shadow: 6px 6px 12px #b8bec7, -6px -6px 12px #ffffff. Add pressed (active) state with inset shadows: inset 4px 4px 8px #b8bec7, inset -4px -4px 8px #ffffff."

### 1.3 Dark Luxury
**Use Case:** Premium tier features, high-end SaaS presentations.
**Implementation:** Near-black background (`#0A0A0A`), NOT pure black. Use a single vibrant accent color (e.g., Electric Blue `#0066FF`). Thin, low-opacity borders.
**Prompt:** "Build a dark luxury SaaS landing page. Background: #0D0D1A. Primary text: #F1F1EE. Accent color: electric blue #0066FF for buttons. Cards use #111827 background with a 1px border at rgba(255,255,255,0.08)."

### 1.4 Bento Grid
**Use Case:** Feature showcases, product overviews.
**Implementation:** CSS Grid with varying spans (`grid-column: span 2`). Mix large highlight cards with small data cards.
**Prompt:** "Build a bento grid feature section on a #0A0A0A background. Create a responsive CSS Grid with 3 columns and auto rows. Include 6 cards of varying sizes. Dark cards use #111111 background, light accent cards use #1A1A2E. Round all cards with 16px border-radius."

## 2. Scroll & Animation Patterns

### 2.1 Smooth Scroll (Lenis)
**Use Case:** Elevating the feel of marketing and landing pages.
**Implementation:** Intercept native scroll via Lenis library for physics-based momentum.
**Prompt:** "Add Lenis smooth scrolling. Initialize with duration: 1.2, easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)). Integrate with GSAP ScrollTrigger."

### 2.2 Scroll-Triggered Reveal
**Use Case:** Fading elements in as they enter the viewport.
**Implementation:** IntersectionObserver toggling an `opacity` and `translateY` transition. Stagger for lists.
**Prompt:** "Use IntersectionObserver to detect when each element is 20% visible. Start states: opacity:0, transform:translateY(30px). On intersection, transition to opacity:1, translateY(0) over 0.6s."

## 3. UI Components

### 3.1 Mega Menu
**Use Case:** E-commerce, complex documentation sites.
**Implementation:** Absolutely positioned grid panel triggered on hover/click revealing multi-column links and featured media.
**Prompt:** "Create a mega menu. Navbar link hover triggers full-width panel dropdown. 4-column CSS grid inside panel. Animate panel: opacity 0 to 1, translateY(-8px) to 0, over 0.2s."

### 3.2 Sticky Sidebar + Content
**Use Case:** Application dashboards, user settings.
**Implementation:** Two columns. Left sidebar uses `position: sticky; top: 0; height: 100vh`.
**Prompt:** "Build a SaaS dashboard. Sidebar: 240px wide, dark background (#111827), fixed to left side. Main content area flex-1."

## 4. Typography & Color Systems

### 4.1 Type Scale & Hierarchy
**Use Case:** Ensuring consistent visual weighting across the site.
**Implementation:** Use `clamp()` for fluid typography (e.g., `clamp(40px, 5vw, 64px)` for H1). Negative letter-spacing for large display text.

### 4.2 60-30-10 Color Rule
**Use Case:** Balanced color application.
**Implementation:** 60% dominant background, 30% secondary cards/sections, 10% vivid accent brand color.

---
*Note: Refer to this document when prompting AI generation tools for new VAREX components to maintain the desired aesthetic standards.*
