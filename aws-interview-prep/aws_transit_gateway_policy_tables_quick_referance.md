# 🚀 AWS Interview Cheat Sheet: TRANSIT GATEWAY POLICY TABLES (Q302–Q307)

*This master reference sheet covers Transit Gateway Policy Tables, an advanced structural construct used to enforce macro-level traffic filtering and segmentation at the transit network hub.*

---

## 📊 The Master TGW Policy Table Architecture

```mermaid
graph TD
    subgraph "Hub: AWS Transit Gateway"
        subgraph "Routing vs Filtering Engine"
            RT[🔀 TGW Route Table <br/> 'Where does it go?']
            PT[🛡️ TGW Policy Table <br/> 'Is it legally allowed?']
        end
        
        Assoc_In[📥 Ingress Attachment <br/> (Traffic enters TGW)]
        Assoc_Out[📤 Egress Attachment <br/> (Traffic exits TGW)]
    end
    
    subgraph "Spoke Networks"
        VPC_Dev[(☁️ DEV VPC)]
        VPC_Prod[(☁️ PROD VPC)]
    end
    
    VPC_Dev ==>|1. Packet hits TGW| Assoc_In
    Assoc_In ==>|2. Policy Table Evaluation| PT
    
    PT -. "Match: Block DEV to PROD" .-x|3. Traffic Dropped| PT
    PT ==>|Match: Allow Web Traffic| RT
    
    RT ==>|4. Route Lookup| Assoc_Out
    Assoc_Out ==>|5. Forward to Dest| VPC_Prod
    
    style RT fill:#2980b9,color:#fff
    style PT fill:#c0392b,color:#fff
    style VPC_Dev fill:#f39c12,color:#fff
    style VPC_Prod fill:#27ae60,color:#fff
```

---

## 3️⃣0️⃣2️⃣ Q302: What is a Transit Gateway Policy Table in AWS?
- **Short Answer:** A Transit Gateway Policy Table is an advanced networking construct that allows you to define macro-level `ALLOW` or `BLOCK` filtering logic explicitly for traffic entering or exiting a Transit Gateway Attachment. It serves as a centralized segmentation tool.
- **Production Scenario:** A bank mandates that the generic 'Contractor VPC' can never, under any circumstances, communicate with the 'Vault VPC'. Even if a router accidentally creates a mathematical path between them, the TGW Policy Table explicitly blocks the Traffic natively at the hub, overriding the Route Table.
- **Interview Edge:** *"A Policy Table acts as a macro-firewall governing the entire Spoke network. Instead of managing complex Security Groups inside every single VPC to prevent lateral movement, you enforce the boundary aggressively at the Transit Gateway."*

## 3️⃣0️⃣3️⃣ Q303: How is a Transit Gateway Policy Table different from a Route Table in AWS?
- **Short Answer:** 
  1) **Route Tables** determine *Pathing* ("Where is the IP `10.0.1.55`, and what specific network interface do I send the packet to get it there?"). 
  2) **Policy Tables** determine *Enforcement* ("I know exactly how to get to `10.0.1.55`, but is this source VPC legally authorized to speak to that destination VPC?").
- **Interview Edge:** *"Route Tables are built for connectivity. Policy Tables are built for isolation. If a packet hits the TGW and the Route Table says 'Go left' but the Policy Table says 'Drop', the packet is mathematically destroyed."*

## 3️⃣0️⃣4️⃣ Q304: What are the types of Transit Gateway Policy Tables in AWS?
- **Short Answer:** There are two foundational execution trajectories:
  1) **Ingress:** Evaluates traffic the absolute millisecond it leaves the Spoke VPC and legally enters the Transit Gateway hub.
  2) **Egress:** Evaluates traffic precisely as it prepares to leave the Transit Gateway hub to enter the Destination Spoke VPC.
- **Production Scenario:** An Architect utilizes an Ingress Policy Table on the Public Web VPC Attachment to rigorously drop spoofed IP ranges before they are allowed to theoretically traverse the internal TGW routing engine.

## 3️⃣0️⃣5️⃣ Q305: What are the benefits of using Transit Gateway Policy Tables in AWS?
- **Short Answer:** 
  1) **Global Segmentation:** It provides an incredibly simple, policy-based approach to isolating environments (e.g., blocking PROD from DEV).
  2) **Governance:** It ruthlessly centralizes security. A network engineer cannot accidentally create a route bypassing security because the overarching Policy Table acts as an immutable filtering backstop.
  3) **Reduced Route Table Sprawl:** It eliminates the need to create hundreds of complex 'VRF-lite' isolated Route Tables just to prevent two attachments from talking to each other.

## 3️⃣0️⃣6️⃣ Q306: How are Transit Gateway Policy Tables associated with Transit Gateway Attachments in AWS?
- **Short Answer:** Utilizing the **Attachment Associations** mechanism. When you provision a physical VPC Attachment connecting to the TGW, you explicitly map that specific attachment ID strictly to a specific Policy Table. 
- **Interview Edge:** *"This is highly modular. You can create a single 'Strict-Isolation-Policy' table, and cleanly associate it with 50 different 'Development' VPC attachments. The logic uniformly covers all 50 Spokes instantly."*

## 3️⃣0️⃣7️⃣ Q307: Can Transit Gateway Policy Tables be shared across multiple Transit Gateways in AWS?
- **Short Answer:** No. TGW Policy Tables are strictly and structurally localized to the exact physical Transit Gateway they are instantiated on. You fundamentally cannot share the mathematical table object across different Transit Gateways, even if the TGWs are actively peered together.
- **Interview Edge:** *"Because Policy Tables cannot be natively shared across TGW boundaries, scaling this globally requires Infrastructure as Code (Terraform/CloudFormation). A Senior DevOps engineer scripts the exact same Policy Table rules and mathematically deploys them redundantly to every regional TGW globally to guarantee absolute compliance parity."*
