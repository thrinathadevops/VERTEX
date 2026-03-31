# 🚀 AWS Interview Cheat Sheet: SCHEDULED INSTANCES (Q385–Q395)

*This master reference sheet covers the legacy AWS Scheduled Instances tier, detailing how to answer these archaic questions while proudly flaunting structural knowledge of their modern AWS deprecation.*

---

## 📊 The Modern Scheduled Capacity Architecture

```mermaid
graph TD
    subgraph "Legacy (DEPRECATED): EC2 Scheduled Instances"
        Legacy_Contract[📜 Scheduled Reserved Instance <br/> Contract: 'Every Friday 5PM-9PM' <br/> (No longer available for purchase)]
    end
    
    subgraph "Modern Architectures (The Right Answer)"
        ASG_Schedule[⚙️ Auto Scaling Group <br/> Scheduled Scaling Action]
        ASG_Schedule -. "Action triggers Friday 5PM" .-> EC2_Modern[🖥️ Boots On-Demand Instance]
        
        EventBridge[⏰ Amazon EventBridge <br/> Cron Jobs]
        EventBridge -. "Cron triggers API Call" .-> Lambda[⚡ AWS Lambda <br/> 'StartInstances' Script]
    end
    
    style Legacy_Contract fill:#7f8c8d,color:#fff
    style ASG_Schedule fill:#2980b9,color:#fff
    style EventBridge fill:#f39c12,color:#fff
    style Lambda fill:#27ae60,color:#fff
    style EC2_Modern fill:#27ae60,color:#fff
```

---

## 3️⃣8️⃣5️⃣ Q385: What are EC2 Scheduled Instances?
- **Short Answer:** Historically, EC2 Scheduled Instances (officially 'Scheduled Reserved Instances') were physical billing constructs that allowed companies to reserve guaranteed capacity for extremely rigid, predictable recurring windows (e.g., locking down 10 servers exactly from 3:00 PM to 6:00 PM every single Friday).
- **Interview Edge:** *"If an interviewer asks about this, you must instantly establish dominance by stating: **'AWS has officially retired the Scheduled Reserved Instances offering.'** Today, you can no longer purchase this pricing model whatsoever. A Senior Architect flawlessly replaces this legacy model explicitly by utilizing **AWS Auto Scaling Scheduled Actions** or **Amazon EventBridge Cron Rules**."*

## 3️⃣8️⃣6️⃣ Q386: What are some use cases for EC2 Scheduled Instances?
- **Short Answer:** It was historically utilized for radically predictable, non-continuous batch spikes. (e.g., A bank generating payroll processing runs exclusively on Friday afternoons, or an animation studio rendering 3D video strictly overnight from 2:00 AM to 6:00 AM while the artists slept).

## 3️⃣8️⃣7️⃣ Q387: How do you create a Scheduled Instance?
- **Short Answer:** Before deprecation, you utilized the dedicated **Scheduled Instances** pane in the EC2 Console, defined the exact hourly window (Start/End time) and day of the week, specified the instance size, and mathematically committed to that exact schedule for a 1-year unbroken term.

*(Note: The user sequence deliberately skipped Q388).*

## 3️⃣8️⃣9️⃣ Q389: What is the minimum and maximum duration for a Scheduled Instance?
- **Short Answer:** The legacy service strictly mandated a minimum duration block of **1 hour**, and a maximum duration block of **24 hours**, which must accrue to at least 1,200 total hours across the mandatory 1-year contract.

## 3️⃣9️⃣0️⃣ Q390: How can you monitor your Scheduled Instances?
- **Short Answer:** You fundamentally monitored them utilizing Amazon CloudWatch for live compute metrics (CPU Utilization) and AWS Cost Explorer to mathematically track if the developers were actively using the capacity that the FinOps team was financially forced to pay for.

## 3️⃣9️⃣1️⃣ Q391: How can you optimize the use of EC2 Scheduled Instances?
- **Short Answer:** The only true optimization was preventing empty runtime. Because Scheduled Instances functionally charged you for the scheduled block interval *even if you never turned the servers on*, optimizing meant aggressively guaranteeing the batch workloads physically fired exactly on time using automated AWS Step Functions.

## 3️⃣9️⃣2️⃣ Q392: Can you use other pricing models with EC2 Scheduled Instances?
- **Short Answer:** *CRITICAL ARCHITECTURAL CORRECTION:* **No, because the Scheduled Instance was its own standalone pricing model.** 
- **Interview Edge:** *"The drafted answer claims they were 'available only with On-Demand pricing'. This is a massive trap. Scheduled Instances were inherently a distinct class of **Reserved Instances** (giving a 5-10% discount off On-Demand). They operated structurally identically to RIs, where you bought a financial voucher for a time window."*

## 3️⃣9️⃣3️⃣ Q393: Can you modify the schedule of a Scheduled Instance after it has been created?
- **Short Answer:** *CRITICAL ARCHITECTURAL CORRECTION:* **Absolutely not.** 
- **Interview Edge:** *"The drafted answer states you could easily change the Start/End time after creation. This is a fatal FinOps software error. Just like Standard Reserved Instances, Scheduled Instances were bound by strict 1-year iron-clad financial contracts. You physically could not cancel or alter the start/end schedule window once you clicked 'Purchase'. If your batch job moved to Saturdays, you were still financially forced to pay for the empty Friday window for the rest of the year."*

## 3️⃣9️⃣4️⃣ Q394: Can you launch different instance types on a single Scheduled Instance?
- **Short Answer:** No. The financial reservation contract was rigidly locked to the exact physical instance type (e.g., `c4.large`) that you explicitly selected at the absolute time of purchase.

## 3️⃣9️⃣5️⃣ Q395: Can you launch Scheduled Instances in different regions?
- **Short Answer:** The specific physical voucher reservation was mathematically restricted strictly to the single Availability Zone (AZ) you bought it in to guarantee capacity placement. You could launch *other* Scheduled Instances across the globe, but each was treated as an isolated, non-transferable regional contract.
