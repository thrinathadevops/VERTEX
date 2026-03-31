# 🚀 AWS Interview Cheat Sheet: ELASTIC IPs (Q70–Q86)

*This master reference sheet breaks down the architectural nuances of Elastic IPs (EIPs)—specifically focusing on their static nature, their binding to Network Interfaces (ENIs), and the unique billing models AWS enforces to prevent IP hoarding.*

---

## 📊 The Master Elastic IP (EIP) Binding Architecture

```mermaid
graph TD
    subgraph "AWS Global IPv4 Pool"
        Pool[🌊 AWS Public IPv4 Address Pool]
    end
    
    subgraph "Your AWS Account (us-east-1)"
        EIP[📌 Elastic IP: 54.21.99.111 <br/> State: Allocated to Account]
        
        subgraph "Amazon VPC - Public Subnet"
            EC2_A[🖥️ EC2 Instance A <br/> Active Web Server]
            ENI_A[🔌 Network Interface A <br/> Private IP: 10.0.1.55]
            EC2_A --- ENI_A
            
            EC2_B[🖥️ EC2 Instance B <br/> Standby Web Server]
            ENI_B[🔌 Network Interface B <br/> Private IP: 10.0.1.77]
            EC2_B --- ENI_B
        end
    end
    
    Pool ==>|1. Allocate (Q72)| EIP
    
    EIP ==>|2. Associate (Q73)| ENI_A
    EIP -. "3. Rapid Re-Map <br/> on Failure (Q71)" .-> ENI_B
    
    style Pool fill:#2980b9,color:#fff
    style EIP fill:#8e44ad,color:#fff
    style EC2_A fill:#27ae60,color:#fff
    style EC2_B fill:#7f8c8d,color:#fff
    style ENI_A fill:#e67e22,color:#fff
    style ENI_B fill:#e67e22,color:#fff
```

---

## 7️⃣0️⃣ Q70: What is an Elastic IP in AWS?
- **Short Answer:** An Elastic IP (EIP) is a static, persistent public IPv4 address that you permanently allocate to your AWS account. Unlike standard ephemeral public IPs (which violently change every time an EC2 instance stops/starts), an EIP belongs to you until you explicitly release it back to AWS.
- **Production Scenario:** You hardcode an IP address into a third-party corporate firewall whitelist. If you use a normal AWS Public IP, the moment your EC2 instance reboots, the IP changes, and the firewall blocks you. Using an EIP guarantees your whitelisted IP never changes.
- **Interview Edge:** *"An EIP physically abstracts the underlying compute from the network layer. It allows me to seamlessly mask instance failures by rapidly unbinding the EIP from a dead server and immediately binding it to a healthy replacement server."*

## 7️⃣1️⃣ Q71: What are some practical use cases for Elastic IPs in AWS?
- **Short Answer:** The primary usages include: 1) Hardcoding static Public IPs for external DNS (`A Records`), 2) Providing IP stability for third-party Vendor Whitelisting, and 3) Binding to a NAT Gateway to ensure all outbound private traffic presents a single, unified static IP to the internet.
- **Production Scenario:** A banking partner refuses to accept API requests unless they originate from a known, static IP address. The Architect deploys a NAT Gateway, binds an Elastic IP to it, and routes all private Lambda/EC2 outbound traffic through that NAT.
- **Interview Edge:** *"While ELB (Load Balancers) are the preferred method for ingress web traffic, EIPs are absolutely mandatory for providing static outbound IP addresses strictly required by legacy enterprise firewalls."*

## 7️⃣2️⃣ Q72: How do you allocate an Elastic IP in AWS?
- **Short Answer:** Open the EC2 Console -> Select **Elastic IPs** -> Click **Allocate Elastic IP address** -> Choose the AWS Region pool -> Click **Allocate**. 
- **Production Scenario:** Reserving 3 static IP addresses from the AWS pool before deploying a multi-AZ NAT Gateway architecture via Terraform (`aws_eip` resource).
- **Interview Edge:** *"Allocating an EIP does NOT associate it with a server. Allocation simply pulls the IP from the massive AWS global pool and permanently locks it into your specific AWS Account billing ledger."*

## 7️⃣3️⃣ Q73: How do you associate an Elastic IP with an EC2 instance in AWS?
- **Short Answer:** In the EC2 Console, select the allocated EIP -> Click **Actions** -> choose **Associate Elastic IP address** -> explicitly select the Instance ID (or the ENI ID) -> Click **Associate**.
- **Production Scenario:** A newly launched bastion host needs to be accessible via SSH. The admin selects a previously allocated EIP and associates it with the bastion host's primary ENI.
- **Interview Edge:** *"Architecturally, you aren't actually associating the EIP to the EC2 instance physically; you are mathematically mapping the EIP to the underlying Elastic Network Interface (ENI). The AWS Internet Gateway (IGW) handles the 1-to-1 NAT translation dynamically."*

