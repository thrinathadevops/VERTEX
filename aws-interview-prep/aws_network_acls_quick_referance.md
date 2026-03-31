# 🚀 AWS Interview Cheat Sheet: NETWORK ACLs (Q151–Q168)

*This master reference sheet details Network Access Control Lists (NACLs), the stateless subnet-level firewalls that act as the absolute first line of defense in AWS, operating with strict mathematical rule execution.*

---

## 📊 The Master Network ACL (Stateless) Architecture

```mermaid
graph TD
    subgraph "Global Internet"
        Hacker([🦹 Malicious IP: 99.88.77.66])
        Client([👨‍💻 Valid User: 55.44.33.22])
    end
    
    subgraph "Amazon VPC"
        IGW[🚪 Internet Gateway]
        
        subgraph "Subnet Perimeter (NACL layer)"
            NACL[🛡️ Network ACL <br/> Rule 100: ALLOW 55.44.33.22 Inbound <br/> Rule 200: DENY 99.88.77.66 Inbound]
            
            subgraph "Public Subnet (10.0.1.0/24)"
                SG[🔒 Security Group <br/> Stateful Firewall]
                EC2[🖥️ Web Server]
                
                SG ==>|Stateful: Auto-Allows Return| EC2
            end
        end
    end
    
    Hacker ==> IGW
    Client ==> IGW
    
    IGW ==>|Packet Evaluation| NACL
    NACL -. "DENIED (Rule 200)" .-x Hacker
    NACL ==>|ALLOWED (Rule 100)| SG
    
    EC2 ==>|Response Data| SG
    SG ==>|STATELESS RETURN: <br/> Must explicitly allow Ephemeral Ports (1024-65535) Outbound| NACL
    NACL ==>|Outbound Rule 100| IGW
    IGW ==> Client
    
    style Hacker fill:#c0392b,color:#fff
    style Client fill:#2980b9,color:#fff
    style NACL fill:#8e44ad,color:#fff
    style SG fill:#f39c12,color:#fff
    style EC2 fill:#27ae60,color:#fff
```

---

## 1️⃣5️⃣1️⃣ Q151: What is a Network ACL in AWS?
- **Short Answer:** A Network Access Control List (NACL) is an optional, stateless, virtual firewall that operates exclusively at the Subnet boundary. It acts structurally as the absolute first line of defense for inbound traffic entering a subnet, and the final line of defense for outbound traffic leaving a subnet.
- **Production Scenario:** A company identifies a massive DDoS (Distributed Denial of Service) attack originating from a specific IP block (`203.0.113.0/24`). The Architect modifies the Web Subnet NACL to explicitly DENY all inbound traffic from that CIDR block, dropping the malicious packets instantly at the perimeter before they ever reach the EC2 instances.
- **Interview Edge:** *"NACLs operate at Layer 4 (Transport layer). Because they are attached to the subnet, they govern all EC2 instances inside that subnet simultaneously, making them the ultimate tool for sweeping, macro-level security blocks."*

## 1️⃣5️⃣2️⃣ Q152: What is the difference between a Network ACL and a Security Group?
- **Short Answer:** 
  1. **Attachment:** NACLs attach to Subnets; SGs attach to ENIs (Instances).
  2. **State:** NACLs are **Stateless** (return traffic must be explicitly allowed via a separate outbound rule); SGs are **Stateful** (if inbound is allowed, the outbound return traffic is organically permitted).
  3. **Rules:** NACLs support both `ALLOW` and `DENY` rules using numbered precedence. SGs exclusively support `ALLOW` rules (everything else is implicitly denied).
- **Production Scenario:** A web server needs to process HTTPS. The Architect adds Port 443 Inbound to the Security Group (which automatically allows the outbound response). However, on the NACL, the Architect must explicitly write an Inbound Rule for Port 443, AND write an Outbound Rule for Ephemeral Ports (1024-65535) to allow the response to exit.
- **Interview Edge:** *"The 'Stateless' nature of NACLs forces engineers to deeply understand ephemeral ports. If you open Port 80 Inbound on a NACL but forget to open Ephemeral Ports Outbound, the connection will establish but the data response will be mathematically trapped inside the subnet."*

