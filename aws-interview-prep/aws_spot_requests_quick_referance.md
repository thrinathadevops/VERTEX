# 🚀 AWS Interview Cheat Sheet: EC2 SPOT REQUESTS (Q348–Q357)

*This master reference sheet covers EC2 Spot Requests—the volatile, hyper-discounted compute mechanism fundamentally architected for massive, stateless workloads like big data processing and CI/CD pipelines.*

---

## 📊 The Master EC2 Spot Instance Architecture

```mermaid
graph TD
    subgraph "The AWS Datacenter (Excess Capacity)"
        Capacity[💻 Unused AWS Compute Racks <br/> 'The Spot Market Pool']
    end
    
    subgraph "The AWS Auto Scaling Engine"
        ASG_Spot[⚙️ Auto Scaling Group <br/> Spot Fleet Configuration]
        Request[📝 Spot Request <br/> Max Bid: $0.15/hr]
    end
    
    subgraph "The Customer Workload (Stateless)"
        Queue[📥 SQS Message Queue <br/> 10,000 Images to process]
        Worker_1[🖥️ Spot EC2 <br/> Processing...]
        Worker_2[🖥️ Spot EC2 <br/> Processing...]
    end
    
    ASG_Spot ==>|Generates| Request
    Request ==>|Bids on| Capacity
    
    Capacity ==>|Leases instances at 90% DB| Worker_1
    Capacity ==>|Leases instances at 90% DB| Worker_2
    
    Queue -. "Worker pulls job" .-> Worker_1
    
    Demand[📈 Random Datacenter Demand Spike <br/> Market Price hits $0.20/hr] ==> Capacity
    Demand -. "Triggers 2-Minute Warning" .-x|AWS Violently Reclaims Server| Worker_1
    
    style Capacity fill:#7f8c8d,color:#fff
    style Request fill:#2980b9,color:#fff
    style Queue fill:#f39c12,color:#fff
    style Worker_1 fill:#27ae60,color:#fff
    style Worker_2 fill:#27ae60,color:#fff
    style Demand fill:#c0392b,color:#fff
```

---

## 3️⃣4️⃣8️⃣ Q348: What is an EC2 Spot Request?
- **Short Answer:** An EC2 Spot Request is a programmatic API petition explicitly demanding AWS to launch a compute instance *only* if the current floating "Spot Market Price" is mathematically lower than the maximum price per hour you are willing to spend.
- **Production Scenario:** A data engineering team needs 500 servers to process genomic sequencing data over the weekend. Because the workload isn't time-urgent, they submit Spot Requests. They receive $50,000 worth of compute power for just $5,000.

## 3️⃣4️⃣9️⃣ Q349: What is the AWS Spot Market?
- **Short Answer:** It is the internal, highly dynamic AWS trading marketplace where AWS attempts to structurally liquidate the massive amounts of unused physical server capacity sitting idle in their global datacenters at extreme financial discounts (frequently up to 90% off standard On-Demand pricing).

## 3️⃣5️⃣0️⃣ Q350: How can you create an EC2 Spot Request?
- **Short Answer:** You physically navigate to **EC2 -> Spot Instances -> Request Spot Instances**. You define your structural parameters (AMI, Instance Type, VPC Subnet) and explicitly declare your "Maximum price per instance hour". If you leave the Max Price blank, AWS legally defaults to capping your bid perfectly at the current On-Demand rate.

## 3️⃣5️⃣1️⃣ Q351: What happens when the Spot price exceeds the maximum price specified in the Spot Request?
- **Short Answer:** AWS initiates an aggressive structural reclamation protocol. AWS grants the instance a strict, non-negotiable **2-Minute Interruption Notice** via the Instance Metadata Service (IMDS). Once that 120-second timer hits zero, the Spot instance is ruthlessly disrupted.
- **Interview Edge:** *"A major architectural update here: historically, the answer was always 'AWS terminates it'. Today, a Senior Architect configures the **Interruption Behavior** in the Launch Template. You can gracefully instruct AWS to **Hibernate** or **Stop** the instance instead of mathematically Terminating it, perfectly preserving the EBS volume state until market prices creatively drop again."*

