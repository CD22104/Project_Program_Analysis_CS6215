# Zero-cost SoCLaaS access

The course document identifies SoCLaaS as a free NUS SoC service. Its Portal is
https://soclaas-portal.comp.nus.edu.sg and the course-linked guide is
https://dochub.comp.nus.edu.sg/cf/guides/soclaas/start . The supplied configuration
uses https://soclaas-api.comp.nus.edu.sg/v1 . No paid fallback is permitted.

On 2026-10-15, this server resolved the API hostname to 137.132.84.188, but direct
TCP connections to port 443 and an authenticated GET `/models` timed out. No
authentication response was received, so the key has not yet been validated.
DNS resolution alone does not establish service access. No proxy environment
variables were present during the check.

The public gateway page checked on 2026-10-15 explicitly restricts its key Portal
and documentation to the NUS network, but does not establish that the API has the
same restriction. A timeout alone does not identify the cause. First test the API
from the user's own computer; an authentication response proves transport access.
If that computer can reach it, the SSH route below can be used. Otherwise, connect
that computer using the current NUS nVPN guide and test again.
Official guides: https://nusit.nus.edu.sg/services/wifi_internet/nvpn/ and
https://nusit.nus.edu.sg/eguides/ . The current desktop guide lists Cisco Secure
Client; use the current student profile instructions in A.S.K., not old Pulse
Secure configuration copied from historical PDFs.

1. Connect the server to the NUS network/VPN, or use a laptop that can reach the
   service while connected to NUS VPN.
2. Store the personal key in `~/.config/course/soclaas.env` (mode 600), along with
   `SOCLAAS_BASE_URL` and `SOCLAAS_MODEL`. The file is already present on the user's
   server and should not be copied into the repository.
3. Run `PYTHONPATH=src .env-baseline/bin/python scripts/check_model.py` from the
   project root. It displays model IDs or a nonsecret error. Choose a fixed model
   ID for formal experiments; an alias such as `default` must also record each
   response's actual returned model ID and any service fingerprint.

If only the laptop has VPN access, run this in its terminal, replacing SERVER_ALIAS
with the SSH address/alias normally used to connect to this server:

```bash
ssh -N -o ExitOnForwardFailure=yes \
  -R 127.0.0.1:9443:soclaas-api.comp.nus.edu.sg:443 SERVER_ALIAS
```

Keep that terminal open. Add these nonsecret entries to the server's existing
private config file:

```text
SOCLAAS_CONNECT_HOST=127.0.0.1
SOCLAAS_CONNECT_PORT=9443
```

The client connects through the loopback tunnel but retains the SoCLaaS hostname
for TLS SNI and certificate verification. It does not disable TLS checks or change
the HTTP authorization destination. Port 9443 is bound only to loopback. The SSH
server must permit remote forwarding. This route uses the user's existing NUS
access; it does not bypass institutional access controls.
