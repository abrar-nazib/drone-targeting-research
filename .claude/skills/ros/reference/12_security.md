# ROS 2 Security (Jazzy)

> Security is not in the immediate scope for this drone project (single-machine sim), but kept for completeness.

> **Underlying spec**: SROS2 (the `sros2` Python package + `ros2 security` CLI verb)
> wraps the OMG **DDS-Security 1.1** specification — Authentication,
> Access Control, and Cryptographic plugins (PKI / X.509 + S/MIME-signed
> XML policies). ROS 2 sits on top of DDS, so all crypto is enforced by
> the RMW layer rather than by ROS itself.
>
> **RMW support**: DDS-Security is implemented by RTI Connext, eProsima
> Fast DDS, and Eclipse Cyclone DDS. For ROS 2 Jazzy:
> - `rmw_fastrtps_cpp` (default) — supported, but Fast DDS must be
>   built with `-DSECURITY=ON` (the binary distribution from ROS apt
>   already is). Note that Fast DDS uses Shared Memory transport by
>   default on a single host — packets never hit the network, so
>   `tcpdump` will see nothing even with security off; disable SHM in
>   the Fast-DDS XML profile if you want to inspect loopback traffic.
> - `rmw_cyclonedds_cpp` — supported.
> - `rmw_connextdds` — supported (commercial).
> - **Cross-vendor secure communication is NOT supported** — every
>   participant on the domain must use the same RMW.

## Setting up security (Introducing ros2 security)
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Advanced/Security/Introducing-ros2-security.html

The `sros2` package adds a `ros2 security` verb to the ROS 2 CLI and
provides Python helpers for generating PKI material. Tested on Linux,
macOS, Windows; with both `rclcpp` and `rclpy` clients.

### Environment variables (the four that matter)

| Variable | Purpose | Typical value |
|---|---|---|
| `ROS_SECURITY_KEYSTORE` | Absolute path to the keystore directory containing CA, certs, and per-node enclaves. Required. | `~/sros2_demo/demo_keystore` |
| `ROS_SECURITY_ENABLE` | Master switch. If unset or `false`, the RMW runs unencrypted regardless of other vars. | `true` |
| `ROS_SECURITY_STRATEGY` | What the RMW does when an enclave is missing or signature invalid. `Enforce` = refuse to start the node. `Permissive` = fall back to insecure communication and continue. | `Enforce` |
| `ROS_SECURITY_ENCLAVE_OVERRIDE` | Forces a specific enclave for processes that don't accept `--enclave` (notably the `ros2` CLI itself). | `/talker_listener/talker` |

Typical shell setup:
```bash
export ROS_SECURITY_KEYSTORE=~/sros2_demo/demo_keystore
export ROS_SECURITY_ENABLE=true
export ROS_SECURITY_STRATEGY=Enforce
```

### `ros2 security` CLI subcommands

| Subcommand | Purpose |
|---|---|
| `create_keystore <KEYSTORE_DIR>` | Bootstrap a new keystore: creates `public/`, `private/`, `enclaves/`; generates the Identity CA and Permissions CA (X.509, P-256 EC, 10-year validity by default) and the default `governance.xml` / `governance.p7s`. |
| `create_enclave <KEYSTORE_DIR> <ENCLAVE_NAME>` | Create a new enclave directory under `enclaves/<ENCLAVE_NAME>/`, generate its keypair + identity CSR, sign the cert with the Identity CA, and emit a default permissive `permissions.xml` + signed `permissions.p7s`. Enclave names look like ROS namespaces (`/talker_listener/talker`). |
| `create_permission <KEYSTORE_DIR> <ENCLAVE_NAME> <POLICY_XML>` | Re-derive the enclave's `permissions.xml` from a higher-level policy file (the SROS2 policy schema, which is more concise than raw DDS permissions XML), then sign it. |
| `generate_artifacts -k <KEYSTORE_DIR> -e <ENCLAVE> [-p <POLICY>]` | One-shot convenience: creates the keystore if missing, creates each named enclave, and applies a policy file. The recommended workflow for production. |
| `list_keys <KEYSTORE_DIR>` | List the identity certificates registered in `public/`. |
| `list_enclaves <KEYSTORE_DIR>` | List every enclave under `enclaves/`. |

