## Design System: RECRUITMENT INTERVIEW AI PROFESSIONAL

### Pattern
- **Name:** Conversion-Optimized + Feature-Rich
- **CTA Placement:** Above fold
- **Sections:** Hero > Features > CTA

### Style
- **Name:** Exaggerated Minimalism
- **Keywords:** Bold minimalism, oversized typography, high contrast, negative space, loud minimal, statement design
- **Best For:** Fashion, architecture, portfolios, agency landing pages, luxury brands, editorial
- **Performance:** ⚡ Excellent | **Accessibility:** ✓ WCAG AA

### Colors
| Role | Hex |
|------|-----|
| Primary | #0F172A |
| Secondary | #334155 |
| CTA | #0369A1 |
| Background | #F8FAFC |
| Text | #020617 |

*Notes: Professional Blue + Success Green + Neutral*

### Typography
- **Heading:** Poppins
- **Body:** Open Sans
- **Mood:** modern, professional, clean, corporate, friendly, approachable
- **Best For:** SaaS, corporate sites, business apps, startups, professional services
- **Google Fonts:** https://fonts.google.com/share?selection.family=Open+Sans:wght@300;400;500;600;700|Poppins:wght@400;500;600;700
- **CSS Import:**
```css
@import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;400;500;600;700&family=Poppins:wght@400;500;600;700&display=swap');
```

### Key Effects
font-size: clamp(3rem 10vw 12rem), font-weight: 900, letter-spacing: -0.05em, massive whitespace

### Avoid (Anti-patterns)
- Outdated forms
- Hidden filters

### Pre-Delivery Checklist
- [ ] No emojis as icons (use SVG: Heroicons/Lucide)
- [ ] cursor-pointer on all clickable elements
- [ ] Hover states with smooth transitions (150-300ms)
- [ ] Light mode: text contrast 4.5:1 minimum
- [ ] Focus states visible for keyboard nav
- [ ] prefers-reduced-motion respected
- [ ] Responsive: 375px, 768px, 1024px, 1440px

