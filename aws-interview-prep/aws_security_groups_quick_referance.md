# 🚀 AWS Interview Cheat Sheet: SECURITY GROUPS (Q169–Q202)

*This master reference sheet breaks down the foundational stateful firewalls of AWS: Security Groups. It explicitly corrects widespread industry misconceptions regarding "Deny" rules and intra-group routing.*

---

## 📊 The Master Security Group (Stateful) Architecture

```mermaid
graph TD
    subgraph "Amazon VPC - Public Subnet"
        subgraph "Instance-Level Firewall Boundary"
            SG[🔒 Web Security Group <br/> Inbound: ALLOW Port 443 <br/> Outbound: ALLOW ALL]
            
            EC2_A[🖥️ EC2 Instance A]
            EC2_B[🖥️ EC2 Instance B]
        end
        
        DB_SG[🔒 DB Security Group <br/> Inbound: ALLOW Port 3306 from Web SG ID]
        RDS[(🗄️ Amazon RDS)]
    end
    
    Client([👨‍💻 Internet User])
    Hacker([🦹 Malicious User])
    
    Client ==>|HTTPS Request| SG
    SG ==>|Allowed (Port 443)| EC2_A
    EC2_A ==>|STATEFUL RETURN: <br/> Bypasses Outbound Rules completely| Client
    
    Hacker -.->|SSH Request (Port 22)| SG
    SG -.-x|Implicit Deny <br/> (Traffic Dropped)| Hacker
    
    EC2_A ==>|Routes via SG Reference| DB_SG
    DB_SG ==> RDS
    
    style SG fill:#f39c12,color:#fff
    style DB_SG fill:#f39c12,color:#fff
    style EC2_A fill:#27ae60,color:#fff
    style EC2_B fill:#27ae60,color:#fff
    style RDS fill:#3498db,color:#fff
    style Client fill:#2980b9,color:#fff
    style Hacker fill:#c0392b,color:#fff
```

---

## 1️⃣6️⃣9️⃣ Q169: What is a Security Group in AWS?
- **Short Answer:** A Security Group (SG) is a fully managed, stateful virtual firewall that governs inbound and outbound traffic strictly at the Elastic Network Interface (ENI) / Instance level. 
- **Production Scenario:** You launch an EC2 web server. To ensure it can accept internet traffic, you map it to a Security Group containing an Inbound Rule explicitly allowing Port 443 from `0.0.0.0/0`.
- **Interview Edge:** *"Unlike network appliances that sit physically in front of a subnet, an AWS Security Group wraps directly around the ENI. This means lateral traffic *between* two instances on the exact same subnet is still rigorously inspected by the Security Group."*

## 1️⃣7️⃣0️⃣ Q170: What is the difference between a Security Group and a Network ACL?
- **Short Answer:** 
  1. **Behavior:** SGs are **Stateful** (return traffic is automatically allowed); NACLs are **Stateless** (return traffic requires explicit outbound rules).
  2. **Attachment layer:** SGs bind to instances (ENIs); NACLs bind to the entire subnets.
  3. **Rule Logic:** SGs only support explicit `ALLOW` rules; NACLs support both `ALLOW` and `DENY` rules.
- **Interview Edge:** *"Security Groups act as a whitelist. Everything is denied by default until explicitly allowed. NACLs act as the perimeter wall that can actively drop malicious traffic before it even reaches the instance."*

## 1️⃣7️⃣1️⃣ Q171: Can you associate multiple Security Groups with an instance?
- **Short Answer:** Yes. You can attach up to 5 Security Groups to a single ENI by default.
- **Production Scenario:** Using a modular architecture. You attach `SG-Web` (allows Port 443), `SG-Management` (allows internal SSH), and `SG-Monitoring` (allows Datadog Agent traffic) concurrently to a single EC2 instance. The AWS Hypervisor evaluates all rules as a combined, unified Allow list.
- **Interview Edge:** *"Stacking Security Groups is a massive enterprise best practice. Instead of creating bloated, messy SGs that cover every port, Senior Architects create atomic, single-purpose SGs (e.g., 'Allows-SSH', 'Allows-Web') and cleanly attach multiples to an instance as needed. This prevents configuration drift."*

