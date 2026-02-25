export default function ServicesPage() {
  const divisions = [
    {
      icon: "🛠",
      title: "Engineering Services",
      items: ["Cloud Architecture Design","DevSecOps Implementation","Infrastructure Automation","Security Hardening","CI/CD Pipeline Setup"],
    },
    {
      icon: "🛡",
      title: "Cybersecurity & Resilience",
      items: ["DevSecOps Pipelines","Container Security","Zero Trust Architecture","Compliance & Audit (ISO 27001, SOC2)","VAPT & Threat Modelling"],
    },
    {
      icon: "🗂",
      title: "SAP SD Consulting",
      items: ["S/4HANA SD Module Implementation","Order-to-Cash Optimisation","SAP SD Integration (CRM/MM)","SAP Support & Rollouts","Pricing & Condition Configuration"],
    },
    {
      icon: "🎯",
      title: "Talent Acceleration & AI Hiring",
      items: ["AI-driven ATS screening","Expert 30-min technical interview","Pre-vetted DevOps/Security specialists","Hire in 7 Days model","Scorecard + video recording (premium)"],
    },
  ];

  return (
    <div className="space-y-10">
      <header className="text-center">
        <h1 className="text-3xl font-bold mb-2">What We Do</h1>
        <p className="text-slate-300 max-w-xl mx-auto text-sm">
          Four specialised divisions delivering engineering, security, SAP consulting, and AI-powered technical hiring.
        </p>
      </header>

      <section className="grid gap-6 md:grid-cols-2">
        {divisions.map((div) => (
          <div key={div.title} className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
            <span className="text-3xl mb-3 block">{div.icon}</span>
            <h2 className="text-base font-semibold mb-3">{div.title}</h2>
            <ul className="space-y-1.5">
              {div.items.map((item) => (
                <li key={item} className="flex items-start gap-2 text-xs text-slate-300">
                  <span className="mt-0.5 h-1.5 w-1.5 rounded-full bg-sky-400 flex-shrink-0" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </section>
    </div>
  );
}