## 7️⃣4️⃣ Q74: Can you associate an Elastic IP with a running EC2 instance in AWS?
- **Short Answer:** Yes, absolutely. You can hot-swap an EIP onto a running instance with zero downtime. 
- **Production Scenario:** An engineer realizes an active production server is using an ephemeral public IP. They instantly allocate a new EIP and associate it on the fly without stopping the active server application.
- **Interview Edge:** *"While it is hot-swappable, be warned: associating an EIP to an instance that already possesses a standard ephemeral public IP will instantaneously destroy the ephemeral IP, breaking any active connections relying on that old IP."*

## 7️⃣5️⃣ Q75: Can you disassociate an Elastic IP from an EC2 instance in AWS?
- **Short Answer:** Yes. You can disassociate it at any time. Once disassociated, the EIP completely detaches from the instance but remains "Allocated" (owned) by your AWS account.
- **Production Scenario:** Terminating a legacy application server, but explicitly disassociating the EIP first to ensure the company retains ownership of the highly-valuable static IP address for a future application.
- **Interview Edge:** *"Disassociating an EIP is safe, but be aware of the billing trap: AWS actively charges you money for EIPs that are allocated but NOT associated to a running resource."*

## 7️⃣6️⃣ Q76: How many Elastic IPs can you allocate per AWS account?
- **Short Answer:** By default, AWS imposes a strict soft limit of **5 Elastic IPs per Region** per AWS Account. 
- **Production Scenario:** A company tries to deploy its 6th NAT Gateway and receives a `Client.AddressLimitExceeded` error. They must open a Service Quota ticket with AWS Support to increase the EIP limit to 50.
- **Interview Edge:** *"This limit exists to prevent mass IPv4 exhaustion. Because standard IPv4 addresses are a rapidly depleting global commodity, AWS forces you to prove legitimate business justification before granting more than 5."*

## 7️⃣7️⃣ Q77: Is there a cost for using Elastic IPs in AWS?
- **Short Answer:** Yes, but the billing model is counter-intuitive: **AWS charges you explicitly when you are NOT using the EIP.** If the EIP is attached to a *Running* EC2 instance, it is generally free (historically, though AWS recently introduced a small hourly charge for all public IPv4s in 2024). Regardless, leaving an EIP sitting idle in your account unattached generates a strict penalty fee.
- **Production Scenario:** A junior dev spins up 4 EIPs for a weekend project, terminates the EC2 instances, but forgets to release the EIPs. At the end of the month, the company is billed for 4 idle EIPs.
- **Interview Edge:** *"AWS uses financial penalties to combat IP hoarding. If you stop the attached EC2 instance, the EIP immediately begins incurring the 'idle' hourly charge because you are preventing AWS from giving that IP to another customer."*

## 7️⃣8️⃣ Q78: Can you use Elastic IPs with AWS Transit Gateway?
- **Short Answer:** No, not directly. An EIP is a public IP construct designed for edge-internet access (via an IGW). Transit Gateway is a localized Layer-3 router for private IP traffic.
- **Production Scenario:** If a Transit Gateway Spoke VPC needs internet access, the traffic routes from the Spoke VPC -> through the Transit Gateway -> into a centralized Egress VPC -> which translates the traffic out via a NAT Gateway (which has the EIP attached).
- **Interview Edge:** *"You never bind an EIP to a Transit Gateway. You bind it to a NAT Gateway or firewall appliance sitting inside an 'Egress VPC', and point the Transit Gateway routes to that firewall."*

## 7️⃣9️⃣ Q79: How do you release an Elastic IP in AWS?
- **Short Answer:** First, disassociate it from any instance. Then, select the EIP in the console -> go to **Actions** -> select **Release Elastic IP addresses** -> click **Release**.
- **Production Scenario:** Completing the teardown of a staging environment. To stop the hourly "idle EIP" billing penalty, the Architect completely releases the EIPs back into the AWS global pool.
- **Interview Edge:** *"Releasing an EIP is a violently permanent action. Once you release that exact IP back to the AWS pool, another customer will immediately grab it, and you will likely never see that exact IPv4 address again."*

