# 🚀 AWS Interview Cheat Sheet: SITE-TO-SITE VPN CONNECTIONS (Q278–Q283)

*This master reference sheet covers the operational mechanics of AWS Site-to-Site VPNs, detailing the setup sequences and the critical, advanced networking nuances regarding Maximum Transmission Unit (MTU) fragmentation.*

---

## 📊 The Master Site-to-Site VPN (MTU Fragmentation) Architecture

```mermaid
graph TD
    subgraph "Corporate Network (MTU: 1500 Bytes)"
        Server[🏢 On-Premises Server <br/> Sends 1500-Byte Payload]
        CGW[🧱 Customer Gateway Router <br/> Must adjust for IPSec Overhead]
    end
        
    subgraph "The Internet (IPSec Tunnel)"
        VPN[🔒 IPSec Encrypted Tunnel <br/> Adds ~60 Bytes of Crypto Headers <br/> Effective Payload MTU: ~1436 Bytes]
    end
    
    subgraph "AWS Data Center"
        VGW[☁️ Virtual Private Gateway <br/> Decrypts payload]
        EC2[🖥️ Amazon EC2 <br/> Receives payload]
    end
    
    Server ==>|1500 Bytes| CGW
    CGW ==>|Capsule + Encryption| VPN
    VPN ==>|Capsule| VGW
    VGW ==>|Decrypted 1500 Bytes| EC2
    
    CGW -. "If MSS Clamping is missing, <br/> the oversized packet fractures and dies" .-x|Fragmentation Drop| VPN
    
    style Server fill:#7f8c8d,color:#fff
    style CGW fill:#c0392b,color:#fff
    style VPN fill:#f39c12,color:#fff
    style VGW fill:#8e44ad,color:#fff
    style EC2 fill:#27ae60,color:#fff
```

---

## 2️⃣7️⃣8️⃣ Q278: What is a Site-to-Site VPN connection in AWS?
- **Short Answer:** A Site-to-Site VPN connection explicitly bridges your physical corporate data center (via your router) to your Amazon VPC (via AWS's Virtual Private Gateway or Transit Gateway) utilizing highly secure, persistent IPSec encrypted tunnels running over the public internet. 
- **Production Scenario:** A company running legacy Oracle databases on physical hardware in their office builds a Site-to-Site VPN so their modern web servers running in AWS EC2 can seamlessly fetch data from the physical office database using private `10.x.x.x` IPs.

## 2️⃣7️⃣9️⃣ Q279: What are the benefits of using Site-to-Site VPN connections in AWS?
- **Short Answer:** It securely bridges the hybrid cloud gap, encrypting data directly in-transit natively without requiring developers to write complex TLS/SSL application logic. 
- ***CRITICAL ARCHITECTURAL CORRECTION:* ** *Note: The originally drafted answer states "It allows you to securely access resources from anywhere using a standard VPN client." This is a massive terminology error.* A Site-to-Site VPN absolutely **does not** use a "standard VPN client" on a laptop; it intrinsically requires a massive physical hardware router to anchor the entire office building. If you want employees to log in from "anywhere" globally utilizing a software client on their laptop, that defines **AWS Client VPN**, which is a fundamentally different service architecture.
- **Interview Edge:** *"If an interviewer asks how a traveling executive connects to a Site-to-Site VPN from an airport, you explicitly answer: 'They don't. Site-to-Site is for fixed structural buildings. The executive must use AWS Client VPN to dial in remotely.'"*

## 2️⃣8️⃣0️⃣ Q280: What are the requirements for setting up a Site-to-Site VPN connection in AWS?
- **Short Answer:** You fundamentally require an AWS Virtual Private Gateway (VGW) and a physical Customer Gateway (CGW) router that explicitly possesses a static Public internet IP address and supports IPSec encryption algorithms.
- ***CRITICAL ARCHITECTURAL CORRECTION:* ** *Note: The originally drafted answer mandates "An Amazon VPC with a public subnet and an Internet Gateway attached." This is functionally false.* The structural purpose of a Site-to-Site VPN is to provide purely private routing. You absolutely **do not** need a Public Subnet or an Internet Gateway (IGW) attached to your VPC to terminate a VPN properly. The connection terminates on the VGW precisely so you can avoid opening the VPC to the wider internet.

## 2️⃣8️⃣1️⃣ Q281: What are the steps involved in setting up a Site-to-Site VPN connection in AWS?
- **Short Answer:** 
  1. **Provision VGW:** Create the Virtual Private Gateway and structurally attach it to the target VPC.
  2. **Provision CGW:** Define the logical Customer Gateway in AWS by inputting your physical router's static internet IP.
  3. **Establish VPN:** Create the actual Site-to-Site VPN construct, gluing the VGW and CGW together.
  4. **Configure Hardware:** Download the AWS-generated text configuration file and physically apply the IKE/IPSec commands directly into your physical hardware router.
  5. **Configure Routing:** Enable 'Route Propagation' explicitly on the VPC Subnet Route Tables.

## 2️⃣8️⃣2️⃣ Q282: What is the maximum transmission unit (MTU) and why is it important in Site-to-Site VPN connections?
- **Short Answer:** The MTU represents the largest physical IP packet size (in bytes) that can transit the network. It is fiercely critical here because VPN IPSec encrypts packets by forcefully "wrapping" them in additional cryptographic headers. If your server sends a maximum 1500-byte packet, the VPN adds ~60 bytes of encryption data to it. The packet is now severely oversized (1560 bytes), resulting in violent packet fragmentation and massive performance degradation.
- **Production Scenario:** A developer successfully runs standard API calls over the VPN. However, when they attempt to download a massive 10GB database dump over the VPN, the connection completely hangs. The Architect identifies that large packets are being silently dropped by the Customer Gateway due to oversized payload structures.
- **Interview Edge:** *"To solve MTU issues on a VPN, a Senior Architect configures 'TCP MSS Clamping' (Maximum Segment Size) explicitly on the Customer Gateway router. This mathematically forces the sending servers to shrink their raw payloads natively to ~1436 bytes, perfectly allowing room for the IPSec encryption headers without causing fragmentation fracturing."*

## 2️⃣8️⃣3️⃣ Q283: How do you troubleshoot Site-to-Site VPN connection issues in AWS?
- **Short Answer:** 
  1. Check AWS CloudWatch for `TunnelState` metrics to verify structural IPSec phase 1 & 2 completion.
  2. Verify the Customer Gateway's public IP perfectly matches the IP configured in AWS. 
  3. Verify the hardware firewall isn't aggressively blocking UDP port 500 or UDP port 4500 (the ports legally required for the IPSec cryptographic handshake).
  4. Confirm that the exact pre-shared keys (PSK) have been typed flawlessly into the hardware router.
- **Interview Edge:** *"Beyond cryptographic failures, the most common 'silent failure' is asymmetric routing. If traffic flows down Tunnel 1 to the Datacenter, but the physical router attempts to send the return traffic back up Tunnel 2, AWS routinely drops the asynchronous connection. I aggressively configure my BGP metrics (AS-PATH prepending) to ensure both AWS and my router natively agree on which tunnel is the primary Active path."*
