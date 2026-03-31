# 🚀 AWS Interview Cheat Sheet: SAVINGS PLANS (Q358–Q365)

*This master reference sheet covers AWS Savings Plans—the modern, hyper-flexible financial framework that drastically reduces enterprise compute costs by committing to a flat hourly dollar spend rather than rigid physical server counts.*

---

## 📊 The Master Compute Financial Hierarchy

```mermaid
graph TD
    subgraph "Standard AWS Billing"
        OD[💸 On-Demand <br/> Full Price / Zero Commitment]
    end
    
    subgraph "AWS Savings Plans (1 or 3 Year)"
        EC2_SP[📉 EC2 Instance Savings Plan <br/> Up to 72% Discount <br/> 'Locked to Family & Region']
        Comp_SP[📉 Compute Savings Plan <br/> Up to 66% Discount <br/> 'Maximum Flexibility']
    end
    
    subgraph "The Flexibility Matrix (Compute Savings Plan)"
        Fargate[🐳 AWS Fargate]
        Lambda[⚡ AWS Lambda]
        EC2_A[🖥️ EC2 m5 (Windows in US-East)]
        EC2_B[🖥️ EC2 c5 (Linux in EU-West)]
    end
    
    Comp_SP ==>|Discount Automatically Applies to| Fargate
    Comp_SP ==>|Discount Automatically Applies to| Lambda
    Comp_SP ==>|Discount Automatically Applies to| EC2_A
    Comp_SP ==>|Discount Automatically Applies to| EC2_B
    
    EC2_SP -. "Strictly Applies Only to" .-> EC2_A
    
    style OD fill:#c0392b,color:#fff
    style EC2_SP fill:#d35400,color:#fff
    style Comp_SP fill:#27ae60,color:#fff
    style Fargate fill:#2980b9,color:#fff
    style Lambda fill:#2980b9,color:#fff
    style EC2_A fill:#8e44ad,color:#fff
    style EC2_B fill:#8e44ad,color:#fff
```

---

## 3️⃣5️⃣8️⃣ Q358: What is an EC2 Savings Plan?
- **Short Answer:** A Savings Plan is a massive volume discount program. Instead of renting individual servers, the enterprise mathematically commits to spending a specific flat dollar amount per hour (e.g., $100/hour) continuously across either a 1-year or 3-year term. Internally, any compute utilized up to that $100/hour watermark receives an automatic 72% algorithmic discount.
- **Production Scenario:** A company calculates they spend at minimum $5,000 an hour on compute globally across all teams 24/7. They purchase a massive Compute Savings Plan committing to $3,000/hr. The first $3,000 of global compute they use every hour drops in price by 66% autonomously, saving them millions annually without touching their application infrastructure.

## 3️⃣5️⃣9️⃣ Q359: How does an EC2 Savings Plan differ from a Reserved Instance?
- **Short Answer:** Reserved Instances (RIs) mathematically lock you strictly to physical server variables (You must commit precisely to "10 Linux `m5.large` nodes in `us-east-1`"). A Savings Plan throws away hardware assignments and only requires a pure financial commitment in dollars-per-hour, affording massive flexibility.
- ***CRITICAL ARCHITECTURAL CORRECTION:* ** *Note: The originally drafted answer conflates two different plan types.* There are two plans: 
  1) **EC2 Instance Savings Plans** (Least Flexible - 72% Discount): It locks you to a specific Instance Family (e.g., `M5`) and Region (`us-east-1`), but you can change instance sizes (micro to xlarge).
  2) **Compute Savings Plans** (Most Flexible - 66% Discount): This is the plan that mathematically allows you to seamlessly move across instance families, operating systems, and Regions, and even covers AWS Lambda and Fargate container usage autonomously!

## 3️⃣6️⃣0️⃣ Q360: Can you change or cancel an EC2 Savings Plan?
- **Short Answer:** *CRITICAL ARCHITECTURAL CORRECTION:* **NO.** **You absolutely cannot cancel, modify, or exchange a Savings Plan once it is purchased.** 
- **Interview Edge:** *"This is the most lethal trap in FinOps interviews. Savings Plans are iron-clad financial legal contracts. You cannot cancel a 3-year Savings Plan if your company shrinks. Your only architectural recourse is to ensure you never commit to 100% of your usage upfront; conservative Architects only commit SPs to 60-70% of total steady-state traffic."*

## 3️⃣6️⃣1️⃣ Q361: What are the benefits of using an EC2 Savings Plan?
- **Short Answer:** Aside from up to 72% margin discounts, the supreme benefit is **Operational Friction Reduction**. With legacy Reserved Instances, DevOps teams routinely wasted thousands of hours manually migrating instances to match legacy RI profiles. With Savings Plans, developers can freely upgrade instance types and shift workloads between Fargate and EC2, and the Savings Plan discount dynamically follows the workload organically.

## 3️⃣6️⃣2️⃣ Q362: How can you monitor your EC2 Savings Plan usage?
- **Short Answer:** Utilizing AWS Cost Explorer specifically via the **Savings Plans Utilization** and **Savings Plans Coverage** Dashboards.
- **Interview Edge:** *"Utilization vs Coverage is a classic FinOps question. **Coverage** tracks what percentage of your total fleet is currently running on cheap Savings Plan rates vs expensive On-Demand rates. **Utilization** tracks if you are actually using the dollar amount you committed to. Run 100% Utilization to ensure you aren't wasting money!"*

## 3️⃣6️⃣3️⃣ Q363: What is the difference between an EC2 Savings Plan and a Reserved Instance Marketplace?
- **Short Answer:** A Savings Plan is structurally non-transferable (you are stuck with it for 1 or 3 years). Standard Standard Reserved Instances possess an official secondary AWS Marketplace where companies can actively attempt to sell their remaining unneeded RI term contracts to other physical AWS customers if they go bankrupt or migrate away from AWS. (You cannot sell Savings Plans on any marketplace).

## 3️⃣6️⃣4️⃣ Q364: Can you use an EC2 Savings Plan with other pricing models?
- **Short Answer:** Mechanically, yes. The billing engine applies the discounts automatically in sequence. For example, if your application runs on Spot Instances (90% off), the Savings Plan absolutely does not apply to Spot instances (they are already hyper-discounted). The SP engine ignores Spot and intelligently hunts for full-price On-Demand instances elsewhere in the corporate AWS account to aggressively apply the discount to.

## 3️⃣6️⃣5️⃣ Q365: How can you optimize the use of EC2 Savings Plans?
- **Short Answer:** You utilize the **Savings Plans Recommendations** engine fundamentally built directly into AWS Cost Explorer. It analytically evaluates the last 7, 30, or 60 days of your physical compute usage and mathematically extrapolates exactly how many dollars-per-hour you should commit to maximize discount margins without accidentally over-committing and risking stranded unutilized hours.