### Minimal end-to-end example (single host)
```bash
mkdir -p ~/sros2_demo && cd ~/sros2_demo

# 1. Bootstrap CAs and governance.
ros2 security create_keystore demo_keystore

# 2. Create one enclave per node.
ros2 security create_enclave demo_keystore /talker_listener/talker
ros2 security create_enclave demo_keystore /talker_listener/listener

# 3. Turn security on for this shell.
export ROS_SECURITY_KEYSTORE=~/sros2_demo/demo_keystore
export ROS_SECURITY_ENABLE=true
export ROS_SECURITY_STRATEGY=Enforce

# 4. Run nodes, naming the enclave on each one.
ros2 run demo_nodes_cpp talker  --ros-args --enclave /talker_listener/talker
ros2 run demo_nodes_py  listener --ros-args --enclave /talker_listener/listener
```

### Securing the `ros2` CLI itself
The CLI also needs an enclave. Two caveats:
1. Set `ROS_SECURITY_ENCLAVE_OVERRIDE` to point it at one.
2. The ROS daemon caches discovery state and bypasses your env, so use
   `--no-daemon`:
   ```bash
   export ROS_SECURITY_ENCLAVE_OVERRIDE=/talker_listener/listener
   ros2 node list --no-daemon --spin-time 3
   ros2 topic echo --no-daemon /chatter
   ```

## The Keystore
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Advanced/Security/The-Keystore.html

`ros2 security create_keystore` produces a fixed three-subdirectory
layout. Sensitivity tiers matter for deployment (see Deployment
Guidelines below).

### Directory layout
```
$ROS_SECURITY_KEYSTORE/
├── public/                          # World-readable, ship to every device
│   ├── ca.cert.pem                  # Trust anchor (self-signed root CA)
│   ├── identity_ca.cert.pem         # → symlink to ca.cert.pem
│   └── permissions_ca.cert.pem      # → symlink to ca.cert.pem
├── private/                         # NEVER ship to target devices
│   ├── ca.key.pem                   # Root CA private key
│   ├── identity_ca.key.pem          # → symlink to ca.key.pem
│   └── permissions_ca.key.pem       # → symlink to ca.key.pem
└── enclaves/                        # Per-process security context
    ├── governance.xml               # Domain-wide policy (human-readable)
    ├── governance.p7s               # S/MIME-signed governance
    └── <ENCLAVE_PATH>/              # e.g. talker_listener/talker/
        ├── cert.pem                 # Identity cert (signed by Identity CA)
        ├── key.pem                  # Identity private key
        ├── permissions.xml          # Per-enclave ACL (human-readable)
        ├── permissions.p7s          # S/MIME-signed permissions
        ├── governance.p7s           # → link to enclaves/governance.p7s
        ├── identity_ca.cert.pem     # → link to public/identity_ca.cert.pem
        └── permissions_ca.cert.pem  # → link to public/permissions_ca.cert.pem
```

### What the six files in an enclave do
- `cert.pem` + `key.pem` — used by the **Authentication** plugin to
  prove this participant's identity during DDS discovery.
- `governance.p7s` — domain-wide knobs (allow unauthenticated joiners?
  encrypt discovery? default rule for unlisted topics?). Same file is
  symlinked into every enclave so the whole domain agrees on policy.
- `permissions.p7s` — per-enclave allow/deny list of topics, services,
  parameters this enclave may publish/subscribe/call.
- `identity_ca.cert.pem` / `permissions_ca.cert.pem` — the trust
  anchors the participant uses to verify peers and signatures.

### Verifying a signed file (debugging)
```bash
cd $ROS_SECURITY_KEYSTORE/enclaves
openssl smime -verify -in governance.p7s \
              -CAfile ../public/permissions_ca.cert.pem
openssl smime -verify -in talker_listener/talker/permissions.p7s \
              -CAfile ../public/permissions_ca.cert.pem
```
With `ROS_SECURITY_STRATEGY=Enforce`, hand-editing `governance.xml` or
`permissions.xml` invalidates the `.p7s` signature and the node
refuses to start until you re-sign or re-run `create_permission`.

### Mapping nodes to enclaves
The enclave is selected at runtime via `--enclave /path/under/enclaves`
on the node's command line, or via `ROS_SECURITY_ENCLAVE_OVERRIDE` for
processes that don't parse `--ros-args` cleanly. One enclave per
process is the recommended granularity (not one per node, even though
enclave paths look like node namespaces).

## Security on Two (multi-machine)
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Advanced/Security/Security-on-Two.html