## 3️⃣5️⃣2️⃣ Q352: How can you ensure the availability of your applications when using Spot instances?
- **Short Answer:** You fundamentally **never** run a stateful database or a single-node web server on Spot. You structurally couple Spot instances tightly with **Auto Scaling Groups (ASG)** and Elastic Load Balancers. You configure the ASG with a "Mixed Instances Policy," commanding it to maintain 2 unbreakable On-Demand instances for guaranteed baseline survival, while dynamically bursting 10 Spot Instances to absorb heavy traffic. If the Spot instances die, the ASG automatically provisions On-Demand instances to compensate.

## 3️⃣5️⃣3️⃣ Q353: What are the benefits of using Spot instances?
- **Short Answer:** 
  1) **Astronomical Yield Calculation:** Mathematical cost savings routinely soaring to 90%. 
  2) **Hyperscale Acceleration:** By deliberately paying 90% less per node, a financial firm can organically spin up 10 times the amount of structural compute they could historically afford, radically slashing batch-processing time from 10 hours down to 1 hour.

## 3️⃣5️⃣4️⃣ Q354: What are the disadvantages of using Spot instances?
- **Short Answer:** **Extreme volatility and zero SLA on survival.** If AWS suddenly experiences a massive surge of Enterprise On-Demand requests, AWS immediately evicts your Spot instances without human mercy to hand the physical hypervisors over to the full-paying clients. 
- **Interview Edge:** *"Spot is strictly for **Stateless, Fault-Tolerant, Loosely Coupled** architectures. If your application locally stores session state in memory, and the instance receives a 2-minute kill warning, every user intimately logged into that server abruptly gets kicked out. Spot instances mandate externalized state tracking (like DynamoDB or ElastiCache)."*

## 3️⃣5️⃣5️⃣ Q355: How can you monitor Spot instances and Spot Requests?
- **Short Answer:** You natively leverage Amazon CloudWatch alongside Amazon EventBridge. 
- **Production Scenario:** An Architect configures an AWS EventBridge rule specifically mathematically listening for the exact API payload: `EC2 Spot Instance Interruption Warning`. When that warning fires, EventBridge instantly triggers an AWS Lambda function that aggressively copies the active log files off the dying server and safely dumps them into an S3 bucket before the server physically evaporates 120 seconds later.

## 3️⃣5️⃣6️⃣ Q356: What is the difference between a Spot instance and a Reserved instance?
- **Short Answer:** 
  1) **Contract Length:** Spot has zero contract; you lease by the second and can be fired in 2 minutes. Reserved Instances enforce a grueling 1-year or 3-year unbreakable financial contract.
  2) **Availability:** Spot provides zero guarantee of hardware availability. A Reserved Instance strictly guarantees capacity (if you buy a *Zonal* Reserved Instance).
  3) **Discount:** Spot floats wildly between 50%–90%. RIs grant a flat, mathematical 40%–72% discount.

## 3️⃣5️⃣7️⃣ Q357: How can you optimize the use of Spot instances?
- **Short Answer:** Do not tie yourself to a single instance physically. You utilize an AWS **Spot Fleet**. A Spot Fleet logically allows you to mathematically request multiple physical instance sizes simultaneously (e.g., "Give me `m5.large` OR `c5.large` OR `t3.xlarge`—whichever one is currently cheapest"). If AWS runs completely out of `m5` capacity, the Spot Fleet organically pivots and steals `c5` capacity instead to keep your application alive. 
- **Interview Edge:** *"You natively optimize survival by spreading out your **Spot Capacity Pools**. A Pool is a specific instance type inside a specific Availability Zone. By spreading your Fleet across 10 different Capacity Pools, it is mathematically near-impossible for AWS to forcefully evict 100% of your servers concurrently."*