## 1️⃣7️⃣2️⃣ Q172: How do you create a Security Group in AWS?
- **Short Answer:** Open the EC2 or VPC Console -> Click **Security Groups** -> Click **Create security group** -> Specify a Name and strictly select the target VPC -> Manually add Inbound and Outbound rules -> Click **Create**.
- **Interview Edge:** *"When using CloudFormation or Terraform to create a Security Group, it is legally required to map it to a specific VPC ID. SGs cannot bridge logically across different VPCs natively."*

## 1️⃣7️⃣3️⃣ Q173: Can you modify a Security Group after it has been associated with an instance?
- **Short Answer:** Yes. Modifying the rules of an SG instantly applies those new firewalls rules dynamically to every single ENI/Instance currently using that group with zero downtime.
- **Production Scenario:** You notice Port 22 is open to the world (`0.0.0.0/0`). You edit the Security Group and delete the Port 22 rule. Within milliseconds, SSH access to 5,000 EC2 instances currently using that group is securely severed.

## 1️⃣7️⃣4️⃣ Q174: What is the default behavior of a new Security Group?
- **Short Answer:** By default, a newly minted Security Group has **NO Inbound Rules** (meaning all incoming traffic is implicitly denied). Conversely, it has exactly one **Outbound Rule** allowing `0.0.0.0/0` (meaning all outbound traffic is implicitly allowed).
- **Interview Edge:** *"The default `0.0.0.0/0` outbound rule is a massive security risk in highly regulated banking environments. A Senior Architect always deletes the default outbound rule and restricts egress strictly to necessary AWS backend services."*

## 1️⃣7️⃣5️⃣ Q175: Can you use a Security Group to block traffic from specific IP addresses?
- **Short Answer:** *CRITICAL ARCHITECTURAL CORRECTION:* **No, you physically cannot create a "DENY" rule in an AWS Security Group.** Security Groups act strictly as a whitelist. If you want to block a specific IP, you either: 1) Do not add it to the ALLOW list, or 2) You deploy an explicit DENY rule in a **Network ACL** or an **AWS WAF**.
- **Interview Edge:** *"This is the most common pitfall in AWS interviews. An interviewer will explicitly ask 'How do I deny IP XYZ in a Security Group?' The only valid Senior answer is: 'You cannot. Security Groups evaluate approvals, not denials. You must drop to the NACL or WAF layer to inject explicit deny logic.'"*

## 1️⃣7️⃣6️⃣ Q176: How can you test the effectiveness of a Security Group?
- **Short Answer:** Execute synthetic network requests (e.g., cURL, Ping, SSH) from a source machine against the target EC2 instance. If the port is not explicitly whitelisted in the Security Group, the connection will indefinitely hang and time out, as SGs silently drop packets without returning a TCP RST notification.
- **Interview Edge:** *"To test effectively at an enterprise scale, I utilize the AWS Reachability Analyzer. It performs complex mathematical proofs across the VPC architecture without actually sending physical packets, pinpointing exactly which SG prevents connectivity."*

## 1️⃣7️⃣7️⃣ Q177: Can you log Security Group traffic?
- **Short Answer:** Yes, entirely through **VPC Flow Logs**. Flow logs capture every packet entering and exiting the ENI, recording the exact Security Group `ACCEPT` or `REJECT` action to CloudWatch Logs or S3.
- **Production Scenario:** Tracing an API outage by querying Athena for Flow Logs where the action is `REJECT` to mathematically prove the EC2 instance is blocking the payload.

## 1️⃣7️⃣8️⃣ Q178: What is the order of precedence for Security Group rules?
- **Short Answer:** *There is no order of precedence.* Unlike NACLs (which execute numbered sequences), AWS evaluates every single Security Group rule simultaneously combined as one massive logical `ALLOW` list. If *any* rule across *any* attached Security Group permits the traffic, the packet passes.
- **Interview Edge:** *"Because SGs lack numbered priority, they cannot conflict. If SG-A allows Port 80, and SG-B allows Port 443, the ENI simply accepts both."*

## 1️⃣7️⃣9️⃣ Q179: How can you troubleshoot issues with a Security Group?
- **Short Answer:** 1) Verify the SG is legally attached to the ENI. 2) Ensure the Inbound Rule maps exactly to the Client IP/Port. 3) Cross-reference the Subnet NACL. (If the NACL blocks it, the packet dies before the SG can ever evaluate it). 4) Query VPC Flow Logs.

## 1️⃣8️⃣0️⃣ Q180: Can you apply a Security Group to multiple instances?
- **Short Answer:** Yes. Applying a single Security Group to hundreds of identically classed EC2 instances (like an Auto Scaling Group) guarantees architectural consistency.

