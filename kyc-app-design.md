## Design System: FINTECH KYC VERIFICATION CORPORATE ELEGANT

### Pattern
- **Name:** Enterprise Gateway
- **Conversion Focus:**  logo carousel
- **CTA Placement:** Contact Sales (Primary) + Login (Secondary)
- **Color Strategy:** Corporate: Navy/Grey. High integrity. Conservative accents.
- **Sections:** 1. Hero (Video/Mission), 2. Solutions by Industry, 3. Solutions by Role, 4. Client Logos, 5. Contact Sales

### Style
- **Name:** Glassmorphism
- **Keywords:** Frosted glass, transparent, blurred background, layered, vibrant background, light source, depth, multi-layer
- **Best For:** Modern SaaS, financial dashboards, high-end corporate, lifestyle apps, modal overlays, navigation
- **Performance:** ⚠ Good | **Accessibility:** ⚠ Ensure 4.5:1

### Colors
| Role | Hex |
|------|-----|
| Primary | #F59E0B |
| Secondary | #FBBF24 |
| CTA | #8B5CF6 |
| Background | #0F172A |
| Text | #F8FAFC |

*Notes: Dark tech colors + trust + vibrant accents*

### Typography
- **Heading:** IBM Plex Sans
- **Body:** IBM Plex Sans
- **Mood:** financial, trustworthy, professional, corporate, banking, serious
- **Best For:** Banks, finance, insurance, investment, fintech, enterprise
- **Google Fonts:** https://fonts.google.com/share?selection.family=IBM+Plex+Sans:wght@300;400;500;600;700
- **CSS Import:**
```css
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap');
```

### Key Effects
Backdrop blur (10-20px), subtle border (1px solid rgba white 0.2), light reflection, Z-depth

### Avoid (Anti-patterns)
- Light backgrounds
- No security indicators

### Pre-Delivery Checklist
- [ ] No emojis as icons (use SVG: Heroicons/Lucide)
- [ ] cursor-pointer on all clickable elements
- [ ] Hover states with smooth transitions (150-300ms)
- [ ] Light mode: text contrast 4.5:1 minimum
- [ ] Focus states visible for keyboard nav
- [ ] prefers-reduced-motion respected
- [ ] Responsive: 375px, 768px, 1024px, 1440px