Extends the single-machine setup so two hosts ("Alice" and "Bob") can
talk securely. Keystore lives on Alice; only the per-enclave material
needed by Bob's node is copied to Bob.

### Procedure
1. **On Bob — create an empty keystore directory:**
   ```bash
   ssh Bob
   mkdir ~/sros2_demo
   exit
   ```
2. **On Alice — copy the talker enclave to Bob.** This is enough
   because each enclave directory already contains links to the public
   CA cert, governance, and permissions CA cert it needs. The private
   CA key on Alice is *not* shipped.
   ```bash
   cd ~/sros2_demo/demo_keystore
   scp -r enclaves/talker_listener/talker \
       USER@Bob:~/sros2_demo/demo_keystore/enclaves/talker_listener/
   # Also copy the public CA bundle so Bob can verify Alice's cert:
   scp -r public USER@Bob:~/sros2_demo/demo_keystore/
   ```
3. **On Bob — set the security env vars and run the talker:**
   ```bash
   export ROS_SECURITY_KEYSTORE=~/sros2_demo/demo_keystore
   export ROS_SECURITY_ENABLE=true
   export ROS_SECURITY_STRATEGY=Enforce
   ros2 run demo_nodes_cpp talker --ros-args --enclave /talker_listener/talker
   ```
4. **On Alice — run the listener with its own enclave:**
   ```bash
   ros2 run demo_nodes_py listener --ros-args --enclave /talker_listener/listener
   ```

Both authentication (each side proves its identity to the other via
the CA) and encryption (DDS-Security crypto plugin) protect the
network traffic. To add a third machine, repeat: copy that machine's
enclave + the `public/` bundle, set env vars, run with `--enclave`.

## Examine Traffic
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Advanced/Security/Examine-Traffic.html

