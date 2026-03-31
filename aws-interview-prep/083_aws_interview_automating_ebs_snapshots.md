# 🚀 AWS Interview Question: Automating EBS Snapshots

**Question 83:** *Your manager asks you to ensure that every Amazon EBS volume in the production account is reliably backed up every night at midnight. How do you technically automate this?*

> [!NOTE]
> This is a timeline-based DevOps question. If you only answer "EventBridge and Lambda," you sound like an engineer from 2016. While technically correct, you must demonstrate modern maturity by immediately transitioning your answer to **Amazon Data Lifecycle Manager (DLM)** or **AWS Backup** to prove you prefer managed automation over maintaining custom code.

---

## ⏱️ The Short Answer
To guarantee daily automated snapshot creation for all targeted EBS volumes, you can utilize three escalating architectural approaches:
1. **The Legacy Custom Code (EventBridge + Lambda):** You configure an Amazon EventBridge (CloudWatch Events) Cron rule to trigger an AWS Lambda function every night at midnight. The Lambda executes a Python `boto3` script to locate the volumes, create a snapshot, and manually delete any snapshots older than 30 days.
2. **The Modern EC2 Standard (Amazon Data Lifecycle Manager):** Writing custom Lambda scripts for basic backups is an anti-pattern today. Instead, you configure Amazon Data Lifecycle Manager (DLM). DLM is a managed native AWS service where you simply define a policy (e.g., "Take a snapshot every 24 hours and retain 30 copies"). DLM automatically targets any EBS volume sporting a specific meta-tag (like `Environment: Production`).
3. **The Enterprise Standard (AWS Backup):** If the company wants to orchestrate backups centrally across Database, Storage, and Compute layers spanning multiple AWS accounts, you bypass DLM and universally utilize **AWS Backup** to enforce the snapshot schedule.

---

## 📊 Visual Architecture Flow: The Evolution of Automation

```mermaid
graph TD
    subgraph "The Legacy Way (High Maintenance / Custom Code)"
        Cron[🕒 Amazon EventBridge <br/> Cron: 0 0 * * *]
        Lambda[λ AWS Lambda <br/> Python: create_snapshot()]
        EBS_Old[(💽 Production EBS)]
        
        Cron -->|Triggers Execution| Lambda
        Lambda -. "Dev must manually write code <br/> to delete old snapshots" .-> EBS_Old
    end
    
    subgraph "The Modern Operations Way (Zero Code / Tag-Based)"
        DLM[⚙️ Amazon Data Lifecycle Manager <br/> Policy: Keep last 30 days]
        Tag[🏷️ Resource Tag: <br/> 'Backup = Daily']
        EBS_New[(💽 Production EBS)]
        
        DLM ==>|Autonomously Sweeps & <br/> Targets matching tags| EBS_New
        EBS_New --- Tag
    end
    
    style Cron fill:#f39c12,color:#fff
    style Lambda fill:#e67e22,color:#fff
    style EBS_Old fill:#e74c3c,color:#fff
    style DLM fill:#8e44ad,color:#fff
    style Tag fill:#2980b9,color:#fff
    style EBS_New fill:#27ae60,stroke:#2ecc71,stroke-width:2px,color:#fff
```

---

## 🏢 Real-World Production Scenario

**Scenario: The Infinite Snapshot Bill**
- **The Broken Legacy System:** A junior DevOps engineer sets up daily EBS backups using an EventBridge cron rule triggering a Python Lambda function. The script perfectly takes a snapshot every night. However, the engineer failed to program the complex logic required to *delete* old snapshots. 
- **The Financial Impact:** Over the next two years, the script blindly generates over 3,000 completely redundant snapshots. Because AWS bills for snapshot storage, the company receives an inexplicable $5,000 monthly bill purely for holding onto worthless, three-year-old EBS data.
- **The Architect's Resolution:** The Cloud Architect completely deletes the EventBridge and Lambda stack. They instead deploy an **Amazon Data Lifecycle Manager (DLM)** policy. They configure the DLM GUI to systematically target any EBS volume tagged with `Backup: True`. They set the schedule to `Daily` and hardcode the Lifecycle Retention Policy strictly to `14 Days`.
- **The Result:** The next night, DLM autonomously backs up the hard drives. Exactly 14 days later, DLM natively issues an API call to permanently delete the 15th-day snapshot, creating a perfect, infinitely rolling, self-cleaning backup cycle that mathematically caps the AWS storage bill and requires absolutely zero Python code maintenance.

---

## 🎤 Final Interview-Ready Answer
*"Historically, automating Amazon EBS snapshots required actively managing infrastructure code—specifically, orchestrating an Amazon EventBridge scheduled cron rule to continuously trigger a custom AWS Lambda Python script. While this still technically works, relying on custom scripts for foundational infrastructure tasks is an operational anti-pattern because engineers frequently forget to script the lifecycle retention logic, leading to infinite localized snapshot storage bills. Today, I completely bypass custom code and exclusively utilize managed services like Amazon Data Lifecycle Manager (DLM) or AWS Backup. I simply attach a specific resource tag (like 'Policy=DailyBackup') to our production EBS volumes. DLM autonomously sweeps the environment, finds the tagged volumes, executes the daily snapshot, and critically—natively enforces the retention lifecycle by automatically purging any snapshot older than 30 days, guaranteeing compliance with zero code overhead."*
