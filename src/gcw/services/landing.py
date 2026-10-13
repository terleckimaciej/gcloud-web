"""Landing pages (level L0): services reachable by name alone, without a resource cache.

``gcw bigquery`` opens the BigQuery start page, ``gcw pubsub`` the Pub/Sub one.
These services have no routes and no resource listing yet, so one table of
``name -> Landing`` replaces what would otherwise be dozens of near-empty
service modules.

When a service grows real routes it gets its own module in ``gcw.services``
(like ``run``) and its entry is removed from here; the command name stays the
same, so nothing changes for the user.

Paths are relative to ``https://console.cloud.google.com/`` and are written
without a leading slash and without a query string: ``?project=…`` is appended
later by ``gcw.web.url``. Every path still has to be checked against the real
console before it is marked verified in the plan.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Landing:
    """The start page of a service that has no routes of its own.

    Attributes:
        path: Console path opened by ``gcw <name>``, e.g. ``"cloudpubsub"``.
        help: One-line description shown in ``gcw services``.
    """

    path: str
    help: str


LANDINGS: dict[str, Landing] = {
    # Compute
    "appengine": Landing("appengine", "App Engine services and versions"),
    "batch": Landing("batch/jobs", "Batch jobs"),
    "filestore": Landing("filestore/instances", "Filestore instances"),
    # Build and delivery
    "build": Landing("cloud-build/builds", "Cloud Build history and triggers"),
    "deploy": Landing("deploy/delivery-pipelines", "Cloud Deploy delivery pipelines"),
    "source": Landing("source/repos", "Cloud Source Repositories"),
    # Serverless and integration
    "workflows": Landing("workflows", "Workflows"),
    "scheduler": Landing("cloudscheduler", "Cloud Scheduler jobs"),
    "tasks": Landing("cloudtasks", "Cloud Tasks queues"),
    "pubsub": Landing("cloudpubsub", "Pub/Sub topics and subscriptions"),
    "eventarc": Landing("eventarc/triggers", "Eventarc triggers"),
    "apigateway": Landing("api-gateway/apis", "API Gateway APIs"),
    "apigee": Landing("apigee", "Apigee API management"),
    # Databases
    "bigtable": Landing("bigtable/instances", "Bigtable instances"),
    "spanner": Landing("spanner/instances", "Spanner instances"),
    "firestore": Landing("firestore/databases", "Firestore databases"),
    "memorystore": Landing("memorystore/redis/instances", "Memorystore for Redis instances"),
    "alloydb": Landing("alloydb/clusters", "AlloyDB clusters"),
    # Data and analytics
    "bigquery": Landing("bigquery", "BigQuery studio and datasets"),
    "dataflow": Landing("dataflow/jobs", "Dataflow jobs"),
    "dataplex": Landing("dataplex", "Dataplex lakes and catalog"),
    "datastream": Landing("datastream/streams", "Datastream streams"),
    "datafusion": Landing("data-fusion/instances", "Cloud Data Fusion instances"),
    "looker": Landing("looker/instances", "Looker instances"),
    "transfer": Landing("transfer/jobs", "Storage Transfer Service jobs"),
    # AI
    "vertex": Landing("vertex-ai", "Vertex AI"),
    "workbench": Landing("vertex-ai/workbench/instances", "Vertex AI Workbench instances"),
    # Networking
    "vpc": Landing("networking/networks/list", "VPC networks"),
    "addresses": Landing("networking/addresses/list", "Reserved IP addresses"),
    "firewall": Landing("networking/firewalls/list", "VPC firewall rules"),
    "routes": Landing("networking/routes/list", "VPC routes"),
    "lb": Landing("net-services/loadbalancing/list/loadBalancers", "Load balancers"),
    "dns": Landing("net-services/dns/zones", "Cloud DNS zones"),
    "cdn": Landing("net-services/cdn/list", "Cloud CDN origins"),
    "nat": Landing("net-services/nat/list", "Cloud NAT gateways"),
    "vpn": Landing("hybrid/vpn/list", "Cloud VPN tunnels and gateways"),
    "interconnect": Landing("hybrid/interconnects/list", "Cloud Interconnect connections"),
    # Security
    "kms": Landing("security/kms", "Cloud KMS key rings"),
    "certificates": Landing("security/ccm/list/certificates", "Certificate Manager certificates"),
    "armor": Landing("net-security/securitypolicies/list", "Cloud Armor security policies"),
    "scc": Landing("security/command-center", "Security Command Center"),
    "recaptcha": Landing("security/recaptcha", "reCAPTCHA keys"),
    "orgpolicies": Landing("iam-admin/orgpolicies/list", "Organization policies"),
    "quotas": Landing("iam-admin/quotas", "Quotas and system limits"),
    # Operations
    "monitoring": Landing("monitoring", "Cloud Monitoring overview"),
    "alerts": Landing("monitoring/alerting", "Monitoring alerting policies"),
    "uptime": Landing("monitoring/uptime", "Monitoring uptime checks"),
    "errors": Landing("errors", "Error Reporting"),
    "trace": Landing("traces/list", "Cloud Trace"),
    "profiler": Landing("profiler", "Cloud Profiler"),
    # Management
    "billing": Landing("billing", "Billing accounts and reports"),
    "apis": Landing("apis/dashboard", "Enabled APIs and services"),
    "projects": Landing("cloud-resource-manager", "Projects and resource hierarchy"),
    "support": Landing("support", "Support cases"),
    "marketplace": Landing("marketplace", "Marketplace"),
}
