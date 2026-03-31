# 🚀 AWS Interview Question: EC2 Auto Recovery via CloudWatch

**Question 3:** *How do you configure CloudWatch to recover an EC2 instance?*

> [!NOTE]
> This is a critical production operations question. Interviewers look for your understanding of **Status Checks** and the difference between OS-level and hardware-level failures.

---

## ⏱️ The Short Answer
Amazon CloudWatch can be configured to automatically recover an EC2 instance if the underlying AWS hardware fails. This is done by creating a CloudWatch Alarm triggered by the `StatusCheckFailed_System` metric. When the alarm triggers the "Recover" action, the instance is seamlessly migrated to healthy hardware while preserving its Instance ID, Private IP, Elastic IP, and attached EBS volumes.

---

## 🔍 Detailed Explanation: The Two Types of Status Checks

Before configuring recovery, you must understand what kind of failures CloudWatch can actually fix:

| Check Type | What it Monitors | What Causes a Failure | Can Auto-Recovery Fix It? |
| :--- | :--- | :--- | :--- |
| **📈 Instance Status** | OS-level issues | Kernel panic, OS corruption, Network misconfig, High CPU, Disk Full | ❌ **No.** (Requires Auto Scaling, SSM, or Manual Reboot) |
| **⚙️ System Status** | AWS Hardware-level | Loss of network connectivity, Loss of system power, Software issues on the physical host | ✅ **Yes!** (CloudWatch Auto Recovery handles this perfectly) |

> [!WARNING]
> **Important Distinction:** Auto Recovery works **only** for System Status Check failures. If your application crashes or the OS freezes, this alarm will not help you.

---

## 🛠️ Step-by-Step Configuration

### Method 1: AWS Console
1. **Navigate:** Go to the EC2 Dashboard and select your target instance.
2. **Status Checks:** Click on the `Status checks` tab.
3. **Trigger:** Click `Actions` → `Monitor and troubleshoot` → `Manage CloudWatch alarms`.
4. **Configure Metric:** Set the alarm metric to `StatusCheckFailed_System`.
5. **Threshold:** Set it to `Greater/Equal to 1`.
6. **Evaluation Period:** 2 consecutive periods of 1 minute (Recommended for production to avoid false positives).
7. **Action:** Select the `Recover this instance` action option.
8. **Save:** Create Alarm.

### Method 2: AWS CLI (Production Engineers Prefer This)
To automate this via Infrastructure as Code (IaC) or CLI:

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name "EC2-Hardware-Recovery-Alarm" \
  --metric-name StatusCheckFailed_System \
  --namespace AWS/EC2 \
  --statistic Maximum \
  --period 60 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --dimensions Name=InstanceId,Value=i-xxxxxxxxxxxxxxxxx \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:automate:us-east-1:ec2:recover
```

---

## 🏢 Real-World Production Scenario

**Scenario: Legacy Core Banking API**
- **The Setup:** An EC2 instance is running a monolithic, legacy core banking API directly behind an Application Load Balancer (ALB). 
- **The Catch:** Due to strict enterprise software licensing restrictions, Auto Scaling is explicitly set to `min=1, max=1`. The API cannot functionally run on multiple instances simultaneously.
- **The Incident:** At 3:00 AM, the underlying AWS physical hardware catastrophically fails. The `StatusCheckFailed_System` metric spikes to `1`.
- **The Result (Without Recovery):** Severe application downtime, a broken SLA, immediate customer complaints, and a stressed engineer woken up to manually migrate the server from a snapshot.
- **The Result (With Auto Recovery):** Within 2 minutes, CloudWatch automatically moves the instance to healthy physical hardware. The Private IP, IAM roles, and volume data remain exactly the same. Zero manual intervention is required.

---

## 🧠 Important Interview Edge Points (To Impress)

> [!TIP]
> **The Golden Follow-Up Question:** 
> *Interviewer: "Why configure CloudWatch Auto Recovery instead of just using an Auto Scaling Group (ASG)?"*
> 
> **Your Answer:** "Auto Scaling is vastly superior for application-level failures and stateless web servers because it inherently replaces the broken instance with a completely freshly launched one. However, CloudWatch Auto Recovery is specifically designed for **single-instance workloads**, stateful databases, or legacy applications with very strict MAC/IP licensing constraints where replacing the instance entirely would break configuration. CloudWatch Auto Recovery *preserves* the exact existing instance setup on new hardware rather than throwing it away."

---

## ⭐ Enterprise Golden Rules
- ✔️ **Enable recovery alarms** for all standalone production EC2 instances.
- ✔️ **Use Auto Scaling instead** whenever the application is fully stateless.
- ✔️ **Combine with SNS** to ensure operations teams still proactively get a Slack/Email notification when an automated recovery is triggered.
- ✔️ **Monitor both checks.** Set up alerts for `StatusCheckFailed_Instance` as well, so your engineering team is notified of OS-level failures even if you can't natively auto-recover from them.

> [!IMPORTANT]
> **Final Interview-Ready Summary:**
> *"To ensure high availability against hardware failures, we configure a CloudWatch Alarm specifically on the `StatusCheckFailed_System` metric. By attaching the `Recover` action to this alarm, AWS automatically migrates our instance to healthy managed hardware while securely preserving its exact network footprint and volume data, resulting in minimal downtime and zero manual intervention."*
