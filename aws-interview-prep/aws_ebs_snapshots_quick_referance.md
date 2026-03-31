# 🚀 AWS Interview Cheat Sheet: EBS SNAPSHOTS (Q466–Q472)

*This master reference sheet covers Amazon EBS Snapshots, the incremental, point-in-time backup mechanisms stored deeply inside Amazon S3 that guarantee the durability of block storage.*

---

## 📊 The Master EBS Snapshot Architecture (Incremental Backups)

```mermaid
graph TD
    subgraph "The Primary EBS Volume (us-east-1)"
        Vol[💽 EBS Volume <br/> 'Active Block Storage']
    end
    
    subgraph "Hidden S3 Storage backend"
        Snap1[📸 Snapshot 1 (Monday) <br/> Base: 10 GB]
        Snap2[📸 Snapshot 2 (Tuesday) <br/> Delta: +2 GB]
        Snap3[📸 Snapshot 3 (Wednesday) <br/> Delta: +1 GB]
    end
    
    subgraph "Cross-Region Disaster Recovery (eu-west-1)"
        Copy[📦 AMI / Snapshot Copy]
        Restored[💽 Restored EBS Volume]
    end
    
    Vol ==>|Full Backup| Snap1
    Vol ==>|Incremental Block Changes| Snap2
    Vol ==>|Incremental Block Changes| Snap3
    
    Snap3 -. "1. Copy across AWS Backbone" .-> Copy
    Copy -. "2. Restore to Volume" .-> Restored
    
    style Vol fill:#2980b9,color:#fff
    style Snap1 fill:#f39c12,color:#fff
    style Snap2 fill:#d35400,color:#fff
    style Snap3 fill:#c0392b,color:#fff
    style Copy fill:#8e44ad,color:#fff
    style Restored fill:#27ae60,color:#fff
```

---

## 4️⃣6️⃣6️⃣ Q466: What is an EBS snapshot?
- **Short Answer:** An EBS Snapshot is an asynchronous, point-in-time exact physical replica of an active EBS virtual hard drive. Snapshots are stored transparently and redundantly inside Amazon S3, natively ensuring 99.999999999% (11 9s) of durability.
- **Interview Edge:** *"A Senior Architect knows that EBS Snapshots are fundamentally **Incremental**. The absolute first snapshot mathematically backs up the entire 100GB volume. The second snapshot taken the next day structurally only backs up the 2GB of data blocks that were actively changed since yesterday, saving the enterprise massive S3 storage costs."*

## 4️⃣6️⃣7️⃣ Q467: Can you restore an EBS snapshot to a different region?
- **Short Answer:** *CRITICAL ARCHITECTURAL CORRECTION:* **Yes, but requires a mechanical 2-step process.**
- **Interview Edge:** *"The drafted answer just says 'Yes'. If you say 'Yes' in an interview and stop, they will fail you. You absolutely cannot physically restore a Snapshot residing in `us-east-1` directly into an active EBS Volume in `eu-west-2`. Snapshots are rigidly locked to their geographical region. You must explicitly execute the **Copy Snapshot** API to physically transfer the bytes across the AWS global backbone. Only once the clone exists in the new region can you execute the Restore."*

## 4️⃣6️⃣8️⃣ Q468: How can you troubleshoot an issue with an EBS snapshot that is failing to create?
- **Short Answer:** 
  1) **Permissions:** Verify the IAM Role actively holds the `ec2:CreateSnapshot` permission policy. 
  2) **Concurrent Limits:** AWS places hard API quotas on actively "Pending" snapshots per volume (usually 5). If you are spamming the API too fast, you must mathematically wait for the massive backend data transfer to S3 to complete before initiating another concurrent snapshot.

## 4️⃣6️⃣9️⃣ Q469: Can you encrypt an EBS snapshot?
- **Short Answer:** Yes. It is heavily integrated with AWS KMS (Key Management Service).
- **Production Scenario:** If the original source EBS Volume is completely unencrypted, the resulting Snapshot is organically unencrypted. To resolve this structural security flaw, you must execute a "Copy Snapshot" command and explicitly inject a KMS key during the copy operation. The cloned Snapshot will natively emerge 100% encrypted, allowing you to restore a fully encrypted EBS volume from it.

## 4️⃣7️⃣0️⃣ Q470: How can you troubleshoot an issue with an EBS snapshot that is causing data loss?
- **Short Answer:** True "Data Loss" from a snapshot is almost mechanically impossible due to S3's 11-9s of durability. However, **File System Corruption** frequently occurs if the underlying SQL Database was actively writing heavy I/O to the disk at the exact millisecond the snapshot triggered. 
- **Interview Edge:** *"To prevent corrupted snapshots, AWS mechanically recommends unmounting the volume or natively utilizing AWS Systems Manager VSS (Volume Shadow Copy Service) on Windows to organically freeze the database I/O, take the snapshot perfectly consistently, and instantly unfreeze the database."*

## 4️⃣7️⃣1️⃣ Q471: Can you delete an EBS snapshot that is being used by an instance?
- **Short Answer:** *CRITICAL ARCHITECTURAL CORRECTION:* **An EC2 Instance mathematical does not "use" a Snapshot.** An instance uses an **EBS Volume**. 
- **Interview Edge:** *"The drafted answer contains a major logic flaw. The correct restriction is: You absolutely cannot delete an EBS Snapshot that is currently physically registered as the Root Volume of an active Amazon Machine Image (AMI). To delete the snapshot, you must fundamentally **Deregister the AMI** API pointer first. Once the AMI is destroyed, the orphaned S3 snapshot unlocks and can be legally deleted to stop billing."*

## 4️⃣7️⃣2️⃣ Q472: How can you troubleshoot an issue with an EBS snapshot that is failing to restore?
- **Short Answer:** 
  1) **Size Constraint:** You are mathematically forbidden from restoring a 50GB Snapshot into a 40GB EBS Volume. The requested destination volume *must* physically be exactly equal to or vastly larger than the fundamental snapshot size.
  2) **KMS Decryption Auth:** The IAM User initiating the restore must legally possess the `kms:Decrypt` permission on the exact CMK (Customer Managed Key) that the snapshot is intrinsically encrypted with. If they lack decryption rights, the restore fails instantly.
