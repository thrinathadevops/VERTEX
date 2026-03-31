# 🚀 AWS Interview Cheat Sheet: AMAZON ROUTE 53 (Q607–Q629)

*This master reference sheet marks Phase 11: Global Networking, covering Amazon Route 53—the only AWS service with a 100% physically backed SLA, orchestrating global DNS, health checks, and traffic routing.*

---

## 📊 The Master Active/Passive Failover Architecture

```mermaid
graph TD
    subgraph "Amazon Route 53 Engine"
        DNS[🌐 Application Endpoint <br/> 'www.company.com']
        HC1[❤️ Health Check <br/> Ping Primary ELB every 10s]
    end
    
    subgraph "Primary Region (us-east-1)"
        ELB1[⚖️ Application Load Balancer]
        App1[🖥️ Production Cluster]
        ELB1 ==> App1
    end
    
    subgraph "Disaster Recovery Region (us-west-2)"
        ELB2[⚖️ Standby Load Balancer]
        App2[🖥️ Warm Standby Cluster]
        ELB2 ==> App2
    end
    
    HC1 -. "Monitors HTTP 200 OK" .-> ELB1
    
    DNS ==>|Primary Record (Active)| ELB1
    DNS -.-x|Secondary Record (Passive)| ELB2
    
    Fail[💥 ELB 1 Fails Health Check]
    HC1 -.-> Fail
    Fail -. "Route 53 triggers DNS Failover" .-> DNS
    DNS ==>|Traffic Rerouted automatically| ELB2
    
    style DNS fill:#8e44ad,color:#fff
    style ELB1 fill:#27ae60,color:#fff
    style ELB2 fill:#f39c12,color:#fff
    style Fail fill:#c0392b,color:#fff
```

---

## 6️⃣0️⃣7️⃣ & Q611: What is Amazon Route 53 and what is its role?
- **Short Answer:** Route 53 is a highly available and scalable cloud Domain Name System (DNS) web service designed to route end users mathematically to internet applications by translating human-readable names (`www.example.com`) into numeric IP addresses (`192.0.2.1`). It mechanically serves three distinct roles: **Domain Registration, DNS Routing, and Global Health Checking.**

## 6️⃣1️⃣5️⃣ Q615: Can you explain the difference between an A record, CNAME record, and ALIAS record?
- **Short Answer:** 
  1) **A Record:** Mathematically maps a domain specifically to a raw IPv4 address (e.g., `10.0.1.5`).
  2) **CNAME Record:** Maps a domain to another domain string (e.g., `blog.example.com` -> `myblog.wordpress.com`).
- **Interview Edge:** *"A Senior Architect absolutely never uses a standard CNAME record for AWS resources. The DNS protocol strictly forbids using a CNAME on the apex/root node of a domain (e.g., `example.com`). AWS invented the **Alias Record** specifically to safely bypass this DNS limitation. An Alias Record acts like a CNAME but is mapped internally by AWS natively to Load Balancers, API Gateways, and CloudFront, allowing you to seamlessly map your root domain while automatically absorbing backend IP shifts for free."*

## 6️⃣0️⃣8️⃣ & Q617 & Q626: What are the different Routing Policies in Route 53?
- **Short Answer:**
  - **Simple Routing:** Standard DNS. Returns exactly one record.
  - **Weighted Routing:** Distributes traffic mathematically (e.g., 90% of requests go to V1, 10% to V2 Canary).
  - **Latency-Based Routing:** Route 53 possesses a global geographic map. If a user in Tokyo requests the site, Route 53 dynamically routes them to the `ap-northeast-1` load balancer precisely because it calculates it has the lowest millisecond physical distance to the user.
  - **Geolocation Routing:** Strictly forces traffic based on country borders regardless of latency (e.g., forcing all traffic from Germany exclusively to Frankfurt servers to comply with GDPR data laws).

## 6️⃣1️⃣6️⃣ & Q627: How can you use Route 53 to configure failover routing for your application?
- **Short Answer:** Implement **Active/Passive Failover**. 
- **Architectural Flow:** You construct a Primary Alias Record pointing to `us-east-1` and a Secondary Alias Record pointing to the DR site in `us-west-2`. You explicitly attach a Route 53 Health Check mathematically onto the Primary ELB. If the ELB fails to return an `HTTP 200 OK` 3 times in a row, Route 53 algorithmically yanks the Primary record out of global DNS and seamlessly starts exclusively returning the DR IP address to the world.

## 6️⃣0️⃣9️⃣ & Q610 & Q629: How do you route traffic to an S3 bucket or CloudFront distribution?
- **Short Answer:** You explicitly utilize the Route 53 **Alias Record** feature. Set the Alias target directly to the specific S3 Website Endpoint or the explicit CloudFront distribution URL (e.g., `d111111abcdef8.cloudfront.net`). 
- **Production Scenario:** The S3 Bucket Name MUST mathematically perfectly match the Route 53 Domain Name. You unequivocally cannot route `www.mywebsite.com` to an S3 bucket structurally named `my-random-bucket-123`. The bucket physically must be named `www.mywebsite.com`.

## 6️⃣1️⃣8️⃣ & Q619: How do you host a domain or configure routing if the domain is hosted outside AWS?
- **Short Answer:** You physically create a **Hosted Zone** inside Route 53. The Hosted Zone autonomously generates exactly four unique AWS Name Servers (NS). If you bought the domain on GoDaddy, you simply log mechanically into GoDaddy's portal, delete their default Name Servers, and manually paste in the 4 AWS Name Servers. Route 53 now legally globally controls the domain's traffic flow.

## 6️⃣2️⃣0️⃣ & Q621 & Q625: How do you troubleshoot DNS propagation and resolution issues?
- **Short Answer:** 
  1) **The TTL Trap:** If you update an A record but your browser is still routing to the old dead IP address, the **Time To Live (TTL)** mathematically has not expired. If a junior developer sets the TTL to 86,400 seconds, the entire global internet will painfully aggressively cache the broken IP address for a full 24 hours. A Senior Architect always dynamically drops the TTL to **60 seconds** two days prior to a massive migration cutover.
  2) **Command Line Tools:** Use the `dig` or `nslookup` tools directly against Google's public DNS (`@8.8.8.8`) to mathematically verify if the globe sees your new AWS IPs, or if the delay is just locally cached in your corporate firewall.
