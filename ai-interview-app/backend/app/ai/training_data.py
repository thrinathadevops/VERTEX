"""
Real-World Interview Training Data
───────────────────────────────────
This module contains curated, real-world interview questions sourced from
actual technical interviews at top companies. The AI engine uses these as
few-shot examples and seed questions to generate realistic interview experiences.

HOW THIS WORKS:
- The LLM doesn't "learn" in the traditional sense
- Instead, we inject these real examples into the prompt as CONTEXT
- The LLM then mimics the style, depth, and approach of real interviewers
- This is called "few-shot prompting" + "retrieval-augmented generation"

HOW TO ADD YOUR OWN TRAINING DATA:
1. Add real questions to the appropriate category below
2. Include expected_answer_points — these tell the AI what a GOOD answer looks like
3. Add follow_up questions — real interviewers always dig deeper
4. Set difficulty and interviewer_style to control the tone

The more examples you add, the better the AI mimics real interviewers.
"""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class TrainingQuestion:
    """A single real-world interview question with scoring context."""
    question: str
    category: str  # e.g., "incident_response", "system_design", "security"
    difficulty: str  # "warm_up", "intermediate", "advanced", "expert"
    role_tags: list[str]  # e.g., ["devops", "sre", "cloud"]
    interviewer_style: str  # How a real interviewer would frame this
    context: str  # Real-world scenario setup
    expected_answer_points: list[str]  # What a strong answer MUST include
    red_flags: list[str]  # Signs of a weak/fake answer
    follow_ups: list[str]  # What a real interviewer asks next
    scoring_rubric: dict[str, str]  # Score range → what it means
    ideal_answer_summary: str  # What a 9-10 answer sounds like


@dataclass
class InterviewerBehavior:
    """Defines how a real interviewer behaves in specific situations."""
    scenario: str
    what_real_interviewer_does: str
    what_generic_ai_does_wrong: str
    correct_approach: str


# ═══════════════════════════════════════════════════════════════════
#  REAL INTERVIEWER BEHAVIORS — teach the AI how to act
# ═══════════════════════════════════════════════════════════════════

INTERVIEWER_BEHAVIORS: list[InterviewerBehavior] = [
    InterviewerBehavior(
        scenario="Candidate gives a vague answer",
        what_real_interviewer_does="Pushes back: 'You said you used Terraform — can you tell me specifically how you managed state? Did you use remote state? Workspaces? How did you handle state locking with a team of 10?'",
        what_generic_ai_does_wrong="Accepts the vague answer and moves to the next question",
        correct_approach="Always probe for specifics. If they say 'I used X', ask HOW they used it, what problems they hit, and what they'd do differently.",
    ),
    InterviewerBehavior(
        scenario="Candidate clearly memorised a textbook answer",
        what_real_interviewer_does="Throws a curveball: 'OK, but what happens when that approach fails at 3 AM and your on-call gets woken up? What's your ACTUAL runbook?'",
        what_generic_ai_does_wrong="Gives a high score because the answer contains correct keywords",
        correct_approach="Test for REAL experience by asking about failures, edge cases, and what went wrong. Textbook answers lack these.",
    ),
    InterviewerBehavior(
        scenario="Candidate mentions a tool/technology",
        what_real_interviewer_does="Deep dives: 'You mentioned Prometheus — what exporters did you use? What was your retention policy? Did you hit cardinality issues? How did you handle federation across clusters?'",
        what_generic_ai_does_wrong="Moves on to an unrelated question",
        correct_approach="Pick ONE technology they mentioned and drill 2-3 levels deep. Real experience shows in the details.",
    ),
    InterviewerBehavior(
        scenario="Candidate has a gap in knowledge",
        what_real_interviewer_does="Notes it but stays professional: 'That's OK, let me rephrase — if you had to design this from scratch today, what would you consider?'",
        what_generic_ai_does_wrong="Ignores the gap or harshly criticises",
        correct_approach="Give them a chance to think through it. You're testing problem-solving, not memorisation.",
    ),
    InterviewerBehavior(
        scenario="Starting the interview",
        what_real_interviewer_does="Starts conversational: 'Before we dive in, tell me about a project you're really proud of from your last role. What was your specific contribution?'",
        what_generic_ai_does_wrong="Jumps straight to a technical question",
        correct_approach="Warm up with something from their resume. It relaxes them AND gives you context for harder questions.",
    ),
    InterviewerBehavior(
        scenario="Candidate gives an excellent answer",
        what_real_interviewer_does="Pushes even further: 'Great answer. Now what if the requirements change and you need to handle 10x the traffic? How would your design evolve?'",
        what_generic_ai_does_wrong="Simply moves to the next unrelated question",
        correct_approach="When someone is strong, challenge them more. This separates good from exceptional.",
    ),
    InterviewerBehavior(
        scenario="Evaluating the answer",
        what_real_interviewer_does="Looks for: (1) Did they mention monitoring/alerting? (2) Did they consider failure modes? (3) Did they mention rollback? (4) Did they think about security? (5) Did they mention cost implications?",
        what_generic_ai_does_wrong="Scores based on length and keyword presence",
        correct_approach="Production readiness markers: monitoring, rollback, security, cost, and team coordination should all be present in senior-level answers.",
    ),
]


