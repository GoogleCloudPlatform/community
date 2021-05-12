---
title: Google Cloud Directory Sync Examples
description: Common and Complex Use Cases for Syncing Active Directory Users to Cloud Identity Using Google Cloud Directory Sync.
author: akaashr
tags: gcds, activedirectory
date_published: 2021-05-21
---

Akaash Rampersad | Customer Engineer, Infrastructure Modernization | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

## Objectives

This tutorial covers a few scenarios where Google Cloud Directory Sync (GCDS) can be used to sync existing User and Group Identities from an Active Directory Domain. In each scenario you will see the steps required to configure GCDS to solve a specific requirement.


## Costs

[Google Cloud Directory Sync](https://support.google.com/a/answer/106368?hl=en#) and [Google Cloud Identity Free](https://cloud.google.com/identity/docs/editions) are free to use.


## Before you begin

This tutorial assumes that the following prerequisites have been met.

### Prerequisites

- [x] [Google Cloud Directory Sync](https://support.google.com/a/answer/106368?hl=en#) should be installed and configured
- [x] Google Cloud should be [federated](https://cloud.google.com/architecture/identity/federating-gcp-with-active-directory-synchronizing-user-accounts) with Active Directory


## The GCDSDemo Company

To properly demonstrate the configuration of Google Cloud Directory Sync (GCDS), let's first examine an example AD Domain built to represent a typical environment. 

Let’s assume that we’re working with a customer called The GCDSDemo Company and they are in the process of migrating to Google Cloud. The first step of their journey is syncing their existing Identities from Active Directory so that they can login using the same Credentials.

### Active Directory Configuration

Let’s quickly examine the example Domain (***gcdsdemo.joonix.net***) for The GCDSDemo Company. You’ll notice there are two (2) Organizational Units (OU) of interest: ***Corp*** and ***GCP***.

![ADUC OUs Screenshot](https://github.com/akaashr/community/blob/master/tutorials/gcds-use-cases-common-and-complex/01-AD-OUs.png)

In the ***Corp*** OU there are few sub-OUs but we’ll be focusing on the ***IT*** and ***R&D*** sub-OUs since the User objects we need synced are located there.

![ADUC IT Users Screenshot](https://github.com/akaashr/community/blob/master/tutorials/gcds-use-cases-common-and-complex/02-AD-IT-Users.png)

![ADUC R&D Users Screenshot](https://github.com/akaashr/community/blob/master/tutorials/gcds-use-cases-common-and-complex/03-AD-RD-Users.png)

Let’s also assume that the IT Administrators of ***gcdsdemo.joonix.net*** made a design decision to put the Security Groups for Google Cloud in a separate OU to ensure that those Groups don’t inadvertently get assigned to resources within their on-premise environment.

![ADUC GCP Groups Screenshot](https://github.com/akaashr/community/blob/master/tutorials/gcds-use-cases-common-and-complex/04-AD-GCP-Groups.png)

### Google Cloud Directory Sync Configuration

The [Installation and Configuration Guide](https://cloud.google.com/architecture/identity/federating-gcp-with-active-directory-synchronizing-user-accounts#connecting_to_active_directory) for GCDS recommends leaving the `Base DN` blank. For most Organizations this wouldn’t be an issue and normally works well. However, there are two main considerations with this approach:

1. The larger the Forest sub-tree (number of objects) the longer queries take to run.

2. The default search for User and Group objects will return ***all*** matching entries which can inadvertently cause unintended Users and/or Groups to sync with Google Cloud Identity. 

For example, consider that the Security Groups are not mail-enabled therefore they can only be identified by their `userPrincipalName` attribute. If the default LDAP Query were to be executed, ***all*** Security Groups including those that are out of scope will be returned as matching:

![GCDS Default Search Screenshot](https://github.com/akaashr/community/blob/master/tutorials/gcds-use-cases-common-and-complex/05-GCDS-Default-Search.png)

This can usually be mitigated by manually assigning an email address to the Security Groups (even if they are not mail-enabled) and switching the Query to use the `mail` attribute or as we will see in the next section, manipulating the `Base DN` to be more specific.


## Scenario #1 - User Accounts and Groups are not in the same Organizational Unit (OU)

This scenario is typically found in most on-premise environments; the User objects and Group objects are located in different OUs and there is no common “anchor OU” for them both. Additionally this scenario explores configuring the `Base DN` in the Search Rules to ensure that the search scope is smaller which will also help with preventing unintended Users and Groups from being synced.

For this example, assume the following is true:
- [x] GCDS is installed and configured per the [documentation](https://cloud.google.com/architecture/identity/federating-gcp-with-active-directory-synchronizing-user-accounts)
- [x] The Security Groups are ***not*** mail-enabled and ***do not*** have an email address assigned
      For mail-enabled Groups, you would use `mail` instead of `userPrincipalName`
- [x] The Users reside in the ***Corp*** > ***IT*** > ***Users***  and ***Corp*** > ***R&D*** > ***Users*** sub-OUs
- [x] All Users in the sub-OUs will be synced to Google Cloud

### User Accounts Lookup

With User objects being present in multiple OUs, the Best Practice is to set the `Base DN` for your LDAP Query to be the OU that is common and uplevel hierarchically relative to the User objects’ OU.

In this case, since ***IT*** and ***R&D*** are Child OUs of ***Corp*** then the `Base DN` for the LDAP Query should be set to:

`OU=Corp,DC=gcdsdemo,DC=joonix,DC=net`

Testing the LDAP Query yields the following list of Users:

![GCDS Users BaseDN Screenshot](https://github.com/akaashr/community/blob/master/tutorials/gcds-use-cases-common-and-complex/06-GCDS-Users-BaseDN.png)

### Groups Lookup

The Group Search LDAP Query follows the same structure as the User Search LDAP Query i.e. the `Base DN` would be set to the OU that is common and uplevel hierarchically relative to the Group objects’ OU, which in this case is ***GCP*** > ***Groups***.

The `Base DN` should then be set to:

`OU=Groups,OU=GCP,DC=gcdsdemo,DC=joonix,DC=net`

Testing the LDAP Query yields the following list of Groups:

![GCDS Groups BaseDN Screenshot](https://github.com/akaashr/community/blob/master/tutorials/gcds-use-cases-common-and-complex/07-GCDS-Groups-BaseDN.png)

Notice that the Builtin Security Groups like ***grouppolicycreatorowners@gcdsdemo.joonix.net*** and ***domaincontrollers@gcdsdemo.joonix.net*** don’t show up, which is the behavior we want.

### Summary

Setting the `Base DN` on the Search Rules is useful when you want to limit the scope of the Search and allows for a more targeted approach to syncing Identities to Google Cloud. In the next Scenario, we’ll discuss tuning the LDAP Query to further narrow the scope for syncing to ensure that only the appropriate User objects and Group objects are selected.


## Scenario #2 - Selectively syncing User Accounts based on Group Membership

Building on the previous scenario, some Organizations may not want to have all Users in an OU synced to Google Cloud. Instead, they would want to selectively sync Users that are part of specific Groups. Let’s examine how we can configure this in GCDS.

For this example, assume the following is true:
- [x] GCDS is installed and configured per the [documentation](https://cloud.google.com/architecture/identity/federating-gcp-with-active-directory-synchronizing-user-accounts)
- [x] The Security Groups are ***not*** mail-enabled and ***do not*** have an email address assigned
      For mail-enabled Groups, you would use `mail` instead of `userPrincipalName`
- [x] Only User Accounts that are members of ***GCP*** > ***Groups*** will be synced to Google Cloud
      Example: Users in ***GCP-OrgAdmins***, ***GCP-InfraAdmins*** etc
- [x] The Security Groups are relatively static and new Groups will be added on a case-by-case basis

### User Accounts Lookup

Selectively syncing User Accounts based on Group Membership requires a couple changes:
1. Modifying the LDAP Query to include the `memberOf` LDAP filter
2. Creating a User Search Rule for ***each*** Group that contains User Accounts to sync

To modify the LDAP Query to include the `memberOf` filter, we must first get a list of all the Distinguished Names (DN) of the in scope Groups.

`Get-ADGroup -Filter {name -like "GCP*"} | Format-Table Name, DistinguishedName -Auto`

**Sample Output - Do Not Copy**
```
Name               DistinguishedName
----               -----------------
GCP-AllUsers       CN=GCP-AllUsers,OU=Corp,DC=gcdsdemo,DC=joonix,DC=net
GCP-Developers     CN=GCP-Developers,OU=Groups,OU=GCP,DC=gcdsdemo,DC=joonix,DC=net
GCP-InfraAdmins    CN=GCP-InfraAdmins,OU=Groups,OU=GCP,DC=gcdsdemo,DC=joonix,DC=net
GCP-NetworkAdmins  CN=GCP-NetworkAdmins,OU=Groups,OU=GCP,DC=gcdsdemo,DC=joonix,DC=net
GCP-OrgAdmins      CN=GCP-OrgAdmins,OU=Groups,OU=GCP,DC=gcdsdemo,DC=joonix,DC=net
GCP-ProductionTeam CN=GCP-ProductionTeam,OU=Groups,OU=GCP,DC=gcdsdemo,DC=joonix,DC=net
```

Using these DNs, we will need to modify the LDAP Query as follows:

`(&(memberof=DN_OF_SECURITY_GROUP)(objectCategory=person)(objectClass=user)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))`

Example using the ***GCP-OrgAdmins*** Security Group

`(&(memberof=CN=GCP-OrgAdmins,OU=Groups,OU=GCP,DC=gcdsdemo,DC=joonix,DC=net)(objectCategory=person)(objectClass=user)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))`

To validate that the filter is configured correctly, either create a new User Search rule or update the existing one to include the new LDAP Query syntax and then click the ***Test LDAP Query*** button.

Here’s the results of the Query:

![GCDS Users memberOf Screenshot](https://github.com/akaashr/community/blob/master/tutorials/gcds-use-cases-common-and-complex/08-GCDS-Users-memberOf.png)

Let’s quickly verify the Group Membership of the ***GCP-OrgAdmins*** Group to ensure the validity of the Query.

`Get-ADGroupMember -Identity "GCP-OrgAdmins" | Get-ADUser -Properties * | Format-Table Name,UserPrincipalName,Mail -Auto`

**Sample Output - Do Not Copy**
```
Name                UserPrincipalName                       Mail
----                -----------------                       ----
Mary Jackson        Mary.Jackson@gcdsdemo.joonix.net        Mary.Jackson@gcdsdemo.joonix.net
Srinivasa Ramanujan Srinivasa.Ramanujan@gcdsdemo.joonix.net Srinivasa.Ramanujan@gcdsdemo.joonix.net
Bill Nye            Bill.Nye@gcdsdemo.joonix.net            Bill.Nye@gcdsdemo.joonix.net
Isaac Newton        Isaac.Newton@gcdsdemo.joonix.net        Isaac.Newton@gcdsdemo.joonix.net
```

Great! We can clearly see the LDAP Query worked and now only the Users that are part of the ***GCP-OrgAdmins*** Group are in scope to sync.

The next step is to create a User Search Rule for the remaining Groups to ensure all the Users are synced.

![GCDS Users Search Rule memberOf Screenshot](https://github.com/akaashr/community/blob/master/tutorials/gcds-use-cases-common-and-complex/09-GCDS-Users-SearchRule-memberOf.png)

Notice that the `Base DN` is still configured to be `OU=Corp,DC=gcdsdemo,DC=joonix,DC=net` but the LDAP Query is still able to return the correct list of Users because the Distinguished Name of the Security Group is used in the Query which overrides the `Base DN` scope.

### Summary

Leveraging the `memberOf` LDAP filter is a great way to narrow the scope of User identities to sync and ensures that only the explicitly defined User Accounts exist in Google Cloud. However, this approach does require the extra legwork of creating User Search Rules for every Group and as new Groups are added, new User Search Rules will also have to be added which can become tedious to manage.

In the next scenario, we’ll examine a strategy to minimize the number of User and Group Search Rules.


## Scenario #3 - Reducing the number of User Search Rules

In this scenario, we’ll examine how to configure GCDS to automatically detect new Groups and sync the Users that are part of those Groups only.

For this example, assume the following is true:
- [x] GCDS is installed and configured per the [documentation](https://cloud.google.com/architecture/identity/federating-gcp-with-active-directory-synchronizing-user-accounts)
- [x] The Security Groups are ***not*** mail-enabled and ***do not*** have an email address assigned
      For mail-enabled Groups, you would use `mail` instead of `userPrincipalName`
- [x] Only User Accounts that are members of a Group that is prefixed with ***GCP*** will be synced to Google Cloud
      Example: Users in ***GCP-OrgAdmins***, ***GCP-InfraAdmins*** etc

### Prerequisite

In the previous scenario we modified the LDAP Query to use the memberOf LDAP filter and had to create a new User Search Rule for each Group. This is due to the memberOf filter not supporting Wildcards (*). 

To workaround this, we must first create a new Security Group that will be common to every User that will exist in Google Cloud. This Group does not need to have any IAM Bindings or be used for anything other than identifying the User Accounts to sync. This is akin to the ***Domain Users*** built-in Security Group in Active Directory.

For this example, we’ll create a Security Group called ***GCP-AllUsers***.

`New-ADGroup -Name "GCP-AllUsers" -Path "OU=Groups,OU=GCP,DC=gcdsdemo,DC=joonix,DC=net" -Description "[NO IAM] All Users being synced to Google Cloud" -GroupScope "Global"`

Next we need to populate the Group with the User Accounts that are already members of the other GCP Groups.

`Get-ADGroup -Filter {name -like "GCP*"} | Get-ADGroupMember | Add-ADPrincipalGroupMembership -MemberOf "GCP-AllUsers"`

Now let’s verify the Group Membership

`Get-ADGroupMember -Identity "GCP-AllUsers" | Format-Table Name,DistinguishedName -Auto`

**Sample Output - Do Not Copy**
```
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
```

Next we need to clean up the User Search Rules.

### User Account Lookup

Now that there is a default Security Group for all Users that will be synced to Google Cloud, we can modify one (1) of the Search Rules to lookup the members of ***GCP-AllUsers*** and then remove the others since they won’t be needed.

Using the DN of the ***GCP-AllUsers*** Group the LDAP Query will need to be modified as follows: 

`(&(memberof=CN=GCP-AllUsers,OU=Groups,OU=GCP,DC=gcdsdemo,DC=joonix,DC=net)(objectCategory=person)(objectClass=user)(!(userAccountControl:1.2.840.113556.1.4.803:=2))`

![GCDS Users All Users memberOf Screenshot](https://github.com/akaashr/community/blob/master/tutorials/gcds-use-cases-common-and-complex/11-GCDS-Users-AllUsers-memberOf.png)

To validate that the filter is configured correctly, either create a new User Search rule or update the existing one to include the new LDAP Query syntax and then click the ***Test LDAP Query*** button.

Here’s the results of the Query: 

![GCDS Users All Users memberOf Results Screenshot](https://github.com/akaashr/community/blob/master/tutorials/gcds-use-cases-common-and-complex/12-GCDS-Users-AllUsers-memberOf-results.png)

### Summary

Having to manage multiple User Search Rules can quickly become overwhelming to maintain. Leveraging a single, default Security Group that has no permissions in Google Cloud makes it easier in the long run. It also provides a single location that can be audited to ensure that the appropriate Users are synced.


## Scenario #4 - Selectively syncing Groups based on Group Name

In some cases, Organizations may choose to selectively sync Groups based on an attribute in the Group name such as a Prefix (eg. ***GCP***) or Description (eg. ***“Users in this group…”***). This can be accomplished by manipulating the LDAP Query used in the Group Search Rule to target a wildcard match of the desired attribute. Let’s examine how we can configure this in GCDS.

For this example, assume the following is true:
- [x] GCDS is installed and configured per the [documentation](https://cloud.google.com/architecture/identity/federating-gcp-with-active-directory-synchronizing-user-accounts)
- [x] The Security Groups are ***not*** mail-enabled and ***do not*** have an email address assigned
      For mail-enabled Groups, you would use `mail` instead of `userPrincipalName`
- [x] User Accounts that need to be synced to Google Cloud are already added to the ***GCP-AllUsers*** Group that has no access or IAM Bindings
- [x] The Groups that need to be synced to Google Cloud must match any of the following criteria:
       * The name must match a prefix (eg. ***GCP***)
       * The description must contain a word or phrase (eg. ***“GCP approved”***)

### Group Lookup

Unlike the `memberOf` filter used in the User LDAP Query, the `group` Object Category does support wildcards. Here’s the format of the LDAP Query using a wildcard:

`(&(objectCategory=group)(cn=*Name*)(|(groupType:1.2.840.113556.1.4.803:=2147483650)(groupType:1.2.840.113556.1.4.803:=2147483656)))`

Here’s an example of the LDAP Query that would be used to search for all Groups that have the word ***Admins*** in the name:

`(&(objectCategory=group)(cn=*admins*)(|(groupType:1.2.840.113556.1.4.803:=2147483650)(groupType:1.2.840.113556.1.4.803:=2147483656)))`

Let’s assume that we need to sync the following Groups to Google Cloud:
1. Groups in the ***GCP*** > ***Groups*** OU that are prefixed with ***GCP***
2. Groups in the ***Corp*** > ***R&D*** > ***Groups*** OU that are either prefixed with ***RD*** or contain the word ***GCP*** in the description field

![AD GCP Groups Screenshot](https://github.com/akaashr/community/blob/master/tutorials/gcds-use-cases-common-and-complex/13-AD-GCP-Groups-Sync.png)

![AD R&D Groups Screenshot](https://github.com/akaashr/community/blob/master/tutorials/gcds-use-cases-common-and-complex/14-AD-RD-Groups-Sync.png)

#### 1 - Groups prefixed with GCP

To search for Groups prefixed with ***GCP*** in the ***GCP*** > ***Groups*** OU, we would use the following LDAP Query along with the `Base DN`:

`(&(objectCategory=group)(cn=GCP*)(|(groupType:1.2.840.113556.1.4.803:=2147483650)(groupType:1.2.840.113556.1.4.803:=2147483656)))`

`OU=Groups,OU=GCP,DC=gcdsdemo,DC=joonix,DC=net`

Testing the Query yields the following results:

![GCDS Groups GCP Screenshot](https://github.com/akaashr/community/blob/master/tutorials/gcds-use-cases-common-and-complex/15-GCDS-Groups-GCP-name.png)

#### 2 - Groups prefixed with RD or contain the word GCP in the description

To search for Groups prefixed with RD or have GCP in the description, in the Corp > R&D > Groups OU, we would use the following LDAP Query along with the Base DN:

`(&(objectCategory=group)(|(cn=RD*)(description=*GCP*))(|(groupType:1.2.840.113556.1.4.803:=2147483650)(groupType:1.2.840.113556.1.4.803:=2147483656)))`

`OU=Groups,OU=R&D,OU=Corp,DC=gcdsdemo,DC=joonix,DC=net`

Testing the Query yields the following results:

![GCDS Groups R&D Screenshot](https://github.com/akaashr/community/blob/master/tutorials/gcds-use-cases-common-and-complex/16-GCDS-Groups-RD-name.png)

As expected, the four (4) Security Groups matching the criteria are found. The Security Group ***Restricted-Users*** does not have a name prefixed with ***RD*** nor does it have ***GCP*** in the description therefore it is omitted from the search.

### Summary

Having the ability to selectively sync Groups into Google Cloud using wildcards can ease the operational burden of having to constantly update or add new Group Search Rules as Groups are newly created. Additionally it encourages Administrators to follow a standardized naming convention for Groups that need to exist in Google Cloud.


## What's next

In this tutorial we covered a few scenarios where LDAP Queries can be manipulated from within GCDS to broaden or narrow the scope of a particular User or Group Search. Each Organization’s requirements for syncing identities from on-premise to Google Cloud are different which is why the customizability of GCDS is a powerful tool for Administrators and Security Engineers to ensure that the right Users and Groups are synced to the Cloud.

- To get started with GCDS today, [click here](https://support.google.com/a/answer/106368?hl=en#).