## 1️⃣5️⃣3️⃣ Q153: How many Network ACLs can you associate with a subnet?
- **Short Answer:** Exactly **One**. A subnet physically cannot be governed by multiple NACLs simultaneously.
- **Production Scenario:** An Architect attempts to attach `NACL-A` (Database Rules) and `NACL-B` (Web Rules) to the same subnet. AWS explicitly blocks this. The Architect must natively construct a single, combined `NACL-C` and bind it to the subnet mathematically.
- **Interview Edge:** *"While a Subnet can only have one NACL, a single NACL can be associated with multiple Subnets. I leverage this to apply a unified 'Corporate Security Baseline' across dozens of subnets concurrently."*

## 1️⃣5️⃣4️⃣ Q154: What is the default behavior of a new Network ACL?
- **Short Answer:** This is a lethal trick question. It depends strictly on *how* it was made. The **Default NACL** (which is created automatically when a VPC is born) is implicitly open (ALLOWS all inbound/outbound). A **Custom NACL** (one that you create manually) is implicitly closed (DENIES *all* inbound/outbound traffic until you add rules).
- **Production Scenario:** A Junior Developer creates a custom NACL and attaches it immediately to the Production Database Subnet before adding any rules. The database instantly goes offline because the newly associated custom NACL defaults to `DENY ALL`.
- **Interview Edge:** *"Differentiating between the 'Default VPC NACL' (allow all) and a 'Custom NACL' (deny all) is a classic architect exam trap perfectly designed to test production-level risk awareness."*

## 1️⃣5️⃣5️⃣ Q155: How do you create a Network ACL in AWS?
- **Short Answer:** Open the VPC Console -> Click **Network ACLs** -> Click **Create network ACL** -> Specify a Name and strictly select the target VPC -> Click **Create network ACL**.
- **Production Scenario:** Using Terraform to provision an `aws_network_acl` and explicitly writing `aws_network_acl_rule` blocks to define the exact baseline security posture before attaching it to critical infrastructure.
- **Interview Edge:** *"Creation is entirely isolated from association. When you create a NACL, it just mathematically floats in the VPC until you explicitly map it to a Subnet Route Table."*

## 1️⃣5️⃣6️⃣ Q156: Can you modify a Network ACL after it has been associated with a subnet?
- **Short Answer:** Yes, entirely dynamically. Any rules you add, delete, or re-prioritize take effect almost instantaneously (within seconds) for all running infrastructure inside the attached subnet.
- **Production Scenario:** Security detects active lateral movement from a breached server. The Architect modifies the active NACL, deleting the inter-subnet ALLOW rules, and severing the infected subnet from the rest of the AWS network instantly.
- **Interview Edge:** *"While SGs govern individual instance interfaces, modifying a NACL allows me to structurally quarantine an entire blast radius of 500 EC2 instances simultaneously with a single API call."*

## 1️⃣5️⃣7️⃣ Q157: Can you use a Network ACL to block traffic from specific IP addresses?
- **Short Answer:** Yes. Because NACLs uniquely support `DENY` rules (unlike SGs), they are historically the primary tool in AWS utilized to block malicious IPs.
- **Production Scenario:** A specific competitor's IP address (`88.77.66.55/32`) is scraping your web application. You create a NACL Inbound Rule numbered `50` (high priority) explicitly setting the action to `DENY` for that exact IP.
- **Interview Edge:** *"While NACLs can block IPs, AWS WAF (Web Application Firewall) is vastly superior for this today. NACLs have rigid rule limits; WAF can dynamically block thousands of malicious IPs automatically at the CloudFront/ALB layer before it ever reaches the VPC network."*

## 1️⃣5️⃣8️⃣ Q158: How can you test the effectiveness of a Network ACL?
- **Short Answer:** You test practically by initiating network requests (Ping/SSH/Curl) from a controlled outside EC2 instance (e.g., in a different VPC/Subnet) to verify the target Subnet mathematically drops the packet without response. 
- **Production Scenario:** The Architect deploys a `DENY Port 22` (SSH) rule on the public NACL. To test, they attempt to SSH into a bastion host from the open internet. The connection simply times out indefinitely because the NACL silently drops the traffic.
- **Interview Edge:** *"When a NACL denies traffic, it drops it silently (blackholing). It does not send a TCP RST (reset) packet. Testing feels like shouting into a void because the connection just organically hangs until timeout."*