# ═══════════════════════════════════════════════════════════════════
#  REAL-WORLD QUESTIONS — categorised by domain
# ═══════════════════════════════════════════════════════════════════

TRAINING_QUESTIONS: list[TrainingQuestion] = [

    # ─── INCIDENT RESPONSE ────────────────────────────────────
    TrainingQuestion(
        question="It's 2 AM. PagerDuty fires — your main API gateway is returning 503s for 40% of requests. You're the on-call engineer. Walk me through exactly what you do in the first 15 minutes.",
        category="incident_response",
        difficulty="advanced",
        role_tags=["sre", "devops", "platform"],
        interviewer_style="Scenario-based pressure test — tests real incident handling, not theory",
        context="Production outage scenario. This tests if the candidate has actually handled real incidents or is just reciting theory.",
        expected_answer_points=[
            "Acknowledge the alert and check the severity/blast radius",
            "Open an incident channel (Slack/Teams) and notify stakeholders",
            "Check dashboards first — Grafana/Datadog — look at error rate, latency percentiles, request volume",
            "Check if there was a recent deployment — correlate with deployment timeline",
            "Check upstream/downstream dependencies — is it the gateway or a backend service?",
            "Look at resource utilisation — CPU, memory, connection pool exhaustion",
            "If deployment-related — initiate rollback immediately, don't debug in production",
            "Check load balancer health checks — are backends being marked unhealthy?",
            "Communicate status updates every 10-15 minutes to stakeholders",
            "Document timeline in incident channel",
        ],
        red_flags=[
            "Starts debugging code instead of checking monitoring",
            "Doesn't mention communication/stakeholder notification",
            "No mention of rollback as an option",
            "Tries to SSH into servers as the first step",
            "Doesn't check if a recent deployment caused it",
        ],
        follow_ups=[
            "OK you've rolled back and the 503s stopped. But now your CTO asks — how do we prevent this from happening again? What do you put in the post-mortem?",
            "What if the rollback didn't fix it? What's your next step?",
            "How would you set up alerting to catch this earlier — maybe before it hits 40%?",
        ],
        scoring_rubric={
            "9-10": "Mentions triage, monitoring, communication, rollback, blast radius, and timeline documentation. Shows real experience.",
            "7-8": "Covers most steps but misses communication or documentation aspects.",
            "5-6": "Generic — 'I would check the logs and restart the service'. No structured approach.",
            "3-4": "Vague — 'I would investigate the issue'. No concrete steps.",
            "1-2": "Unable to articulate incident response process.",
        },
        ideal_answer_summary="A strong candidate describes a structured incident response: triage → dashboards → blast radius → recent changes → rollback if needed → communicate → document. They mention specific tools and show they've done this before.",
    ),

    TrainingQuestion(
        question="Your Kubernetes cluster has a memory leak that's causing nodes to go into NotReady state every 48 hours. The team's current solution is a cron job that restarts the nodes every 24 hours. How would you properly diagnose and fix this?",
        category="incident_response",
        difficulty="expert",
        role_tags=["sre", "devops", "kubernetes"],
        interviewer_style="Diagnoses engineering maturity — are they OK with band-aids or do they find root causes?",
        context="This exposes whether the candidate accepts workarounds or drives proper fixes. Many teams actually do the cron-restart approach.",
        expected_answer_points=[
            "Identify the cron restart as a band-aid, not a solution",
            "Use kubectl top nodes/pods to identify which pods are consuming memory",
            "Check if containers have proper resource limits set",
            "Look for pods without memory limits (unbounded consumption)",
            "Use tools like kubectl debug or ephemeral containers to profile",
            "Check for known issues — Java apps without container-aware JVM flags, Node.js heap settings",
            "Consider using Vertical Pod Autoscaler for right-sizing",
            "Set up proper resource quotas per namespace",
            "Add Prometheus alerts for memory trending (predict OOM before it happens)",
            "Check for DaemonSets or system pods that might be leaking",
        ],
        red_flags=[
            "Thinks the cron job is acceptable",
            "Suggests just adding more memory to nodes",
            "Doesn't mention resource limits",
            "Can't explain Kubernetes memory management",
        ],
        follow_ups=[
            "How would you set up proactive alerting so you know BEFORE nodes go NotReady?",
            "What's your approach to capacity planning to prevent this class of issue entirely?",
            "How do you enforce that all new deployments have proper resource limits?",
        ],
        scoring_rubric={
            "9-10": "Identifies band-aid, uses systematic diagnosis, mentions resource limits, profiling tools, and preventive measures.",
            "7-8": "Good diagnosis approach but misses prevention or automation.",
            "5-6": "Identifies it as a problem but solution is 'just increase memory'.",
            "3-4": "Doesn't see the cron job as a problem.",
            "1-2": "Unable to discuss Kubernetes resource management.",
        },
        ideal_answer_summary="Immediately identifies the cron restart as a symptom fix, not a root cause fix. Uses systematic profiling to trace the leak, sets proper resource limits, implements monitoring to predict issues, and adds policy enforcement to prevent recurrence.",
    ),

    # ─── CI/CD & DEPLOYMENT ──────────────────────────────────
    TrainingQuestion(
        question="Your team pushes 15 microservices, each with its own repo. Currently, deployments take 45 minutes and fail 30% of the time. The CTO wants same-day hotfix capability. How do you redesign this?",
        category="cicd",
        difficulty="advanced",
        role_tags=["devops", "platform", "sre"],
        interviewer_style="Real business problem — tests architecture thinking + practical delivery",
        context="This is a very common real-world problem. Tests if the candidate can balance speed with safety.",
        expected_answer_points=[
            "Identify WHY deployments fail — flaky tests? Environment drift? Manual steps?",
            "Standardise CI pipelines across services (shared templates / reusable workflows)",
            "Implement parallel builds — 15 sequential = slow, parallel = fast",
            "Canary or blue-green deployments for safe rollouts",
            "Feature flags to decouple deployment from release",
            "Automated smoke tests after each deployment",
            "GitOps approach (ArgoCD/Flux) for declarative, auditable deployments",
            "Break the deployment into stages — build → test → staging → canary → production",
            "Rollback automation — if smoke tests fail, auto-rollback",
            "Deployment dashboard for visibility across all 15 services",
        ],
        red_flags=[
            "Suggests deploying all 15 at once",
            "No mention of testing or validation",
            "Ignores the 30% failure rate and focuses only on speed",
            "No rollback strategy",
        ],
        follow_ups=[
            "How would you handle database migrations during these deployments?",
            "What if two of those 15 services have a tight dependency — they must be deployed together?",
            "How do you handle config changes vs code changes in your pipeline?",
        ],
        scoring_rubric={
            "9-10": "Addresses root cause of failures, implements progressive delivery, includes rollback, monitoring, and organisational aspects.",
            "7-8": "Good technical solution but misses organisational or process improvements.",
            "5-6": "Generic CI/CD knowledge without addressing the specific 30% failure problem.",
            "3-4": "Suggests manual fixes or doesn't address the scale (15 services).",
            "1-2": "Doesn't understand the problem.",
        },
        ideal_answer_summary="First diagnoses WHY 30% fail (root cause). Then implements: standardised pipeline templates, parallel execution, canary deployments, automated rollback on failure, feature flags for hotfix capability, and a deployment dashboard.",
    ),

    # ─── SECURITY ─────────────────────────────────────────────
    TrainingQuestion(
        question="During a routine audit, you discover that 8 of your 15 microservices have hardcoded AWS credentials in their source code, and some of these repos are public. What do you do RIGHT NOW, and what's your 30-day remediation plan?",
        category="security",
        difficulty="advanced",
        role_tags=["devsecops", "security", "devops"],
        interviewer_style="Crisis response + long-term planning — tests both urgency and systematic thinking",
        context="This actually happens more than people admit. Tests security incident response AND prevention.",
        expected_answer_points=[
            "IMMEDIATE: Rotate ALL exposed credentials — this is step 1, non-negotiable",
            "IMMEDIATE: Make the public repos private until remediated",
            "IMMEDIATE: Check CloudTrail/audit logs for unauthorised usage of those credentials",
            "IMMEDIATE: Notify security team and management (this is a reportable incident)",
            "SHORT-TERM: Implement git-secrets or truffleHog in CI to prevent future commits",
            "SHORT-TERM: Move all secrets to a secrets manager (Vault, AWS Secrets Manager, etc.)",
            "MEDIUM-TERM: Implement SAST/DAST scanning in the CI pipeline",
            "MEDIUM-TERM: Least-privilege IAM — each service gets only the permissions it needs",
            "LONG-TERM: Implement short-lived credentials (IAM roles for service accounts, IRSA for EKS)",
            "LONG-TERM: Security training for the development team",
            "LONG-TERM: Regular secret scanning across all repos",
        ],
        red_flags=[
            "Doesn't treat this as urgent",
            "Suggests just deleting the credentials from code (they're in git history!)",
            "Doesn't mention credential rotation",
            "No audit of whether credentials were misused",
        ],
        follow_ups=[
            "The credentials were used to spin up crypto miners. How does your response change?",
            "How do you handle the git history — those credentials are still in old commits?",
            "How would you implement this for a team that resists using a secrets manager because 'it's slower to develop'?",
        ],
        scoring_rubric={
            "9-10": "Immediate rotation, git history cleanup, audit logs check, systematic prevention with secrets manager and CI scanning.",
            "7-8": "Good immediate response but incomplete long-term plan.",
            "5-6": "Rotates credentials but doesn't address git history or prevention.",
            "3-4": "Suggests removing from code without rotation.",
            "1-2": "Doesn't understand the severity.",
        },
        ideal_answer_summary="Treats this as a security incident. Immediately rotates credentials, checks for misuse, makes repos private. Then systematically implements secrets management, pre-commit hooks, CI scanning, and least-privilege IAM.",
    ),

    # ─── CLOUD ARCHITECTURE ──────────────────────────────────
    TrainingQuestion(
        question="Your SaaS platform serves 50K requests/second. The CEO says 'we need to be in EU and APAC by Q3 for compliance and latency.' Currently you're single-region US-East. Design the multi-region architecture.",
        category="system_design",
        difficulty="expert",
        role_tags=["cloud", "architect", "sre"],
        interviewer_style="Architecture deep-dive with real business constraints (compliance + latency + timeline)",
        context="Multi-region is one of the hardest problems in infrastructure. This separates seniors from leads.",
        expected_answer_points=[
            "Data residency/sovereignty — EU data must stay in EU (GDPR)",
            "DNS-based routing (Route53 geolocation/latency-based routing)",
            "CDN layer (CloudFront/Akamai) for static content globally",
            "Database strategy — active-active vs active-passive, CRDTs vs eventual consistency",
            "Consider DynamoDB Global Tables or CockroachDB for multi-region writes",
            "Session management — how do you handle auth tokens across regions?",
            "Deployment pipeline — how do you deploy to 3 regions safely?",
            "Failover strategy — automatic vs manual, RTO/RPO targets",
            "Cost implications — multi-region roughly 2-3x cost",
            "Testing strategy — how do you test failover? Chaos engineering?",
        ],
        red_flags=[
            "Ignores data residency/compliance completely",
            "Suggests just putting a CDN in front of a single region",
            "Doesn't discuss database replication strategy",
            "No mention of cost implications",
        ],
        follow_ups=[
            "How do you handle write conflicts if a user in EU updates their profile while the replication to US is still in-flight?",
            "What's your rollback plan if the EU region deployment has a bug but US and APAC are fine?",
            "How do you actually test that failover works? Do you chaos-engineer in production?",
        ],
        scoring_rubric={
            "9-10": "Addresses compliance, database replication, DNS routing, deployment, failover, cost, and testing. Mentions specific tradeoffs.",
            "7-8": "Good architecture but misses compliance or cost aspects.",
            "5-6": "Generic multi-region answer without addressing the specific 50K rps challenge.",
            "3-4": "Suggests CDN as the only solution.",
            "1-2": "Doesn't understand multi-region architecture.",
        },
        ideal_answer_summary="Addresses GDPR compliance first, designs DNS-based geo-routing, picks appropriate multi-region database (with tradeoffs), designs deployment strategy for 3 regions, includes failover testing, and provides cost estimates.",
    ),

    # ─── MONITORING & OBSERVABILITY ──────────────────────────
    TrainingQuestion(
        question="Your team deployed a new feature and response times increased by 200ms. Nobody noticed for 3 days until a customer complained. How do you build an observability setup that catches this in 5 minutes, not 3 days?",
        category="observability",
        difficulty="intermediate",
        role_tags=["sre", "devops", "platform"],
        interviewer_style="Post-incident improvement — tests if they can build systems that prevent recurring problems",
        context="This is a very common real incident. Tests understanding of proactive monitoring vs reactive debugging.",
        expected_answer_points=[
            "SLOs/SLIs — define what 'good' latency is (e.g., P99 < 500ms)",
            "Baseline alerting — alert when latency deviates from baseline by X%",
            "Error budgets — if latency SLO is burning too fast, alert",
            "Deployment annotations in Grafana — correlate deploys with metric changes",
            "Automated canary analysis — compare canary metrics vs production before promoting",
            "Distributed tracing (Jaeger/Tempo) — trace the 200ms to which service/query",
            "APM integration — New Relic/Datadog APM for method-level profiling",
            "Runbook links in alerts — tell the on-call engineer WHAT TO DO",
            "Synthetic monitoring — external probes checking end-to-end response time",
            "Dashboard with deployment markers — visual correlation",
        ],
        red_flags=[
            "Only suggests adding more logging",
            "Doesn't mention SLOs or baselines",
            "No mention of deployment correlation",
            "Suggests manual dashboard checking",
        ],
        follow_ups=[
            "How do you avoid alert fatigue? Your team already has 50 alerts, half are noisy.",
            "What's your approach to defining SLOs — who decides what 'good enough' latency is?",
            "How would you implement this for a team that's never used observability tools before?",
        ],
        scoring_rubric={
            "9-10": "SLOs, deployment correlation, canary analysis, tracing, and preventive measures. Shows real experience.",
            "7-8": "Good monitoring setup but misses the proactive angles (canary, SLOs).",
            "5-6": "Generic — 'set up alerting for high latency'. No depth.",
            "3-4": "Only mentions logging.",
            "1-2": "Doesn't understand observability.",
        },
        ideal_answer_summary="Defines SLOs first, implements baseline-deviation alerting, adds deployment annotations for correlation, sets up canary analysis for new deploys, and adds synthetic monitoring for external validation.",
    ),

    # ─── IaC & TERRAFORM ─────────────────────────────────────
    TrainingQuestion(
        question="Your Terraform state file got corrupted during a team member's apply. Half the resources show as needing to be destroyed and recreated, including your production database. What do you do?",
        category="iac",
        difficulty="advanced",
        role_tags=["devops", "cloud", "platform"],
        interviewer_style="Real crisis scenario — tests depth of Terraform knowledge beyond basic usage",
        context="State corruption is a real and terrifying problem. This shows if they truly understand Terraform internals.",
        expected_answer_points=[
            "DO NOT RUN terraform apply — this will destroy production resources",
            "Check if there's a state file backup (S3 versioning, Terraform Cloud state history)",
            "Restore the state from the last known good version",
            "If no backup — use terraform import to manually re-map resources to state",
            "Enable state locking (DynamoDB for AWS) to prevent concurrent modifications",
            "Enable S3 versioning on the state bucket for future recovery",
            "Consider Terraform Cloud or Spacelift for managed state with audit trail",
            "Implement CI-based terraform plan/apply — no manual applies",
            "Add pre-commit hooks that run terraform validate and terraform plan",
            "Post-mortem: why was someone running apply manually?",
        ],
        red_flags=[
            "Suggests running terraform apply to 'fix it'",
            "Doesn't know about state file backups or versioning",
            "Can't explain terraform import",
            "Doesn't mention state locking",
        ],
        follow_ups=[
            "How do you prevent this from happening again? Should developers have access to run terraform apply directly?",
            "What's your approach to structuring Terraform — monorepo or per-service? Why?",
            "How do you handle secrets in Terraform — database passwords, API keys?",
        ],
        scoring_rubric={
            "9-10": "Immediate protection (don't apply), restore from backup, import if needed, prevent recurrence with locking and CI.",
            "7-8": "Knows to restore but misses prevention aspects.",
            "5-6": "Vaguely mentions backups but can't explain the recovery process.",
            "3-4": "Suggests destroying and recreating resources.",
            "1-2": "Doesn't understand Terraform state.",
        },
        ideal_answer_summary="First rule: don't apply. Restore state from S3 versioning or Terraform Cloud history. If not available, use terraform import. Then implement: state locking, CI-only applies, S3 versioning, and remove manual access.",
    ),

    # ─── CONTAINERS & DOCKER ─────────────────────────────────
    TrainingQuestion(
        question="Your Docker image for a Python microservice is 1.8GB and takes 12 minutes to build. Your team is complaining about slow CI and slow rolling updates in Kubernetes. Fix it.",
        category="containers",
        difficulty="intermediate",
        role_tags=["devops", "backend", "platform"],
        interviewer_style="Practical optimisation — tests real Docker expertise vs tutorial-level knowledge",
        context="Oversized images are extremely common. This tests practical optimisation skills.",
        expected_answer_points=[
            "Use multi-stage builds — build stage with dev deps, runtime stage with only production",
            "Use slim/alpine base images (python:3.12-slim instead of python:3.12)",
            "Use .dockerignore to exclude tests, docs, .git, node_modules, etc.",
            "Order Dockerfile layers for cache efficiency — COPY requirements.txt first, then code",
            "Use pip install --no-cache-dir to reduce image size",
            "Consider distroless images for production (no shell, minimal attack surface)",
            "Pin specific versions of base images (not :latest)",
            "Use docker buildx with cache mounts for faster CI builds",
            "Consider using BuildKit cache mounts for pip/npm caches across builds",
            "Measure with docker history to identify large layers",
        ],
        red_flags=[
            "Doesn't know multi-stage builds",
            "Suggests using alpine for Python without mentioning musl/glibc issues",
            "No mention of .dockerignore",
            "Doesn't understand layer caching",
        ],
        follow_ups=[
            "You switched to Alpine but now some Python packages fail to install because they need glibc. What do you do?",
            "How do you handle private pip packages in your Docker build without leaking credentials?",
            "What's your strategy for keeping base images up to date with security patches?",
        ],
        scoring_rubric={
            "9-10": "Multi-stage build, slim base, .dockerignore, layer ordering, cache optimisation, and security considerations.",
            "7-8": "Multi-stage + slim base but misses CI cache optimisation.",
            "5-6": "Knows to use slim image but can't explain multi-stage builds.",
            "3-4": "Suggests just using a different base image.",
            "1-2": "Doesn't understand Docker optimisation.",
        },
        ideal_answer_summary="Multi-stage build with python:3.12-slim as runtime, pip requirements first for cache hits, .dockerignore, BuildKit cache mounts for CI, and distroless for security. Target: <200MB, <2min build.",
    ),

    # ─── COST OPTIMISATION ───────────────────────────────────
    TrainingQuestion(
        question="Your AWS bill jumped from $15K to $45K last month. The CFO wants answers by Friday. Walk me through how you investigate and reduce this.",
        category="finops",
        difficulty="intermediate",
        role_tags=["cloud", "devops", "sre"],
        interviewer_style="Business impact scenario — tests FinOps skills and communication with non-technical stakeholders",
        context="Cloud cost spikes are a universal pain point. Tests analytical thinking and communication skills.",
        expected_answer_points=[
            "AWS Cost Explorer — filter by service, region, usage type to identify the spike",
            "Check for: forgotten dev/staging environments, orphaned resources",
            "Look at EC2 right-sizing — are instances over-provisioned?",
            "Check for unattached EBS volumes and unused Elastic IPs",
            "Review data transfer costs — often the hidden killer",
            "Check for RDS multi-AZ or over-provisioned database instances",
            "Look at NAT Gateway costs — VPC endpoints can eliminate this",
            "Savings Plans or Reserved Instances for predictable workloads",
            "Spot instances for fault-tolerant workloads (CI/CD, batch processing)",
            "Set up AWS Budgets with alerts to catch spikes early",
            "Tag everything — cost allocation tags for accountability",
        ],
        red_flags=[
            "Immediate reaction is just to downsize everything",
            "No systematic investigation approach",
            "Doesn't mention communicating findings to CFO in business terms",
            "Ignores quick wins (orphaned resources)",
        ],
        follow_ups=[
            "You found that 60% of the increase is data transfer between AZs. How do you fix this without changing your architecture?",
            "How do you prevent this from happening again? What governance do you put in place?",
            "How do you present this to the CFO in a way they understand?",
        ],
        scoring_rubric={
            "9-10": "Systematic investigation, specific cost categories, both quick wins and long-term strategy, business communication.",
            "7-8": "Good investigation but misses communication/governance aspects.",
            "5-6": "Generic — 'right-size instances'. No investigation methodology.",
            "3-4": "Just suggests turning things off.",
            "1-2": "Doesn't understand cloud cost management.",
        },
        ideal_answer_summary="Systematic approach: Cost Explorer analysis → identify top contributors → quick wins (orphaned resources) → right-sizing → architectural changes (VPC endpoints, spot) → governance (budgets, tags). Presents to CFO in business terms.",
    ),

    # ─── WARM-UP / RESUME-BASED ──────────────────────────────
    TrainingQuestion(
        question="I see you worked at {company} for {years}. Tell me about the most complex infrastructure challenge you faced there and how you solved it.",
        category="warm_up",
        difficulty="warm_up",
        role_tags=["devops", "sre", "cloud", "devsecops", "platform"],
        interviewer_style="Conversational opener that reveals real experience depth — uses resume context",
        context="This warm-up question is personalised from the resume. It sets the tone and gives interview context.",
        expected_answer_points=[
            "Describes a specific, real challenge (not generic)",
            "Explains their role and what they specifically did (not 'the team did')",
            "Mentions constraints they faced (time, budget, team size)",
            "Describes the outcome with measurable results",
            "Shares what they learned or would do differently",
        ],
        red_flags=[
            "Very generic answer without specifics",
            "Uses 'we' for everything without clarifying their contribution",
            "Can't provide numbers or metrics",
            "Describes something too simple for their experience level",
        ],
        follow_ups=[
            "What was the biggest risk in that approach? How did you mitigate it?",
            "If you had to do it over, what would you change?",
            "How did you get buy-in from the rest of the team?",
        ],
        scoring_rubric={
            "9-10": "Specific challenge, clear personal contribution, measurable outcome, lessons learned.",
            "7-8": "Good story but vague on metrics or personal contribution.",
            "5-6": "Generic challenge without depth.",
            "3-4": "Can't describe a meaningful challenge.",
            "1-2": "No answer or irrelevant.",
        },
        ideal_answer_summary="Describes a specific infrastructure challenge, their exact role, the technical approach they chose (with alternatives considered), the measurable outcome, and what they learned.",
    ),
]


