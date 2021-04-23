---
title: Activating DNSSEC for Cloud DNS domains
description: Improve security for your Cloud DNS domains - activate DNSSEC validation for Cloud DNS-hosted domains that are DNSSEC-enabled.
author: dupuy
tags: DNS, DNSSEC, Domain registrars, DS records
date_published: 2017-10-11
---

Alexander Dupuy | Software Engineer | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

[DNSSEC][1] (DNS Security Extensions) authenticates DNS answers to block
forgeries and is the basis for [DANE e‑mail security][2]. Google Cloud DNS can
use DNSSEC to sign the managed zones for your domains. But until you add a DS
(Delegated Signer) record for your `example.com` domain to its .COM top-level
domain (TLD) registry, DNS resolvers can't verify DNSSEC.

[1]: https://www.isc.org/wp-content/uploads/2016/06/Winstead_DNSSEC-Tutorial.pdf
[2]: https://www.internetsociety.org/blog/2016/01/lets-encrypt-certificates-for-mail-servers-and-dane-part-1-of-2/

This tutorial is for DNS domain administrators using Google Cloud DNS who have
enabled DNSSEC on the managed zones for their domains. It shows how to activate
DNSSEC validation for those domains by adding DS records through their domain
registrars. The specifics depend on the domain registrar, and this does not give
detailed instructions for all domain registrars. It does have basic instructions
and links for the most popular registrars and many others that support DNSSEC.

This tutorial also has instructions for *de-activating* DNSSEC by removing DS
records. This is an essential step you **must** perform before disabling DNSSEC
for Google Cloud DNS.

## Objectives

1.  Confirm DNSSEC support by domain registrar and TLD registry.

2.  Confirm full propagation of DNSSEC records and get DNSKEY information.

3.  Activate DNSSEC by adding a DS record through the domain registrar.

4.  Confirm DNSSEC validation of the domain.

Alternately, once you have already activated DNSSEC for a domain:

1.  De-activate DNSSEC by removing the DS record through the domain registrar.

2.  Confirm propagation of the DS removal by the TLD registry.

**Figure 1.** *Overview of tutorial components*

