# 🚀 AWS Interview Question: Elastic Load Balancer (ELB) Types

**Question 18:** *What are the different types of load balancers in AWS?*

> [!NOTE]
> This is a mandatory Networking question. Interviewers use this to verify you understand the OSI Model (Layer 4 vs. Layer 7) and can properly architect traffic routing for modern microservice architectures. 

---

## ⏱️ The Short Answer
AWS provides three primary types of Elastic Load Balancers: The **Application Load Balancer (ALB)**, which operates at Layer 7 and is ideal for HTTP/HTTPS microservices; the **Network Load Balancer (NLB)**, which operates at Layer 4 and is used for ultra-high-performance TCP/UDP traffic; and the **Classic Load Balancer (CLB)**, which is an outdated legacy balancer that AWS actively discourages using for new applications.

---

## 📊 Visual Architecture Flow: Load Balancer Decision Tree

```mermaid
graph TD
    User([🌐 Incoming Internet Traffic]) --> Decision{What OSI Layer <br> does the app need?}

    Decision -->|Layer 7 (HTTP/HTTPS)| ALB[🟢 Application Load Balancer]
    ALB --> ALBRoute1(Routes intelligently by URL Path: /api vs /web)
    ALB --> ALBRoute2(Routes by Host headers or Query params)
    
    Decision -->|Layer 4 (TCP/UDP)| NLB[🔵 Network Load Balancer]
    NLB --> NLBRoute1(Ultra-low latency passthrough)
    NLB --> NLBRoute2(Predictable Static IP support)

    Decision -->|Legacy | CLB[🔴 Classic Load Balancer]
    CLB --> CLBRoute(Do not use in modern cloud architecture)
    
    style ALB fill:#27ae60,stroke:#2ecc71,stroke-width:2px,color:#fff
    style NLB fill:#2980b9,stroke:#3498db,stroke-width:2px,color:#fff
    style CLB fill:#c0392b,stroke:#e74c3c,stroke-width:2px,color:#fff
```

---

## 🔍 Detailed Explanation of the Balancers

### 1. 🟢 Application Load Balancer (ALB) - *The Intelligent Router*
Operates exactly at **Layer 7** of the OSI model. 
- **The Protocol:** It understands HTTP, HTTPS, and WebSockets natively.
- **The Brain:** The defining feature of an ALB is its ability to logically "see" inside the web request. It can look at the URL Path (e.g., `/images` vs `/cart`) or the Host Header (e.g., `api.mycompany.com`) and physically route that exact packet to an entirely different Target Group (like a specialized microservice container).
- **Security:** Natively integrates with AWS WAF (Web Application Firewall).

### 2. 🔵 Network Load Balancer (NLB) - *The Performance Workhorse*
Operates exactly at **Layer 4** of the OSI model.
- **The Protocol:** It primarily handles raw TCP, UDP, and TLS traffic.
- **The Brain:** It is essentially "blind" to the web content. It does not understand HTTP paths or headers. It simply takes raw network packets and blasts them to a target port at lightning speed.
- **Why use it?:** It can effortlessly handle millions of requests per second while maintaining ultra-low latency. Uniquely, **NLBs provide a static Elastic IP address** per subnet (ALBs do not), which is often a strict requirement for legacy corporate firewalls whitelisting your platform.

### 3. 🔴 Classic Load Balancer (CLB) - *The Legacy Balancer*
The original 2009 AWS Load Balancer. It attempts to blend Layer 4 and Layer 7 features but does neither well compared to the ALB and NLB.
- **The Status:** Deprecated / Retiring.
- **The Rule:** You should never architect a modern AWS environment with a CLB. Always explicitly mention to the interviewer that you only use them to support very old legacy EC2-Classic workloads.

---

## 🆚 Feature Comparison Table

| Feature | 🟢 ALB (Application) | 🔵 NLB (Network) |
| :--- | :--- | :--- |
| **OSI Layer** | Layer 7 (Application) | Layer 4 (Transport) |
| **Protocols** | HTTP, HTTPS, WebSockets | TCP, UDP, TLS |
| **Routing Intelligence** | High (URL Path, Headers) | Low (Raw Port Passthrough) |
| **Static IPs** | ❌ No (IPs constantly change) | ✅ Yes (1 Static IP per Subnet) |
| **AWS WAF Support** | ✅ Yes | ❌ No |

---

## 🏢 Real-World Production Scenario

### Scenario 1: The Modern E-Commerce Microservices (ALB)
- **The Architecture:** An enterprise runs an online catalog using Docker containers.
- **The Execution:** All public internet traffic safely hits one single **Application Load Balancer**.
- **The Routing:** If the traffic path is `example.com/api/payment`, the ALB intelligently sends it exclusively to the highly secure Payment container cluster. If the path is `example.com/images`, it routes entirely to a cheaper NGINX static image cluster. This drastically reduces computing costs.

### Scenario 2: The Real-Time Financial Trading Engine (NLB)
- **The Architecture:** A high-frequency stock trading application that depends on raw TCP socket connections.
- **The Execution:** The platform is placed securely behind a **Network Load Balancer**.
- **The Routing:** Because it completely skips Layer 7 HTTP packet inspection, the NLB achieves absolute minimal latency (bare metal speeds), ensuring trades are executed in milliseconds. It also safely provides the exact 3 static IPs that partner bank firewalls require to explicitly whitelist the application.

---

## 🎤 Final Interview-Ready Answer
*"AWS primarily offers three Elastic Load Balancers. The **Application Load Balancer (ALB)** operates at OSI Layer 7, intelligently peering inside HTTP traffic to route requests to specific microservices based on URL paths or headers. The **Network Load Balancer (NLB)** operates at Layer 4, blindly passing raw TCP/UDP traffic for ultra-low latency gaming or financial apps, uniquely providing strict static IP addresses. We generally ignore the legacy **Classic Load Balancer (CLB)** unless supporting heavily outdated infrastructure. In modern production, we proudly put all our containerized web microservices behind ALBs and our high-performance TCP socket servers behind NLBs."*
