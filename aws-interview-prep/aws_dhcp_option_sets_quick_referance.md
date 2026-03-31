# 🚀 AWS Interview Cheat Sheet: DHCP OPTION SETS (Q60–Q69)

*This master reference sheet details how AWS fundamentally manages IP assignment and DNS resolution organically within a Virtual Private Cloud using DHCP Option Sets.*

---

## 📊 The Master DHCP & Active Directory DNS Architecture

```mermaid
graph TD
    subgraph "Amazon VPC - Underlying DHCP Layer"
        VPC[(☁️ Amazon VPC <br/> '10.0.0.0/16')]
        DHCP[⚙️ DHCP Option Set <br/> Associated with VPC]
        
        subgraph "Internal Network (IP Assignment Phase)"
            EC2_New[🖥️ New EC2 Instance <br/> Booting up...]
            Router[🔀 VPC Edge Router <br/> Base IP + 2 (10.0.0.2)]
            
            EC2_New -. "1. DHCP Discover Broadcast" .-> Router
            Router -. "2. Reads Option Set Config" .-> DHCP
        end
        
        subgraph "Custom Configurations Provided"
            DNS[🌐 Custom DNS Server <br/> Active Directory (10.0.1.55)]
            NTP[🕒 Custom Time Server <br/> NTP (10.0.1.66)]
        end
        
        DHCP ==>|Injects config| Router
        Router ==>|3. Assigns IPs & Pushes Custom DNS| EC2_New
        EC2_New ==>|All DNS Queries now hit AD| DNS
    end
    
    style VPC fill:#27ae60,color:#fff
    style DHCP fill:#8e44ad,color:#fff
    style EC2_New fill:#f39c12,color:#fff
    style Router fill:#2980b9,color:#fff
    style DNS fill:#c0392b,color:#fff
    style NTP fill:#c0392b,color:#fff
```

---

## 6️⃣0️⃣ Q60: What is a DHCP option set in AWS?
- **Short Answer:** A DHCP (Dynamic Host Configuration Protocol) Option Set is a configuration blueprint attached directly to an AWS VPC. When an EC2 instance organically boots up, it asks the network for an IP address. The DHCP Option Set dictates exactly what network configuration (IP addresses, Custom DNS servers, Domain Names, and NTP Time Servers) is pushed directly into the operating system of that EC2 instance.
- **Production Scenario:** By default, AWS provides its own "AmazonProvidedDNS" to resolve internet queries. An enterprise company replaces this by creating a Custom DHCP Option Set so that every new server automatically talks to the company's private DNS servers instead.
- **Interview Edge:** *"DHCP in AWS is completely abstracted. You never spin up a 'DHCP Server' EC2 instance. The VPC Edge Router (always the VPC Network Base IP + 2) physically acts as the DHCP server, acting on the rules defined in the attached Option Set."*

## 6️⃣1️⃣ Q61: What are some practical use cases for DHCP option sets in AWS?
- **Short Answer:** The single most massive use case is **Hybrid Cloud Active Directory Integration**. If a company uses Microsoft Active Directory to manage `.corp.internal` domains, the DHCP Option Set forces all AWS EC2 instances to use the Corporate mapped DNS servers so they can instantly resolve internal network names without manual OS configuration.
- **Production Scenario:** A company deploys 500 EC2 instances. If they don't use a custom DHCP Option Set, they have to run a bash script on all 500 servers to manually edit `/etc/resolv.conf` to point to the corporate DNS. The DHCP Option Set automates this at the VPC level instantly.
- **Interview Edge:** *"When combining AWS with on-premise infrastructure via Direct Connect, injecting custom Domain Name Servers (DNS) and Network Time Protocol (NTP) servers via the DHCP Option Set is the foundational step for achieving cross-cloud domain resolution."*

## 6️⃣2️⃣ Q62: How do you create a DHCP option set in AWS?
- **Short Answer:** Open the VPC Console -> Navigate to **DHCP option sets** -> Click **Create DHCP option set** -> Enter your custom values (e.g., Domain name: `corp.internal`, Domain name servers: `10.0.1.55`, NTP servers) -> Click **Create DHCP option set**.
- **Production Scenario:** Creating a highly specific Option Set during a massive SAP migration, forcing all SAP application instances in AWS to natively sync time against a centralized, highly-secured on-premises NTP server.
- **Interview Edge:** *"Creating an Option Set is just generating a blueprint. Much like creating an Internet Gateway, it fundamentally does absolutely nothing until you physically attach it to a VPC."*

## 6️⃣3️⃣ Q63: How do you associate a DHCP option set with a VPC in AWS?
- **Short Answer:** Open the VPC Console -> Navigate to **Your VPCs** -> Select the target VPC -> Click **Actions** -> Choose **Edit DHCP options set** -> Select the custom Option Set from the dropdown -> Click **Save**.
- **Production Scenario:** Toggling a legacy VPC off the default AWS `AmazonProvidedDNS` and swapping it dynamically over to the new enterprise `ActiveDirectory_DHCP` option set.
- **Interview Edge:** *"A critical architectural concept: You do not assign DHCP sets to Subnets. You assign them exclusively to the massive VPC boundary. The entire VPC inherently shares the same DNS resolution rules."*

