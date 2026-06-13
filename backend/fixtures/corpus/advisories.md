# Threat advisories & response playbooks (paraphrased, mock)

## Advisory: Edge gateway unauthenticated RCE (KEV-listed)
Internet-facing edge gateways with an unpatched management interface are being actively
exploited for unauthenticated remote code execution. Treat as critical when the CVE is on
the CISA KEV catalog or has a high EPSS score. Recommended actions:
1. Isolate the affected host from the network immediately.
2. Rotate credentials and revoke active sessions originating from the host.
3. Apply the vendor patch; if unavailable, restrict management-interface exposure.
4. Hunt for lateral movement using known threat-intel indicators.

## Playbook: Suspicious privilege escalation
A sudden Global Administrator / privileged-role grant following a failed-signin burst is a
strong compromise signal. Disable the suspicious account, review recent role assignments,
and require re-authentication for privileged users.

## Playbook: Anomalous sign-in (impossible travel)
Sign-ins from geographically impossible locations within a short window indicate credential
theft. Force password reset, revoke tokens, and check for mailbox/forwarding rule changes.
