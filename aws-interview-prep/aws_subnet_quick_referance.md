# 🚀 AWS Interview Cheat Sheet: Advanced SUBNETS (Q15–Q29)

*This master reference sheet covers deep-dive structural mechanics for Amazon VPC Subnets, Route Tables, CIDR restrictions, and physical Availability Zone boundaries.*

---

## 📊 The Master Subnet Topology Architecture

```mermaid
graph TD
    subgraph "AWS Region (e.g., us-east-1)"
        subgraph "Virtual Private Cloud (VPC CIDR: 10.0.0.0/16)"
            RT_Pub[🔀 Public Route Table <br/> 0.0.0.0/0 -> IGW]
            RT_Priv[🔀 Private Route Table <br/> Local Only]
            
            subgraph "Availability Zone A (us-east-1a)"
                PubA[🌥️ Public Subnet A <br/> 10.0.1.0/24 (Unique)]
                PrivA[🔒 Private Subnet A <br/> 10.0.2.0/24 (Unique)]
            end
            
            subgraph "Availability Zone B (us-east-1b)"
                PubB[🌥️ Public Subnet B <br/> 10.0.3.0/24 (Unique)]
                PrivB[🔒 Private Subnet B <br/> 10.0.4.0/24 (Unique)]
            end
            
            RT_Pub -. "1 Route Table can link to <br/> multiple Subnets (Q26)" .-> PubA
            RT_Pub -. "1 Route Table can link to <br/> multiple Subnets (Q26)" .-> PubB
            
            RT_Priv -. "Routes" .-> PrivA
            RT_Priv -. "Routes" .-> PrivB
        end
        
        IGW[🌐 Internet Gateway]
        DX[🏢 AWS Direct Connect <br/> or Site-to-Site VPN (Q28)]
        
        RT_Pub ==> IGW
    end
    
    DataCenter[🏢 On-Premises Data Center] ==>|Bypasses Internet| DX
    DX ==>|Private Link| RT_Priv
    
    style IGW fill:#2980b9,color:#fff
    style DX fill:#8e44ad,color:#fff
    style RT_Pub fill:#f39c12,color:#fff
    style RT_Priv fill:#f39c12,color:#fff
    style PubA fill:#27ae60,color:#fff
    style PubB fill:#27ae60,color:#fff
    style PrivA fill:#c0392b,color:#fff
    style PrivB fill:#c0392b,color:#fff
    style DataCenter fill:#34495e,color:#fff
```

---

## 1️⃣5️⃣ Question 15: Can you explain what VPC subnets are in AWS?
- **Short Answer:** Subnets are isolated partitions of your master VPC IP address range. While a VPC spans an entire AWS Region, a Subnet is physically constrained to exactly one Availability Zone (AZ). 
- **Production Scenario:** Carving a giant `10.0.0.0/16` network into smaller `10.0.1.0/24` networks so you can organize web servers, app servers, and databases into distinct security tiers.
- **Interview Edge:** *"A VPC is just a logical container. You physically cannot launch an EC2 instance until you create a Subnet to give it a specific IP address space."*

## 1️⃣6️⃣ Question 16: Can you have multiple subnets within the same availability zone in AWS VPC?
- **Short Answer:** Yes. You can create dozens of subnets inside a single Availability Zone, provided their IP ranges (CIDR blocks) do not overlap.
- **Production Scenario:** Creating a Public Subnet (for ALBs), a Private App Subnet (for EC2), and a Private Data Subnet (for RDS) all physically residing inside `us-east-1a`.
- **Interview Edge:** *"Segmenting a single AZ into multiple subnets enables strict, multi-tier 'Defense-in-Depth' architecture locally before scaling regionally."*

## 1️⃣7️⃣ Question 17: Can you have overlapping IP addresses in different subnets in AWS VPC?
- **Short Answer:** Absolutely not. AWS explicitly prohibits overlapping CIDR blocks within the same VPC. Mathematical routing would critically fail if two subnets claimed the exact same IP addresses.
- **Production Scenario:** Trying to assign `10.0.1.0/24` to Subnet A, and then attempting to assign `10.0.1.0/24` to Subnet B. The AWS console will throw a hard error and block the creation.
- **Interview Edge:** *"IP space must be entirely mutually exclusive. If I define a subnet as `10.0.1.0/24`, those 256 IPs belong exclusively to that specific AZ forever."*

