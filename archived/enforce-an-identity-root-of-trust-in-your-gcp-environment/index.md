---
title: Enforcing an identity root of trust in your Google Cloud environment
description: Shows how to establish a root of trust of identities in your Google Cloud environment, so that no individual acting alone can log in as a super admin and change any setting.
author: awalko
tags: Security, IAM
date_published: 2020-08-17
---

Adrien Walkowiak | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This document shows how to establish a root of trust of your identities in your Google Cloud organization by controlling the
most powerful users of the Admin console, the *super admin* users. This helps to ensure that no single individual can log in
as a super admin and change any setting, intentionally or not, without the knowledge and participation of another trusted 
person.

To trust your Google Cloud environment, it is essential that you trust how you provisioned it in the first place. 
Establishing that root of trust in your organization can seem challenging, but it should not be. This document shows how you
can tightly control the most privileged access to your identity management console, which is an essential control that you
need to enforce in order to protect your Google Cloud organization itself.

Identities (Google Cloud users or groups) are separate from everything else in Google Cloud. You can manage identities in 
the Google Admin console (`admin.google.com`) and grant access to Google Cloud resources (for example, projects and Cloud
Storage buckets) in the Cloud Console (`console.cloud.google.com`), as long as you have the right level of access in each
console. To trust that your cloud environment is secure, you need to secure access to both consoles and make sure that you
are aware when any privileged access is used to make changes.

## Objectives

