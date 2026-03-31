# 🚀 AWS Interview Cheat Sheet: VPN & CUSTOMER GATEWAYS (Q252–Q270)

*This master reference sheet breaks down Hybrid Cloud Connectivity, specifically detailing how AWS Site-to-Site VPNs mathematically bridge on-premises corporate infrastructure with the AWS Cloud via encrypted IPSec tunnels.*

---

## 📊 The Master Site-to-Site VPN Architecture

```mermaid
graph LR
    subgraph "Corporate On-Premises Data Center"
        Server[🏢 Internal Server <br/> 192.168.1.50]
        CGW[🧱 Customer Gateway (CGW) <br/> Physical Cisco/Juniper Router <br/> Public IP: 203.0.113.12]
        Server ==>|Private Traffic| CGW
    end
    
    subgraph "The Public Internet"
        Tunnel_1[🔒 IPSec Tunnel 1 <br/> Encrypted]
        Tunnel_2[🔒 IPSec Tunnel 2 <br/> Encrypted (Redundant)]
    end
    
    subgraph "Amazon Web Services (AWS)"
        VGW[☁️ Virtual Private Gateway (VGW) <br/> AWS-side Router]
        VPC[(☁️ Amazon VPC <br/> 10.0.0.0/16)]
        
        VGW ==>|Propagates Routes| VPC
    end
    
    CGW <==>|Establishes| Tunnel_1
    CGW <==>|Establishes| Tunnel_2
    
    Tunnel_1 <==>|Connects to| VGW
    Tunnel_2 <==>|Connects to| VGW
    
    style Server fill:#7f8c8d,color:#fff
    style CGW fill:#c0392b,color:#fff
    style Tunnel_1 fill:#f39c12,color:#fff
    style Tunnel_2 fill:#f39c12,color:#fff
    style VGW fill:#8e44ad,color:#fff
    style VPC fill:#27ae60,color:#fff
```

---

## 2️⃣5️⃣2️⃣ Q252: What is a VPN in AWS?
- **Short Answer:** A Virtual Private Network (VPN) in AWS establishes a secure, heavily encrypted tunnel over the chaotic public internet. It essentially 'tricks' two geographically separated networks (like your physical office and your AWS VPC) into behaving mathematically as if they are physically plugged into the exact same local router.
- **Interview Edge:** *"Without a VPN, connecting to AWS requires sending data in plaintext over the internet, or paying a fortune for a dedicated physical fiber cable (AWS Direct Connect). A VPN offers the perfect compromise: Enterprise-grade encryption utilizing your existing, cheap internet service provider."*

## 2️⃣5️⃣3️⃣ Q253: What are the benefits of using a VPN in AWS?
- **Short Answer:** It provides secure and private hybrid connectivity. This empowers an enterprise to extend their on-premises network securely into the cloud, drastically reducing costs compared to private leased lines, massively accelerating deployment speed, and enforcing strict compliance (IPSec encryption in-transit).

## 2️⃣5️⃣4️⃣ Q254: What types of VPN are available in AWS?
- **Short Answer:** AWS broadly supports two distinct architectures: **AWS Site-to-Site VPN** (Connecting entire physical branch offices/datacenters to AWS) and **AWS Client VPN** (Connecting individual remote human workers/laptops to AWS).

## 2️⃣5️⃣5️⃣ Q255: What is Site-to-Site VPN in AWS?
- **Short Answer:** A persistent, persistent IPSec connection establishing a secure bridge between an entire physical on-premises network gateway (the Customer Gateway) and the AWS VPC network gateway (the Virtual Private Gateway or Transit Gateway). 
- **Production Scenario:** A hospital headquarters in New York automatically routes all internal medical imaging API calls securely to their AWS datastore backend without altering application-level code.

## 2️⃣5️⃣6️⃣ Q256: What is Client VPN in AWS?
- **Short Answer:** A fully-managed, elastic OpenVPN-based service that enables individual remote employees to securely connect their laptops to the AWS VPC from anywhere in the world using a software client, rather than requiring a massive physical hardware router.
- **Production Scenario:** During a pandemic lockdown, 5,000 corporate employees securely access internal AWS corporate HR databases directly from their home WiFi utilizing the AWS Client VPN desktop application authenticated via Active Directory.

## 2️⃣5️⃣7️⃣ Q257: What are the components of a VPN in AWS?
- **Short Answer:** A Site-to-Site VPN requires three structural pillars: 1) The *Customer Gateway* (The on-premise configuration logic). 2) The *Virtual Private Gateway* (The AWS-side routing target). 3) The actual *VPN Connection* object (The underlying IPSec tunnel gluing the two gateways together).

## 2️⃣5️⃣8️⃣ Q258: What is a VPN gateway in AWS?
- **Short Answer:** Formally known as a Virtual Private Gateway (VGW), it is the highly-available, redundant virtual edge router seamlessly attached directly to your Amazon VPC. It serves mathematically as the AWS-side anchor endpoint for the IPSec tunnels.

## 2️⃣5️⃣9️⃣ Q259: What is a customer gateway in AWS?
- **Short Answer:** In the physical world, it is the actual hardware firewall/router sitting in your corporate IT closet (e.g., a Cisco ASA). In the AWS Console, the "Customer Gateway" refers specifically to the *logical AWS resource* you create that explicitly tells AWS what the public static IP address of your physical closet router is.

