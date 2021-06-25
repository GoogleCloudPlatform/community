---
title: Google Cloud Directory Sync examples
description: Learn from four use cases for synchronizing Active Directory users to Cloud Identity using Google Cloud Directory Sync.
author: akaashr
tags: gcds, activedirectory
date_published: 2021-06-21
---

Akaash Rampersad | Customer Engineer, Infrastructure Modernization | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This document describes four scenarios in which you can use Google Cloud Directory Sync (GCDS) to synchronize user and group identities from an Active Directory
domain.

In these scenarios, you manipulate LDAP queries with GCDS to broaden or narrow the scope of a user or group search. Each organization’s requirements for
synchronizing identities from on-premises to Google Cloud are different, which is why the customizability of GCDS is a powerful tool for administrators and
security engineers, to help ensure that the right users and groups are synchronized to the cloud.

To follow the instructions in this document, you need to have installed and configured
[Google Cloud Directory Sync](https://support.google.com/a/answer/106368) and have
[federated](https://cloud.google.com/architecture/identity/federating-gcp-with-active-directory-synchronizing-user-accounts) Google Cloud with Active Directory.

## Costs

You can use [Google Cloud Directory Sync](https://support.google.com/a/answer/106368) and
[Google Cloud Identity Free](https://cloud.google.com/identity/docs/editions) at no charge.

## Overview of the demonstration environment

This document uses a fictitious organization, GCDSDemo Company, to demonstrate the configuration of Google Cloud Directory Sync.

In these examples, the GCDSDemo Company is in the process of migrating to Google Cloud. The first step of their migration is synchronizing their existing
identities from Active Directory so that they can log in using the same credentials.

### Example Active Directory configuration
 
Consider the example domain (`gcdsdemo.joonix.net`) for the GCDSDemo Company. There are two top-level organizational units (OUs) that
contain user objects that need to be synchronized: `Corp` and `GCP`.

![ADUC OUs screenshot](https://storage.googleapis.com/gcp-community/tutorials/gcds-use-cases-common-and-complex/01-AD-OUs.png)

In the `Corp` organizational unit, the nested organizational units (sub-OUs) `IT` and `R&D` contain the user objects that must be synchronized.

![ADUC IT users screenshot](https://storage.googleapis.com/gcp-community/tutorials/gcds-use-cases-common-and-complex/02-AD-IT-Users.png)

![ADUC R&D users screenshot](https://storage.googleapis.com/gcp-community/tutorials/gcds-use-cases-common-and-complex/03-AD-RD-Users.png)

In this scenario, the IT administrators of `gcdsdemo.joonix.net` made a design decision to put the security groups for Google Cloud in a separate organizational
unit to ensure that those groups don’t inadvertently get assigned to resources within their on-premises environment.

![ADUC Google Cloud groups screenshot](https://storage.googleapis.com/gcp-community/tutorials/gcds-use-cases-common-and-complex/04-AD-GCP-Groups.png)

### Google Cloud Directory Sync configuration

The
[GCDS installation and configuration guide](https://cloud.google.com/architecture/identity/federating-gcp-with-active-directory-synchronizing-user-accounts#connecting_to_active_directory) recommends leaving the **Base DN** field blank. For most organizations, this works well. However, there are two main
considerations with this approach:

- The time that a query takes to run increases with the number of objects in the subtree.

- The default search for user objects and group objects returns _all_ matching entries, which can cause unintended users or groups to synchronize
  with Google Cloud Identity. 

For example, consider that the security groups are not mail-enabled, so they can only be identified by their `userPrincipalName` attribute. If the default LDAP 
query is executed, then _all_ security groups—including those that are out of scope—are returned as matching:

![GCDS default search screenshot](https://storage.googleapis.com/gcp-community/tutorials/gcds-use-cases-common-and-complex/05-GCDS-Default-Search.png)

You can usually mitigate this behavior by manually assigning an email address to the security groups (even if they are not mail-enabled) and switching the query
to use the `mail` attribute. Alternatively, as shown in the next section, you can make the **Base DN** value more specific.

## Scenario #1: User accounts and groups are not in the same organizational unit

In this scenario, the user objects and group objects are located in different organizational units, which is typical in most on-premises environments. The users
are in the `Corp` > `IT` > `Users` and `Corp` > `R&D` > `Users` sub-OUs, and all users in these sub-OUs will be synchronized to Google Cloud.

This scenario also demonstrates configuring the **Base DN** value in the search rules to make the search scope smaller, which helps to prevent unintended users
and groups from being synchronized.

### User accounts lookup

When user objects are in multiple sub-OUs, the best practice is to set the **Base DN** value for your LDAP query to be the parent organizational unit that the 
sub-OUs have in common and uplevel hierarchically relative to the user objects’ OU.

In this case, because `IT` and `R&D` are child OUs of `Corp`, the **Base DN** value for the LDAP query should be the following:

    OU=Corp,DC=gcdsdemo,DC=joonix,DC=net

This LDAP query gives the following list of users:

![GCDS users BaseDN screenshot](https://storage.googleapis.com/gcp-community/tutorials/gcds-use-cases-common-and-complex/06-GCDS-Users-BaseDN.png)

### Group lookup

The group search LDAP query follows the same structure as the user search LDAP query. Set the **Base DN** value to the OU that is common, and uplevel
hierarchically relative to the group objects’ OU, which in this case is `GCP` > `Groups`.

The **Base DN** value for the LDAP query should be the following:

    OU=Groups,OU=GCP,DC=gcdsdemo,DC=joonix,DC=net

This LDAP query gives the following list of groups:

![GCDS groups Base DN screenshot](https://storage.googleapis.com/gcp-community/tutorials/gcds-use-cases-common-and-complex/07-GCDS-Groups-BaseDN.png)

The built-in security groups like `grouppolicycreatorowners@gcdsdemo.joonix.net` and `domaincontrollers@gcdsdemo.joonix.net` are not returned, which is the
desired behavior.

## Scenario #2: Selectively synchronizing user accounts based on group membership

In this scenario, you tune the LDAP query to further narrow the scope for synchronizing to ensure that only the appropriate user objects and group objects are 
selected.
 
In contrast with the previous scenario, some organizations may not want to have all users in an organizational unit synchronized to Google Cloud. Instead, the
organization may want to selectively synchronize users that are part of specific groups.

In this scenario, only user accounts that are members of `GCP` > `Groups` (such as users in `GCP-OrgAdmins` or `GCP-InfraAdmins`) are synchronized to Google
Cloud. The security groups are relatively static, and new groups will be added on a case-by-case basis.

### User accounts lookup

Selectively synchronizing user accounts based on group membership requires a couple of changes from the solution in the previous scenario:

- Modifying the LDAP query to include the `memberOf` LDAP filter
- Creating a user search rule for each group that contains user accounts to synchronize

To modify the LDAP query to include the `memberOf` filter, you first get a list of all of the distinguished names (DN) of the in-scope groups:

    Get-ADGroup -Filter {name -like "GCP*"} | Format-Table Name, DistinguishedName -Auto

The output looks similar to this:

    Name               DistinguishedName
    ----               -----------------
    GCP-AllUsers       CN=GCP-AllUsers,OU=Corp,DC=gcdsdemo,DC=joonix,DC=net
    GCP-Developers     CN=GCP-Developers,OU=Groups,OU=GCP,DC=gcdsdemo,DC=joonix,DC=net
    GCP-InfraAdmins    CN=GCP-InfraAdmins,OU=Groups,OU=GCP,DC=gcdsdemo,DC=joonix,DC=net
    GCP-NetworkAdmins  CN=GCP-NetworkAdmins,OU=Groups,OU=GCP,DC=gcdsdemo,DC=joonix,DC=net
    GCP-OrgAdmins      CN=GCP-OrgAdmins,OU=Groups,OU=GCP,DC=gcdsdemo,DC=joonix,DC=net
    GCP-ProductionTeam CN=GCP-ProductionTeam,OU=Groups,OU=GCP,DC=gcdsdemo,DC=joonix,DC=net

Using these DNs, modify the LDAP query as follows:

    (&(memberof=DN_OF_SECURITY_GROUP)(objectCategory=person)(objectClass=user)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))

Example using the `GCP-OrgAdmins` security group:

    (&(memberof=CN=GCP-OrgAdmins,OU=Groups,OU=GCP,DC=gcdsdemo,DC=joonix,DC=net)(objectCategory=person)(objectClass=user)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))

To validate that the filter is configured correctly, either create a new user search rule or update the existing one to include the new LDAP query syntax, and
then click the ***Test LDAP Query*** button.

Here are the results of the query:

![GCDS users memberOf screenshot](https://storage.googleapis.com/gcp-community/tutorials/gcds-use-cases-common-and-complex/08-GCDS-Users-memberOf.png)

Verify the members of the `GCP-OrgAdmins` group to ensure the validity of the query:

    Get-ADGroupMember -Identity "GCP-OrgAdmins" | Get-ADUser -Properties * | Format-Table Name,UserPrincipalName,Mail -Auto

The output looks similar to this:

    Name                UserPrincipalName                       Mail
    ----                -----------------                       ----
    Mary Jackson        Mary.Jackson@gcdsdemo.joonix.net        Mary.Jackson@gcdsdemo.joonix.net
    Srinivasa Ramanujan Srinivasa.Ramanujan@gcdsdemo.joonix.net Srinivasa.Ramanujan@gcdsdemo.joonix.net
    Bill Nye            Bill.Nye@gcdsdemo.joonix.net            Bill.Nye@gcdsdemo.joonix.net
    Isaac Newton        Isaac.Newton@gcdsdemo.joonix.net        Isaac.Newton@gcdsdemo.joonix.net

This output shows that the LDAP Query worked, and only the users that are part of the `GCP-OrgAdmins` group are in scope to synchronize.

The next step is to create a user search rule for the remaining groups to ensure that all of the users are synchronized.

![GCDS users search rule memberOf screenshot](https://storage.googleapis.com/gcp-community/tutorials/gcds-use-cases-common-and-complex/09-GCDS-Users-SearchRule-memberOf.png)

Notice that the **Base DN** value is still configured to be `OU=Corp,DC=gcdsdemo,DC=joonix,DC=net`, but the LDAP query is still able to return the correct list 
of users because the distinguished name of the security group is used in the query, which overrides the **Base DN** scope.

### Summary

Using the `memberOf` LDAP filter is a great way to narrow the scope of user identities to synchronize, and it ensures that only the explicitly defined user
accounts exist in Google Cloud. However, this approach does require the extra work of creating user search rules for every group. As new groups are added, you
need to add new user search rules, which can become tedious to manage.

The next scenario demonstrates a strategy to minimize the number of user and group search rules.

## Scenario #3: Reducing the number of user search rules

This scenario demonstrates how to configure GCDS to automatically detect new groups and synchronize the users that are part of those groups.

In this scenario, only user accounts that are members of a group that is prefixed with `GCP` (such as `GCP-OrgAdmins` or `GCP-InfraAdmins`) will be synchronized 
to Google Cloud.

### Create a group for all users

In the previous scenario, you modified the LDAP query to use the `memberOf` LDAP filter and had to create a new user search rule for each group. This is because
the `memberOf` filter does not accept wildcards (`*`) as input. 

To work around this, you first create a new security group that will be common to every user that will exist in Google Cloud. This group does not need to have
any IAM bindings or be used for anything other than identifying the user accounts to synchronize. This is similar to the `Domain Users` built-in security group
in Active Directory.

For this example, you create a security group called `GCP-AllUsers`.

    New-ADGroup -Name "GCP-AllUsers" -Path "OU=Groups,OU=GCP,DC=gcdsdemo,DC=joonix,DC=net" -Description "[NO IAM] All Users being synced to Google Cloud" -GroupScope "Global"

Next, you populate the group with the user accounts that are already members of the other `GCP` groups:

    Get-ADGroup -Filter {name -like "GCP*"} | Get-ADGroupMember | Add-ADPrincipalGroupMembership -MemberOf "GCP-AllUsers"

Verify the members of the group:

    Get-ADGroupMember -Identity "GCP-AllUsers" | Format-Table Name,DistinguishedName -Auto

The output looks similar to this:

    Name                     DistinguishedName
    ----                     -----------------
    Dorothy Vaughan          CN=Dorothy Vaughan,OU=Users,OU=IT,OU=Corp,DC=gcdsdemo,DC=joonix,DC=net
    Mary Jackson             CN=Mary Jackson,OU=Users,OU=IT,OU=Corp,DC=gcdsdemo,DC=joonix,DC=net
    Srinivasa Ramanujan      CN=Srinivasa Ramanujan,OU=Users,OU=IT,OU=Corp,DC=gcdsdemo,DC=joonix,DC=net
    Leonardo Pisano Bigollo  CN=Leonardo Pisano Bigollo,OU=Users,OU=IT,OU=Corp,DC=gcdsdemo,DC=joonix,DC=net
    Bill Nye                 CN=Bill Nye,OU=Users,OU=IT,OU=Corp,DC=gcdsdemo,DC=joonix,DC=net
    Isaac Newton             CN=Isaac Newton,OU=Users,OU=IT,OU=Corp,DC=gcdsdemo,DC=joonix,DC=net
    Florence Nightingale     CN=Florence Nightingale,OU=Users,OU=IT,OU=Corp,DC=gcdsdemo,DC=joonix,DC=net
    Louis Pasteur            CN=Louis Pasteur,OU=Users,OU=IT,OU=Corp,DC=gcdsdemo,DC=joonix,DC=net
    Chen-Ning Yang           CN=Chen-Ning Yang,OU=Users,OU=IT,OU=Corp,DC=gcdsdemo,DC=joonix,DC=net
    Susumu Tonegawa          CN=Susumu Tonegawa,OU=Users,OU=IT,OU=Corp,DC=gcdsdemo,DC=joonix,DC=net
    Albert Einstein          CN=Albert Einstein,OU=Users,OU=R&D,OU=Corp,DC=gcdsdemo,DC=joonix,DC=net
    Marie Curie              CN=Marie Curie,OU=Users,OU=R&D,OU=Corp,DC=gcdsdemo,DC=joonix,DC=net
    Neil deGrasse Tyson      CN=Neil deGrasse Tyson,OU=Users,OU=R&D,OU=Corp,DC=gcdsdemo,DC=joonix,DC=net
    George Washington Carver CN=George Washington Carver,OU=Users,OU=R&D,OU=Corp,DC=gcdsdemo,DC=joonix,DC=net
    Charles Darwin           CN=Charles Darwin,OU=Users,OU=R&D,OU=Corp,DC=gcdsdemo,DC=joonix,DC=net
    Nikola Tesla             CN=Nikola Tesla,OU=Users,OU=R&D,OU=Corp,DC=gcdsdemo,DC=joonix,DC=net
    Stephen Hawking          CN=Stephen Hawking,OU=Users,OU=R&D,OU=Corp,DC=gcdsdemo,DC=joonix,DC=net
    Grace Hopper             CN=Grace Hopper,OU=Users,OU=R&D,OU=Corp,DC=gcdsdemo,DC=joonix,DC=net
    Mae Jemison              CN=Mae Jemison,OU=Users,OU=R&D,OU=Corp,DC=gcdsdemo,DC=joonix,DC=net

### User account lookup

Now that you have a default security group for all users that will be synchronized to Google Cloud, you can modify one of the search rules to look up the members
of `GCP-AllUsers` and then remove the others, since they won’t be needed.

Using the distinguished names of the `GCP-AllUsers` group, you modify the LDAP query as follows: 

    (&(memberof=CN=GCP-AllUsers,OU=Groups,OU=GCP,DC=gcdsdemo,DC=joonix,DC=net)(objectCategory=person)(objectClass=user)(!(userAccountControl:1.2.840.113556.1.4.803:=2))

![GCDS users all users memberOf screenshot](https://storage.googleapis.com/gcp-community/tutorials/gcds-use-cases-common-and-complex/11-GCDS-Users-AllUsers-memberOf.png)

To validate that the filter is configured correctly, either create a new user search rule or update the existing one to include the new LDAP query syntax, and
then click the ***Test LDAP Query*** button.

Here are the results of the query: 

![GCDS users all users memberOf results screenshot](https://storage.googleapis.com/gcp-community/tutorials/gcds-use-cases-common-and-complex/12-GCDS-Users-AllUsers-memberOf-results.png)

### Summary

The need to manage multiple user search rules can quickly become overwhelming. Using a single, default security group that has no permissions in Google Cloud
makes it easier in the long run. It also provides a single location that can be audited to ensure that the appropriate users are synchronized.

## Scenario #4: Selectively synchronizing groups based on group name

In some cases, organizations may choose to selectively synchronize groups based on an attribute in the group name (such as a prefix) or description. You can
accomplish this by manipulating the LDAP query used in the group search rule to target a wildcard match of the desired attribute.

In this scenario, user accounts that need to be synchronized to Google Cloud are already in the `GCP-AllUsers` group that has no access or IAM bindings.

### Group lookup

Unlike the `memberOf` filter used in the User LDAP query, the `group` object category does accept wildcards as input. Here’s the format of the LDAP query using a
wildcard:

    (&(objectCategory=group)(cn=*Name*)(|(groupType:1.2.840.113556.1.4.803:=2147483650)(groupType:1.2.840.113556.1.4.803:=2147483656)))

Here’s an example of the LDAP query that would be used to search for all groups that have `admins` in the name:

    (&(objectCategory=group)(cn=*admins*)(|(groupType:1.2.840.113556.1.4.803:=2147483650)(groupType:1.2.840.113556.1.4.803:=2147483656)))

In this scenario, you need to synchronize the following groups to Google Cloud:

- Groups in the `GCP` > `Groups` OU that are prefixed with `GCP`
- Groups in the `Corp` > `R&D` > `Groups` OU that are either prefixed with `RD` or contain the word `GCP` in the description field

![AD GCP Groups screenshot](https://storage.googleapis.com/gcp-community/tutorials/gcds-use-cases-common-and-complex/13-AD-GCP-Groups-Sync.png)

![AD R&D Groups screenshot](https://storage.googleapis.com/gcp-community/tutorials/gcds-use-cases-common-and-complex/14-AD-RD-Groups-Sync.png)

#### Groups prefixed with `GCP`

To search for groups prefixed with `GCP` in the `GCP` > `Groups` OU, you use the following LDAP query along with the **Base DN**:

    (&(objectCategory=group)(cn=GCP*)(|(groupType:1.2.840.113556.1.4.803:=2147483650)(groupType:1.2.840.113556.1.4.803:=2147483656)))

    OU=Groups,OU=GCP,DC=gcdsdemo,DC=joonix,DC=net

Testing the query yields the following results:

![GCDS groups GCP screenshot](https://storage.googleapis.com/gcp-community/tutorials/gcds-use-cases-common-and-complex/15-GCDS-Groups-GCP-name.png)

#### Groups prefixed with `RD` or with `GCP` in the description

To search for groups with names prefixed with `RD` or with `GCP` in the description in the `Corp` > `R&D` > `Groups` OU, you use the following LDAP query along 
with the **Base DN**:

    (&(objectCategory=group)(|(cn=RD*)(description=*GCP*))(|(groupType:1.2.840.113556.1.4.803:=2147483650)(groupType:1.2.840.113556.1.4.803:=2147483656)))

    OU=Groups,OU=R&D,OU=Corp,DC=gcdsdemo,DC=joonix,DC=net

Testing the query yields the following results:

![GCDS groups R&D screenshot](https://storage.googleapis.com/gcp-community/tutorials/gcds-use-cases-common-and-complex/16-GCDS-Groups-RD-name.png)

The four security groups matching the criteria are found. The security group `Restricted-Users` does not have a name prefixed with `RD`, nor does it 
have `GCP` in the description, so it is not returned by the search.

### Summary

Having the ability to selectively synchronize groups into Google Cloud using wildcards can ease the operational burden of needing to frequently update or add new
group search rules as groups are newly created. Additionally, this approach encourages administrators to follow a standardized naming convention for groups that
need to exist in Google Cloud.

## What's next

To get started with GCDS, see the [Google Cloud Directory Sync documentation](https://support.google.com/a/answer/106368).
