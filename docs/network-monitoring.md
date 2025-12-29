# Network monitoring considerations for the VNet-attached Container Apps environment

## VNet itself
A virtual network provides isolation and routing, but it does not collect traffic telemetry on its own. Adding the VNet module only attaches the Container Apps environment to a delegated subnet for private networking; no monitoring data is emitted unless you enable additional services.

## Recommended monitoring layers
- **Container Apps diagnostics**: Enable diagnostic settings on the Container Apps environment and individual apps to send logs/metrics (ingress, egress, TCP resets, HTTP status codes) to Log Analytics. This surfaces per-app network health rather than raw packets.
- **Application Insights / OpenTelemetry**: Track outbound dependencies from the backend (e.g., HTTP, gRPC, SQL) to see latency, failure rates, and destinations. This is the primary way to monitor “outbound transactions” at the app layer.
- **Network security telemetry**: If a subnet supports NSGs or Azure Firewall, enable flow logs or firewall diagnostics to see allowed/denied traffic. The Microsoft.App–delegated subnet used by Container Apps does not emit flow logs by default, so add a firewall or shared egress path if packet-level visibility is required.
- **Private DNS and endpoint health**: Monitor DNS resolution failures and private endpoint connectivity via Azure Monitor logs/metrics to catch egress issues to internal services.
- **Front Door / WAF (if adopted)**: Offload TLS and WAF at the edge and stream WAF/edge access logs to Log Analytics for request-level visibility before traffic reaches nginx.

## Takeaways
- The VNet module hardens isolation but is not a monitoring solution by itself.
- Combine platform diagnostics (Container Apps), app-level telemetry (Application Insights/OpenTelemetry), and, where supported, flow logs or firewall diagnostics to observe outbound traffic and transactions.
