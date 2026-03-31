# 🚀 AWS Interview Cheat Sheet: INTERNET GATEWAYS (Q40–Q49)

*This master reference sheet details the critical mechanics of creating, attaching, detaching, and routing traffic through an Amazon VPC Internet Gateway (IGW).*

---

## 📊 The Master Internet Gateway Architecture

```mermaid
graph TD
    subgraph "The Public Internet"
        World([🌐 Global Customer Traffic])
    end
    
    subgraph "Amazon VPC - Network Perimeter"
        
        subgraph "VPC Edge Attachment (Q42 / Q44)"
            IGW[🚪 Internet Gateway <br/> Status: Attached]
            Detached[❌ Detached IGW <br/> Status: Detached]
        end
        
        subgraph "Route Table Layer (Q45 / Q47)"
            Main[🔀 Main Route Table <br/> No IGW Route (Private)]
            Custom[🔀 Custom Route Table <br/> 0.0.0.0/0 -> IGW]
        end
        
        subgraph "Subnet Layer"
            Pub_Sub[🌥️ Public Subnet <br/> Needs Public IPs]
            Priv_Sub[🔒 Private Subnet]
        end
        
        IGW <==>|Bi-directional Traffic| Custom
        Custom -. "Explicit Association (Q48)" .-> Pub_Sub
        Main -. "Implicit Association" .-> Priv_Sub
        
        Detached -. "Cannot route data <br/> until Attached (Q41)" .-> Main
    end
    
    World <==>|Inbound / Outbound| IGW
    
    style World fill:#2980b9,color:#fff
    style IGW fill:#27ae60,color:#fff
    style Detached fill:#c0392b,color:#fff
    style Main fill:#7f8c8d,color:#fff
    style Custom fill:#f39c12,color:#fff
    style Pub_Sub fill:#27ae60,color:#fff
    style Priv_Sub fill:#c0392b,color:#fff
```

---

## 4️⃣0️⃣ Q40: Can you explain what an internet gateway is in AWS VPC?
- **Short Answer:** An Internet Gateway (IGW) is a horizontally scaled, highly-available, redundant AWS managed component. It physically attaches to the perimeter of your VPC, enabling two-way communication between the instances inside your VPC and the external public internet.
- **Production Scenario:** You deploy an Application Load Balancer to serve your website. Without an IGW attached to the VPC, external customers physically cannot hit the Load Balancer IP address.
- **Interview Edge:** *"An IGW serves two distinct purposes: providing a physical target in your route tables for internet-routable traffic, and transparently performing Network Address Translation (NAT) for EC2 instances that possess public IPv4 addresses."*

## 4️⃣1️⃣ Q41: Can you explain how you can create an internet gateway in AWS VPC?
- **Short Answer:** Open the VPC Console -> Navigate to **Internet Gateways** -> Click **Create Internet Gateway** -> Assign a Name tag -> Click **Create**. Following creation, you must explicitly **Attach** it to a specific VPC.
- **Production Scenario:** Writing a Terraform module where the `aws_internet_gateway` resource must strictly depend on the `aws_vpc` resource existing first.
- **Interview Edge:** *"Creating an IGW simply generates the virtual appliance. In a disconnected state, it is completely inert. It does nothing until it is explicitly attached to a VPC boundary."*

## 4️⃣2️⃣ Q42: Can you explain how you can attach an internet gateway to a VPC in AWS?
- **Short Answer:** Once the IGW is created, select it in the VPC Console -> Click the **Actions** dropdown -> Choose **Attach to VPC** -> Select your target VPC from the list -> Click **Attach**.
- **Production Scenario:** Connecting a newly built isolated VPC to the internet so that instances inside it can download operating system patches directly.
- **Interview Edge:** *"A strict architectural rule: A VPC can only have exactly ONE Internet Gateway attached to it at any given time. You cannot attach multiple IGWs for 'extra bandwidth' because IGWs already scale infinitely by design."*

## 4️⃣3️⃣ Q43: Can you explain how you can check if an internet gateway is attached to a VPC in AWS?
- **Short Answer:** In the VPC Console, select the specific Internet Gateway and look at the **Details** pane at the bottom of the screen. The **State** column will clearly read either `Attached` or `Detached`, and the **VPC ID** will display the connected network.
- **Production Scenario:** Troubleshooting an outage where web servers suddenly lost internet access. The Architect checks the IGW state to confirm someone didn't accidentally tear down the attachment.
- **Interview Edge:** *"In an enterprise environment, checking attachment status is typically done programmatically via the AWS CLI (`aws ec2 describe-internet-gateways`) during automated network audits."*

