# Near Real-Time Data Analytics Pipeline (AWS Serverless)

This repository contains an AWS-based serverless architecture for processing near real-time event data. The system ingests application events, validates and secures requests with JWT-based authentication, and stores data in an optimized format for cost-effective analytics.

> **Note:** This repository is not intended as a deployment guide. It serves as a reference architecture and code example for secure and scalable data pipelines in the cloud.  

---

## Architecture Overview

The ingestion and processing pipeline follows this path:

API Gateway -> SQS -> Kinesis Firehose -> S3 -> Athena

- **Event submission**  
  Events are sent to the `/events` API Gateway resource, protected by a **custom Lambda authorizer** (`lambda/jwt-authorizer/lambda_function.py`).  

- **Authentication**  
  Clients must present a **JWT Bearer token**, issued by the `/token` resource (`lambda/events-jwt-issuer/lambda_function.py`). Tokens are:
  - Signed symmetrically (HS256)  
  - Valid for 20 minutes  
  - Issued only if client credentials (ID + secret + audience) are valid  

- **Decoupling & batching**  
  Validated events are transformed via VTL mapping and placed into an **Amazon SQS queue**, enabling **decoupling** between ingestion and processing.  

- **Stream delivery**  
  An SQS-triggered Lambda batches events and pushes them to **Amazon Kinesis Firehose**. Firehose converts the data into **Parquet** with Snappy compression and writes to S3 in time-partitioned folders.  

- **Analytics**  
  Data stored in S3 (partitioned by date and hour) is queried using **Amazon Athena**, powered by schemas defined in the **Glue Data Catalog**.  

---

## Security Considerations

This project emphasizes **security by design** across both application and cloud layers:

### Application Security
- **JWT-based authentication** ensures only trusted clients can push data.  
- Tokens are short-lived (20 minutes), reducing replay attack windows.  
- All requests are rate-limited and throttled at the API Gateway level.  
- Input events must conform to strict JSON schemas (see `examples/schemas/glue-data-catalog-json-schema.json`).  

### Cloud Security
- **Least privilege IAM roles/policies** limit Lambda and service access.  
- **Secrets Manager** securely stores client secrets, rotated every 30 days by a custom Lambda (`lambda/shared-secret-rotate/lambda_function.py`).  
- **CloudWatch logging** in JSON format enables structured monitoring without exposing sensitive data.  
- **Dashboards & alarms** track metrics such as failed authorizations, rejected requests, and throughput.  
- **Serverless design** eliminates server patching overhead and leverages AWS-managed scalability and availability.  

---

## Implementation Notes

- **SQS for decoupling**: Protects downstream services from burst traffic and enables fault tolerance.  
- **Firehose Parquet conversion**: Reduces storage costs and speeds up Athena queries.  
- **Partitioned S3 storage**: Organizes data by date/hour for efficient queries.  
- **S3 Lifecycle rules**: Moves infrequently accessed data between storage tiers to save costs.
- **Cloud-native observability**: Metrics, logs, and alarms in CloudWatch provide real-time insights into system health and security.  
- **Scalability & HA**: Fully serverless, automatically scales with traffic, and avoids single points of failure.  

---

## Examples

The `examples/` directory contains reference materials and scripts that demonstrate how the pipeline works end-to-end:

- **`send_event_scripts/`**  
  Provides scripts for simulating event submission through the full pipeline. These scripts handle:
  - Requesting a JWT token from the `/token` endpoint  
  - Using the token to send events to the `/events` endpoint  
  - Ensuring event data conforms to the expected schema  

- **`athena_queries/`**  
  Includes sample SQL queries designed for **Amazon Athena**, showing how data stored in S3 (in Parquet format and partitioned by time) can be queried efficiently.  

- **`schemas/`**  
  Contains JSON schema definitions (such as `glue-data-catalog-json-schema.json`) used for validating event data and registering schema information in the **AWS Glue Data Catalog**.  

These examples serve as practical references for testing the pipeline, verifying schema compliance, and exploring how data can be analyzed once ingested. They are not intended as production-ready code, but as demonstrations of how different components interact securely and efficiently.  


## AWS Services Used

- **Lambda functions** (custom authorizer, JWT issuer, SQS processor, secret rotation)  
- **Lambda layers**  
- **Amazon S3** (partitioned data lake storage with lifecycle rules)  
- **Amazon API Gateway** (request entrypoint, auth, rate limiting)  
- **API Gateway custom authorizers**  
- **Amazon SQS** (queue-based decoupling)  
- **Amazon Kinesis Data Firehose** (streaming transform + delivery to S3)  
- **AWS Glue Data Catalog** (schemas for Athena)  
- **Amazon Athena** (serverless SQL queries over S3 data)  
- **AWS Secrets Manager** (client_secret storage + rotation)  
- **IAM Roles/Policies** (least privilege execution)  
- **Amazon CloudWatch** (logs, dashboards, alarms)  

---

## Summary

This project demonstrates a **secure, serverless, and scalable analytics pipeline** for ingesting, validating, and analyzing event data. With strong security controls (JWT auth, secrets rotation, IAM least privilege) and cloud-native design (SQS buffering, Firehose transformation, Athena queries), the system provides a blueprint for building resilient data pipelines in AWS.  