## 1️⃣8️⃣1️⃣ Q181: Can you use a Security Group to allow traffic between instances in different subnets?
- **Short Answer:** Yes. Security Groups transcend subnet boundaries. Because they are fundamentally tied to the Elastic Network Interface (ENI), two instances in entirely completely different subnets can seamlessly communicate as long as their respective SGs allow the traffic.
- **Production Scenario:** A Web Server in the Public Subnet querying a DB Server in the Private Subnet.

## 1️⃣8️⃣2️⃣ Q182: Can you use a Security Group to block traffic based on the protocol or port number?
- **Short Answer:** *ARCHITECTURAL CORRECTION:* SGs **cannot explicitly block (deny)** protocols. SGs restrict access by explicitly *omitting* those ports/protocols from the `ALLOW` configuration. If you do not write an ALLOW rule for UDP, UDP is implicitly blocked.
- **Interview Edge:** *"Always use precise terminology: SGs implicitly omit traffic; NACLs explicitly block traffic."*

## 1️⃣8️⃣3️⃣ Q183: Can you prioritize rules in a Security Group?
- **Short Answer:** No. Because there are no `DENY` rules, there is mathematically no logical requirement for prioritization. Everything is evaluated concurrently as a sheer whitelist.

## 1️⃣8️⃣4️⃣ Q184: Can you use Security Groups to restrict outbound traffic?
- **Short Answer:** Yes. While the default SG configuration allows all outbound egress (`0.0.0.0/0`), you can delete this baseline rule and explicitly lock down egress.
- **Production Scenario:** Hardening a highly compliant database instance by deleting the default Outbound Rule and only allowing outbound API calls to AWS KMS (Port 443) and an internal patch server IP.

## 1️⃣8️⃣5️⃣ Q185: Can you create a Security Group that allows traffic from any IP address?
- **Short Answer:** Yes. You achieve this by setting the Source of the Inbound Rule to `0.0.0.0/0` (for IPv4) and `::/0` (for IPv6).
- **Interview Edge:** *"While technically possible, applying `0.0.0.0/0` to ports like SSH (22) or RDP (3389) is an instantaneous security violation and will aggressively flag your environment in AWS Security Hub."*

## 1️⃣8️⃣6️⃣ Q186: How can you prevent unauthorized access to your instances using Security Groups?
- **Short Answer:** Implement the Principle of Least Privilege. Only expose required HTTP/HTTPS ports to Application Load Balancers (ALBs), completely strip Port 22 (SSH) allocations, and ensure database tiers only accept ingress directly from the exact Security Group ID of the Application tier.

## 1️⃣8️⃣7️⃣ Q187: Can you use Security Groups to restrict access to specific ports?
- **Short Answer:** Yes. Every Security Group rule securely dictates a strict Protocol (TCP/UDP), a strict Port Range (e.g., Port 443), and a strict Source (an IP address or an entire alternative SG ID).

## 1️⃣8️⃣8️⃣ Q188: How can you monitor changes to Security Groups?
- **Short Answer:** Using **AWS CloudTrail**. Every time an engineer executes an API action like `AuthorizeSecurityGroupIngress` or `RevokeSecurityGroupEgress`, CloudTrail logs the timestamp, the IAM User identity, and the exact IP address modifications.

## 1️⃣8️⃣9️⃣ Q189: Can you apply different Security Groups to different network interfaces of an instance?
- **Short Answer:** Yes. If an EC2 instance possesses `eth0` (Public ENI) and `eth1` (Private Backend ENI), you assign `SG-Public` to `eth0` and a vastly stricter `SG-Private` to `eth1`, allowing multi-homed firewall routing on a single piece of compute hardware.

## 1️⃣9️⃣0️⃣ Q190: What is the difference between a Security Group and a Network Security Group (NSG) in Azure?
- **Short Answer:** While both conceptually act as firewalls, AWS SGs bind strictly to Instance ENIs and behave exclusively statefully. Azure NSGs can structurally bind to either single VMs *or* entire Subnets (Azure NSGs effectively combine the mechanical behaviors of both AWS SGs and AWS NACLs into one engine).

*Note: Q191 was omitted in the prompt sequence.*

## 1️⃣9️⃣2️⃣ Q192: Can you use Security Groups to allow traffic between VPCs?
- **Short Answer:** Yes. Upon establishing VPC Peering, Transit Gateway, or PrivateLink, you can seamlessly reference Private IPs across the VPCs in your Security Groups.
- **Interview Edge:** *"In a standard VPC Peering correlation, you can directly reference the actual Security Group ID of the paired VPC within your local Route Table, completely eliminating hardcoded IPs across enterprise accounts."*