## 1️⃣5️⃣9️⃣ Q159: How can you log Network ACL traffic?
- **Short Answer:** You utilize **VPC Flow Logs**. Flow logs capture the 'Action' (`ACCEPT` or `REJECT`), allowing you to precisely see which traffic was permitted to cross the NACL boundary and which packets were structurally destroyed.
- **Production Scenario:** An Architect pipes VPC Flow Logs directly into an S3 bucket, and uses Amazon Athena SQL queries where `action = 'REJECT'` to identify exactly which external IPs are probing the NACL for open database ports.
- **Interview Edge:** *"VPC Flow Logs are critical for proving compliance. When an auditor asks 'How do you prove that internal traffic is not leaking out of the subnet?', the only mathematically sound proof is executing Athena queries against Flow Log REJECT patterns."*

## 1️⃣6️⃣0️⃣ Q160: What is the order of precedence for Network ACL rules?
- **Short Answer:** Rules are evaluated strictly in sequential numerical order, starting from the lowest rule number. The moment the NACL matches a packet to a rule, it instantly executes that rule's logic (`ALLOW` or `DENY`) and ceases all further evaluation for that specific packet.
- **Production Scenario:** The NACL has Rule 100: `DENY 10.0.1.55`. It has Rule 200: `ALLOW 10.0.0.0/16`. If IP `10.0.1.55` attempts to enter, it is dropped at Rule 100, and Rule 200 is never evaluated.
- **Interview Edge:** *"This is why Senior Architects always leave massive gaps when numbering NACL rules (e.g., 100, 200, 300). If you number them 1, 2, 3, and later need to securely inject a critical DENY rule between 1 and 2, you are physically unable to without completely deleting and rewriting the rule stack."*

## 1️⃣6️⃣1️⃣ Q161: How can you troubleshoot issues with a Network ACL?
- **Short Answer:** 1) Ensure the numerical rule evaluation logic isn't flawed (e.g., a broad ALLOW overriding a specific DENY). 2) Verify Ephemeral Ports (1024-65535) are explicitly opened on the outbound rules. 3) Leverage VPC Flow Logs to trace the exact numerical packet drop.
- **Production Scenario:** A developer is baffled because their web server (allowed Port 80 Inbound) cannot respond to users. The Architect traces the logic and identifies the NACL Outbound Rules are missing exactly Ephemeral Port `32768`, strangling the return traffic statically.
- **Interview Edge:** *"99% of all 'broken' NACL deployments are the direct result of Engineers not understanding Ephemeral Ports. Because NACLs are stateless, you MUST explicitly allow high-numbered ports outbound so the server can legally reply to the client."*

## 1️⃣6️⃣2️⃣ Q162: What is the maximum number of rules you can have in a Network ACL?
- **Short Answer:** By default, AWS supports 20 numbered rules per NACL (incoming and outgoing separately). You can aggressively request a quota increase up to a hard limit of **40 rules**, but the AWS console historically supported scaling limits mathematically up to 32,767 rule *numbers*. (Note: The user's prompt notes 32,767. While AWS permits numbering from 1 to 32766, the actual structural limit of *enforced* rules is 40 due to network processing latency limits).
- **Production Scenario:** An Architect attempts to dump 500 malicious IP addresses into a single NACL. The API aggressively rejects it because it vastly exceeds the 40-rule structural quota limit. 
- **Interview Edge:** *"A Senior Architect knows you never use a NACL to manage thousands of IP blocks. Because AWS evaluates NACL rules sequentially on every single packet, having massive rule sets exponentially increases network latency. If you hit rule limits, you pivot immediately to AWS WAF or AWS Network Firewall."*

## 1️⃣6️⃣3️⃣ Q163: Can you apply a Network ACL to multiple subnets?
- **Short Answer:** Yes. This is standard architectural practice. A single NACL can serve as the baseline parameter for 50 different subnets simultaneously.
- **Production Scenario:** An Enterprise has 10 identical Web Subnets distributed across multiple Availability Zones. The Architect builds a single `NACL-Web-Baseline` and maps it directly to all 10 subnets, eliminating configuration drift.
- **Interview Edge:** *"While 1 NACL maps to many Subnets natively, remember the inverse rule: 1 Subnet can only be mapped to exactly 1 NACL. You cannot stack NACLs on a subnet like you can stack Security Groups on an EC2 instance."*

## 1️⃣6️⃣4️⃣ Q164: How do you troubleshoot a situation where traffic is not passing through a Network ACL?
- **Short Answer:** 1) Confirm the Subnet is actually associated with the NACL. 2) Check the `*` (Asterisk) rule at the bottom of the NACL, which is the system-enforced explicit `DENY ALL` catch-all. 3) Cross-reference the Security Groups. (If the NACL allows traffic but the SG denies it, the connection still fails).
- **Production Scenario:** A junior admin allows Port 3306 on the NACL. The ping still fails. The Architect checks the EC2 Security Group and realizes the SG does not have Port 3306 open. Security in AWS is an intersection; both the NACL and SG must structurally agree.
- **Interview Edge:** *"When troubleshooting, I always verify Ephemeral Return ports first, then verify the exact rule precedence order. A high-priority (low number) ALLOW rule covering `0.0.0.0/0` will completely override and break any specific DENY rules below it."*

