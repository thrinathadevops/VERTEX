# 🚀 AWS Interview Cheat Sheet: Advanced ROUTE TABLES (Q30–Q39)

*This master reference sheet covers the explicit routing logic, custom configurations, and troubleshooting mechanics of AWS VPC Route Tables.*

---

## 📊 The Master Route Table Topology Architecture

```mermaid
graph TD
    subgraph "Amazon VPC - Network Routing Layer"
        
        subgraph "Main Route Table (Default / Implicit)"
            Main[🔀 Main Route Table <br/> Target: Local Only]
            SubN[🌥️ Unassociated Subnets]
            Main -. "Implicitly controls" .-> SubN
        end
        
        subgraph "Custom Route Tables (Explicit / User-Defined)"
            Pub[🔀 Custom Public RT <br/> (Q35: IGW Route)]
            Priv[🔀 Custom Private RT <br/> (Q36: NAT Route)]
            Edge[🔀 Custom Edge RT <br/> (Q38: Propagated Routes)]
            
            Pub_Sub[🌥️ Public Subnet]
            Priv_Sub[🔒 Private Subnet]
            
            Pub -. "Explicit Association (Q33)" .-> Pub_Sub
            Priv -. "Explicit Association (Q33)" .-> Priv_Sub
        end
        
        IGW[🌐 Internet Gateway]
        NAT[🔄 NAT Gateway]
        VGW[🛡️ Virtual Private Gateway <br/> (BGP Propagation)]
        Dead[☠️ Deleted VPC Peering <br/> (Q37: Blackhole)]
        
        Pub ==>|0.0.0.0/0| IGW
        Priv ==>|0.0.0.0/0| NAT
        VGW -. "Dynamically Injects <br/> Routes via BGP" .-> Edge
        Priv -. "10.200.0.0/16 <br/> Status: Blackhole" .-> Dead
    end
    
    style Main fill:#7f8c8d,color:#fff
    style Pub fill:#f39c12,color:#fff
    style Priv fill:#8e44ad,color:#fff
    style Edge fill:#2980b9,color:#fff
    style IGW fill:#27ae60,color:#fff
    style NAT fill:#d35400,color:#fff
    style VGW fill:#8e44ad,color:#fff
    style Dead fill:#c0392b,color:#fff
```

---

## 3️⃣0️⃣ Q30: What is a route table in AWS VPC and how is it used?
- **Short Answer:** A route table is a set of explicit rules (routes) that dictate exactly where network traffic is physically directed from within a VPC. Every subnet must be associated with a route table to function.
- **Production Scenario:** A web server needs to send an API request to a 3rd-party payment gateway. The route table evaluates the destination IP, matches it against the `0.0.0.0/0` rule, and directs the packets to the Internet Gateway.
- **Interview Edge:** *"A route table is the directional brain of the subnet. Without a route table, a subnet is essentially a blind, isolated vacuum; traffic simply cannot leave the local CIDR block."*

## 3️⃣1️⃣ Q31: Can you explain the difference between a main route table and a custom route table in AWS VPC?
- **Short Answer:** The **Main Route Table** is automatically generated upon VPC creation and implicitly controls any subnet that you haven't assigned a specific route table to. A **Custom Route Table** is manually created by the user to forcefully establish granular, explicit routing intelligence (like isolating private databases).
- **Production Scenario:** A junior developer creates 10 subnets but forgets to associate them with anything. AWS autonomously assigns them to the Main Route Table to ensure they don't break.
- **Interview Edge:** *"As a strict security baseline, I always leave the Main Route Table completely empty (local routes only). I then explicitly build Custom Route Tables for Public and Private tiers. This guarantees no subnet is ever accidentally exposed to the internet by default."*

## 3️⃣2️⃣ Q32: How do you create a custom route table in AWS VPC?
- **Short Answer:** Programmatically via Terraform/CloudFormation, or manually by navigating to the AWS VPC Console -> Selecting **Route Tables** -> Clicking **Create Route Table** -> and binding it to your target VPC.
- **Production Scenario:** Designing a 3-tier architecture from scratch. The Architect creates three Custom Route Tables: `RT-Public`, `RT-Private-App`, and `RT-Private-DB`.
- **Interview Edge:** *"Creating the Route Table is just step one. An empty Custom Route Table only possesses the default 'Local' route, meaning it operates as a perfectly locked-down private perimeter until you explicitly add egress rules."*

## 3️⃣3️⃣ Q33: How do you associate a subnet with a custom route table in AWS VPC?
- **Short Answer:** In the VPC Console, select the Subnet, navigate to **Actions** -> **Edit route table association**, explicitly select the newly created Custom Route Table, and save the configuration.
- **Production Scenario:** Moving a subnet from the 'Main Route Table' into the `RT-Public` route table specifically to allow the EC2 instances inside it to become public-facing web servers.
- **Interview Edge:** *"Subnet Association is a strict 1-to-1 relationship. If you associate a subnet with a Custom Route Table, it instantly and permanently breaks its implicit tie to the Main Route Table."*