The result of completing the process in this document is having a
[Google Cloud organization](https://cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy#organizations) 
node in which your domain is controlled using
[Cloud Identity](https://support.google.com/cloudidentity/answer/7319251) in the [Admin console](https://admin.google.com).

This process includes the following objectives:

* You have an account for your primary domain name in the Admin console.
* Only *super admins* can manage your organization.
* Super admins have dedicated identities that require the use of a physical second-factor authenticator to log in. This 
  means that they will not use their day-to-day user as a super admin user, for security reasons. For example, they can use
  supadmin1@example.com for administrative tasks in the Admin console and john.doe@example.com for normal Google Cloud
  activities.
* Super admins' physical tokens are out of the reach of your designated super admin users. This ensures that in order to log
  in as a super admin user, your trusted users need to request access to a physical vault. This lets you trust that your
  identity setup is the way that you expect it to be at any time, because you can track who logged in to make changes, and
  insert your own process to determine why they logged in and what they changed.
* Your Google Cloud Organization node has been created.
* Super admin users have delegated their Google Cloud access to a special IAM admin group in Google Cloud. This enforces 
  separation of duty and makes it easier to manage Google Cloud permissions without the need to log in as a super admin 
  user.

## Concepts

Before getting into the specifics of establishing an identity root of trust for your cloud environment, it’s crucial to 
understand the different parties involved between your domain [Cloud Identity](https://cloud.google.com/identity) account 
and your Google Cloud organization.

The key principle to remember is that the Admin console is used to centrally manage identities in Google Cloud (user
identities and how they get authenticated) and that actual permissions are managed in Google Cloud with
[IAM policies](https://cloud.google.com/resource-manager/docs/access-control-org#using_predefined_roles).

![architecture diagram](https://storage.googleapis.com/gcp-community/tutorials/enforce-an-identity-root-of-trust-in-your-gcp-environment/image7.png)

In this diagram, the user@example.com authentication path is where Cloud Identity is used, while the access and 
authorization of Google Cloud resources is governed by Cloud IAM policies.

You can provision users and groups in the [Admin console](https://admin.google.com), which lets you manage settings and 
identities for Google Cloud products like Google Cloud Platform and G Suite. If your users only need access to Google Cloud
Platform, you can give them [Cloud Identity licences](https://support.google.com/cloudidentity/answer/7384684), which exist
in the Free and Premium tiers. There is a default limit of 50 free users for each Cloud Identity account. To raise this 
limit, contact Google Cloud support.

To manage your identities within the Admin console, you can designate
[super admin users](https://support.google.com/a/answer/2405986), which have full access to manage your Cloud Identity 
account. The super admin role is highly privileged and should be tightly controlled for security. This is why it is 
important to follow a root of trust ceremony to prove to your organization that no single individual can use these 
sensitive credentials without approval.

Super admin users can configure everything in their respective Cloud Identity domain and can grant the Organization 
Administrator Cloud IAM role to users in their respective Google Cloud organization. The Organization Administrator
Cloud IAM role allows users to grant IAM permissions to any identity at any level in your Google Cloud hierarchy.

It is a best practice to use this account to create your Google Cloud organization and delegate all Google Cloud 
administration to other identities, such as a dedicated Google Cloud admin group.

For details on securing these super admin credentials, see
[Security best practices for administrator accounts](https://support.google.com/a/answer/9011373).

The general pattern is to limit the usage and exposure of super admin credentials to a minimum number of trusted persons
within your organization and tightly control when and how they can use these credentials to modify your current setup.

Here are the constraints to keep in mind:

* A Google Cloud organization can only be created by a super admin user under the same domain name.
* Google Cloud users need to be logged in as users known to Google (for example, G Suite, Cloud Identity, or Google Account 
  user).
* You can add additional domains under the primary domain in your account. For details, see
  [Limitations with multiple domains](https://support.google.com/a/answer/182081).
* Users can only be created under one of the domain names tied to their account.
* User permissions are managed in Google Cloud directly, with Cloud IAM policies, not in the Admin console.
* Only users with the Organization Administrator Cloud IAM role can grant other users IAM permissions at all levels in 
  Google Cloud.

It is recommended to establish a provisioning ceremony (similar to encryption key signing) for super admin accounts. The
main reason is that these accounts have the ability to change any setting in your Admin console, which can affect
Google Cloud users and G Suite users (if any). A compromised or rogue super admin could potentially create other super admin
accounts and block or impersonate regular users to gain admin access to your Google Cloud organization.

Super admins will use physical second-factors keys (FIDO U2F Security Keys, such as
[Titan Security Keys](https://cloud.google.com/titan-security-key)) to log in. These keys, including spare keys, will be 
stored in one or more physical vaults. Each super admin activity is logged and retained in long-term immutable storage. 
Super admin users should have no purpose in Google Cloud other than designating the Organization Administrators. You can
[order Titan Security Keys online](https://store.google.com/product/titan_security_key).

Most organizations provision regular cloud users through automation, from their on-premises user directory. It is also a good
practice to integrate these regular cloud users with your existing SSO solution by configuring it in the Admin console 
security settings. Super admin users cannot authenticate through SSO, because Google needs to be able to authenticate them even 
if the SSO setup is broken temporarily.

## Summary of the process

This section contains a high-level summary of the necessary steps to create a new Google Cloud organization. Later sections
provide details about each of these steps.

### Admin console account setup

1.  Acquire administrative access to the domain name that will become the Google Cloud Organization.
1.  Create super admin email addresses for this domain to receive key communication from Google on your organization and
    reset access to the super admin users when necessary.
1.  Claim ownership of your domain by setting up your own domain in Cloud Identity and create the first super admin account 
    in Cloud Identity using a secure password.

### Secure super admin credentials

1.  Connect each dedicated physical token and its spare to this super admin account as a second factor for two-factor 
    authentication.
1.  Create the other two super admin accounts with separate passwords and second-factor pairs.
1.  (Optional) Set up the recovery options (phone and email) if allowed by your internal policy. Disable password reset for
    all super admin accounts.

### Set up your Google Cloud Organization

1.  Use a super admin user to log in to Google Cloud and create your Google Cloud Organization node.
1.  Delegate the Organization Administrator Cloud IAM role in IAM to the desired identity (for example, a trusted admin 
    group).
    
### Finish Admin Console account setup

1.  (Optional) Set up SSO in Cloud Identity.
1.  Export admin logs to a trusted SIEM (security information and event management) system.
1.  Secure all of the super admin accounts following the key ceremony logout procedure by locking the key into one or more
    vaults and logging out all super admin sessions from the trusted workstation.

## Complete prerequisite steps

Before you begin the process of setting up Cloud Identity, complete the following prerequisite steps.

### Define root ceremonies

Define root ceremonies for events like the following:

  * Initiate root of trust: create Cloud Identity for a domain
  * Super admin user creation
  * Super admin user login/logout
  * Cloud Identity update
  * Super admin user account rotation or retirement

### Identify trusted privileged users for the bootstrapping process

  * **Cloud Identity super admin**: A designated trusted person to be initiated as the Cloud Identity super administrator.
    Keep in mind that super admin users can update your G Suite configuration, if you have one.
  * **Google Cloud Organization administrator**: A designated trusted person or group to be initiated as the Organization
    Administrator role in Google Cloud.
  * **Trusted witnesses**: A list of trusted witnesses with the ability to randomly select one or more witnesses out of the
    list for a specific process, such as Titan key rotation, vault opening, and super admin life events (for example, super 
    admin creation, login, super admin rotation).

### Acquire domain and verify ability to create DNS records

1.  Acquire administrative access to the domain name that will become the Google Cloud Organization. You can either purchase
    a new domain name or use an existing domain name or subdomain. Be sure to use a trusted DNS provider.
2.  Ensure that the domain name administrator is available to create DNS TXT records for the selected domain. To set up your
    Cloud Identity account for your domain, you need the ability to prove that you own the domain.

This document uses `cloudflyer.info` as the example domain name.

### Create email addresses for the initial super admin user

You need a new valid email address from your domain, created especially for each super admin in Cloud Identity. This
requires that the domain name has been properly configured to handle email, with MX records pointing to valid mail servers.

These email addresses will receive key communication from Google about your organization, and you can also use these email
addresses to [reset access](https://support.google.com/cloudidentity/answer/33561) to the super admin users when necessary. 

The super admin email addresses need to be separate dedicated accounts, not to be used for day-to-day activities.

This document uses the following as the example super admin email addresses:

  * `super-admin-1@cloudflyer.info`
  * `super-admin-2@cloudflyer.info`
  * `super-admin-3@cloudflyer.info`

### Make hardware and supporting software available

* **Second-factor authenticator keys**: Make at least two new and unused dedicated
  [2FA Titan Security Keys](https://cloud.google.com/titan-security-key/) per super admin ready to be associated to the 
  super admin accounts.
* **Physical vault**: Prepare one or more physical vaults to store the hardware 2FA keys. The designated super admin users 
  should *not* have access to the vaults without permission.
* **Password vault**: Prepare a trusted password retention system or tool to store the super admin password.
* **Trusted workstation**: Prepare a trusted physical machine with internet connectivity capable of running a Chrome browser
  and accepting a USB key. This workstation should be highly secured according to your own internal standards. Generally, 
  this workstation is not used for day-to-day activity and is locked down to only allow access to the Admin console and 
  Google Cloud. For additional security, you can also control which internal users can log in to the machine.

## Set up Cloud Identity

In this section, you create your first super admin user in Cloud Identity and claim ownership of your domain in the Admin
console. After this is done, you create the additional super admin users and (optionally) set up your SSO connection to allow 
future regular users to connect to your Google Cloud Organization in an integrated fashion.

This entire section should be conducted as a ceremony on its own, because in it you create all super admin accounts and set 
up your Google Cloud Organization for the first time.

At the end of this process, all keys should be clearly identified (with stickers, separate envelopes, or both) and placed in
one or more vaults. Witnesses should be present during the entire event.

The root of trust for your Google Cloud Organization starts here.

1.  Go to [Cloud Identity Free tier setup](https://gsuite.google.com/signup/gcpidentity/welcome) and fill out the form to get started.
    This is mainly gathering high-level information about your business and first super admin user. You will also need to agree to
    the [Cloud Identity agreement](https://admin.google.com/terms/cloud_identity/1/2/en/na_terms.html) to continue.

1.  Create the first super admin account in Cloud Identity using a secure password.

1.  Set up your Cloud Identity account for this domain. Sign in as the super admin user you just created. At this point, no two-factor
    authentication is used yet, so you will be asked to provide a phone number for this super admin user. Use the security code received
    by SMS to log in.

    ![Set up Cloud Identity](https://storage.googleapis.com/gcp-community/tutorials/enforce-an-identity-root-of-trust-in-your-gcp-environment/image2.png)

1.  If you agree, accept the [Google Terms of Service](https://accounts.google.com/TOS) and the [Google Privacy Policy](https://www.google.com/policies/privacy/)
    to continue.

1.  To verify ownership of your domain, click **Start** and add the DNS record in your public DNS zone for this domain. Wait until the verification
    happens, which may take several minutes.

    ![Verify domain ownership](https://storage.googleapis.com/gcp-community/tutorials/enforce-an-identity-root-of-trust-in-your-gcp-environment/image6.png)

    Here is an example of this verification record in the cloudflyer.info DNS zone:

    ![Custom resource records](https://storage.googleapis.com/gcp-community/tutorials/enforce-an-identity-root-of-trust-in-your-gcp-environment/image9.png)

1.  After your domain is verified, log in to the [Cloud Identity Admin console](http://admin.google.com).

    ![Admin console](https://storage.googleapis.com/gcp-community/tutorials/enforce-an-identity-root-of-trust-in-your-gcp-environment/image4.png)

1.  Create the other two super admin accounts with separate passwords and second-factor pairs.

1.  Start the creation of the other super admin users for this role and [associate the right second factor](https://support.google.com/accounts/answer/185839)
    to each account specifically.

1.  Tie each dedicated physical token and its spare to this super admin account as a second factor for two-factor 
    authentication.
    
    Titan Security Keys are the [recommended](https://support.google.com/accounts/answer/6103523) way of 
    implementing your second factor for Google accounts. Any FIDO U2F-capable key should work as a second factor.

1.  Verify that access for each super admin account access is working with their own password and second-factor authenticators: Log in and 
    out with both keys (main and spare) for each account.
    
1.  Configure all of the other security settings according to your own security requirements.

1.  (Optional) Set up the recovery options (phone and email) if allowed by your internal policy.

    Assuming that the super admin account was created under a trust ceremony, to protect that trust, you should disable password reset for all super
    admin accounts. Follow [this process](https://support.google.com/a/answer/33561) to reset super admin credentials when no recovery options are available.

1.  Log out all super admins and store the labeled second-factor devices in one or more vaults.

1.  (Optional) For the main Google Cloud Organization, follow
    [these steps to enable SSO](https://cloud.google.com/solutions/federating-gcp-with-active-directory-configuring-single-sign-on) in Cloud Identity and
    [Set up SSO in Cloud Identity](https://support.google.com/cloudidentity/answer/6349809).

1.  (Optional) Set up a directory sync with your existing user directory (for example, LDAP or AD) for the right users and 
    groups to be provisioned automatically to your Cloud Identity account. This usually requires “bot” privileged users to 
    allow for the synchronization. Google recommends using [Google Cloud Directory Sync](https://support.google.com/a/topic/2679497)
    for this. 

    To learn more about synchronizing identities for Google Cloud, see
    [Using your existing identity management system with Google Cloud Platform](https://cloud.google.com/blog/products/identity-security/using-your-existing-identity-management-system-with-google-cloud-platform).

## Set up your Google Cloud Organization

In this section, you create your Google Cloud Organization node, define your Organization Admin groups, and set up log 
exports and alerting on super admin events.

You must be a super admin to execute this step. Follow your ceremony to log in as a super admin if not already logged in.

1.  Go to the [Cloud Console](https://console.cloud.google.com/).

    You should see a screen like this:

    ![terms of service](https://storage.googleapis.com/gcp-community/tutorials/enforce-an-identity-root-of-trust-in-your-gcp-environment/image1.png)

    After you agree to the terms and conditions, the Google Cloud organization is created.

    ![project selector](https://storage.googleapis.com/gcp-community/tutorials/enforce-an-identity-root-of-trust-in-your-gcp-environment/image3.png)

1.  Verify that your super admin users have the
    [Organization Administrator](https://console.cloud.google.com/iam-admin/roles/details/roles%3Cresourcemanager.organizationAdmin)
    role in the IAM section:

    ![permissions](https://storage.googleapis.com/gcp-community/tutorials/enforce-an-identity-root-of-trust-in-your-gcp-environment/image5.png)

1.  Delegate the Organization Administrator Cloud IAM role in IAM to the desired identity (for example, a trusted admin group).

    This role is also sensitive on the Google Cloud side. It should not be used as an account for day-to-day activity.
    
1.  Delegate the Google Cloud administration to a group of trusted individuals, to avoid needing to use the
    super admin users for day-to-day operations.
    
    You need to provision identities for these users (like a dedicated group in Cloud Identity) prior to assigning them the Google Cloud Organization
    Administrator role in the Cloud Console:

    ![IAM](https://storage.googleapis.com/gcp-community/tutorials/enforce-an-identity-root-of-trust-in-your-gcp-environment/image10.png)

Before completing this root of trust ceremony, we recommend that you
[export your Admin console logs](https://support.google.com/a/answer/4579579) to a trusted SIEM (security information and event management) system. You can
do this with solutions like [Splunk](https://splunkbase.splunk.com/app/3791/#/details), or through automation with tools like the
[CFT G Suite exporter](https://github.com/terraform-google-modules/terraform-google-gsuite-export) module in Google Cloud.
If no existing solution is satisfying, you can export admin logs using custom code and the [G Suite SDK](https://developers.google.com/admin-sdk).

Secure all of the super admin accounts following the key ceremony logout procedure by locking the keys into one or more
vaults and logging out all super admin sessions from the trusted workstation.

## Managing multiple Google Cloud organizations

You can allow users from one domain to access other Google Cloud organizations using Cloud IAM policies. You don’t need to
provision separate identities for all of the Google Cloud organizations you own, unless you want to force your users to log
in using different identities each time they access a Google Cloud organization.

The only roles that can't be granted across organizations are the
[primitive roles](https://cloud.google.com/iam/docs/understanding-roles#role_types) (Owner, Editor, and Viewer), which are 
not recommended for production use.

You can restrict which domains are allowed in your Google Cloud Organization using the `iam.allowedPolicyMemberDomains`
[organization policy constraint](https://cloud.google.com/resource-manager/docs/organization-policy/org-policy-constraints) after the
organization is created.

## Conclusion

You should now be in a good shape to trust your initial setup on both Cloud Identity and Google Cloud. What you accomplished
by following a root of trust ceremony for your Cloud Identity account is ensuring that no single user in your organization
can log in as a super admin on their own and change your setup in either Cloud Identity or Google Cloud. The main security 
mechanism to achieve this is to physically hold on to the second factors that are used to log in as a super admin.

At this point, your users should rarely need to log in as super admin users, except—for example—when they need to modify 
sensitive settings in the Admin console. Any time you need someone to log in as a super admin, you should follow your
super admin login ceremony so that you keep trusting your setup in both Google Cloud and Cloud Identity.

We recommend that you [turn on alerts](https://support.google.com/a/answer/9288157) on super admin events in the Admin
console to double-check that no changes happen outside of your controlled ceremonies.

## What's next

* [Enterprise onboarding checklist](https://cloud.google.com/docs/enterprise/onboarding-checklist)
* [Security best practices for you administrator accounts](https://support.google.com/cloudidentity/answer/9011373)
* [Sign in to the Admin console](https://support.google.com/cloudidentity/answer/182076)
* [Set session length in Cloud Identity](https://support.google.com/cloudidentity/answer/7576830)
* [Enabling SSO in Cloud Identity](https://cloud.google.com/solutions/federating-gcp-with-active-directory-configuring-single-sign-on)
* [GCDS best practices](https://support.google.com/a/answer/7177267)
