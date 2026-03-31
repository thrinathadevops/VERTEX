# 🚀 AWS Interview Cheat Sheet: TRANSIT GATEWAY ROUTE TABLES (Q308–Q312)

*This master reference sheet unpacks Transit Gateway Route Tables—the core dynamic logic engines enabling VRF-Lite macro-segmentation across massive multi-account cloud architectures.*

---

## 📊 The Master TGW Route Table Architecture (VRF-Lite)

```mermaid
graph TD
    subgraph "AWS Transit Gateway (The Hub)"
        RT_Prod[🔀 TGW Route Table: PRODUCTION <br/> - 10.1.0.0/16 (VPC A) <br/> - 10.2.0.0/16 (VPC B)]
        RT_NonProd[🔀 TGW Route Table: NON-PROD <br/> - 10.3.0.0/16 (VPC C) <br/> - 10.4.0.0/16 (VPC D)]
    end
    
    subgraph "Spoke VPC Attachments"
        Prod_A[☁️ VPC A <br/> (Associated to Prod TGW RT)]
        Prod_B[☁️ VPC B <br/> (Associated to Prod TGW RT)]
        Dev_C[☁️ VPC C <br/> (Associated to Non-Prod TGW RT)]
        Dev_D[☁️ VPC D <br/> (Associated to Non-Prod TGW RT)]
    end
    
    Prod_A ==>|Route Lookup| RT_Prod
    Prod_B ==>|Route Lookup| RT_Prod
    Dev_C ==>|Route Lookup| RT_NonProd
    Dev_D ==>|Route Lookup| RT_NonProd
    
    RT_Prod ==>|Transitive Path Allowed| Prod_B
    RT_NonProd ==>|Transitive Path Allowed| Dev_D
    
    RT_Prod -.-x|FATAL ERROR: Production Table <br/> does not know Dev exists| Dev_C
    RT_NonProd -.-x|FATAL ERROR: Non-Prod Table <br/> does not know Prod exists| Prod_A
    
    style RT_Prod fill:#c0392b,color:#fff
    style RT_NonProd fill:#2980b9,color:#fff
    style Prod_A fill:#27ae60,color:#fff
    style Prod_B fill:#27ae60,color:#fff
    style Dev_C fill:#f39c12,color:#fff
    style Dev_D fill:#f39c12,color:#fff
```

---

## 3️⃣0️⃣8️⃣ Q308: How is a Transit Gateway Route Table different from a VPC Route Table in AWS?
- **Short Answer:** 
  1) **Scope of Control:** VPC Route Tables strictly manipulate traffic *leaving* an internal VPC Subnet. Transit Gateway (TGW) Route Tables strictly manipulate traffic bouncing *between* external Attachments (like VPCs, VPNs, and Direct Connects) at the central hub. 
  2) **Capacity:** A VPC Route Table accommodates up to exactly 1,000 routes. A TGW Route Table mathematically scales to handle 10,000 routes.
- **Production Scenario:** The EC2 instance references the local VPC Route table to figure out how to escape the Subnet and reach the TGW. Once the packet physically enters the TGW, the TGW Route Table takes over to figure out which Spoke to hurl the packet down next.

## 3️⃣0️⃣9️⃣ Q309: What are the benefits of using Transit Gateway Route Tables in AWS?
- **Short Answer:** 
  1) It intrinsically provides **VRF-Lite (Virtual Routing and Forwarding)** capabilities, allowing you to establish entirely segregated, non-overlapping routing domains on the exact same physical router hardware.
  2) It aggressively collapses static route spaghetti by seamlessly supporting dynamic route propagation across thousands of independent attachments.

## 3️⃣1️⃣0️⃣ Q310: What is the maximum number of Transit Gateway Route Tables that can be associated with a Transit Gateway in AWS?
- **Short Answer:** *CRITICAL ARCHITECTURAL CORRECTION:* **The default quota is 20 Transit Gateway Route Tables per Transit Gateway.** (You can mathematically request a soft-limit AWS structural quota increase up to a maximum of 100 TGW Route tables).
- **Interview Edge:** *"Be extremely careful here. The original drafted answer stated an absolute maximum of 5. This is severely incorrect. The default limit is 20, capable of jumping to 100. If an enterprise requires more than 100 massively distinct macro-segments on a single router, an Architect must structurally provision a secondary TGW or pivot to AWS Cloud WAN."*

## 3️⃣1️⃣1️⃣ Q311: How are Transit Gateway Route Tables associated with Transit Gateway Attachments in AWS?
- **Short Answer:** It functions on a strict two-pillar architecture: **Associations** and **Propagations**. 
  1) **Association:** You physically instruct an Attachment (e.g., VPC A) to use exactly *one* specific TGW Route table to determine where its outbound traffic is allowed to travel.
  2) **Propagation:** You physically instruct the Attachment to advertise ("propagate") its existence dynamically into *one or more* TGW Route Tables, effectively announcing "I am here, and here is my IP block" to whichever tables need to know it.

## 3️⃣1️⃣2️⃣ Q312: What is the difference between a static route and a propagated route in a Transit Gateway Route Table in AWS?
- **Short Answer:** 
  1) **Propagated Routes:** Are organically and dynamically stitched into the table the moment an Attachment is formed. If the VPC gets deleted, the propagated route systematically disappears autonomously. (This is identical to dynamic BGP learning).
  2) **Static Routes:** Are rigorously hard-coded by a Network Administrator. They are permanently pinned to the table routing logic regardless of the physical health of the destination attachment.
- **Production Scenario:** An Architect sets up dynamic **Propagated Routes** for all 500 internal VPCs so routing adjusts organically if a DevOps team deletes a development VPC. However, the Architect explicitly uses **Static Routes** for an egress "Blackhole" (e.g., pointing a malicious `0.0.0.0/0` proxy route entirely to a static dead-end to drop malicious lateral pings).
