"""BigQuery: console routes for datasets and the tables inside them.

Commands::

    gcw bigquery                           BigQuery studio
    gcw bigquery datasets [NAME]           list of datasets, or one dataset
    gcw bigquery tables [DATASET.TABLE]    list of tables, or one table

A table is named ``DATASET.TABLE``, as in standard SQL, because a table ID is
only unique inside its dataset. Neither kind needs a location in the URL; the
cache keeps a dataset's location for listings. The console selects a resource
through the ``ws`` query parameter, which holds the project and the dataset or
table; the route fills it from ``{project}``, ``{dataset}`` and ``{table}``.

Datasets are listed with the BigQuery API v2. Tables are listed dataset by
dataset, in parallel; a dataset that cannot be read is skipped. URL templates
and endpoints are unverified until checked against the real console and API.
"""

from gcw.cache.store import Resource
from gcw.context.resolve import Context
from gcw.web.route import Route

API = "https://bigquery.googleapis.com/bigquery/v2"

NAME = "bigquery"
HELP = "BigQuery datasets and tables"
LANDING = "bigquery"

KINDS = {
    "datasets": Route(
        path="bigquery?ws=!1m4!1m3!3m2!1s{project}!2s{name}",
        list_path="bigquery",
    ),
    "tables": Route(
        path="bigquery?ws=!1m5!1m4!4m3!1s{project}!2s{dataset}!3s{table}",
        list_path="bigquery",
    ),
}


def list_datasets(context: Context, token: str) -> list[Resource]:
    """List datasets with their location (``US``, ``EU``, ``europe-west1``, ...) in lower case."""
    from gcw.api.client import list_all

    items = list_all(f"{API}/projects/{context.project}/datasets", token, "datasets")
    return [
        Resource(item["datasetReference"]["datasetId"], (item.get("location") or "").lower() or None)
        for item in items
    ]


def list_tables(context: Context, token: str) -> list[Resource]:
    """List tables of every dataset as ``DATASET.TABLE``.

    Raises:
        ApiError: The datasets could not be listed, or every dataset failed.
    """
    from gcw.api.client import list_all, run_parallel

    base = f"{API}/projects/{context.project}/datasets"
    datasets = [item["datasetReference"]["datasetId"] for item in list_all(base, token, "datasets")]
    results = run_parallel({
        dataset: (lambda dataset=dataset: list_all(f"{base}/{dataset}/tables", token, "tables"))
        for dataset in datasets
    })
    errors = [result for result in results.values() if isinstance(result, Exception)]
    if errors and len(errors) == len(results):
        raise errors[0]
    return [
        Resource(f"{dataset}.{item['tableReference']['tableId']}")
        for dataset, items in results.items()
        if not isinstance(items, Exception)
        for item in items
    ]
