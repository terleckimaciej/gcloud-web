# 0008. Data through each service's REST `list`, Cloud Asset Inventory deferred

- Status: Accepted
- Date: 2026-10-11

## Context

Cloud Asset Inventory (`searchAllResources`) returns all resources of a project in one request. It requires enabling the API in the project and the `cloudasset.viewer` role, which in a corporate environment means bureaucracy. g9s also rejected it because of its generic data shape.

## Decision

The MVP fetches data through each service's `list` endpoints (REST over `urllib`, in parallel threads). This needs only the permissions the user already has if they can see the resources in the console. Where an API aggregates across locations (`locations/-`), we use that.

## Consequences

Works everywhere without extra permissions. The cost is about 10 requests per project instead of one, but in the background, so it makes no difference to the user. Cloud Asset Inventory comes back in stage 2 as an optional speed-up with autodetection.
