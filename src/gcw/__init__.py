"""gcw ("gcloud web"): open Google Cloud console pages from the terminal.

Package layout; dependencies point downwards only (``cli`` -> ``services`` ->
``api`` / ``cache`` / ``context`` / ``web``):

    cli       user-facing entry point: argument parsing, TAB completion, shell integration
    services  one module per GCP service: console routes and resource listing
    context   active account, project and region resolved from the gcloud configuration
    cache     local resource cache that powers completion
    api       access tokens and a minimal REST client for Google APIs
    web       console URL building and opening the browser
"""
