# 🚀 AWS Interview Cheat Sheet: TRANSIT GATEWAY MULTICAST (Q313–Q318)

*This master reference sheet covers Transit Gateway Multicast—the only native construct in the entire AWS Cloud ecosystem legally capable of running one-to-many Multicast IP protocols.*

---

## 📊 The Master TGW Multicast Architecture 

```mermaid
graph TD
    subgraph "The One-to-Many Multicast Protocol"
        Publisher[📡 Video Streaming Server <br/> (Amazon EC2 Nitro Instance)]
        
        TGW((🔀 AWS Transit Gateway <br/> IGMPv2 Router))
        
        subgraph "Multicast Group ID: MCAST-12345"
            Sub_1[🖥️ Subscriber EC2 <br/> (VPC A)]
            Sub_2[🖥️ Subscriber EC2 <br/> (VPC B)]
            Sub_3[🖥️ Subscriber EC2 <br/> (VPC C)]
        end
    end
    
    Publisher ==>|1. Sends singular UDP packet| TGW
    
    TGW ==>|2. Mathematically duplicates packet| Sub_1
    TGW ==>|2. Mathematically duplicates packet| Sub_2
    TGW ==>|2. Mathematically duplicates packet| Sub_3
    
    style Publisher fill:#c0392b,color:#fff
    style TGW fill:#2980b9,color:#fff
    style Sub_1 fill:#27ae60,color:#fff
    style Sub_2 fill:#27ae60,color:#fff
    style Sub_3 fill:#27ae60,color:#fff
```

---

## 3️⃣1️⃣3️⃣ Q313: What is Transit Gateway Multicast in AWS?
- **Short Answer:** Transit Gateway Multicast is an exclusive routing feature that allows a massive Transit Gateway to mathematically duplicate a single inbound IP packet and securely distribute it simultaneously to thousands of subscribing 'listener' networks (across multiple VPCs and VPNs) concurrently without destroying the sender's compute bandwidth.
- **Interview Edge:** *"For 10 years, AWS structurally blocked Multicast IP routing at the hypervisor level. If your legacy application required Multicast, you could not migrate to AWS. Transit Gateway Multicast finally shattered that restriction, allowing enterprises to lift-and-shift legacy financial ticker apps entirely into the cloud."*

## 3️⃣1️⃣4️⃣ Q314: What are some use cases for Transit Gateway Multicast in AWS?
- **Short Answer:** 
  1) **Media Streaming:** Distributing live HD video or audio feeds simultaneously to thousands of end-users.
  2) **Financial Services:** Broadcasting ultra-low latency stock market ticker data (e.g., Bloomberg feeds) to hundreds of asynchronous trading algorithms at the exact same microsecond.
  3) **Network Scaling:** Distributing singular routing or configuration updates to thousands of virtual firewalls instantly.

## 3️⃣1️⃣5️⃣ Q315: How does Transit Gateway Multicast work in AWS?
- **Short Answer:** It relies exclusively on **Internet Group Management Protocol (IGMP)**. The Transit Gateway fundamentally acts as the physical Multicast Router. When a completely isolated VPC Instance wants to 'tune in' to the video stream, it physically sends an IGMP 'Join' request back to the TGW. The TGW registers the instance strictly as a subscriber, and begins legally mirroring all stream UDP packets specifically to that instance's Elastic Network Interface.

## 3️⃣1️⃣6️⃣ Q316: What is the difference between unicast and multicast traffic in AWS?
- **Short Answer:** 
  1) **Unicast (One-to-One):** Standard internet tracking. If Netflix wants to send a movie to 100 people, it physically eats the bandwidth cost of transmitting 100 entirely separate data streams out of its server.
  2) **Multicast (One-to-Many):** The server blindly shoots out exactly 1 continuous stream of packets. The router intercepts that 1 stream, completely clones it mathematically thousands of times in memory, and pushes it to every subscribed endpoint without the originating server ever noticing.

## 3️⃣1️⃣7️⃣ Q317: Can Transit Gateway Multicast be used with other AWS services such as Amazon EC2 or Amazon RDS?
- **Short Answer:** It is built precisely for **Amazon EC2** (specifically, instances built on the modern Nitro System architecture). 
- ***CRITICAL ARCHITECTURAL CORRECTION:* ** *Note: The originally drafted answer states you can Multicast to Amazon RDS. This is catastrophically false.* Amazon RDS is a relational transactional database. You mathematically cannot 'Multicast' UDP streams to SQL databases. Multicast operates strictly at the UDP network layer and is explicitly consumed by application-level software running on Nitro EC2 instances, not AWS Managed Database engines. 
- **Interview Edge:** *"If an interviewer asks what compute powers this, explicitly state: 'AWS Transit Gateway Multicast is physically restricted to Amazon EC2 instances running cleanly on the AWS Nitro System hypervisor. Older Xen-based hypervisor instances mathematically cannot receive the IGMP duplicate packets.'"*

## 3️⃣1️⃣8️⃣ Q318: What is the maximum number of Transit Gateway Multicast groups that can be created per Transit Gateway in AWS?
- **Short Answer:** *CRITICAL ARCHITECTURAL CORRECTION:* **The absolute hard limit is not 1000 Multicast Groups natively.** AWS structurally defines a quota of **5 Transit Gateway Multicast Domains** per Transit Gateway, and exactly **1 Multicast Domain associated per VPC Attachment**. While you can route hundreds of distinct multicast IP addresses *inside* a domain, the number of structural TGW *Groups/Domains* is famously capped very low to prevent cascading hypervisor CPU exhaustion.
