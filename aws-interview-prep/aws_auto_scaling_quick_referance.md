# 🚀 AWS Interview Cheat Sheet: AUTO SCALING & LAUNCH CONFIGURATIONS (Q519–Q533)

*This master reference sheet covers Auto Scaling Groups (ASG) and explicitly highlights the architectural deprecation of legacy "Launch Configurations" in favor of modern "Launch Templates."*

---

## 📊 The Master Auto Scaling Architecture

```mermaid
graph TD
    subgraph "Deployment Blueprint"
        LT[📜 Launch Template (V3) <br/> AMI, Instance Type, Key Pair, Security Group]
    end
    
    subgraph "Auto Scaling Group (ASG)"
        State[⚙️ Min: 2 | Desired: 2 | Max: 5]
        EC2_1[🖥️ EC2 Instance 1]
        EC2_2[🖥️ EC2 Instance 2]
    end
    
    subgraph "Amazon CloudWatch"
        Alarm[⏰ CPU > 80% Alarm]
    end
    
    LT ==>|Dictates Configuration| State
    State ==>|Boot| EC2_1
    State ==>|Boot| EC2_2
    
    EC2_1 -. "Sends Metrics" .-> Alarm
    EC2_2 -. "Sends Metrics" .-> Alarm
    
    Alarm -. "Triggers Scale Out" .-> State
    State -. "Boots 3rd Instance" .-> EC2_3[🖥️ EC2 Instance 3]
    
    style LT fill:#8e44ad,color:#fff
    style State fill:#2980b9,color:#fff
    style Alarm fill:#f39c12,color:#fff
    style EC2_1 fill:#27ae60,color:#fff
    style EC2_2 fill:#27ae60,color:#fff
    style EC2_3 fill:#27ae60,color:#fff
```

---

## 5️⃣1️⃣9️⃣ Q519: Can you explain some practical real-time scenarios related to Auto Scaling?
- **Short Answer:** 
  1) **Predictable/Seasonal Traffic:** A retail site uses *Scheduled Scaling* to force the server count to scale from 5 to 50 exactly 24 hours before Black Friday begins.
  2) **Unpredictable Spikes:** A local pizza shop uses *Dynamic Target Tracking* to algorithmically add EC2 instances instantly if the average CPU suddenly crosses 70% during the Super Bowl.
  3) **Cost Optimization:** Using *Scheduled Scaling* to drop the Dev environment cluster size to exactly 0 servers every Friday at 6:00 PM to save weekend billing costs.

## 5️⃣2️⃣3️⃣ Q523: Can you explain the difference between scaling out and scaling up?
- **Short Answer:** 
  - **Scaling Out (Horizontal):** Adding computationally identical clones to the cluster (e.g., going from two `m5.large` instances to five `m5.large` instances). *This is what ASG does natively.*
  - **Scaling Up (Vertical):** Physically stopping an individual server and mutating its hardware to a much larger tier (e.g., upgrading a single `t2.micro` to an `m5.24xlarge`).

## 5️⃣2️⃣4️⃣ Q524: Can you explain what is meant by minimum, maximum, and desired capacity in Auto Scaling?
- **Short Answer:** 
  - **Minimum:** The absolute hard floor. If an instance dies, ASG mathematically replaces it to enforce this floor. (Best Practice for HA: Min 2).
  - **Desired:** The exact number of instances that should theoretically be running *right now*.
  - **Maximum:** The FinOps hard ceiling. The ASG physically cannot scale past this number, preventing a DDoS attack from spinning up 10,000 instances and bankrupting the company.

## 5️⃣2️⃣5️⃣ Q525: Can you explain what is meant by termination policies in Auto Scaling?
- **Short Answer:** When CloudWatch commands the ASG to "Scale In" (destroy servers), the Termination Policy mathematically chooses *which* server dies first. 
- **Interview Edge:** *"The default AWS termination policy prioritizes **Availability Zone Rebalancing** above all else. If `us-east-1a` has 6 instances and `us-east-1b` has 4 instances, the ASG mathematically murders an instance in 1a first. If the AZs are perfectly balanced, it then falls back to destroying the instance launched from the **Oldest Launch Configuration** to naturally cycle out stale AMIs."*

## 5️⃣2️⃣1️⃣ Q521: Can you explain how to use Amazon CloudWatch with Auto Scaling?
- **Short Answer:** The ASG itself does not mechanically monitor CPU. You create an Amazon CloudWatch Metric Alarm (e.g., `CPUUtilization > 70% for 3 minutes`). When the math trips, CloudWatch fires an SNS notification that directly triggers the ASG's Step Scaling or Target Tracking policy.

## 5️⃣2️⃣6️⃣ Q526: Can you explain how to use Auto Scaling with Elastic Load Balancing?
- **Short Answer:** You explicitly attach an ALB Target Group to the ASG. When the ASG boots a new EC2 instance, it autonomously registers the instance's Private IP address into the Target Group natively without human script intervention.

---
## The Pivot: Launch Configurations vs Launch Templates

## 5️⃣2️⃣7️⃣ & Q529: Can you explain the difference between a launch configuration and a launch template?
- **Short Answer:** A Launch Configuration is the legacy, strongly deprecated blueprint containing AMI and hardware settings. A **Launch Template** is the modern standard. 
- **Interview Edge:** *"An Architect entirely refuses to use Launch Configurations today. Launch Templates mathematically support **Versioning** (V1, V2, V3), explicit support for **EC2 Dedicated Hosts**, and the native ability to launch **Spot Fleets** mixing On-Demand and Spot instances in the exact same ASG. Launch Configurations could do none of this."*

## 5️⃣2️⃣8️⃣ Q528: What is a Launch Configuration in AWS?
- **Short Answer:** A deprecated blueprint telling the ASG exactly "What to build" (AMI ID, Security Group, Instance Type, IAM Profile) when CloudWatch tells the ASG "When to build". 

## 5️⃣3️⃣0️⃣ Q530: Can you modify a Launch Configuration after it has been created?
- **Short Answer:** *CRITICAL ARCHITECTURAL CORRECTION:* **No. Absolutely not.** 
- **Interview Edge:** *"The drafted answer claims you can modify a Launch Configuration. This is a fatal AWS error that will bomb an interview. Launch Configurations are strictly **Immutable**. If you made a typo, you geometrically cannot edit it. You must systematically clone it, create a brand NEW Launch Configuration, and then attach the new configuration to the ASG. (Conversely, Launch Templates ARE natively editable via Versioning!)."*

## 5️⃣3️⃣1️⃣ Q531: Can you create multiple Launch Configurations for an Auto Scaling group?
- **Short Answer:** No. An ASG structurally allows exactly one Launch Configuration active at any given time. However, modern architectures using **Launch Templates** uniquely allow "Mixed Instance Policies", heavily blending multiple instance types seamlessly.

## 5️⃣3️⃣2️⃣ Q532: Can you copy a Launch Configuration from one region to another?
- **Short Answer:** No. They are violently Region-specific because AMIs, Security Groups, and Subnet IDs do not mathematically traverse AWS Regions. You must reconstruct the template in the DR region natively.

## 5️⃣3️⃣3️⃣ Q533: What happens when a Launch Configuration is deleted?
- **Short Answer:** You physically cannot delete a Launch Configuration if an active ASG is currently pointing to it. If the ASG is deleted and the configuration is orphaned and deleted, existing instances launched from it continue running flawlessly until they are manually stopped.