# ═══════════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def get_questions_by_category(category: str) -> list[TrainingQuestion]:
    """Filter training questions by category."""
    return [q for q in TRAINING_QUESTIONS if q.category == category]


def get_questions_by_role(role_tag: str) -> list[TrainingQuestion]:
    """Filter training questions by role tag."""
    tag = role_tag.lower()
    return [q for q in TRAINING_QUESTIONS if tag in [t.lower() for t in q.role_tags]]


def get_questions_by_difficulty(difficulty: str) -> list[TrainingQuestion]:
    """Filter training questions by difficulty."""
    return [q for q in TRAINING_QUESTIONS if q.difficulty == difficulty]


def format_training_context_for_prompt(
    role: str,
    turn_number: int,
    total_turns: int,
) -> str:
    """
    Format relevant training data as context for the LLM prompt.
    This is the key function that injects real-world interview patterns.
    """
    # Select appropriate difficulty for this turn
    if turn_number == 1:
        difficulty = "warm_up"
    elif turn_number <= total_turns * 0.4:
        difficulty = "intermediate"
    elif turn_number <= total_turns * 0.7:
        difficulty = "advanced"
    else:
        difficulty = "expert"

    # Get relevant example questions for this role
    role_questions = get_questions_by_role(role)
    diff_questions = [q for q in role_questions if q.difficulty == difficulty]
    if not diff_questions:
        diff_questions = role_questions[:3]  # Fallback to any role questions

    # Build the context
    parts = []

    # Add interviewer behavior instructions
    parts.append("=== HOW REAL INTERVIEWERS BEHAVE ===")
    for b in INTERVIEWER_BEHAVIORS[:4]:  # Top 4 behaviors
        parts.append(f"• SCENARIO: {b.scenario}")
        parts.append(f"  REAL INTERVIEWER: {b.what_real_interviewer_does}")
        parts.append(f"  DON'T DO THIS: {b.what_generic_ai_does_wrong}")
        parts.append("")

    # Add example questions as few-shot examples
    parts.append("=== EXAMPLE QUESTIONS AT THIS DIFFICULTY LEVEL ===")
    for q in diff_questions[:2]:  # Show 2 examples max
        parts.append(f"• Example Q: {q.question}")
        parts.append(f"  Style: {q.interviewer_style}")
        parts.append(f"  Key points to evaluate: {', '.join(q.expected_answer_points[:5])}")
        parts.append(f"  Follow-ups: {', '.join(q.follow_ups[:2])}")
        parts.append("")

    return "\n".join(parts)


