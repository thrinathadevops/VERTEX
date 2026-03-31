# 🚀 AWS Interview Cheat Sheet: AMAZON SQS (Q723–Q742)

*This master reference sheet begins Phase 15: Application Integration. It covers Amazon Simple Queue Service (SQS)—the oldest service in AWS, and the definitive architectural standard for decoupling microservices.*

---

## 📊 The Master SQS Producer/Consumer Architecture

```mermaid
graph TD
    subgraph "Producer Layer"
        API[🌐 API Gateway]
        Web[🖥️ Web Frontend (EC2)]
    end
    
    subgraph "Amazon SQS Engine"
        Queue[📬 SQS Standard Queue <br/> 'Buffer / Shock Absorber']
        DLQ[☠️ Dead-Letter Queue <br/> 'Poison Pill Isolation']
    end
    
    subgraph "Consumer Layer"
        Worker1[⚙️ EC2 Worker Node]
        Worker2[⚙️ EC2 Worker Node]
    end
    
    API ==>|SendMessage| Queue
    Web ==>|SendMessage| Queue
    
    Queue -. "Poll" .-> Worker1
    Queue -. "Poll" .-> Worker2
    
    Worker1 -. "Fails to process 5 times" .-> DLQ
    Worker2 ==>|DeleteMessage| Success((✅ DB Write))
    
    style Queue fill:#2980b9,color:#fff
    style DLQ fill:#c0392b,color:#fff
    style Worker1 fill:#f39c12,color:#fff
    style Worker2 fill:#f39c12,color:#fff
```

---

## 7️⃣2️⃣3️⃣ & Q724 & Q739: What is Amazon SQS and what are its core benefits?
- **Short Answer:** Amazon SQS is a fully managed, serverless message queuing service. 
- **Interview Edge:** *"The absolute #1 architectural benefit of SQS is **Decoupling**. If a massive Super Bowl ad drives 1 million users to your web server (Producer) in 60 seconds, your backend database (Consumer) will violently crash. By placing an SQS queue between them, SQS acts as an infinite shock absorber. It buffers the 1 million requests safely in the queue, allowing the database to pull and process the messages calmly at its own pace without ever crashing."*

## 7️⃣3️⃣0️⃣ & Q735: What is the exact difference between Standard and FIFO SQS queues?
- **Short Answer:** 
  1) **Standard Queue:** Offers **Unlimited Throughput** (millions of msgs/sec). However, it uses "Best-Effort Ordering" (messages might arrive slightly out of order) and "At-Least-Once Delivery" (a message might occasionally be delivered twice).
  2) **FIFO Queue (First-In-First-Out):** Guarantees **Strict Ordering** and **Exactly-Once Processing**. A banking application mathematically must use FIFO to ensure a $100 deposit is processed identically before a $50 withdrawal. FIFO natively maxes out at `3,000` messages per second (with batching).

## 7️⃣3️⃣4️⃣ & Q725: What is the maximum message size in Amazon SQS?
- **Short Answer:** The hard physical limit is exactly **256 KB** of raw text (JSON, XML).
- **Interview Edge:** *"If an interviewer asks how to send a 1GB video through SQS, acknowledging the 256KB limit is not enough. A Senior Architect uses the **SQS Extended Client Library**. This library natively uploads the 1GB video payload directly to Amazon S3, and then pushes a tiny 1KB JSON reference pointer containing the S3 URL into the SQS queue."*

## 7️⃣4️⃣1️⃣ Q741: What is a Visibility Timeout in Amazon SQS?
- **Short Answer:** When `Worker Node A` polls a message from SQS, that message is logically locked and completely hidden from `Worker Node B` for a specific duration (default 30 seconds). 
- **Production Scenario:** If `Worker Node A` completes processing the message in 5 seconds, it physically sends the `DeleteMessage` API back to SQS to permanently destroy it. If `Worker Node A` crashes and does NOT successfully delete the message before the 30-second Visibility Timeout expires, the message instantaneously becomes "visible" in the queue again, allowing `Worker Node B` to safely retry processing it.

## 7️⃣2️⃣7️⃣ & Q740: What is a Dead-Letter Queue (DLQ)?
- **Short Answer:** Often, a developer accidentally pushes a corrupted JSON payload ("Poison Pill") into the queue. A worker node polls the corrupt message, crashes, and the Visibility Timeout expires. The message reappears in the queue, causing the next worker to poll it and crash, creating a vicious infinite loop. 
- **Troubleshooting:** You configure a **Redrive Policy**. If the `MaximumReceives` count hits `5` without a successful deletion, SQS forcefully rips the Poison Pill message out of the main queue and physically dumps it into a DLQ for a human developer to debug later.

## 7️⃣2️⃣9️⃣ & Q738: What is Long Polling vs Short Polling?
- **Short Answer:** 
  - **Short Polling (Default):** The consumer asks SQS for a message. If the queue is empty, SQS instantly replies "No messages", charging you for a useless AWS API call.
  - **Long Polling:** The consumer asks SQS for a message and specifies a `WaitTimeSeconds` (between 1 and 20). The TCP connection brutally hangs open for 20 seconds waiting for a message to arrive. If a message arrives at second 15, it is instantly delivered to the application. This drastically slashes API costs and improves latency.

## 7️⃣3️⃣7️⃣ Q737: How do you scale Amazon SQS queues and consumers?
- **Short Answer:** 
  - **The Queue:** Architecturally, an SQS queue physically does not need to be scaled—it mathematically scales infinitely to millions of messages automatically.
  - **The Consumers:** To scale the backend EC2 worker nodes, an Architect configures a CloudWatch Alarm monitoring the `ApproximateNumberOfMessagesVisible` metric to trigger an Auto Scaling Group to boot up more EC2 servers to clear the queue faster.

## 7️⃣3️⃣6️⃣ Q736: What is the maximum retention period for messages?
- **Short Answer:** 14 days. If a message sits completely unread in an SQS queue for 14 days and 1 second, it is mathematically permanently deleted by AWS.

## 7️⃣3️⃣1️⃣ Q731: How can you use Amazon SQS with AWS Lambda?
- **Short Answer:** SQS is a native Event Source for Lambda. Instead of writing code to "poll" SQS continuously, AWS quietly operates a fleet of hidden pollers on your behalf. When messages land in the queue, AWS automatically forcefully invokes your Lambda function and injects the SQS message cleanly into the Lambda `event` JSON object for serverless processing.

## 7️⃣3️⃣3️⃣ Q733: How can you secure Amazon SQS queues?
- **Short Answer:**
  1) **In Transit:** Utilize HTTPS endpoints explicitly.
  2) **At Rest:** Enable AWS KMS (Key Management Service) encryption natively on the queue.
  3) **Access Control:** Construct precise IAM Policies or physically attach an **SQS Resource-Based Policy**, mathematically allowing only specific SNS Topics or S3 Buckets to push messages into the queue.