## 6️⃣4️⃣ Q64: How do you troubleshoot issues with DHCP option sets in AWS?
- **Short Answer:** 1) Verify the VPC actually has the Option Set associated. 2) SSH into the EC2 instance and inspect `/etc/resolv.conf` (Linux) or run `ipconfig /all` (Windows) to structurally confirm the OS actually received the custom DNS IPs. 3) Validate that the Security Groups/NACLs are actively permitting UDP Port 67/68 (DHCP) and TCP/UDP Port 53 (DNS).
- **Production Scenario:** A developer complains their EC2 instance can't resolve an internal database name. The Architect SSHs into the box, checks `/etc/resolv.conf`, and realizes the instance still has the default AWS DNS. The fix is a simple instance reboot to force the DHCP lease renewal.
- **Interview Edge:** *"Changing a DHCP Option Set at the VPC level does not instantly hot-swap the DNS settings on running EC2 instances. In production, you must explicitly reboot the instances or manually force a DHCP lease renewal (`dhclient`) to ingest the new networking rules."*

## 6️⃣5️⃣ Q65: Can you have multiple DHCP option sets associated with a VPC in AWS?
- **Short Answer:** No. It is a strict 1-to-1 relationship. A single VPC can only have exactly **one** DHCP Option Set actively associated with it at any given millisecond.
- **Production Scenario:** Trying to assign one DNS server to Public Subnets and a different DNS server to Private Subnets. Because the DHCP Option Set applies at the VPC perimeter, you cannot natively split DHCP behavior by Subnet. 
- **Interview Edge:** *"Because of this 1:1 VPC limit, if an enterprise organically requires vastly different DNS routing configurations for different environments, they are structurally forced to build entirely separate VPCs."*

## 6️⃣6️⃣ Q66: Can you modify a DHCP option set after it has been associated with a VPC in AWS?
- **Short Answer:** No, DHCP Option Sets are fundamentally **immutable**. Once created, you physically cannot edit the values inside of it. Instead, you must create a brand-new DHCP Option Set with the correct values, and seamlessly associate the new one to the VPC (effectively replacing the old one).
- **Production Scenario:** An IP address for the primary Custom DNS server changes from `.55` to `.56`. The Architect cannot "edit" the Option Set; they generate a new one, map it to the VPC, and then delete the legacy Option Set.
- **Interview Edge:** *"AWS treats DHCP Option Sets as immutable infrastructure. You never mutate them; you replace them. This strict immutability violently reduces configuration drift across enterprise networks."*

## 6️⃣7️⃣ Q67: Can you use a third-party DHCP server instead of the built-in DHCP service in AWS?
- **Short Answer:** Yes, but it is exceptionally rare and highly complex. You would deploy an EC2 instance running DHCP software (like `dnsmasq` or Windows Server DHCP) and then manually strip the DHCP configuration out of your OS images. However, you generally cannot truly "disable" the native AWS VPC DHCP service.
- **Production Scenario:** A massive corporate lift-and-shift migration where they aggressively refuse to change their legacy IP-assignment software, deploying a massive third-party IPAM (IP Address Management) cluster via EC2.
- **Interview Edge:** *"Using third-party DHCP servers in AWS is an extreme architectural anti-pattern. Because AWS fundamentally controls the hypervisor and the networking plane, bypassing native VPC DHCP usually introduces catastrophic scaling and high-availability failures."*

## 6️⃣8️⃣ Q68: Can you use DHCP option sets with AWS Transit Gateway?
- **Short Answer:** Transit Gateway (TGW) itself does not *use* DHCP Option Sets, as TGW is purely a Layer-3 massive core router. However, Transit Gateway seamlessly respects the DHCP architecture: the distributed VPCs attached to the Transit Gateway maintain their own localized DHCP Option Sets to push DNS settings.
- **Production Scenario:** A central Shared Services VPC holds the Active Directory DNS servers. 50 Spoke VPCs are connected via Transit Gateway. All 50 Spoke VPCs have their DHCP Option Sets configured to point to the IP addresses hovering in the Shared Services VPC.
- **Interview Edge:** *"Transit Gateway is the physical highway; the DHCP Option Set is the GPS. By combining them, you establish a global 'Hub-and-Spoke' DNS topology where thousands of EC2 instances globally resolve queries through a single, centralized Active Directory cluster."*

## 6️⃣9️⃣ Q69: How do you delete a DHCP option set in AWS?
- **Short Answer:** Open the VPC Console -> Navigate to **DHCP option sets** -> Select the specific Option Set -> Click **Actions** -> Choose **Delete DHCP option set** -> Confirm deletion.
- **Production Scenario:** Eradicating old configuration files. You physically cannot delete a DHCP option set if it is actively associated with a live VPC. You must first swap the VPC back to the `default` AWS option set before the console permits deletion.
- **Interview Edge:** *"In an enterprise Terraform environment, destroying the `aws_vpc_dhcp_options` resource automatically forces a detachment sequence from the VPC, gracefully rolling the network back to the default AWS resolution behavior."*