How to verify that turning security on actually encrypts the wire.
Tools: `tcpdump` (CLI), Wireshark (GUI). Both filter on UDP because
RTPS (DDS's wire protocol) rides UDP.

### Important Fast DDS gotcha
`rmw_fastrtps_cpp` enables **Shared Memory Transport** by default for
participants on the same host. Packets never traverse the loopback
interface, so `tcpdump -i lo` will see nothing even when security is
off. To inspect single-host traffic, either run the talker and
listener on different machines or disable SHM in a Fast-DDS XML
profile via `FASTRTPS_DEFAULT_PROFILES_FILE`.

### tcpdump filters
RTPS discovery uses UDP **7400** by default; user data uses
**7401-7500** (`7400 + 250*domainId + offset`).

```bash
# Discovery packets (SPDP/SEDP) on multicast 239.255.0.1:
sudo tcpdump -X -i any udp port 7400

# User data:
sudo tcpdump -X -i any udp portrange 7401-7500
```

### What you see without security
- Discovery packets contain plaintext `RTPS` magic, multicast group
  `239.255.0.1`, full node names like `/talker_listener/talker`, and
  the enclave path.
- Data packets contain the message payload in the clear, e.g.
  `Hello World: 2135` is directly visible in the hex dump.

### What you see with `ROS_SECURITY_ENABLE=true`
- Discovery packets are larger and contain the security handshake
  blobs instead of readable node metadata.
- Data packets carry only the `RTPS` header and ciphertext — payload
  is unreadable. This is the DDS-Security **Cryptographic plugin** in
  action (the `dds.sec.crypto.builtin` plugin in Fast DDS, equivalent
  in Cyclone / Connext).

### Wireshark
Apply display filter `rtps` and inspect the `Submessage` tree to see
the same difference graphically. Wireshark's RTPS dissector ships
with mainline releases, no extra plugins needed.

## Access Controls
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Advanced/Security/Access-Controls.html

By default `create_enclave` issues a permissive `permissions.xml`
allowing any topic. Restricting it is what gives you actual access
control.

### DDS topic naming
SROS2 maps ROS names to DDS names by prefix:
- ROS topic `chatter` → DDS topic `rt/chatter`
- ROS request topic `add_two_ints` → `rq/add_two_intsRequest`
- ROS reply topic → `rr/add_two_intsReply`
- ROS parameter topics → `rp/...`
- ROS action topics → `ra/...` / `rs/...`

Permissions XML uses the DDS form (`rt/chatter`), not `chatter`.

### `permissions.xml` schema (raw DDS-Security form)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<dds xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
     xsi:noNamespaceSchemaLocation="http://www.omg.org/spec/DDS-SECURITY/20170901/omg_shared_ca_permissions.xsd">
  <permissions>
    <grant name="/talker_listener/talker">
      <subject_name>CN=/talker_listener/talker</subject_name>
      <validity>
        <not_before>2026-01-01T00:00:00</not_before>
        <not_after>2036-01-01T00:00:00</not_after>
      </validity>
      <allow_rule>
        <domains><id>0</id></domains>
        <publish>
          <topics>
            <topic>rt/chatter</topic>
            <topic>rt/rosout</topic>
          </topics>
        </publish>
        <subscribe>
          <topics>
            <topic>rq/*</topic>          <!-- wildcard allowed -->
          </topics>
        </subscribe>
      </allow_rule>
      <default>DENY</default>            <!-- deny anything not listed -->
    </grant>
  </permissions>
</dds>
```

After editing, re-sign with the Permissions CA so the `.p7s` matches:
```bash
cd $ROS_SECURITY_KEYSTORE/enclaves/talker_listener/talker
openssl smime -sign -text \
  -in  permissions.xml \
  -out permissions.p7s \
  -signer ../../../public/permissions_ca.cert.pem \
  -inkey  ../../../private/permissions_ca.key.pem
```

### SROS2 policy file (higher-level alternative)
SROS2 also accepts a friendlier policy XML keyed by ROS names that is
expanded into the DDS form for you. Apply it with `create_permission`
or `generate_artifacts`:
```bash
ros2 security create_permission \
    demo_keystore \
    /talker_listener/talker \
    /tmp/sros2/sros2/test/policies/sample.policy.xml
```
This regenerates `permissions.xml` + `permissions.p7s` for the named
enclave from a single source-of-truth policy file.

### Enforcement behavior
With `ROS_SECURITY_STRATEGY=Enforce`, attempting to publish a topic
that isn't in the allow-list — including via runtime topic remapping
on the command line — causes the node to fail to start (or to fail to
create the publisher). With `Permissive`, the node falls back to
unsecured communication.

## Deployment Guidelines
**Source**: https://docs.ros.org/en/jazzy/Tutorials/Advanced/Security/Deployment-Guidelines.html

Production guidance for shipping SROS2 to fielded devices.

### Sensitivity tiers
| Directory | Stays in org | Ships to device | Sensitivity |
|---|---|---|---|
| `public/`   | yes | yes | low — just CA certs |
| `private/`  | yes | **no**  | **high — root CA private keys live here** |
| `enclaves/` | yes | yes (only the enclaves that device runs) | medium |

Losing `private/` is unrecoverable: you can no longer issue new certs,
revoke existing ones, or sign new permission files — you must rebuild
the entire trust hierarchy and reprovision every device.

### Recommendations
- **One enclave per application/process** so a compromised process
  can't speak to topics outside its remit.
- **Ship only the enclaves a given device needs** — a sensor node
  doesn't need the planner's enclave material.
- Mount `enclaves/` **read-only** on the device to prevent local
  tampering.
- For real deployments, store the CA private key in an **HSM** and
  reference it via a PKCS#11 URI rather than leaving it as a `.pem`
  file on disk.
- Generate enclaves and CA on an **isolated build host**; never on the
  target device.

### Production workflow (the tutorial's Docker example)
1. **Provisioning host**: a `keystore-creator` container runs
   `ros2 security create_keystore` and `create_enclave`/
   `generate_artifacts` for every application image you intend to
   ship.
2. **Image build**: per-application containers (e.g. `talker`,
   `listener`) bake in **only their own enclave directory** plus the
   `public/` CA bundle, via a shared build-time volume.
3. **Deploy**: ship the per-app images; `private/` never leaves the
   provisioning host.
4. **Runtime**: each container sets `ROS_SECURITY_KEYSTORE`,
   `ROS_SECURITY_ENABLE=true`, `ROS_SECURITY_STRATEGY=Enforce`, and
   launches its node with `--enclave`.

### Notes the page does not cover (but worth knowing)
- The Deployment Guidelines page itself does **not** discuss
  `ROS_SECURITY_STRATEGY` values or security logging — those live on
  the introductory page and in the underlying DDS-Security spec
  respectively.
- Each RMW vendor exposes additional knobs through its own XML/JSON
  config (Fast DDS profiles, Cyclone DDS config, Connext QoS XML) for
  things like SHM disablement, custom crypto plugins, and audit log
  destinations.
