# Access Control Policy

> FICTIONAL SAMPLE. Quarterhour, Inc. is a made-up 12-person scheduling SaaS company used to demonstrate this kit. Any resemblance to a real company is coincidental.

- Document ID: QH-POL-02
- Version: 1.3
- Owner: Dana Whitfield, CTO
- Approved by: Maya Okafor, CEO
- Last reviewed: 2 March 2026
- Review cycle: at least annually

## 1. Purpose

This policy sets the rules for granting, using, reviewing and removing access to Quarterhour systems and customer data.

## 2. Scope

It applies to all employees and contractors, and to every system that stores or processes Quarterhour or customer data, including AWS, GitHub, Google Workspace, Stripe and the Quarterhour admin console.

## 3. Principles

- Access is granted on a least-privilege basis: people get only the access their role needs.
- Access is role-based. Standard roles are defined for Engineering, Support, Sales and Administration.
- Every person has an individual, named account. Shared or generic accounts are not allowed, except the break-glass account described in section 5.3.

## 4. Authentication

### 4.1 Single sign-on

Google Workspace is the company identity provider. Internal applications that support single sign-on must use it. A few tools that do not support single sign-on use separate accounts protected as described in 4.2 and 4.3.

### 4.2 Multi-factor authentication

Multi-factor authentication (MFA) is required for all workforce accounts on Google Workspace, AWS, GitHub and Stripe, and on any other system that supports it. Administrators must use a hardware security key or an authenticator app. SMS codes are not allowed for administrator accounts.

### 4.3 Passwords

Passwords must be at least 14 characters long, unique to each system and stored in the company password manager. Passwords are never shared by email or chat.

## 5. Privileged access

### 5.1 Production administrators

Administrator access to the production AWS account is limited to the CTO and two named senior engineers. The current list is kept in the access register.

### 5.2 Access to customer data

Support staff view customer accounts through the Quarterhour admin console, which limits what each role can see. Direct access to the production database is limited to on-call engineers, goes through AWS Systems Manager Session Manager, and is logged in AWS CloudTrail.

### 5.3 Root and break-glass accounts

The AWS root user is protected with a hardware security key, has no access keys and is used only for tasks that require it. A break-glass administrator account exists for emergencies. Its credentials are sealed in the password manager, and every use is logged and reviewed by the CTO.

## 6. Joiners, movers and leavers

- New access is requested through a ticket and approved by the person's manager before it is granted.
- When someone changes role, access they no longer need is removed within 5 business days.
- When someone leaves, all access is revoked within 24 hours of their last working day, or on the same day for involuntary departures. Company devices are returned and wiped.

## 7. Access reviews

The CTO reviews user access to AWS, GitHub, Google Workspace and production database roles every quarter. The results and any changes are recorded in the access register.

## 8. Remote access

Quarterhour does not operate a corporate office network or VPN. Production servers are not reachable over SSH from the internet. Engineers connect through AWS Systems Manager Session Manager using their individual, MFA-protected identities.

## 9. Policy review

This policy is reviewed at least annually and after any significant change to systems or the organisation.
