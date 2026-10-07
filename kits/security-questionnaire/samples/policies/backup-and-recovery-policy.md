# Backup and Recovery Policy

> FICTIONAL SAMPLE. Quarterhour, Inc. is a made-up company used to demonstrate this kit.

- Document ID: QH-POL-07
- Version: 1.2
- Owner: Dana Whitfield, CTO
- Approved by: Maya Okafor, CEO
- Last reviewed: 3 June 2026
- Review cycle: at least annually

## 1. Purpose

To make sure customer data can be restored after accidental deletion, corruption, or the loss of a hosting region.

## 2. Scope

This policy covers the production PostgreSQL database (Amazon RDS) and customer file uploads stored in Amazon S3. Production runs in the AWS us-east-1 region (United States).

## 3. Backup frequency

- Amazon RDS takes an automated snapshot of the production database every day and keeps transaction logs for point-in-time recovery. The database can be restored to any point within the retention period, normally to within 5 minutes.
- Versioning is turned on for the S3 buckets that hold customer files.

## 4. Retention

- Automated database backups are kept for 35 days.
- One snapshot a month is kept for 12 months.
- Previous versions of S3 objects are kept for 35 days.

## 5. Backup location

Backups are copied to the AWS us-west-2 region (United States), into a separate AWS account that is used only for backups.

## 6. Encryption

All backups and snapshots are encrypted with AES-256 using AWS Key Management Service (KMS) keys.

## 7. Access to backups

Only the CTO and one named senior engineer can restore or delete backups. The backup account blocks deletion of snapshots before the end of their retention period.

## 8. Restore testing

Every quarter, engineering restores the production database from backup into an isolated test environment, checks that the data is complete, and records the result and the time taken. The restored copy is deleted after the test.