## 2️⃣6️⃣0️⃣ Q260: What is a virtual private gateway in AWS?
- **Short Answer:** The Virtual Private Gateway (VGW) is the Amazon VPC-side boundary endpoint. It receives the encrypted internet packets from the Customer Gateway, decrypts them securely on the fly, and routes the raw private data locally into your VPC subnets.

## 2️⃣6️⃣1️⃣ Q261: How can you create a VPN connection in AWS?
- **Short Answer:** 1) Create the Virtual Private Gateway (VGW) and successfully attach it to your VPC. 2) Create the Customer Gateway (CGW) object by inputting your physical router's public IP. 3) Navigate to **Site-to-Site VPN Connections**, select both the VGW and CGW, define routing (Static or Dynamic/BGP), and click Create.

## 2️⃣6️⃣2️⃣ Q262: How can you configure a VPN connection in AWS?
- **Short Answer:** Once the AWS VPN Connection object is generated, AWS magically produces a downloadable configuration file detailing the Pre-Shared Keys (PSKs) and exact IPSec encryption parameters. A physical Network Engineer takes this text file and literally copy-pastes the commands into the CLI of the physical on-premises router (e.g., Cisco, Juniper) to manually boot up the tunnels.

## 2️⃣6️⃣3️⃣ Q263: Can you use third-party VPN devices with AWS?
- **Short Answer:** Yes. AWS specifically adheres rigorously to standard IKEv1 and IKEv2 IPSec protocols, meaning almost any enterprise-grade third-party physical firewall or virtual router appliance can mathematically terminate an AWS VPN connection.

## 2️⃣6️⃣4️⃣ Q264: What is a Customer Gateway in AWS VPN?
- **Short Answer:** The Customer Gateway (CGW) is the logical representation within AWS of the physical or virtual device located within the customer's remote data center. It acts structurally as the absolute edge boundary of the customer's physical network footprint.

## 2️⃣6️⃣5️⃣ Q265: What are the types of Customer Gateway supported in AWS VPN?
- **Short Answer:** AWS natively provides auto-generated configuration scripts for all major industry hardware vendors to ensure seamless integration. *Supported profiles include: Generic, Cisco, Juniper, Check Point, Fortinet, Palo Alto Networks, Sophos, Yamaha, and Zyxel.*

## 2️⃣6️⃣6️⃣ Q266: What are the requirements for setting up a Customer Gateway in AWS VPN?
- **Short Answer:** To successfully construct the IPSec tunnel, the physical device MUST: 1) Possess a static, internet-routable Public IP address. 2) Support IPsec VPN connections. 3) Support AWS-compatible encryption algorithms (e.g., AES-256). 4) Support AWS-compatible hashing algorithms (e.g., SHA-2).

## 2️⃣6️⃣7️⃣ Q267: How do you configure a Customer Gateway in AWS VPN?
- **Short Answer:** In the AWS Console, you create the CGW resource strictly by defining its physical Public IP address. Then you establish the VPN Connection linking it to the Virtual Private Gateway. Finally, you configure your VPC Route Tables to enable "Route Propagation" so the VPC knows to send on-premises traffic to the VGW.
- **Interview Edge:** *"Route Propagation is the secret sauce. If you build the VPN correctly but forget to enable Route Propagation in the VPC Route Table, the data packets will have no geographical idea how to find the VPN tunnel."*

## 2️⃣6️⃣8️⃣ Q268: What is the importance of configuring the correct IPsec configuration parameters in a Customer Gateway in AWS VPN?
- **Short Answer:** IPSec is a rigorous mathematical handshake. If the AWS Virtual Private Gateway is expecting AES-256 encryption using SHA-2 hashing and Diffie-Hellman Group 14, but your physical Customer Gateway attempts to connect using AES-128 and SHA-1, the cryptographic handshake violently fails and the tunnel refuses to build. The parameters must match perfectly.

## 2️⃣6️⃣9️⃣ Q269: Can a single Customer Gateway be used for multiple VPN connections in AWS VPN?
- **Short Answer:** Yes. A single physical Customer Gateway device (and its corresponding logical AWS CGW object) can terminate multiple distinct VPN connections mapping to various different VPCs or AWS Regions. However, each unique VPN connection automatically generates its own distinct Pre-Shared Key (PSK) and unique tunnel interfaces.

## 2️⃣7️⃣0️⃣ Q270: Can you modify the configuration of a Customer Gateway after it is associated with a VPN connection in AWS VPN?
- **Short Answer:** Yes, but it is highly destructive. Because a Customer Gateway is fundamentally rooted in its physical Public IP address, modifying core IP or routing configurations will actively force all associated downstream VPN connections to reset seamlessly, momentarily dropping all active network traffic across the bridge.
- **Interview Edge:** *"When modifying VPN routing in production, a Senior Architect always leverages the fact that AWS VPNs inherently provide TWO tunnels. I force all traffic onto Tunnel 1, safely modify the configuration of Tunnel 2, establish BGP routing on Tunnel 2, and then fail the traffic over gracefully. Zero downtime."*