def format_scoring_context_for_prompt(question: str) -> str:
    """
    Find the most relevant training question and return its scoring rubric.
    This teaches the AI HOW to score like a real interviewer.
    """
    # Find the best matching training question by keyword overlap
    best_match = None
    best_score = 0

    question_words = set(question.lower().split())
    for tq in TRAINING_QUESTIONS:
        tq_words = set(tq.question.lower().split())
        overlap = len(question_words & tq_words)
        if overlap > best_score:
            best_score = overlap
            best_match = tq

    if not best_match or best_score < 3:
        # Use generic real-interviewer evaluation guidelines
        return """
=== REAL INTERVIEWER EVALUATION GUIDELINES ===
Score based on these REAL criteria:
• Does the answer show REAL hands-on experience (not textbook knowledge)?
• Did they mention monitoring, alerting, or how they'd know if things break?
• Did they consider failure modes and rollback plans?
• Did they mention security implications?
• Did they think about cost and scalability?
• Can they explain WHY they made specific choices (not just WHAT)?
• Did they mention trade-offs between approaches?

RED FLAGS to watch for:
• Generic answers that could apply to any company
• Using buzzwords without depth ("we used microservices for scalability")
• No mention of how they'd measure success
• No consideration of team/organisational impact
"""

    parts = [
        "=== SCORING RUBRIC FROM REAL INTERVIEWERS ===",
        f"Similar question pattern: {best_match.category}",
        "",
        "Scoring guide:",
    ]
    for level, desc in best_match.scoring_rubric.items():
        parts.append(f"  {level}: {desc}")

    parts.append("")
    parts.append("Expected strong answer includes:")
    for point in best_match.expected_answer_points[:6]:
        parts.append(f"  ✓ {point}")

    parts.append("")
    parts.append("Red flags (deduct points):")
    for flag in best_match.red_flags[:4]:
        parts.append(f"  ✗ {flag}")

    parts.append("")
    parts.append(f"What a 9-10 answer sounds like: {best_match.ideal_answer_summary}")

    return "\n".join(parts)