![Diagram of DNS delegation and registration](https://storage.googleapis.com/gcp-community/tutorials/dnssec-cloud-dns-domains/overview.png)

## Before you begin

This tutorial assumes that you

-   already own (or are an administrator for) a domain,

-   have access to the delegated Google Cloud DNS managed zone serving that
    domain, and

-   have [enabled DNSSEC signing][3] for that managed zone.

[3]: https://cloud.google.com/dns/dnssec

You also need an online account with the domain registrar for the domain. For
domain registrars without online accounts, you should be in the domain's WHOIS
contact list.

### Domain registrar account

If you aren't sure which domain registrar handles a domain, use the whois
command line tool (see below) or use [GWhois.org][4] ([example][5]). Check the
WHOIS results for reseller information. If there is a reseller, check both the
reseller and the domain registrar for specific instructions in this tutorial.

[4]: https://gwhois.org/
[5]: https://gwhois.org/dns-example.info+dns

```console
$ whois dns-example.info
Domain Name: DNS-EXAMPLE.INFO
Registry Domain ID: D503300000000040442-LRMS
Registrar WHOIS Server:
Registrar URL: http://www.google.com
…
Registrar: Google Inc.
Registrar IANA ID: 895
…
Reseller:
…
Name Server: NS-CLOUD-E1.GOOGLEDOMAINS.COM
Name Server: NS-CLOUD-E2.GOOGLEDOMAINS.COM
…
```

#### TLD *registries* vs. domain *registrars*

Despite similar names, TLD *registries* and domain *registrars* are separate and
have [different roles](https://support.google.com/domains/answer/3251189). For a
few TLDs, often two-letter country code (ccTLDs), the same organization is both
TLD registry and the only domain registrar.

*   **TLD registries**\
    provide WHOIS and DNS name service for top-level domains (TLDs). In most
    cases, they have an API for domain registrars to manage delegation records
    and WHOIS data.

*   **Domain registrars**\
    provide retail services to customers purchasing or renewing domains. They
    interact with TLD registries to manage delegation records in the TLD and
    update WHOIS data for those domains. Many offer web pages for customers to
    make those updates themselves, and some provide web APIs for automation
    tools. Most also provide free DNS name service for domains registered with
    them. But those domain registrar name servers are not used for domains
    delegated to Google Cloud DNS.

*   **Domain resellers**\
    provide only the retail services of domain registrars. They may offer online
    accounts through the domain registrar that interacts with the TLD registry.

The overview diagram above shows all three of these on the right side. To avoid
confusion, this tutorial always uses the terms “*TLD* registries” and “*domain*
registrars.”

## Costs

This tutorial uses Google Cloud DNS, which has monthly costs for both managed
zones and the number of queries handled. Use the [Pricing Calculator][6] to
generate a cost estimate based on your projected usage. Scroll down on that
linked page to see an estimate for Cloud DNS with one zone and up to several
tens of thousands of incoming queries.

[6]: https://cloud.google.com/products/calculator/#id=cb34e9f9-3838-48c2-9346-3d20379aa285

DNSSEC-validating resolvers may make extra queries for DNSKEY records on
DNSSEC-activated domains. There are very few of these queries compared to normal
traffic for most domains.

You can [use NSEC for DNSSEC][7] to allow resolvers to answer queries for
non-existent domains without querying Cloud DNS name servers. This may reduce
queries for some denial-of-service attacks that query for random subdomains.

[7]: https://cloud.google.com/dns/dnssec-advanced#advanced-signing-options

## Activate DNSSEC

After you enable DNSSEC for your managed zone in Google Cloud DNS, you
can activate DNSSEC through its domain registrar. You do this by
creating a DS record for your domain in the parent TLD. That creates a
chain of trust to your domain from its TLD, and beyond that to the
“trust anchor” for the root DNSKEY. Unless you do this, validating
resolvers cannot check DNSSEC signatures for your domain.

### Confirm DNSSEC support

#### TLD DNSSEC support

Although over 90% of top-level domains support DNSSEC, some do not, and it isn’t
possible to activate DNSSEC for a domain in a TLD that does not support it.
Confirm whether the TLD for your domain supports DNSSEC by looking for it in the
[ICANN TLD DNSSEC Report][8].

[8]: http://stats.research.icann.org/dns/tld_report/

-   If your TLD answers YES to the first two questions (Signed? and DS in Root?)
    it supports DNSSEC (these rows are **green**).

-   Some TLDs do not support DNSSEC at all (**light gray** rows). These are
    often two-letter country-code domains (ccTLDs) like .AI or .AL, but some
    (like .AERO) are global TLDs.

-   Some TLDs have enabled DNSSEC signing, but do not have a DS record in the
    root zone (**blue** rows). You might be able to add a DS record to these
    TLDs—when they publish a DS record for the TLD in the root zone it activates
    DNSSEC for your domain. Few if any domain registrars would support DNSSEC
    for such a TLD. In any case, it is not recommended, since you should be
    aware (and in control) of any change in the DNSSEC status of your domain.

If you  cannot reach the ICANN TLD DNSSEC site  for any reason, check with the
[Verisign DNSSEC debugger][9]. Enter the TLD name and hit return; if you see any
red ⊗ errors the TLD ([like AQ][10]) does not support DNSSEC.

[9]: https://dnssec-debugger.verisignlabs.com/
[10]: https://dnssec-debugger.verisignlabs.com/aq

If your top-level domain does not support DNSSEC, you **cannot activate DNSSEC**
and won't be able to complete this tutorial. Consider using a domain name in
another TLD if you need DNSSEC.

#### Domain registrar DNSSEC support

Some domain registrars do not support DNSSEC, or only support DNSSEC for domains
served from their own name servers. If there are no [instructions][specific] for
the domain registrar or reseller, check the [ICANN list][11] of registrars
supporting DNSSEC. Domain registrars may only support DNSSEC for some top-level
domains.

[specific]: #domain-registrar-specific-instructions
[11]: http://dnssec-deployment.icann.org/en/dnssec/deploy.htm

If your TLD registry supports DNSSEC but your domain registrar does not, you can
transfer the domain to another domain registrar. Make sure the new domain
registrar supports DNSSEC for that top-level domain. Unless you transfer the
domain to such a domain registrar, you **cannot activate DNSSEC** and won't be
able to complete this tutorial.

TLD registries and domain registrars may also support only some DNSSEC
algorithms. The default settings for DNSSEC in Google Cloud DNS use algorithms
supported in most cases. If you sign domains with newer algorithms like ECDSA,
your TLD registry or domain registrar may not be able to add a DS record with
that algorithm.

### Confirm DNSSEC record propagation

Before activating DNSSEC through your domain registrar, make sure that your zone
is being served with all DNSSEC data. It can take a while for Google Cloud DNS
to generate DNSSEC keys and signatures, and even longer for validating resolvers
to see those updates. If you activate DNSSEC before that completes, validating
resolvers may fail to resolve names in your domain.

This shell function checks that all authoritative servers for a domain are
serving DNSSEC data:

[embedmd]:# (checksigned.sh /checksigned/ $)
```sh
checksigned() {
    ZONE=`basename "$1" .`.
    if [ "$ZONE" = .. ]
    then
        ZONE=.
    fi
    NAME=`basename "$ZONE" .`
    NO_NS=true
    NO_SEC=false
    OPTS="+cd +noall +answer +nocl +nottl"

    dig $OPTS NS "$ZONE" @publicdns.goog | {
        # Check each delegated name server
        while read DOMAIN TYPE NS
        do
            if [ "$DOMAIN $TYPE" != "$ZONE NS" ]
            then
                   continue
            fi
            NO_NS=false
            if dig +cd +dnssec +norecurse DNSKEY "$ZONE" "@$NS" |
                    egrep 'RRSIG[[:space:]]+DNSKEY' > /dev/null
            then
                echo "$NS has DNSSEC data for $NAME"
            else
                echo "$NS does not have DNSSEC data for $NAME"
                NO_SEC=true
            fi
        done

        if "$NO_NS"
        then
            echo "$NAME is not a delegated DNS zone"
        else
            if "$NO_SEC"
            then
                return
            fi
            MINTTL=`dig +cd SOA "$ZONE" @publicdns.goog |
                    awk '/^[^;]/ && $4=="SOA" { print $11 }'`
            echo "Negative cache for $NAME expires after $MINTTL seconds."
        fi
    }
}
checksigned "$1"
```

```console
$ checksigned dns-example.info
ns-cloud-e1.googledomains.com. has DNSSEC data for dns-example.info
ns-cloud-e2.googledomains.com. has DNSSEC data for dns-example.info
ns-cloud-e3.googledomains.com. has DNSSEC data for dns-example.info
ns-cloud-e4.googledomains.com. has DNSSEC data for dns-example.info
Negative cache for dns-example.info expires after 300 seconds.
```

Be sure to check that the delegated name servers listed in the output of this
command are the same ones listed in the NS records for your managed zone. If
they are different, your Google Cloud DNS managed zone is **not** authoritative
for the domain, and until you update the delegation, you should not add a DS
record based on the DNSKEY information for your managed zone. After updating the
delegation, *be sure to wait for the full TTL of the delegation records to
expire*, so that all resolvers use the new authoritative name servers. TLD
delegation NS records often have TTLs that are much longer (1–2 days is common)
than the TTLs in the authoritative zone itself.

If your domain registrar is **Google Domains**, *its name servers are also at
Google, and their names are very similar.* **Check the letters (‘e’ in the
example above) to make sure they match EXACTLY**.

Once this function generates output similar to the above, the DNSSEC data is
fully propagated. However, validating resolvers may still cache the
non-existence of DNSKEYs for an additional period; you should also wait for the
negative cache data to expire before adding a DS record.

### Get DNSKEY information

Each domain registrar requires different types of information in their
interfaces for adding a DS record (it may also vary depending on the TLD for
your domain). All of this information is taken from one of the DNSKEY records
that Google Cloud DNS creates for your zone when you enable DNSSEC.

There are two different kinds of DNSKEYs, “key-signing keys” that are only used
to sign DNSKEY records, and “zone-signing keys” that sign all (the rest) of the
records in the zone. DS records are generated from the key-signing key
information.

There are four pieces of information about the Key-Signing Key in a DS record;
domain registrars may ask for these separately or just for the complete DS
record data:

-   **Key tag** (1-5 digit number such as *1234*)

-   **Algorithm** (name such as *RSASHA256* or its corresponding number *8*)

-   **Digest type** (name such as *SHA1* or its corresponding number *1*)

-   **Digest** (hexadecimal string such as *2FD4E1C67A2DFC…B76E7391B93EB12*)

Sometimes domain registrars may require or ask for other information, depending
on the top-level domain (TLD) registry:

-   **Public key** (base64 string such as *9gP/WrSoitGLYmyl…TuqqaWKOpBFLaQ==*)

-   **Flags** (always **257**) or **Key type** (key-signing key or **KSK**)

-   **Protocol** (always **3**)

-   **Maximum signature lifetime** (optional, only used for .ORG; *leave blank*)

All of these can be found in the Google Cloud DNS console by navigating to your
managed zone and clicking the "Registrar Setup" link in the upper right corner
of the "Zone details" page.

![Registrar Setup pop-up](https://storage.googleapis.com/gcp-community/tutorials/dnssec-cloud-dns-domains/registrar-setup.png)

You can also use the `gcloud` command-line tool to get this information:

```console
$ EXAMPLE_ZONE=my-zone  # use your managed zone name here
$ gcloud beta dns dnskeys list $EXAMPLE_ZONE
ID  KEY_TAG  TYPE          IS_ACTIVE  DESCRIPTION
0   1234     KEY_SIGNING   True       -
1   12345    ZONE_SIGNING  True       -
```

You need the *ID* of the KEY_SIGNING Key (KSK), which is usually zero (0), to
get a complete DS record and all details of the key you may need to create it
(some details are omitted, and the public key is shortened for display). Set
`EXAMPLE_ZONE` to the zone ID and `KSK_ID` to the ID of the KEY_SIGNING key as
noted above:

```console
$ EXAMPLE_ZONE=my-zone
$ KSK_ID=0
$ gcloud beta dns dnskeys describe $EXAMPLE_ZONE --key-id=$KSK_ID
dsRecord: 1234 7 1 2FD4E1C67A2D28FCED849EE1BB76E7391B93EB12

algorithm: RSASHA1-NSEC3-SHA1
…
digests:
- digest: 2FD4E1C67A2D28FCED849EE1BB76E7391B93EB12
  type: SHA1
…
keyTag: 1234
publicKey: 9gP/WrSoitGLYmylXwE…LIVVWyJ2j/nTuqqaWKOpBFLaQ==
type: KEY_SIGNING
```

If your domain registrar needs numeric values for algorithm or digest types,
they are given in the dsRecord: the first number (`1234` above) is the key tag,
the second number (`7` above) is the algorithm, and the third number (`1` above)
is the digest type. The symbolic names for algorithm and digest type are given
separately below.

The use of SHA in both the algorithm and the DS digest type can be confusing:
the first hash summarizes the records in a record set for signing with a DNSKEY;
the second hash summarizes a DNSKEY for the signed DS record in the parent zone.
The hashes can differ in strength, but preferably by at most a factor of two.
The deprecated SHA-1 should only be used for compatibility with old resolvers,
in which case SHA-1 must be used for *both* DNSSEC algorithm and DS digest (your
Google Cloud DNS project must be whitelisted to use RSASHA1 algorithms).

All values used by Google Cloud DNS are in the following table and in IANA's
[DNSSEC Algorithm Numbers][12] or [DS RR Type Digest Algorithms][13]:

| DNSKEY Algorithm   | Number | Descriptive text               | DS Digest | Number |
| ------------------ | ------ | ------------------------------ | --------- | ------ |
| RSASHA1            | **5**  | RSASHA1                        | SHA-1     | **1**  |
| RSASHA1-NSEC3-SHA1 | **7**  | RSASHA1-NSEC3-SHA1             | SHA-1     | **1**  |
| RSASHA256          | **8**  | RSA/SHA-256                    | SHA-256   | **2**  |
| RSASHA512          | **10** | RSA/SHA-512                    | SHA-256   | **2**  |
| ECDSAP256SHA256    | **13** | ECDSA Curve P-256 with SHA-256 | SHA-256   | **2**  |
| ECDSAP384SHA384    | **14** | ECDSA Curve P-384 with SHA-384 | SHA-384   | **4**  |

[12]: https://www.nameisp.com/
[13]: https://www.name.com

### Add a DS record through the domain registrar

[Specific instructions][specific] for domain registrars supporting DNSSEC are
listed below.

### Confirm DNSSEC validation

You can confirm that resolvers are able to successfully validate your domain
once the DS records have been published by checking with the [Verisign DNSSEC
debugger][14]: just enter your domain name and hit return; you should only see
green checks (e.g. http://dnssec-debugger.verisignlabs.com/publicdns.goog).

[14]: https://dnssec-debugger.verisignlabs.com/

## De-activate DNSSEC

**Before** you disable DNSSEC for a managed zone that you still want to use, you
*must deactivate DNSSEC for your domain through your domain registrar* to ensure
that DNSSEC-validating resolvers can still resolve names in the zone.

This is also necessary when changing the authoritative name servers for a zone
to another DNS operator that does not support DNSSEC, although it usually is not
necessary for a domain registrar transfer.

### Remove DS records through the domain registrar

Do this by removing the DS records for your domain from the parent zone, so that
resolvers no longer try to validate your domain data with DNSSEC. [Specific
instructions][specific] for domain registrars supporting DNSSEC are listed below.

### Confirm TLD registry DS removal propagation

It can take a while for TLD registries to remove DS records, and even longer for
validating resolvers to expire cached data, as TLD records often have very long,
multi-day TTLs. Make sure that all TLD name servers have stopped serving DS
records for your domain, and wait for cached data to expire, before disabling
DNSSEC for your managed zone on Google Cloud DNS. If you disable DNSSEC for your
managed zone before that is complete, validating resolvers may fail to resolve
names for your domain until the DS removal is fully propagated.

This shell function checks that all authoritative servers for a TLD have removed
DS records for your domain, and that cached data at Google Public DNS has
expired:

[embedmd]:# (checkremoved.sh /checkremoved/ $)
```sh
checkremoved() {
    ZONE=`basename "$1" .`.
    if [ "$ZONE" = .. ]
    then
        ZONE=.
    fi
    NAME=`basename "$ZONE" .`
    PARENT=`expr $NAME : '[^.]*.\(.*\)'`.
    NO_NS=true
    OPTS="+cd +noall +answer +nocl +nottl"

    dig $OPTS NS "$PARENT" @publicdns.goog | {
        # Check each TLD (parent) name server
        while read DOMAIN TYPE NS
        do
            if [ "$DOMAIN $TYPE" != "$PARENT NS" ]
            then
                   continue
            fi
            NO_NS=false
            if dig +cd +norecurse DS "$ZONE" "@$NS" |
                    egrep '[[:space:]]IN[[:space:]]+DS[[:space:]]' > /dev/null
            then
                echo "$NS has DS record(s) for $NAME"
            else
                echo "$NS does not have DS records for $NAME"
            fi
        done

        if "$NO_NS"
        then
            echo "$PARENT is not a top-level domain or delegated zone"
        else
            OLDTTL=`dig +cd +dnssec DS "$ZONE" @publicdns.goog |
                    awk '/^[^;]/ && $4=="RRSIG" && $5=="DS" { print $8 }'`
            if [ -n "$OLDTTL" ]
            then
                echo "Cached DS records for $NAME expire after $OLDTTL seconds."
            else
                echo "No cached DS records found in Google Public DNS."
            fi
        fi
    }
}
checkremoved "$1"
```

```console
$ checkremoved example.com
e.gtld-servers.net. has DS record(s) for example.com
b.gtld-servers.net. has DS record(s) for example.com
j.gtld-servers.net. has DS record(s) for example.com
…
i.gtld-servers.net. has DS record(s) for example.com
Cached DS records for example.com expire after 86400 seconds.
```

```console
$ checkremoved google.com
a.gtld-servers.net. does not have DS records for google.com
e.gtld-servers.net. does not have DS records for google.com
k.gtld-servers.net. does not have DS records for google.com
…
l.gtld-servers.net. does not have DS records for google.com
No cached DS records found in Google Public DNS.
```

Once the DS records are removed, and the maximum cache TTL has expired, you can
safely [turn off DNSSEC for the managed zone][16].

[16]: https://cloud.google.com/dns/dnssec#disabling

## Domain registrar-specific instructions

If you don’t find your domain registrar listed here, check the [nTLDStats
listing of domain registrars][17]; if you click through to the page for your
domain registrar and under “Signed Zones” it shows N/A then that domain
registrar is extremely unlikely to support DNSSEC.

[17]: https://ntldstats.com/registrar/

For many small two-letter country code TLDs (ccTLDs), the TLD registry also acts
as the sole registrar. For domains in ccTLDs that support DNSSEC, contacting the
TLD registry or registrar support by e-mail and providing the DS record you need
them to add, may be the most practical solution.

### Google Domains

Google Domains instructions at
https://support.google.com/domains/answer/3290309 (in the subsection titled
“Setting up DNSSEC security for your domain”) to add a DS record and activate
DNSSEC for your Google-registered domain. Follow the instructions for **Using
DNSSEC with custom name servers**, and provide the following information:

-   Key Tag

-   Algorithm (select the appropriate algorithm type from the pop-up menu)

-   Digest type (select the appropriate digest type from the pop-up menu)

-   Digest (long hexadecimal string)

You can also remove DS records and deactivate DNSSEC from the same DNSSEC
management page.

### 1&1 Internet

As of October 2017, [1&1 Internet][18] did not support DS record management
although it had [two signed zones][19] in new gTLDs. Other domain registrars in
the United Internet group ([InternetX](#internetx) and
[United Domains](#united-domains)) *do* support DS record management.

[18]: https://icannwiki.org/1%261_Internet
[19]: https://ntldstats.com/registrar/83-1%261-Internet-AG

### 123 Reg

As of October 2017, 123 Reg (formerly Domain Monster) did not did not document
any support for DS record management, although it had [three signed zones][22]
in new gTLDs.

[22]: https://ntldstats.com/registrar/1390-Mesh-Digital-Limited

### 1API

1API GmbH ([HEXONET][23]) does not provide a web site for registration
management, since they work exclusively through resellers. Contact your domain
reseller for support. The [Hexonet Wiki][24] has information about the DNSSEC
API for 1API resellers.

[23]: https://icannwiki.org/HEXONET
[24]: https://wiki.hexonet.net/wiki/DNSSEC

### Amazon

If Amazon Registrar, Inc. is your domain registrar (or your reseller, for
domains registered through Gandi—all domains except for: .com .net and .org) you
can add and remove DS records using the Route53 console at
https://console.aws.amazon.com/route53/.

Amazon has instructions to add a DS record ([Adding Public Keys for a
Domain][26]). You need to provide the following pieces of information:

[26]: http://docs.aws.amazon.com/Route53/latest/DeveloperGuide/domain-configure-dnssec.html#domain-configure-dnssec-adding-keys

-   Key type (*choose key-signing key* [KSK])

-   Algorithm (select the appropriate algorithm type from the pop-up menu)

-   Public key (long string with letters and numbers, *not the Digest* hex
    string)

Amazon also has instructions to remove a DS record ([Deleting Public Keys for a
Domain][27]).

[27]: http://docs.aws.amazon.com/Route53/latest/DeveloperGuide/domain-configure-dnssec.html#domain-configure-dnssec-deleting-keys

Amazon Route 53 DNS does not support DNSSEC itself (Amazon Registrar only
supports adding DS records for domains managed by other DNS operators, like
Google Cloud DNS). If you configure your Amazon-registered domain to be served
with DNSSEC by Google Cloud DNS, and you need Route 53 features for particular
subdomains, you can delegate unsigned subdomains (with NS records but no DS
record) to the Amazon Route 53 name servers.

### Ascio

If your domain registrar is [Ascio][28] (via a reseller), there is no web
interface to add a DS record to activate DNSSEC for your domain. If you are the
domain owner, contact your reseller for support. Resellers can use the Ascio AWS
Domains API to add or delete DS records, as documented at
http://aws.ascio.info/domains-api-v2/csharp/creatednsseckey.

[28]: https://icannwiki.org/Ascio

### Chengdu West Dimension Digital

As of October 2017, 西都成码 (Chengdu West Dimension Digital) did not support DS
record management, although it had [one signed zone][29].

[29]: https://ntldstats.com/registrar/1556-Chengdu-West-Dimension-Digital-Technology-Co-Ltd

### CSC Corporate Domains

According to the ICANN DNSSEC [support list][30], [CSC Corporate Domains][31]
supports DNSSEC for these top-level domains: `.com .net org .uk .biz .com.au
.net.au .us .eu .be .se .co`. They do not provide any online documentation about
adding a DS record, but have [40 signed domains][32] in new gTLs. Contact them
for support at http://www.csc.com/contact_us/flxwd/93606.

[30]: http://dnssec-deployment.icann.org/en/dnssec/deploy.htm
[31]: https://icannwiki.org/CSC_Corporate_Domains,_Inc.
[32]: https://ntldstats.com/registrar/299-CSC-Corporate-Domains-Inc

### DNSimple

DNSimple has instructions at
https://blog.dnsimple.com/2015/11/ds-records-for-dnssec/ to add a DS record
and activate DNSSEC for your domain.

To remove DS records, see the instructions at
https://support.dnsimple.com/articles/ds-records-changing-dns/.

### Domain.com

As of October 2017, Domain.com did not support DS record management ([no signed
zones][33] in new gTLDs).

[33]: https://ntldstats.com/registrar/886-Domaincom-LLC

### Domain Discount 24

Domain Discount supports adding and removing DS records through their [web
interface][34]. Follow these steps to add a DS record:

[34]: https://login.domaindiscount24.com/en

1.  Select "All Domains" from the menu on the left.

2.  Select the domain you want from the list.

3.  Select the "Expert Mode" checkbox (just above "Nameserver settings").

4.  Click on "Add DSData record".

5.  Provide the following information:

    -   Key tag

    -   Algorithm (select the appropriate algorithm type from the pop-up menu)

    -   Digest type (select the appropriate digest type from the pop-up menu)

    -   Digest (long hexadecimal string)

You can remove DS records to deactivate DNSSEC for your domain on the same page
by clicking on "Remove record" for each record.

### Dyn

An Internet Society [article][35] has instructions for setting up DNSSEC with
[Dyn][36] (Oracle). Skip the first part about setting up DNSSEC for your zone,
since you have already done that with Google Cloud DNS, and go directly to
"Domain registration" at the Dyn registration [console][37], where you need to
provide the following information:

[35]: http://www.internetsociety.org/deploy360/resources/how-to-sign-your-domain-with-dnssec-using-dyn-inc/
[36]: https://icannwiki.org/Dyn
[37]: https://account.dyn.com/dns/domain-registration/

-   Key tag

-   Algorithm (select the appropriate algorithm type from the pop-up menu)

-   Digest type (select the appropriate digest type from the pop-up menu)

-   Digest (long hexadecimal string)

### DynaDot

[DynaDot][38] has instructions at
https://www.dynadot.com/community/help/question/set-DNSSEC to add a DS record
and activate DNSSEC for your Dynadot-registered domain.

[38]: https://icannwiki.org/DynaDot

### eName

As of October 2017, eName did not support DS record management ([no signed
zones][39] in new gTLDs).

[39]: https://ntldstats.com/registrar/1331-eName-Technology-Co-Ltd

### eNom

If your domain registrar is [eNom][40] but you registered your domain through a
reseller such as [NameCheap](#namecheap) you may be able to manage DNSSEC
through your reseller—check for it in this list of domain registrar-specific
instructions.

[40]: https://icannwiki.org/ENom

If you registered your domain directly with eNom, there is no web interface to
add a DS record to activate DNSSEC for your domain. See the instructions at
http://www.enom.com/helpme/ for directions on submitting a support request or
contacting your reseller. Include the DS record you get from Google Cloud DNS in
your support request, along with your domain name.

Removing DS records to deactivate DNSSEC for your domain also requires you to
submit a support ticket. Include all DS records reported by `dig +noall +answer
+nottl DS ZONE.EXAMPLE` (replacing ZONE.EXAMPLE with your domain) in your
support ticket.

### FastDomain

As of October 2017, FastDomain did not support DS record management.

### Gandi

If your domain is registered with Gandi, but you did so through Amazon (as a
reseller) use the [Amazon instructions](#amazon) instead.

See the instructions at http://wiki.gandi.net/en/domains/dnssec to add a DS
record and activate DNSSEC for your Gandi-registered domain. You need to provide
the following pieces of information:

-   Flag (select "257 - KSK" from the pop-up menu)

-   Algorithm (select the appropriate algorithm type from the pop-up menu)

-   Public key (long string with letters and numbers, *not the Digest* hex
    string)

You can also remove DS records and deactivate DNSSEC from the same DNSSEC
management page.

### GKG

GKG supports adding and removing DS records either through their [web
interface][43] as described in their FAQ
https://www.gkg.net/domain/support/faq/dnssec.html#Anchor-3 or using their API
as documented at https://www.gkg.net/ws/ds.html#create-ds.

[43]: https://www.gkg.net/protected/domain/modify

### GoDaddy

[GoDaddy][44] has instructions at
https://www.godaddy.com/help/add-a-ds-record-23865 to "Add a DS Record" and
activate DNSSEC for a GoDaddy-registered domain. If you have chosen a
non-default DNSSEC algorithm for your zone, GoDaddy may not support it for some
top-level domains.

[44]: https://icannwiki.org/GoDaddy

See the instructions at https://www.godaddy.com/help/delete-a-ds-record-23867
to "Delete a DS Record" and deactivate DNSSEC for a GoDaddy-registered domain.
at the same help URL.

There is general background information on "Self-Managed" DNSSEC with GoDaddy at
https://www.godaddy.com/help/about-self-managed-dnssec-6114.

### HiChina

As of October 2017, [HiChina (Alibaba Cloud Computing)][45] did not support DS
record management, although it had [one signed zone][46].

[45]: https://icannwiki.org/HiChina
[46]: https://ntldstats.com/registrar/1599-Alibaba-Cloud-Computing-Ltd-dba-HiChina-wwwnetcn

### HKDNS

As of October 2017, West263 International (HKDNS.HK) did not support DS record
management ([no signed zones][47] in new gTLDs).

[47]: https://ntldstats.com/registrar/1915-West263-International-Limited

### Hover

See the instructions at
https://help.hover.com/hc/en-us/articles/217281647-DNSSEC#add to add a DS
record and activate DNSSEC for your domain.

To remove DS records, see the instructions at
https://help.hover.com/hc/en-us/articles/217281647#edi.

### InternetX

[InternetX (Domain Robot / PSI-USA)][48] [AutoDNS][49] supports DNSSEC; see its
internal help pages for instructions on activating DNSSEC and then creating or
removing DS records for your domain on the "DNSSEC" tab of the Domain update
page.

[48]: https://icannwiki.org/InterNetX
[49]: https://login.autodns.com/

The procedure requires the Public key (long string of letters and numbers)
rather than the Digest (hexadecimal string).

If you registered your domain through a reseller rather than with AutoDNS, you
need to contact your reseller for support. If you are an InternetX customer,
you can contact domain-support@internetx.com for further assistance.

### InterNetworX

[InterNetworX (INWX)][50] has DNSSEC instructions (in English) at
https://kb.inwx.com/?sid=643491&lang=en&action=artikel&cat=22&id=204&artlang=en
and in German at https://kb.inwx.com/?solution_id=1021.

[50]: https://icannwiki.org/InterNetworX

### Joker

Joker supports adding and removing DS records either through their web interface
described at https://joker.com/faq/content/6/461/en/dnssec-support.html or the
API given at https://joker.com/faq/content/27/24/en/domain_modify.html.

### Key-Systems

[Key-Systems][51] uses [Domain Discount 24](#domain-discount-24) for direct
registration by domain owners, and [RRPproxy](#rrproxy) for resellers. Click
either of the previous two links for specific instructions.

[51]: https://icannwiki.org/Key-Systems

### MelbourneIT

As of October 2017, [MelbourneIT][54] did not document any support for DS record
management, although it had [11 signed zones][55] in new gTLDs. If MelbourneIT
is your domain registrar, try contacting their support at
https://www.melbourneit.com.au/contact-us/ to see if they have a manual
process for adding or removing a DS record.

[54]: https://icannwiki.org/MelbourneIT
[55]: https://ntldstats.com/registrar/13-Melbourne-IT-Ltd

### Moniker

Moniker supports enabling and disabling DNSSEC through its [web interface][56].

[56]: https://login.moniker.com/domain/list/page/1/sort/domain/stype/asc/resetfilter/0/option

Follow these steps through their web interface to modify DNSSEC settings:

1.  Go to the "My Domains" page.

2.  Click on your domain name.

3.  Click on the "Whois / Nameserver" tab and scroll to the bottom.

4.  Unfold the "DNSSEC" section to reveal a toggle switch.

5.  Flip the switch to your desired setting.

A notification appears declaring that it may take up to two days for the changes to complete,
but the task usually finishes within a half hour or so.  Once enabled, a new DNSSEC key can
be generated by simply clicking the "Request Key Rollover" button if needed.

### Name.com

[Name.com][57] has instructions at
https://www.name.com/support/articles/205439058-DNSSEC to navigate to DNSSEC
Management on their [web site][58]. To add a DS record and activate DNSSEC for
your domain, you must provide the Key tag, numeric Algorithm, and Digest Type,
as well as the Digest hexadecimal string.

[57]: https://icannwiki.org/Name.com
[58]: https://www.name.com

You can also remove DS records and deactivate DNSSEC on this page.

### Name ISP

Name ISP supports adding and removing DS records through their [web
interface][59] without any need to copy data.

[59]: https://www.nameisp.com/

Follow these steps through their web interface to add a DS record:

1.  Click on "My Domains".

2.  Click on your domain name.

3.  Click on "DS data", which displays "Keys from nameservers."

4.  Click the "Publish" button to the right of the key you want to publish.

To remove DS records and deactivate DNSSEC, click on the "Remove all" button to
the right of "Published keys."

### Namecheap

Namecheap has instructions at
https://www.namecheap.com/support/knowledgebase/article.aspx/9722/2232/ to add
a DS record once you have enabled Namecheap DNSSEC support.

To remove all DS records, simply disable Namecheap DNSSEC support, as described
at the end of the above instructions.

### NameSilo

NameSilo supports adding and removing DS records through their [web
interface][60]. The instructions at
https://www.namesilo.com/Support/DS-Records-%28DNSSEC%29 explain how to
navigate to the page for adding DS records.

[60]: https://www.namesilo.com/account_domains.php

Enter the required DS record information:

-   Digest (long hexadecimal string)

-   Key tag

-   Digest type (select the appropriate digest type from the pop-up menu)

-   Algorithm (select the appropriate algorithm type from the pop-up menu)

Then click on the "Submit" button.

### Network Solutions

As of October 2017, [Network Solutions][61]’ domain registrar did not support
DNSSEC management for customers using other DNS providers such as Google Cloud
DNS, although it had [5 signed zones][62] in new gTLDs.

[61]: https://icannwiki.org/Network_Solutions
[62]: https://ntldstats.com/registrar/2-Network-Solutions-LLC

### Onamae

Onamae (GMO Internet) has DNSSEC instructions (in Japanese) at
http://www.onamae.com/option/dns/.

### OpenSRS

[OpenSRS][63] has instructions (for "Registrant") at
https://help.opensrs.com/hc/en-us/articles/206190417#add to add a DS record
and activate DNSSEC for your domain. If you do not have a Storefront login,
contact your reseller and refer them to the instructions (for "Reseller") at
https://help.opensrs.com/hc/en-us/articles/206190417#adr (include the DS
record you get from Google Cloud DNS in your request, along with your domain
name).

[63]: https://icannwiki.org/OpenSRS

To remove DS records, see the instructions (for "Registrant") at
https://help.opensrs.com/hc/en-us/articles/206190417#mod. If you do not have a
Storefront login, contact your reseller and refer them to the instructions (for
"Reseller") at https://help.opensrs.com/hc/en-us/articles/206190417#mor.

### OVH

[OVH SAS][64] supports adding and removing DS records either through their [web
interface][65] or their API as documented at
https://api.ovh.com/console/#/domain/%7BserviceName%7D/dsRecord#POST.

[64]: https://icannwiki.org/OVH_SAS
[65]: https://www.ovh.com/managerv3/

Follow these steps through their web interface to get to DS record management:

1.  Log in to the [OVH account manager][66].

2.  Click on your domain name (in the **Domain** tab of the welcome page.

3.  Select "Domains & DNS" from the menu on the left.

4.  Click on the "Secure delegation (DNSSEC)" icon.

5.  Select the "DS Records" tab.

[66]: https://www.ovh.com/managerv3/

Add a DS record to activate DNSSEC by clicking on the **+** icon on the right
and providing the following information:

-   Key tag

-   Flag (select "257 - Key Signing Key" from the pop-up menu)

-   Algorithm (select the appropriate algorithm type from the pop-up menu)

-   Public key (long string with letters and numbers, *not the Digest* hex
    string)

Remove DS records by clicking on the trash can icon to the right of each record.

### Public Domain Registry

Public Domain Registry (PDR) also acts as a registrar and has instructions at
http://manage.publicdomainregistry.com/kb/answer/1909 to add a DS record and
activate DNSSEC for your domain, or to remove DS records and deactivate DNSSEC.

### REG.RU

As of October 2017, REG.RU did not support DS record management ([no signed
zones][67] in new gTLDs).

[67]: https://ntldstats.com/registrar/1606-Limited-Liability-Company-Registrar-of-domain-names-REGRU

### Register.com

As of October 2017, [Register.com][68] did not support DNSSEC management for
customers using other DNS providers such as Google Cloud DNS and had [no signed
zones][69] in new gTLDs.

[68]: https://icannwiki.org/Register.com
[69]: https://ntldstats.com/registrar/9-registercom-Inc

### Registro.br

Registro.br supports adding and removing DS records through their [web
interface][70]. They have general information about DNSSEC configuration (in
Portuguese) at http://registro.br/tecnologia/dnssec.html.

[70]: https://registro.br/cgi-bin/nicbr/login

Follow these steps through their web interface to add a DS record:

1.  Navigate to the "Domínios" page.

2.  Click on your domain name.

3.  Click on "Alterar Servidores DNS" (Change DNS Servers).

4.  Click on the "+ DNSSEC" button to display fields for DS 1 and DS 2 (if they
    are not already present).

5.  Enter the required information:

    -   Key tag

    -   Digest (long hexadecimal string)

6.  Click on the "Salvar Dados" (Save Data) button.

The configured Master and Slave name servers are queried for DNSKEY records
and if one with a matching key tag and digest is found, the DS record is
generated and published.

### RRPproxy

If your domain registrar is [RRPproxy][71] (via a reseller), there is no web
interface to add a DS record to activate DNSSEC for your domain. If you are the
domain owner, contact your reseller for support. Resellers can use EPP or the
RRPproxy API to add or delete DS records, as documented at
https://wiki.rrpproxy.net/DNSSEC.

[71]: https://icannwiki.org/RRPproxy

### Todaynic

As of October 2017, Todaynic (时代互联) did not support DS record management ([no
signed zones][72] in new gTLDs).

[72]: https://ntldstats.com/registrar/697-Todayniccom-Inc

### TransIP

TransIP has instructions at https://www.transip.eu/question/110000694/ for
adding a DS record to activate DNSSEC for your domain.

### Tucows

[Tucows][73] uses [Hover](#hover) for direct registration by domain owners, and
[OpenSRS](#opensrs) for resellers. Click either of the previous two links for specific
instructions.

[73]: https://icannwiki.org/Tucows

### Uniregistrar

As of October 2017, [Uniregistrar][76] did not support DS record management ([no
signed zones][77] in new gTLDs).

[76]: https://icannwiki.org/Uniregistry
[77]: https://ntldstats.com/registrar/1659-Uniregistrar-Corp

### United Domains

If your domain registrar is [United Domains AG (UDAG)][78], there is no web
interface to add a DS record to activate DNSSEC for your domain. See the
instructions at https://www.uniteddomains.com/support/contact/ to request
the creation of a DS record for your domain. Include the DS record you get from
Google Cloud DNS in your request, along with your domain name.

[78]: https://icannwiki.org/United_Domains

Removing DS records to deactivate DNSSEC for your domain also requires you to
submit a request. Include all DS records reported by `dig +noall +answer +nottl
DS $ZONE` (setting ZONE to your domain) in your support ticket.

### Wild West Domains

For any domain reseller that uses the Wild West Domains registrar, follow the
instructions for [GoDaddy](#godaddy) using your account with your domain reseller in
place of a GoDaddy account.

### Xin Net

As of October 2017, Xin Net (新网) did not support DS record management ([no
signed zones][80]).

[80]: https://ntldstats.com/registrar/120-Xin-Net-Technology-Corporation