## 3️⃣4️⃣ Q34: How do you add a route to a custom route table in AWS VPC?
- **Short Answer:** In the VPC Console, click the Route Table, select the **Routes** tab, click **Edit routes**, and specify a Target CIDR block mapped to a specific AWS Resource ID (e.g., `igw-12345`).
- **Production Scenario:** Allowing a private server to talk directly to Amazon S3. The Architect adds a route targeting the specific S3 Prefix List and points it to a **VPC Gateway Endpoint** ID.
- **Interview Edge:** *"When adding routes, AWS uses the 'Longest Prefix Match' logic. If you have a route for `10.0.0.0/16` and a more specific route for `10.0.1.0/24`, AWS mathematically honors the more specific `/24` route first."*

## 3️⃣5️⃣ Q35: Can you explain how you can route traffic to a specific internet gateway in AWS VPC?
- **Short Answer:** You physically attach an Internet Gateway (IGW) to the VPC boundary. Then, inside your Custom Route Table, you add a route where the **Destination** is `0.0.0.0/0` (representing the entire internet) and the **Target** is the specific Internet Gateway ID.
- **Production Scenario:** Transforming a dead, private subnet into a live, public-facing Web Subnet capable of hosting active Load Balancers.
- **Interview Edge:** *"The absolute definition of a 'Public Subnet' is any subnet organically tied to a Route Table that possesses a `0.0.0.0/0` route pointing to an actively attached IGW."*

## 3️⃣6️⃣ Q36: Can you explain how you can route traffic to a specific NAT gateway in AWS VPC?
- **Short Answer:** You deploy a NAT Gateway into a *Public Subnet*. Then, you open the Private Subnet's Route Table, add a route for `0.0.0.0/0`, and explicitly set the **Target** to the NAT Gateway ID.
- **Production Scenario:** A deeply hidden database server needs to download severe Linux kernel security patches. The Route Table securely proxies that outbound request through the NAT Gateway.
- **Interview Edge:** *"The most common junior routing mistake is putting the NAT Gateway inside the Private Subnet. It must sit in the Public Subnet (so it has an IGW route) while the Private Route Table specifically targets the NAT."*

## 3️⃣7️⃣ Q37: Can you explain what a blackhole route is in AWS VPC?
- **Short Answer:** A **Blackhole Route** occurs when a Route Table points traffic toward a physical networking device (like an EC2 ENI, a NAT Gateway, or a VPC Peering Connection) that has been deleted or utterly destroyed.
- **Production Scenario:** An engineer excitedly deletes an old VPC Peering connection. However, the Route Table still permanently attempts to forward `10.50.0.0/16` traffic to the dead connection. The AWS Console visibly flags this route as `Status: Blackhole`, and all traffic silently drops.
- **Interview Edge:** *"If a support ticket claims '100% packet loss to a specific IP range', my very first instinct is to check the Route Table for the 'Blackhole' status flag, which instantly confirms the target gateway was improperly decommissioned."*

## 3️⃣8️⃣ Q38: Can you explain what a propagated route is in AWS VPC?
- **Short Answer:** Route Propagation autonomously injects dynamic routes directly into a Custom Route Table, usually driven by external BGP (Border Gateway Protocol) updates from a Virtual Private Gateway (VGW) connected to an on-premises VPN or Direct Connect.
- **Production Scenario:** A corporate data center brings 5 new internal VLAN networks online. Instead of a Cloud Architect manually typing those 5 new CIDR blocks into every AWS Route Table, BGP autonomously "propagates" those routes directly from the on-premise router into AWS.
- **Interview Edge:** *"Enabling Route Propagation completely eliminates manual routing overhead in hybrid cloud architectures. It allows the AWS Route Table to dynamically learn and map to physical on-premises network changes in real-time."*

## 3️⃣9️⃣ Q39: Can you explain how you can troubleshoot routing issues in AWS VPC?
- **Short Answer:** Methodically trace the IP packets. 1) Check Route Tables for missing `0.0.0.0/0` routes or Blackhole statuses. 2) Check NACLs for subnet-level IP blocks. 3) Check Security Groups for missing inbound/outbound rules. 4) Verify physical gateway attachments (IGW/NAT/VGW).
- **Production Scenario:** A private EC2 instance cannot pull updates. The Architect turns on **VPC Flow Logs**, discovers the NAT Gateway isn't dropping the traffic, and traces the failure mathematically to a missing Route Table entry for the external repository API.
- **Interview Edge:** *"Network troubleshooting is purely systematic. If the packet leaves the EC2 interface but never reaches the NAT Gateway, I know with absolute certainty the failure lies physically within the Route Table logic, not the firewall."*