## 4️⃣4️⃣ Q44: Can you explain how you can detach an internet gateway from a VPC in AWS?
- **Short Answer:** Select the IGW in the console -> Click **Actions** -> Choose **Detach from VPC** -> Confirm the detachment. 
- **Production Scenario:** An active security breach is detected. To instantly amputate the entire VPC from the internet and stop data exfiltration, the SOC team rapidly detaches the Internet Gateway, dropping all external connections immediately.
- **Interview Edge:** *"You physically cannot detach an IGW if you have mapped Public IPs or Elastic IPs to resources within the VPC. AWS hard-blocks the detachment; you must un-map the IPs or terminate the instances first."*

## 4️⃣5️⃣ Q45: Can you explain what happens to the route table when an internet gateway is attached to a VPC in AWS?
- **Short Answer:** *Nothing happens automatically in custom configurations.* Technically, AWS *sometimes* adds a default route to the Main Route Table in the Default VPC. However, in a custom VPC, attaching an IGW just creates the physical connection; you must manually add the `0.0.0.0/0` route to your Route Table.
- **Production Scenario:** An engineer attaches an IGW and assumes the VPC is public. They realize instances still can't hit the internet because they forgot to actually write the route targeting the IGW.
- **Interview Edge:** *"Attaching the IGW is like plugging the internet cable into a router. Writing the `0.0.0.0/0 -> IGW` rule in the Route Table is configuring the software to actually send data down that cable."*

## 4️⃣6️⃣ Q46: Can you explain how you can create a custom route table in AWS VPC?
- **Short Answer:** Open the VPC Console -> Click **Route Tables** -> Click **Create Route Table** -> Provide a name -> Select the target VPC -> Click **Create**. Next, you must associate it with subnets.
- **Production Scenario:** Establishing a dedicated 'Public' tier. The Architect creates a Custom Route Table specifically isolation Public Subnets from the implicitly assigned Main Route Table.
- **Interview Edge:** *"Creating a custom route table inherently establishes an explicit boundary. Until you add external routes, it acts as a perfectly secure local-only routing zone."*

## 4️⃣7️⃣ Q47: Can you explain the difference between the main route table and custom route tables in AWS VPC?
- **Short Answer:** The **Main Route Table** is the default fallback; any subnet created without an explicit association is implicitly controlled by it. **Custom Route Tables** are user-defined and explicitly bound to specific subnets to override the default behavior.
- **Production Scenario:** Leaving the Main Route Table entirely private. By doing this, if a junior script automatically creates subnets without routing logic, they fall into the Private Main Route Table, preventing accidental internet exposure.
- **Interview Edge:** *"The Main Route Table is the ultimate fallback net. Modifying the Main Route Table to have an IGW route is universally considered an extreme security anti-pattern."*

## 4️⃣8️⃣ Q48: Can you explain how you can associate a custom route table with a subnet in AWS VPC?
- **Short Answer:** Select the Custom Route Table -> Click the **Subnet Associations** tab -> Click **Edit subnet associations** -> Check the box next to your target Subnet -> Click **Save associations**.
- **Production Scenario:** Explicitly binding three Web Subnets spanning three Availability Zones to a single Custom Public Route Table to uniformize internet routing.
- **Interview Edge:** *"When you associate a subnet with a Custom Route Table, it instantly strips the subnet from the Main Route Table. A subnet can only have one master."*

## 4️⃣8️⃣ Q48: Can you explain how you can create a route in a custom route table in AWS VPC?
- **Short Answer:** Select the Route Table -> Click the **Routes** tab -> Click **Edit routes** -> Click **Add route**. Enter a destination (e.g., `0.0.0.0/0`) and select a Target (e.g., `igw-xxxxxxxx`). Click **Save changes**.
- **Production Scenario:** Modifying a Private Route table to point `0.0.0.0/0` strictly to a NAT Gateway rather than an Internet Gateway.
- **Interview Edge:** *"Routing relies on specificity. If I add a broad `0.0.0.0/0` route to the IGW, but a hyper-specific `10.50.0.0/16` route to a VPC Peering connection, AWS automatically honors the more specific peering route first."*

## 4️⃣9️⃣ Q49: Can you explain how you can delete a custom route table in AWS VPC?
- **Short Answer:** Select the Route Table -> Click **Actions** -> **Delete route table**. You will be blocked from deleting it if it currently has active Subnet associations.
- **Production Scenario:** Cleaning up legacy infrastructure. The Architect must first disassociate all 5 subnets (returning them to the Main Route table) before AWS allows the deletion of the custom table.
- **Interview Edge:** *"Dependencies block deletion in AWS. Furthermore, you cannot ever delete the 'Main Route Table' of a VPC. You can only delete user-created Custom tables."*
