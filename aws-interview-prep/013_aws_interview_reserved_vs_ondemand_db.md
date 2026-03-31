# 🚀 AWS Interview Question: Reserved vs. On-Demand DB Instances

**Question 13:** *How are reserved instances different from on-demand DB instances?*

> [!NOTE]
> This is a FinOps (Cloud Cost) question. Companies want engineers who can build efficiently.

---

## ⏱️ The Short Answer
**On-Demand DB instances** are flexible, have zero commitment, and are billed hourly (expensive). **Reserved DB Instances (RIs)** require a 1-year or 3-year commitment but offer huge cost savings (up to 70%). Production uses RIs; Dev/Test uses On-Demand.

---

## 🔍 Detailed Explanation

### 1. 🕒 On-Demand DB Instances
- **Cost:** Highest baseline cost.
- **Commitment:** None. Start/stop anytime.
- **Best For:** Short-term projects, Dev/Test, unpredictable workloads.

### 2. 🛡️ Reserved DB Instances (RIs)
- **Cost:** 40% to 70% discount. Payment options: No Upfront, Partial, All Upfront.
- **Commitment:** 1-year or 3-year contract.
- **Best For:** Long-running, 24/7 production databases.

---

## 🆚 Comparison Table

| Feature | 🕒 On-Demand DB | 🛡️ Reserved DB (RIs) |
| :--- | :--- | :--- |
| **Cost** | Highest | Highly Discounted |
| **Commitment** | None | 1 or 3 Years |
| **Flexibility** | High (Cancel anytime) | Limited |
| **Primary Use** | Testing, Staging, QA | 24/7 Production |

---

## 🏢 Enterprise Production Scenario

**Scenario:** A SaaS App needs a MySQL DB running 24/7 indefinitely.
- ❌ **On-Demand:** Yearly cost = ₹6,00,000.
- ✅ **Reserved Instance (3-Year):** Yearly cost = ₹3,00,000.
**Result:** 50% savings (~₹3,00,000/year).

---

## 🧠 Advanced Architect Insight

> [!WARNING]
> **The Critical Trap:** RIs are **not** physical instances. They are a *billing discount* automatically applied to matching on-demand instances running in your account. You don't "boot up" an RI; your bill simply drops for instances matching your contract.

> [!TIP]
> **Pro Tip:** "In enterprise tech, we heavily purchase RIs for static Production databases to slash baseline costs, while keeping Developer databases On-Demand so we can shut them down via automation natively on weekends."