## 1️⃣6️⃣5️⃣ Q165: Can you block traffic based on the protocol or port number using a Network ACL?
- **Short Answer:** Yes, structurally. NACL rules allow granular control over Protocol (TCP/UDP/ICMP), Port Range (e.g., 22, 1024-65535), and Source/Destination CIDR block.
- **Production Scenario:** The Architect explicitly blocks all ICMP (Ping) traffic entering the Database Subnet by creating an Inbound Rule matching Protocol `ICMP`, setting the action to `DENY`, and executing it at high priority (Rule 50).
- **Interview Edge:** *"While NACLs block Layer 4 ports beautifully, they are entirely blind to Layer 7 (Application) logic. A NACL can block Port 80, but it mathematically cannot block a SQL Injection attack traversing Port 80—that requires a Web Application Firewall (WAF)."*

## 1️⃣6️⃣6️⃣ Q166: Can you prioritize rules in a Network ACL?
- **Short Answer:** Yes, strictly through the numerical numbering system (1 to 32766). The lower the number, the higher the mathematical priority.
- **Production Scenario:** Rule 10: `DENY 10.0.0.55`. Rule 20: `ALLOW 10.0.0.0/16`. Because Rule 10 is numerically lower, it intercepts the `.55` IP and drops it before Rule 20 can allow it.
- **Interview Edge:** *"If two engineers try to create the exact same rule number simultaneously via the API, the second API call fails structurally. Rule numbers are effectively unique execution indexes."*

## 1️⃣6️⃣7️⃣ Q167: Can you use a Network ACL to allow traffic between subnets in different VPCs?
- **Short Answer:** Yes, but only if the routing layer legally permits it via VPC Peering or Transit Gateway. If VPC peering is established, the NACL can explicitly match the opposing VPC's CIDR block and apply allow/deny logic to it.
- **Production Scenario:** VPC A (`10.1.0.0/16`) is peered to VPC B (`10.2.0.0/16`). The Architect places a NACL on VPC A's database subnet that explicitly states: `ALLOW 10.2.0.0/16 Port 5432 Inbound`.
- **Interview Edge:** *"A NACL cannot 'create' connectivity; it can only parse it. If you allow a subset of IPs in the NACL but VPC peering does not exist, the physical packets will simply die at the Route Table layer before they ever reach the NACL."*

## 1️⃣6️⃣8️⃣ Q168: Can you use a Network ACL to block traffic from specific protocols?
- **Short Answer:** Yes, you can block any standard network protocol (like TCP, UDP, ICMP) or block all protocols entirely (`-1` or `ALL`) based on the rule configuration sequence.
- **Production Scenario:** A high-security financial backend completely denies all UDP traffic from entering the subnet (since UDP is commonly utilized in volumetric amplification attacks) while safely allowing strictly required TCP streams.
- **Interview Edge:** *"Because a NACL sits at the Subnet perimeter, blocking a protocol on the NACL instantly protects every single elastic network interface inside that subnet, guaranteeing total protocol eradication at the macro architectural level."*