## 1️⃣9️⃣3️⃣ Q193: Can you apply Security Groups to resources in other AWS services, such as RDS or Elastic Load Balancing?
- **Short Answer:** Yes. Almost all ENI-backed managed services require SGs. Application Load Balancers, RDS Databases, Redshift clusters, EFS Mount Targets, and Elasticache Memcached nodes all actively leverage Security Groups to mathematically govern ingress algorithms.

## 1️⃣9️⃣4️⃣ Q194: Can you use Security Groups to protect resources in a hybrid cloud environment?
- **Short Answer:** Yes. When connecting over AWS Direct Connect or a VPN tunnel, you simply construct an SG Inbound Rule specifying the specific on-premise IP CIDR block (e.g., `192.168.0.0/16`) to govern exactly which corporate router subnets are allowed to breach the cloud perimeter.

## 1️⃣9️⃣5️⃣ Q195: Can you change the Security Group of an instance while it is running?
- **Short Answer:** Yes. Hot-swapping Security Groups onto a running EC2 instance causes absolutely zero compute downtime or rebooting requirements. The Hypervisor instantly enforces the new connection tracking logic.

## 1️⃣9️⃣6️⃣ Q196: Can you use Security Groups to restrict traffic between instances in the same Security Group?
- **Short Answer:** *ARCHITECTURAL CORRECTION:* Actually, yes! By **default**, instances residing in the exact same Security Group *cannot* communicate with each other. To allow them to talk, you must physically add a 'Self-Referencing' rule (Source = Its own SG-ID). Therefore, avoiding this self-referencing rule technically restricts their lateral traffic indefinitely.
- **Interview Edge:** *"This is an exceptionally common myth. Putting two EC2 instances into the same SG does NOT automatically let them communicate. Without an explicit Self-Ref rule, the hypervisor blocks lateral peer-to-peer traffic natively."*

## 1️⃣9️⃣7️⃣ Q197: Can you assign multiple Security Groups to an instance?
- **Short Answer:** Yes, up to the hard AWS limit of 5 SGs per Network Interface (though this limit can be expanded via an active AWS support quota request).

## 1️⃣9️⃣8️⃣ Q198: How can you troubleshoot connectivity issues with Security Groups?
- **Short Answer:** 1) Audit the Inbound rules (Protocol/Port/Source). 2) Use **AWS Reachability Analyzer** to run path proofs. 3) Cross-check NACLs (which drop unconditionally). 4) Read the destination OS-level firewalls (e.g., Linux `ufw` or Windows Firewall), because AWS SGs cannot bypass OS kernel-level blocks.

## 1️⃣9️⃣9️⃣ Q199: Can you use Security Groups to restrict traffic to and from specific ports and protocols?
- **Short Answer:** Yes. Every Security Group rule must explicitly declare the protocol (TCP/UDP/ICMP/Custom Protocol) and the distinct granular Port Range.

## 2️⃣0️⃣0️⃣ Q200: Can you use Security Groups to block traffic from specific IP addresses?
- **Short Answer:** *ARCHITECTURAL CORRECTION:* No. SGs natively lack explicit DENY capabilities. You explicitly lock out bad actors by fundamentally refusing to place their IP into the `ALLOW` configuration parameters, or by establishing an external WAF/NACL denying their signature.

## 2️⃣0️⃣1️⃣ Q201: Can you use Security Groups to apply different levels of security to different instances?
- **Short Answer:** Yes. Because SGs bind at the ENI level, an Architect deploys vastly different Security Group logic to the Bastion Tier, the Web Tier, the Application Tier, and the Database Tier, establishing robust Defense-in-Depth micro-segmentation.

## 2️⃣0️⃣2️⃣ Q202: How can you ensure that your Security Groups are configured correctly?
- **Short Answer:** Utilizing compliance-auditing pipelines like **AWS Config**. A DevOps engineer deploys AWS Config Rules (e.g., `vpc-sg-open-only-to-authorized-ports`) that constantly scan all SG modifications dynamically. If a developer accidentally opens SSH/22 to `0.0.0.0/0`, AWS Config immediately flags the SG as NON-COMPLIANT and can autonomously trigger an automated remediation Lambda function to delete the rule.