## 1️⃣8️⃣ Question 18: Can you move an EC2 instance from one subnet to another in AWS VPC?
- **Short Answer:** Conceptually yes, but mechanically you are just moving the Network Interface. You must stop the EC2 instance, detach the Elastic Network Interface (ENI), and move it—which fundamentally alters its Private IP address.
- **Production Scenario:** You accidentally launch a backend server into a Public Subnet. You must stop it, re-associate its network interface to the Private Subnet, and update any internal DNS records because its private IP changes.
- **Interview Edge:** *"You can't hot-swap subnets on a running instance. Because moving subnets alters the underlying MAC address and Private IP bound to the ENI, you must orchestrate a hard stop/start."*

## 1️⃣9️⃣ Question 19: How can you secure traffic between subnets in AWS VPC?
- **Short Answer:** By combining Network ACLs (NACLs) to establish stateless barriers at the subnet boundaries, and Security Groups (SGs) to establish stateful barriers directly on the EC2 instances.
- **Production Scenario:** Writing a Security Group rule on the Database EC2 that explicitly states: *"Only accept Port 3306 traffic if it originates from the Application Subnet's specific Security Group ID."*
- **Interview Edge:** *"Inter-subnet routing is allowed by default via the 'Local Route'. I secure lateral movement by heavily restricting Instance-level Security Groups."*

## 2️⃣0️⃣ Question 20: Can you explain the difference between a public subnet and a private subnet in AWS VPC?
- **Short Answer:** A Subnet is "Public" if and only if its Route Table contains a direct path (`0.0.0.0/0`) to an Internet Gateway (IGW). If it lacks that route, it is "Private."
- **Production Scenario:** Hosting highly vulnerable backend databases. By ensuring their Route Table lacks an IGW connection, the external internet mathematically cannot reach them.
- **Interview Edge:** *"There is no check-box that says 'Make Public'. A subnet's exposure is dictated 100% by the presence or absence of an IGW target in its attached Route Table."*

## 2️⃣1️⃣ Question 21: Can you launch a public EC2 instance in a private subnet in AWS VPC?
- **Short Answer:** Yes, via Elastic IPs and NAT Gateways. You can give the instance a public-facing Elastic IP, but route the egress traffic out through a NAT Gateway. However, this is fundamentally an architectural anti-pattern.
- **Production Scenario:** A developer tries to expose a backend server by giving it a Public IP, but because it sits in a Private Subnet with no IGW route, inbound internet traffic simply drops dynamically.
- **Interview Edge:** *"Technically possible, but an extreme security violation. Public IPs belong strictly on Load Balancers or Bastion Hosts physically located in Public Subnets."*

## 2️⃣2️⃣ Question 22: Can you create a VPC without any subnets in AWS?
- **Short Answer:** Yes, you can create a VPC without subnets, but it is functionally useless. A VPC is just a logical IP envelope; you cannot launch compute resources without a subnet to anchor them.
- **Production Scenario:** Running a Terraform script that creates the `aws_vpc` resource, but crashes before building the `aws_subnet` resources. The VPC exists, but is a vacuum.
- **Interview Edge:** *"A subnet is the physical execution layer of a VPC. Without them, you have a network blueprint, but no actual floor space to place servers."*

## 2️⃣3️⃣ Question 23: What is the maximum number of subnets you can create per VPC in AWS?
- **Short Answer:** By default, AWS supports 200 Subnets per VPC. The hard limitation is the actual size of your IPv4 CIDR block.
- **Production Scenario:** A `/16` VPC provides 65,536 IPs. If you carve it entirely into massive `/17` subnets (32,000 IPs each), you can mathematically only create 2 subnets before running out of IP space.
- **Interview Edge:** *"The limit is dictated by IP mathematics. You must aggressively plan your CIDR architecture to ensure you don't exhaust your IP blocks before reaching structural capacity."*

