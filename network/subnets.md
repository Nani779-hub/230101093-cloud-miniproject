# Subnet Architecture and Stateless NACL Design

**Course:** Cloud Computing (CS3081) Mini Project  
**Student Name:** Sachith  
**Roll Number:** 230101093  

---

## 1. Subnet Allocation & Specification

We are given the parent network block `10.20.0.0/16`. Subnets are allocated starting from `10.20.0.0` in descending order of required host count (from largest to smallest requirement), placing each subnet contiguously immediately following the previous one, using the minimal prefix length that satisfies each requirement:

$$\text{Usable Hosts} = 2^{32 - \text{prefix}} - 2 \ge \text{Hosts Needed}$$

### Subnet Allocation Table

| Subnet | Hosts Needed | Prefix | Network Address | Usable Host Range | Broadcast Address | Usable Hosts |
| :--- | :---: | :---: | :--- | :--- | :--- | :---: |
| **app** | 1,000 | `/22` | `10.20.0.0` | `10.20.0.1` – `10.20.3.254` | `10.20.3.255` | 1,022 |
| **public** | 250 | `/24` | `10.20.4.0` | `10.20.4.1` – `10.20.4.254` | `10.20.4.255` | 254 |
| **data** | 100 | `/25` | `10.20.5.0` | `10.20.5.1` – `10.20.5.126` | `10.20.5.127` | 126 |
| **management** | 20 | `/27` | `10.20.5.128` | `10.20.5.129` – `10.20.5.158` | `10.20.5.159` | 30 |

Remaining unallocated space in `10.20.0.0/16`: `10.20.5.160/27` through `10.20.255.255`.

---

## 2. Arithmetic Working & Derivation

### Subnet 1: `app` (Requirement: 1,000 hosts)
1. **Host bits calculation:**
   $$2^h - 2 \ge 1000 \implies 2^h \ge 1002 \implies h = 10 \quad (2^{10} = 1024)$$
2. **Prefix length:**
   $$\text{prefix} = 32 - h = 32 - 10 = 22 \quad (\text{Subnet mask: } 255.255.252.0)$$
3. **Capacity:**
   $$\text{Usable hosts} = 2^{10} - 2 = 1024 - 2 = 1,022 \text{ hosts}$$
4. **Range:**
   - Network address: `10.20.0.0`
   - First usable IP: `10.20.0.1`
   - Last usable IP: `10.20.3.254`
   - Broadcast address: `10.20.3.255`

### Subnet 2: `public` (Requirement: 250 hosts)
1. **Starting address:** Immediately follows `app` broadcast (`10.20.3.255` + 1 = `10.20.4.0`).
2. **Host bits calculation:**
   $$2^h - 2 \ge 250 \implies 2^h \ge 252 \implies h = 8 \quad (2^8 = 256)$$
3. **Prefix length:**
   $$\text{prefix} = 32 - 8 = 24 \quad (\text{Subnet mask: } 255.255.255.0)$$
4. **Capacity:**
   $$\text{Usable hosts} = 2^8 - 2 = 256 - 2 = 254 \text{ hosts}$$
5. **Range:**
   - Network address: `10.20.4.0`
   - First usable IP: `10.20.4.1`
   - Last usable IP: `10.20.4.254`
   - Broadcast address: `10.20.4.255`

### Subnet 3: `data` (Requirement: 100 hosts)
1. **Starting address:** Immediately follows `public` broadcast (`10.20.4.255` + 1 = `10.20.5.0`).
2. **Host bits calculation:**
   $$2^h - 2 \ge 100 \implies 2^h \ge 102 \implies h = 7 \quad (2^7 = 128)$$
3. **Prefix length:**
   $$\text{prefix} = 32 - 7 = 25 \quad (\text{Subnet mask: } 255.255.255.128)$$
4. **Capacity:**
   $$\text{Usable hosts} = 2^7 - 2 = 128 - 2 = 126 \text{ hosts}$$
5. **Range:**
   - Network address: `10.20.5.0`
   - First usable IP: `10.20.5.1`
   - Last usable IP: `10.20.5.126`
   - Broadcast address: `10.20.5.127`

### Subnet 4: `management` (Requirement: 20 hosts)
1. **Starting address:** Immediately follows `data` broadcast (`10.20.5.127` + 1 = `10.20.5.128`).
2. **Host bits calculation:**
   $$2^h - 2 \ge 20 \implies 2^h \ge 22 \implies h = 5 \quad (2^5 = 32)$$
3. **Prefix length:**
   $$\text{prefix} = 32 - 5 = 27 \quad (\text{Subnet mask: } 255.255.255.224)$$
4. **Capacity:**
   $$\text{Usable hosts} = 2^5 - 2 = 32 - 2 = 30 \text{ hosts}$$
5. **Range:**
   - Network address: `10.20.5.128`
   - First usable IP: `10.20.5.129`
   - Last usable IP: `10.20.5.158`
   - Broadcast address: `10.20.5.159`

---

## 3. Stateless NACL Technical Explanations

### Why Stateless NACLs Need Separate Return / Reply Rules
Unlike stateful firewalls (such as AWS Security Groups or iptables with `conntrack`), a **stateless NACL does not maintain a connection tracking state table**. It inspects each packet purely in isolation based strictly on layer-3 IP addresses and layer-4 TCP/UDP ports.

When an inbound TCP connection arrives at the public subnet load balancer (e.g., from client IP $C$ on ephemeral port $P_c \in [1024, 65535]$ destined for load balancer port 443), the inbound rule allows the initial SYN packet. However, when the load balancer generates the SYN-ACK return packet destined for client IP $C$ on port $P_c$, the NACL does not know that this packet belongs to an established session. Consequently, without an explicit outbound rule permitting traffic to ephemeral destination ports (`1024-65535`), the return packet is dropped by the default deny rule. 

Similarly, when the load balancer originates a proxy connection outbound to the backend `app` subnet on destination port 8000, the backend response packet coming back into the public subnet arrives with destination port equal to the load balancer's ephemeral source port. Therefore, an explicit inbound rule allowing TCP traffic on ephemeral ports (`1024-65535`) from the `app` subnet CIDR (`10.20.0.0/22`) is required to admit backend responses.

### Why Rule Ordering Matters for `198.51.100.0/24`
NACL rules are evaluated in strictly ascending numerical order (from lowest rule number to highest), and evaluation terminates on the **first matching rule** ("first match wins"). 

The CIDR `198.51.100.0/24` is a subset of the global Internet range `0.0.0.0/0`. We have an allow rule for standard web traffic (TCP ports 80 and 443) open to `0.0.0.0/0`. If the deny rule for `198.51.100.0/24` were numbered higher than the web allow rules (e.g., allow 443 as rule 100 and deny `198.51.100.0/24` as rule 200), an inbound packet from an abusive host `198.51.100.9` targeting port 443 would match rule 100 first and be permitted through. 

Placing the deny rule at **Rule 100** (a lower rule number than Rule 110 for port 80 and Rule 120 for port 443) guarantees that any packet originating from `198.51.100.0/24` is immediately rejected regardless of the destination port.
