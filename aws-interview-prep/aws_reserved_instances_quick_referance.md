# 🚀 AWS Interview Cheat Sheet: RESERVED INSTANCES (Q366–Q374)

*This master reference sheet covers EC2 Reserved Instances (RIs)—the legacy financial cornerstone of AWS compute discounts, distinguished by its physical capacity reservation capabilities and strict structural immutability.*

---

## 📊 The Master Reserved Instance Architecture

```mermaid
graph TD
    subgraph "EC2 Reserved Instances (1 or 3 Year Term)"
        Root[💸 AWS Reserved Instance Ecosystem]
    end
    
    subgraph "Standard RI (Up to 72% Discount)"
        Std[🛡️ Standard Reserved Instance <br/> Locked purely to Instance Family <br/> (e.g. m5) & OS]
        Market(🛒 AWS RI Marketplace <br/> Can legally sell unwanted <br/> Standard RIs to 3rd parties)
    end
    
    subgraph "Convertible RI (Up to 54% Discount)"
        Conv[🔀 Convertible Reserved Instance <br/> Can legally mutate to <br/> different Families or OS]
        Conv_Lock(🔒 AWS RI Marketplace <br/> FORBIDDEN to sell <br/> Convertible RIs)
    end
    
    Root ==>|Purchasing Path 1| Std
    Root ==>|Purchasing Path 2| Conv
    
    Std -. "Allowed to sell if <br/> no longer needed" .-> Market
    Conv -.-x|FATAL ERROR: <br/> Mathematically unsellable| Conv_Lock
    
    Conv_Change[⚙️ Exchange Process <br/> e.g., Swap t3 for m5 <br/> Must be of equal/greater value]
    Conv ==>|Permits structural exchange| Conv_Change
    
    style Root fill:#8e44ad,color:#fff
    style Std fill:#d35400,color:#fff
    style Market fill:#f39c12,color:#fff
    style Conv fill:#2980b9,color:#fff
    style Conv_Lock fill:#7f8c8d,color:#fff
    style Conv_Change fill:#27ae60,color:#fff
```

---

## 3️⃣6️⃣6️⃣ Q366: What is an EC2 Reserved Instance?
- **Short Answer:** An EC2 Reserved Instance (RI) is a billing discount construct where a company signs a 1-year or 3-year contract legally committing to pay for specific compute architecture parameters, receiving massive hourly discounts in exchange for stripping away their ability to flexibly scale down.
- **Production Scenario:** A monolithic SQL Database must run 24 hours a day, 365 days a year without fail. Purchasing a 3-Year Standard RI for that exact database size drops the hourly AWS invoice by 72% natively.

## 3️⃣6️⃣7️⃣ Q367: What are the benefits of using EC2 Reserved Instances?
- **Short Answer:** Beyond the 72% financial discount, **Zonal** Reserved Instances explicitly offer physical **Capacity Reservation**. 
- **Interview Edge:** *"If an interviewer asks what an RI does that a Savings Plan cannot do, the absolute correct answer is Capacity Reservation. If AWS runs completely out of physical `c5.large` servers during a crisis in `us-east-1a`, your Zonal RI legally guarantees you can boot your server securely because AWS physically cordoned off real silicon specifically for your contract."*

## 3️⃣6️⃣8️⃣ Q368: How long can you reserve an EC2 instance for?
- **Short Answer:** You must commit to either exactly a **1-Year** or **3-Year** mathematical term length. You cannot dynamically reserve for 6 months.

## 3️⃣6️⃣9️⃣ Q369: Can you change or cancel an EC2 Reserved Instance?
- **Short Answer:** *CRITICAL ARCHITECTURAL CORRECTION:* **NO.** **You absolutely cannot cancel a Reserved Instance under any circumstances.**
- **Interview Edge:** *"The drafted answer claims you can cancel an RI for a fee. This is a catastrophic FinOps myth. Once purchased, AWS explicitly forbids cancellation. The only legal escape hatch is utilizing the **AWS Reserved Instance Marketplace**. If you buy a Standard RI and go bankrupt, you can attempt to sell your unwanted RI actively to a third-party AWS customer. (Note: You cannot sell Convertible RIs on the Marketplace; you are physically stuck with those)."*

## 3️⃣7️⃣0️⃣ Q370: Can you use EC2 Reserved Instances across different instance families, sizes, and regions?
- **Short Answer:** 
  1) **Regions:** **NO.** All RIs are strictly locked to the specific region you purchased them in natively (e.g., `eu-west-1`). 
  2) **Families:** Standard RIs are locked to families. Convertible RIs inherently allow family switching.
  3) **Sizes:** Both Standard and Convertible **Regional** RIs seamlessly support *Instance Size Flexibility*. (e.g., If you own an RI for an `m5.xlarge`, the billing engine mathematically covers the cost of two `m5.large` instances running organically).

## 3️⃣7️⃣1️⃣ Q371: How can you monitor your EC2 Reserved Instance usage?
- **Short Answer:** Utilizing AWS Cost Explorer specifically via the **RI Utilization** and **RI Coverage** reports. Furthermore, AWS issues structural alerting emails when an RI term is within 30 days of legally expiring so the FinOps team can predictably renew the contract.

## 3️⃣7️⃣2️⃣ Q372: What is the difference between a Standard Reserved Instance and a Convertible Reserved Instance?
- **Short Answer:** A Standard RI provides the highest discount (72%), but you can never change the underlying instance family or OS natively. A Convertible RI provides a lower discount (54%), but it organically allows you to "Exchange" the RI parameters.
- ***CRITICAL ARCHITECTURAL CORRECTION:* ** *Note: The originally drafted answer stated a Convertible RI allows you to change the "region". This is absolutely false.* A Convertible RI allows exchanging the instance type, family, OS, and tenancy. It mathematically **does not** allow you to change the Region. You must explicitly purchase a new RI deeply inside the new region.
- **Production Scenario:** A company originally buys a Convertible RI for `m5` Windows machines. Exactly 6 months later, their engineers rewrite the app in Python and shift to Linux `t3` servers. They use the Convertible exchange mechanism physically to swap the RI logic over to `t3` Linux without breaching contract or losing their discount.

## 3️⃣7️⃣3️⃣ Q373: Can you use EC2 Reserved Instances with other pricing models?
- **Short Answer:** The billing engine stacks pricing organically. If you run 10 EC2 instances simultaneously, but only own 4 Reserved Instances, the AWS financial engine optimally applies the 4 massive discount vouchers to the identical servers autonomously, and legally bills the remaining 6 servers dynamically at the standard On-Demand rate.

## 3️⃣7️⃣4️⃣ Q374: How can you optimize the use of EC2 Reserved Instances?
- **Short Answer:** FinOps operations heavily leverage **AWS Compute Optimizer** (to verify if the servers are mathematically oversized) and the **AWS Cost Explorer RI Recommendations** report, which mathematically analyzes exactly how many steady-state base hours you used chronologically last month and precisely calculates the optimal number of RIs to legally purchase to maximize standard profit margins.