## 2️⃣4️⃣ Question 24: Can you change the CIDR block of a subnet after it has been created in AWS VPC?
- **Short Answer:** No. Subnet CIDR blocks are permanently immutable. You must tear down the subnet and recreate it from scratch.
- **Production Scenario:** A DevOps team runs out of IP addresses in a `/24` subnet. They are forced to build a brand new `/16` subnet alongside it, migrate the EC2 instances over, and then delete the old subnet.
- **Interview Edge:** *"Because CIDR blocks are immutable, capacity planning is the most critical phase of Cloud Architecture. You must always provision larger subnets than you currently need to avoid disastrous IP exhaustion."*

## 2️⃣5️⃣ Question 25: Can you explain what the purpose of a route table is in AWS VPC?
- **Short Answer:** It is the directional brain of the VPC. It dictates exactly where network packets are permitted to travel based on Destination IP addresses.
- **Production Scenario:** Writing a rule that says: *"If traffic wants to go to the Internet, route it to the IGW. If traffic wants to go to other servers within our 10.0.0.0/16 block, route it locally."*
- **Interview Edge:** *"A subnet is blind without a Route Table. The Route Table provides explicit routing targets—whether that's an IGW, a NAT Gateway, a VPC Peering connection, or a Transit Gateway."*

## 2️⃣6️⃣ Question 26: Can you have multiple route tables associated with a single subnet in AWS VPC?
- **Short Answer:** No. A Subnet can only be associated with exactly one Route Table at a time. However, a single Route Table can operate multiple Subnets simultaneously.
- **Production Scenario:** Building a single "Public Route Table" with an IGW connection, and explicitly associating it with three different Public Subnets across three different AZs to centralize routing logic.
- **Interview Edge:** *"It is a strict 1-to-1 relationship from the Subnet's perspective. It physically cannot follow two contradictory sets of directions."*

## 2️⃣7️⃣ Question 27: How can you restrict access to resources in a private subnet in AWS VPC?
- **Short Answer:** By utilizing Stateless Network ACLs at the subnet boundary to block entire IP ranges, and Stateful Security Groups on the EC2 instances to strictly whitelist specific application ports.
- **Production Scenario:** Dropping all SSH (Port 22) traffic at the NACL level so hackers can't even ping the Subnet, while the Security Group accepts Port 443 traffic exclusively from the Load Balancer.
- **Interview Edge:** *"I apply the Principle of Least Privilege. I strip all external ingress routes from the Route Table, lock down the NACL, and forcefully restrict Security Groups to internal traffic only."*

## 2️⃣8️⃣ Question 28: Can you connect a VPC to an on-premises data center in AWS?
- **Short Answer:** By utilizing a Site-to-Site VPN (encrypted over the public internet) or AWS Direct Connect (a dedicated, private physical fiber-optic line bypassing the internet).
- **Production Scenario:** A bank headquarters in London needs to connect to AWS. They pay for **AWS Direct Connect** to provision a private 10Gbps fiber line directly into their VPC to guarantee absolute security and zero latency.
- **Interview Edge:** *"For rapid deployment, I use a Site-to-Site VPN bridging a Virtual Private Gateway (VGW). For enterprise-grade compliance requiring consistent bandwidth and no open-web exposure, I mandate AWS Direct Connect."*

## 2️⃣9️⃣ Question 29: Can you create a subnet in a different region than the VPC in AWS?
- **Short Answer:** Absolutely not. A VPC spans an entire Region, but a Subnet is physically hardcoded to exactly one Availability Zone (AZ) within that specific Region.
- **Production Scenario:** A company operates in `us-east-1` (Virginia). They physically cannot build a subnet that stretches into `eu-west-1` (Ireland). They must build a completely new VPC in Ireland and use Inter-Region VPC Peering.
- **Interview Edge:** *"A Subnet is a physical reflection of an Availability Zone. Because AWS data centers do not stretch across continents, Subnets fundamentally cannot cross Regional boundaries."*