## 8️⃣0️⃣ Q80: What happens to an Elastic IP when you stop an EC2 instance?
- **Short Answer:** The EIP remains mathematically associated to the stopped instance's Network Interface (ENI) and belongs to your account. However, because the instance is no longer "running", AWS instantly begins charging you the idle EIP penalty fee.
- **Production Scenario:** A massive EC2 rendering farm is powered off for the weekend to save compute costs. However, because the 50 servers all hold Elastic IPs, the company gets hit with 50 idle EIP charges over the weekend.
- **Interview Edge:** *"Stopping an instance breaks the free-tier behavior of an EIP. If an EC2 instance is going to be stopped for weeks, a Senior Architect detaches and releases the EIP to prevent financial bleed."*

## 8️⃣1️⃣ Q81: Can you use an Elastic IP with an instance in a different AWS region?
- **Short Answer:** Absolutely not. Elastic IPs are strictly Regional resources. 
- **Production Scenario:** You possess a highly whitelisted EIP in `us-east-1` (Virginia). A disaster hits the region. You physically cannot detach the EIP and attach it to a backup server in `eu-west-1` (Ireland). 
- **Interview Edge:** *"IPv4 blocks are physically leased to specific AWS geographical sub-regions. An IP in Virginia is mathematically un-routable in London. If you need multi-region static IPs, you must use **AWS Global Accelerator**, not standard EIPs."*

## 8️⃣2️⃣ Q82: Can you use an Elastic IP with an instance in a different AWS account?
- **Short Answer:** Historically no, but recently AWS introduced **Bring Your Own IP (BYOIP)** and standard IP sharing features. However, for a generic AWS-allocated EIP, it belongs strictly to the AWS Account ledger that generated it.
- **Production Scenario:** Company A acquires Company B. They cannot simply "transfer" an AWS-allocated EIP from Account A directly to Account B locally.
- **Interview Edge:** *"If an enterprise requires true multi-account IP portability, they must leverage AWS BYOIP (providing their own corporate IP block) or use AWS Resource Access Manager (RAM) for complex IP Address Management (IPAM) pooling."*

## 8️⃣3️⃣ Q83: Can you use an Elastic IP with a network interface?
- **Short Answer:** Yes. In fact, under the AWS hood, an EIP is *always* associated with an Elastic Network Interface (ENI), not the EC2 computational hardware itself.
- **Production Scenario:** Attaching a secondary ENI to a firewall appliance EC2 instance, and binding a dedicated EIP directly to that secondary ENI to isolate management traffic from application traffic.
- **Interview Edge:** *"Associating directly to an ENI is the pro-move for high availability. If the primary EC2 firewall dies, I just detach the entire ENI (which still holds the EIP) and bolt it instantaneously onto the backup EC2 firewall."*

## 8️⃣4️⃣ Q84: Can you use an Elastic IP with a private IP address?
- **Short Answer:** Yes. This is mechanically how an EIP works. When you associate an EIP, you strictly map it to a specific Private IP address residing on an ENI.
- **Production Scenario:** An EC2 instance has a primary Private IP (`10.0.1.55`) and a secondary Private IP (`10.0.1.77`). The Architect maps the EIP explicitly to the `.77` private IP. Any external internet traffic hitting the EIP securely translates via the Internet Gateway down to the `.77` internal address.
- **Interview Edge:** *"An EIP fundamentally relies on 1-to-1 static NAT performed at the Internet Gateway boundary. The EC2 instance operating system literally never sees the public Elastic IP; it only sees its Private IP."*

## 8️⃣5️⃣ Q85: Can you reserve an Elastic IP for future use?
- **Short Answer:** Yes, by simply clicking "Allocate" and doing nothing else. It remains permanently in your account.
- **Production Scenario:** Securing 3 critical EIPs on a Monday to submit to a banking partner for a 2-week firewall whitelisting process, even though the actual AWS application won't be built until Friday.
- **Interview Edge:** *"While you can reserve them indefinitely, AWS strictly penalizes this reservation with a fixed hourly invoice. Reserving IPs 'just in case' is a rapid way to inflate cloud billing."*

## 8️⃣6️⃣ Q86: Can you use an Elastic IP with a VPC endpoint?
- **Short Answer:** No. VPC Endpoints (specifically Interface Endpoints aka PrivateLink) are engineered explicitly to keep traffic entirely off the public internet. 
- **Production Scenario:** An EC2 instance securely pushing logs to Amazon S3 via a VPC Gateway endpoint. The traffic routes entirely through the AWS Private Backbone.
- **Interview Edge:** *"An EIP relies on an Internet Gateway. A VPC Endpoint exists specifically to bypass the Internet Gateway. Putting a Public IP on a PrivateLink connection defeats the entire mathematical purpose of the endpoint."*
