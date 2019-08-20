---
title: Real-Time Bidder Solution for Google Cloud Platform
description: This paper presents a pair of solutions that can be used as references for building and deploying multi-region, real-time bidders on Google Cloud Platform.
author: jimtravis
tags: Compute Engine, App Engine, Cloud Storage, BigQuery, Prediction API, OpenBidder
date_published: 2014-09-01
---

Real-time bidding (RTB) is a server-to-server integration option for network ad
buyers that allows networks to evaluate and bid on an impression by impression
basis. It enables consolidated buying-and-measurement and real-time algorithmic
optimization in a
[transparent, directly accessible platform](http://static.googleusercontent.com/external_content/untrusted_dlcp/www.google.com/en/us/doubleclick/pdfs/consolidated-buying-platform.pdf). Technology innovation
by ad exchanges, demand-side platforms, and supply-side platforms has driven the
uptick in adoption of RTB but has also created barriers through technical complexity.

Real-time bidding applications, or _bidders_, are non-trivial, global distributed
systems that must be highly available, scalable, and predictable. Typically,
a bidder must respond to an exchange request within
[100 milliseconds](https://developers.google.com/ad-exchange/rtb/test-guide#gtraffic)
and this single constraint influences key decisions everywhere along the
bidder’s technology stack, from the physical infrastructure to the
implementation of bid logic. Ad exchanges offer RTB in multiple regions and
bidders that are physically closer to the exchange servers will observe lower
round-trip latencies, providing additional time for executing sophisticated
bidding logic.

This paper presents a pair of solutions that can be used as references for
building and deploying multi-region, real-time bidders on
Google Cloud Platform. The solution uses the following products and services:

+  [Google Compute Engine](https://cloud.google.com/compute/docs)
    +  Bidders will experience no latency in responding to bid requests from
        Google Ad Exchange, giving them a full 100ms to compute their response.
    +  Bidders run in standard Cloud Platform availability zones that
        support the use of other Google services such as data
        analytics to maximize profits.
    +  Bidders can take advantage of high-performance virtual machines and
        networks to handle more bid requests with fewer instances.
+  [Google Open Bidder](https://developers.google.com/ad-exchange/rtb/open-bidder/)
    +  A framework for implementing bidders that offers an API for easy
       extensibility and a user interface for configuring and maintaining
       bidders and load balancers.
+  [DoubleClick Ad Exchange Hosted Match Tables](https://developers.google.com/ad-exchange/rtb/cookie-guide)
    +  Reduce infrastructure footprint and eliminate additional calls in the
        request pipeline.
    +  Enable pre-targeting filtering and accurate reporting of table sizes and
        match rates.
+  [Google App Engine](https://cloud.google.com/appengine/docs)
    +  Host administrative, campaign management, and client-facing web
        applications that are fully connected with other Google services without operational overhead.
+  [Google Cloud Storage](https://cloud.google.com/storage/docs)
    +  Store server logs and analysis artifacts.
    +  Serve ad payloads taking advantage of Google’s low-latency, edge-caching
        global network.
    +  Preserve disk snapshots and database backups for zone migration and
        disaster recovery.
+  [Google BigQuery](https://cloud.google.com/bigquery/docs) and [Prediction API](https://cloud.google.com/prediction/)
    +  Analyze server logs and exchange reports for tuning the bid model and generating reports and
        dashboards.

Alternative components include:

+  [Google Cloud Datastore](https://cloud.google.com/datastore/docs) and
   [Google Cloud SQL](https://cloud.google.com/sql/docs)
    +  Store bid model, campaigns, and user tracking data.
+  Third-party databases
    +  Preserve existing implementation and expertise and run MySQL, PostgreSQL, Cassandra, or other databases on Compute Engine.

This paper is intended for systems architects, developers, and technical
decision-makers already familiar with RTB and its concepts.


## Overview

This section covers the key functional components of a multi-region RTB bidder
and outlines two solutions for building and deploying on Cloud Platform.
The differences between the two are in the choice of database, the manner in
which bid servers access certain data, and the mechanisms used for cross-region
synchronization. One solution uses techniques common in today’s cloud-based
bidders. The second offers a contrasting set of architectural choices that
aren’t typically considered possible but that become plausible when building
on Google’s infrastructure.

### Functional components

The solutions proposed in this paper are developed around a set of high-level
functional areas common to most, if not all, bidders that are designed for deployment
across availability zones in multiple geographic regions. This section provides
an overview of these components and their implementation on Google Cloud
Platform products and services.

![Functional Components of a Real-Time Bidder](https://storage.googleapis.com/gcp-community/tutorials/real-time-bidder/real-time-bidder-solution-for-google-cloud-platform_image_0.png)

**Figure 1**: _Functional components of a real-time bidder_

#### Bidding components

The core bidder components are those that handle bid and pixel requests, and are involved in storing and serving data as fast as possible to these handlers. These components include the load balancers, bid and pixel servers, usually a distributed key-value store, and, in some cases, the database itself.

Exchanges impose strict deadlines, typically 100ms, within
which the system must respond. DoubleClick Ad Exchange (AdX)
uses a 100ms limit. Bidders that exceed the response deadline have fewer
opportunities and less time to respond.  AdX also throttles traffic to
bidders with error rates higher than 15% so overloaded bidders can stabilize; other exchanges may not. Therefore
it is important to have excellent network connectivity to the exchange servers,
predictable execution characteristics, and a scalable architecture.
Additionally, publishers will favor buyer platforms with low latency responses
to user browser requests, such as pixel handling and ad payloads, so it is
also important that bidders have fast, reliable connectivity to the Internet.

Bidder core components are deployed on Compute Engine, which
provides a great experience for hosting bidding logic for the DoubleClick Ad
Exchange or other exchanges. Compute Engine
enables bidders to run virtual machines in multiple availability zones.
It allows bidders to take advantage of Google’s global network for its high
bandwidth and low latency connectivity among VMs and to other Cloud
Platform services.

##### Frontends

[Compute Engine Load Balancing](https://cloud.google.com/compute/docs/load-balancing/) or
software load balancers (such as [HAProxy](http://haproxy.1wt.eu/)
and [Nginx](http://wiki.nginx.org/HttpUpstreamModule))
running on Compute Engine virtual machines handle all request traffic from
exchanges and user browsers. Load balancing is particularly important for
maximizing aggregate effectiveness of the bidder and minimizing error
rates and request pressure on individual bid servers.

##### Backends

Frontend load balancers route traffic to backend bid servers that execute the
platform’s custom bidding logic. Each exchange request is evaluated against
the proprietary bid model, set of active campaigns, information the bidder
holds about the user, and other data points.

Pixel servers handle tracking, impression, click-through, and conversion
requests directly from the user’s browser and may perform additional
fraud detection. This paper includes, in its use of the term _pixel servers_,
those additional nodes that perform the specific processing that
results from these requests, such as updating data stores, campaign budgets,
user cookies, and tracking information.

Running on Compute Engine means that you are free to
choose your own server technology stack and stand-up existing solutions with
few or no modifications. However, developing a new bidder is a non-trivial task
and it can be advantageous to leverage a framework that provides an easy way
to configure and manage server instances, along with much of the necessary
boilerplate server code to accelerate the development of custom logic.

Open Bidder is an RTB framework that can speed up the development of scalable,
custom bidding applications. Open Bidder works on Compute Engine and is
comprised of three components:

+  **A User Interface** (deployed as a Google App Engine application) &mdash; for importing campaigns, displaying operational metrics, and managing various
system components, including Compute Engine networks and firewalls, server
instances, and load balancers.
+  **An API for Java** &mdash; for extending Open Bidder’s functionality with custom interceptors that implement bidding, impression, and click-through logic. It also provides support for cross-exchange bidding through dependency injection.
+  **A Server** &mdash; for receiving bid, impression, and click-through requests, and executing custom interceptors.

##### Distributed stores

Many bidders rely on distributed key-value stores like
[Memcached](http://memcached.org),
[Redis](http://redis.io) and
[Voldemort](https://github.com/voldemort/voldemort)
for low latency access to
data such as match tables and cookie stores that are consulted on every bid
request, so they must be as fast as possible to avoid adversely
impacting the bidding engine. Some bidders use a non-persistent store for
recording information related to its bid offers for later reconciliation
against the corresponding impression won. This technique can be used, for
example, to update cross-exchange campaigns, and refine bidding behavior
on-the-fly.

Match tables are used to maintain a mapping of exchange-specific user
identifiers to a cookie that identifies the user within the buyer’s domain.
The cookie is then used as a key for the user information accumulated by the
bidder, which is considered when making bidding decisions about the user. This
can be useful when creating
[remarketing](https://support.google.com/adxbuyer/bin/answer.py?answer=166635)
campaigns, refining targeting, and adjusting bid decisions on impressions as
they become available in real time. User data can be left entirely
transient in the distributed key-value store or kept more permanently in a
database. The decision largely reflects the developer’s tolerance
for data loss. Some platforms favor a simple design and rebuild lost
information; others opt for durability. A product like Redis, which can
serve requests from memory-only on the master node and perform persistence
on the slave node, is a popular choice for a blended approach.

Compute Engine offers a high performance, scalable, and efficient
infrastructure upon which you can deploy distributed key-value stores.
Additionally, Google offers a Hosted Match Table service for DoubleClick
Ad Exchange customers that provides the following benefits:

+  **Less infrastructure** to support if the key-value store is only needed for
    match tables.
+  **Better reporting** of table size and match rates.
+  **Elimination of lookups** by mapping the Google User ID to a more useful
    form in bid requests.
+  **Enabling of pre-targeting filtering** based on the existence of the cookie.

#### Data management

The bidder database stores everything from the trained bidding model, campaign
data (active and historical), and exchange-specific data sets (such as categories, labels, agencies, vendors), to transient bid stores and event logs. Different bidder architectures rely on the database in different ways. This paper presents two alternative approaches centered around data access and
replication strategies.

Each reference architecture employs additional _proxy_ nodes for
brokering and handling data events between the database and other components.

#### Analysis and modeling

Analysis and modeling components make up the other segment of the platform’s
data stack. Bidding platforms generate large volumes of log data that can offer
vital insight into the performance of systems, and the effectiveness of bidding
and fraud detection algorithms. They also provide critical input to
model training and tuning.

You can use BigQuery to aggregate, transform, and analyze server logs and
exchange reports. You can access BigQuery interactively or programmatically, and its output can be used immediately as actionable insight or as a stage in a more advanced intelligence pipeline.

Compute Engine is a great platform on which to run Hadoop. MapR, a
Google technology partner, has set world-records in both the
[TeraSort](http://www.mapr.com/company/press-releases/mapr-and-google-compute-engine-set-new-world-record-for-hadoop-terasort)
and [MinuteSort](http://www.mapr.com/blog/hadoop-minutesort-record)
benchmarks
using Google’s virtualized infrastructure. Adding this stage to the data
pipeline, especially with the ability to source data from Cloud Storage
and Cloud Datastore, as well as third-party database clusters, increases the
breadth and depth of the analysis that you can do.

Finally, advanced bidding platforms could develop and refine models by taking
advantage of Google’s Prediction API, a unique service offering that opens up
the power of Google’s machine learning algorithms.

#### Campaign management

The App Engine platform hosts the campaign management application and
other client-facing features, such as reporting and dashboards. App Engine offers
a highly scalable and secure environment that allows you to focus on
building domain-specific tools and not managing infrastructure. App Engine
works directly with Cloud Storage, Cloud SQL, and Cloud Datastore,
enabling seamless integration with the bidder’s data. Task Queues and Sockets
API can be used to facilitate communication to custom databases hosted in
Compute Engine.

#### Storage

Cloud Storage is used for storing and staging log files, intermediate
and final results from BigQuery, MapReduce and Prediction API. Other solutions
can take advantage of the global edge caching as well as the ability to host
data local to either U.S. or Europe for serving static ad content.
[Nearline and Coldline Storage](https://cloud.google.com/storage/docs/storage-classes)
are ideal for third-party database backups and disaster recovery.

### Managed database solution

This solution leverages a highly available and scalable database service fully
managed by Google and the reduced operational overhead that comes with it.
Either Google Cloud Datastore or Cloud SQL, or possibly both, can be
used&mdash;the choice is driven by the nature of the data schema and
application usage semantics. Cloud Datastore is a NoSQL data solution, built
on Google’s [Megastore](http://research.google.com/pubs/pub36971.html),
and offers massive scalability, high availability, and strong write consistency.
It is accessible from many other Google Cloud Platform services, including App
Engine and Compute Engine, and can be used with hosted MapReduce and other
data pipelines, as well as with the Search API for full-text and
location-based searches. Cloud SQL is a secure, fully managed, highly
available MySQL service with built-in, automatic
replication across geographic regions.

#### Reference architecture

![Real-Time Bidder (Managed Database) Architecture](https://storage.googleapis.com/gcp-community/tutorials/real-time-bidder/real-time-bidder-solution-for-google-cloud-platform_image_1.png)

 **Figure 2**: _Real-time bidder (managed database) architecture_

#### Implementation details

One common practice among bidders is loading campaign data such as inventory,
budgets, and preferences, from the database onto the bid servers
during initialization. Having this data accessible directly in the server’s
process space can eliminate extra network calls and the overhead associated
with transferring non-trivial payload on every bid request. This solution
implements such a design. Additionally, a distributed key-value store is used
for non-persistent storage of recent bid data, user information, and a match
table for those exchanges that don’t support hosting.

This solution also makes use of a distributing messaging system to broadcast
relevant events across regions so that the data stores are synchronized and
bid servers are kept up-to-date. Additional servers are used to proxy data
between the core backend components and the managed database. These servers
also enable communication to flow back into the messaging system from the App
Engine application in case, for example, you might want to create a new
campaign or to satisfy a client’s retargeting request.

  ![Managed Database Solution Walkthrough](https://storage.googleapis.com/gcp-community/tutorials/real-time-bidder/real-time-bidder-solution-for-google-cloud-platform_image_2.png)

**Figure 3**: _Managed database solution walkthrough_

##### Diagram walkthrough

###### Bootstrapping

**A1.** Bid servers load campaigns and trained model data for the bid engine.
The data proxy servers manage the query and collation of results from the
managed database(s).

###### Exchange bid requests

**B1.** User browser or device requests an ad placement from Google
DoubleClick or another ad exchange.

**B2.** The exchange checks the bidder pre-targeting (including filtering
based on cookie match, if applicable) and sends a request to the bidder.
The request is then routed to one of the load balancers, and may contain
the domain-specific user cookie which was obtained from the hosted match
table.

**B3.** The load balancer routes the request to a bid server based on the
configured strategy such as least connections, least load, consistent hash,
and round-robin.

**B4.** The bid server uses the cookie to retrieve information about the
user from the cookie store. If the request is not coming from an exchange
that hosts match tables, the bidder’s match table is used to obtain the
domain cookie from the user’s exchange identifier. If the bid engine decides
to bid for the placement, it responds to the exchange and then stores bid information such as
original request, decision indicators, or offer price in the bid store.

**B5.** Ad payloads can be served directly from Cloud Storage.

###### User browser requests

**C1.** User actions trigger requests from their browser directly to the bidder. Requests are handled by the load balancers and include tracking pixels, impressions,
click-through, and conversions.

**C2.** An appropriate pixel server receives the request from the load balancer.

**C3.** The pixel servers match the request against its entry in the bid store
correlating to the ad impression.

**C4.** After processing the request, the pixel server uses the messaging
system to broadcast various update events including, for instance, updates for
budgets based on bids won, user information, and campaign data. Certain types
of events are batched to lessen pressure on the message system and prevent overloading the receivers with high frequency interruptions.

**C5.** The messaging system relays the events across all regions.

**C6.** The bid servers receive budget updates and other events relevant to the
bidding process. This allows the bidder to quickly discard campaigns that
complete, as well as adapt to, real-time data feedback.

**C7.** The data proxy servers receive user information update events, as well
as those related to campaign and budget data.

**C8.** The data proxy servers update the cookie store.

**C9.** The data proxy servers update the database. This optional communication
flow can be accessed to provide real-time updates for visualization. It’s more
common that offline processing will update the data store periodically, which
could reduce I/O and overall cost.

###### Client workflow

**D1.** The platform’s clients access the campaign management tools, view
dashboards, and obtain reports through the web application running on Google App Engine. The bidder may also expose a REST API for some of these features.

**D2.** New campaign creatives and ads are uploaded to Cloud Storage
either directly or through the campaign management application.

**D3.** The application will compose reports with data generated via the data
processing pipeline and stored in Cloud Storage. Additionally,
performance and status reports from DoubleClick can be retrieved and made
available for client download if desired.

**D4.** As clients create new campaigns, perform remarketing and other related
activities, the web application accesses the database directly from App Engine.

**D5.** After storing the new information in the database, tasks carrying these
changes are queued for delivery to the data proxy servers. While it is now
possible to create outbound sockets from App Engine via the Sockets API, a
solution designed to enable point-to-point communication to data proxy servers
across all regions is fragile. This solution recommends using App Engine Task
Queues, one per region, to hold these tasks.

**D6.** Data proxy servers in each region poll for data update tasks independently from servers located in
other regions. The fault-tolerant approach requires
the proxy node to query the queue for its region. No task is delivered more
than once, and should a server go down, the updates will continue to flow
into the backends.

**D7.** Updates to user information and retargeting being the canonical
example, are both made by the data proxy on the cookie store.

**D8.** Campaign updates and other tasks related to the bidding process are
fired into the messaging system. These events must be sent along channels
that are not relayed across regions. This design can easily be modified by
relaxing the previous constraint and using a single task queue (instead of
four as recommended in step D5).

**D9.** Bid servers receive the new campaign and related messages and update
their internal data structures.

###### Analysis workflow

**E1.** Frontend and backend server logs are pushed directly by using an optional aggregation subsystem into Cloud Storage.

**E2.** DoubleClick stores performance and status reports in Cloud
Storage on an hourly basis.

**E3.** BigQuery and a data processing solution like Hadoop running
on Compute Engine are used to aggregate, transform, and process server logs.

**E4.** Some platforms use the BigQuery API to generate dashboards and
reports.

**E5.** Bidders that use machine-learning techniques for optimizing bidding
logic and fraudulent request detection, for instance, can take advantage of
the data processing pipeline to generate input for the Prediction API and feed results back into the database.

### Third-Party database solution

This solution offers an alternative approach to the previous one, relying on a
self-managed, distributed database instead of a hosted service. This
architecture forgoes the use of the distributed key-value store and messaging
subsystems as well, leveraging the capabilities of the database system and
the performance of Google infrastructure to support the design.

#### Reference architecture

![Real-Time Bidder (Third-Party Database) Architecture](https://storage.googleapis.com/gcp-community/tutorials/real-time-bidder/real-time-bidder-solution-for-google-cloud-platform_image_3.png)

**Figure 4**: _Real-time bidder (third-party database) architecture_

#### Implementation details

The previous solution demonstrated the practice of preloading from the database
into the bid servers. While effective in many cases, it is a limiting design.
For one, given that every bid server must be the same, the total amount of data
that is available for consideration (number of campaigns, amount of inventory,
exchange-provided data sets, targeting and preferences, for example) is
constrained by the memory capacity of the virtual machines. Further,
non-trivial querying must be supported by either custom code and data
structures or an embedded database. The design also introduces the burden
of explicit synchronization across many individual nodes. The additional
messaging and non-persistent storage subsystem contribute to an increase in
the total complexity in design, development and management of the bidder.

Modern distributed databases, such as
[Apache Cassandra](http://cassandra.apache.org),
running on Cloud Platform are capable of satisfying the performance
requirements of many bidders. In particular, the databases:

+  Take advantage of high memory, multi-core virtual machines for optimal
    performance and resource utilization.
+  Support configurations that span datacenters and asynchronous replication
    among them.
+  Offer a masterless architecture that eliminates single points of failure and
    blocking writes.
+  Support various read consistency options, allowing the bidder to be tuned as
    desired.
+  Scale nearly linearly as clusters are expanded.
+  Use immutable on-disk representations that enable simple yet robust backup
    schemes without loss of data integrity.
+  Often offer native integration with Hadoop.

Cloud Platform provides:

+  Numerous virtual machine [configurations](https://cloud.google.com/compute/docs/pricing#machinetype) to suit the systems requirements.
+  High-performance local and persistent disks with transparent at-rest
    encryption for data security.
+  High-bandwidth, low-latency networking that can support synchronous
    multi-zone writes within the same region.
+  A global fiber network that helps ensure asynchronous writes across
    regions are optimally routed.

This solution presents an architecture that calls for two multi-region
clusters, one for bid data, which was preloaded in the previous solution,
and one for user data, which was kept in the key-value store in the previous
solution. This approach affords partitioning of database I/O better
correlated to usage.
[Solving Big Data Challenges for Enterprise Application
Performance Management](http://vldb.org/pvldb/vol5/p1724_tilmannrabl_vldb2012.pdf)
may be helpful in providing some background on latency and throughput
scalability characteristics of different third-party systems.

![Third-Party Database Solution Walkthrough](https://storage.googleapis.com/gcp-community/tutorials/real-time-bidder/real-time-bidder-solution-for-google-cloud-platform_image_4.png)

**Figure 5**: _Third-party database solution walkthrough_

##### Diagram walkthrough

This walkthrough highlights only the differences compared to the managed solution.

###### Bootstrapping

**A1.** Bid servers load only the trained model data for the bid engine.

###### Bid request

**B4.** The bid server queries the user database for user information indexed
by the domain cookie, and the bid database for all matching campaigns and
inventory.

###### User browser requests

**C5.** The previous solution used a message bus to facilitate
replication across regions. In this solution, the database performs its own
asynchronous replication across datacenters.

_Figure 3 steps_ C6-9 _are not applicable in this solution._

###### Client workflow

**D7.** Updates to user information, retargeting being the canonical example,
are made by the data proxy on the user database.

**D8.** Campaign updates and other tasks related to the bidding process are
made by the data proxy on the bid database.

_Figure 3 steps D4, D9 are not applicable in this solution._

###### Analysis workflow

**E6.** For those databases that support it, the Hadoop cluster can be
integrated to work with active and historical data directly.

###### Backup and disaster recovery

**F1.** The persistent disks used for database servers can be periodically
snapshotted into Cloud Storage. Additionally, files and logs for
incremental backups and snapshots of the database can be archived and stored
in Nearline or Coldline Storage.

## Conclusion

Real-time bidders are complex distributed systems that have very specific
performance and availability requirements. Cloud Platform offers the
performance, consistency, scale, and reliability at the infrastructure and
product levels on which demand-side platforms can count to build rock-solid
bidding solutions.

## References

1.  [Navigating The Road To The Consolidated Buying Platform](http://static.googleusercontent.com/external_content/untrusted_dlcp/www.google.com/en/us/doubleclick/pdfs/consolidated-buying-platform.pdf),
by Forrester Consulting, January 2013.
2.  [Real-Time Bidding to Take Ever-Bigger Slice of Display Pie](http://www.emarketer.com/Article/Real-Time-Bidding-Take-Ever-Bigger-Slice-of-Display-Pie/1009484#vQAiDfjoTiA5BQDL.99),
by eMarketer.com, posted on November 15, 2012.

## Appendix I &mdash; Best practices

Consider the following best practices for all Google DoubleClick
Ad Exchange bidders, though they may apply equally well for other exchanges.
Please refer to the DoubleClick Ad Exchange RTB
[best practices guide](https://developers.google.com/ad-exchange/rtb/practices-guide)
for additional details and recommendations.

### Take advantage of the Exchange APIs

+  **Set accurate QPS quota **to avoid overloading the bidder and being
    throttled for excessive errors. Not responding to a bid request in a timely
    manner is an error. Set a QPS maximum that is slightly under the capacity
    limit of the bidder to account for unforeseen spikes and bidder node failures.
+  **Upload creative materials ahead of time whenever possible** to expedite approval.
+  **Monitor and analyze performance data that is provided by the exchange.**
    Current and historical performance data is available programmatically through
    the [Performance REST API](https://developers.google.com/ad-exchange/buyer-rest/),
    or through the AdX UI. You can also download and analyze reports that are made
    available on an hourly basis in Cloud Storage. The performance data
    includes various QPS and latency metrics grouped by trading location and are
    useful for correlating timed-out and erroneous responses with your logs.
    Likewise, it’s valuable to see how Google’s servers perceive the round trip
    latency of your bidder. Understanding how DoubleClick Ad Exchange measures
    your bidder is an important tool for debugging performance issues and
    improving overall system quality. In addition, the
    [Creatives REST API](https://developers.google.com/ad-exchange/buyer-rest/creative-guide)
    and snippet status reports can be used to determine whether creative materials have been
    approved, and help debug serving problems. Please refer to the
    [reporting guide](https://developers.google.com/ad-exchange/rtb/report-guide)
    for more details about the offline reports.
+  **Pre-target whenever possible** to reduce traffic and processing loads,
    and maximize actionable callouts.
+  **Use hosted match tables** to provide an additional level of filtering to
    reduce unwanted bid requests and eliminate additional overhead in request
    handling.

### Networking configuration

+  **DNS - Keep it Simple** and avoid the use of "smart" DNS services that use
    tricks, very short TTL settings or geo- or latency-based switching.
    Exchange-side DNS caching and pooling can conflict with these options,
    with side-effects manifesting as thundering herds, starvation, and
    unbalanced, unpredictable traffic patterns. Use a standard DNS service
    and static IP addresses.
+  **Enable Keep-Alive and long-lived connections in load balancers and bid servers** to avoid unnecessary overhead and reduce network round-trips
    associated with establishing new connections. An idle timeout of two
    minutes is recommended. Confirm that the bidder is not closing connections
    needlessly, for example, when returning "no bid" responses.
+  **Do not hash source IP**, as bidder frontends will receive traffic from a
    small number of IP addresses. Instead, use an input that will exhibit a high
    degree of variance such as cookies or URL parameters.

### Server configuration

+  **Tune servers** by maximizing requests per connection and raising the
    limit on the number of connections to the highest value your RAM can
    accommodate. As an example, for Apache prefork MPM, MaxClients should be
    set to roughly the number of processes that can fit into RAM after
    accounting for the OS and other resident processes. Keep memory-to-disk
    swapping off on your bidder machines, since it will cause the bidder
    processes to time out. Always perform load testing to determine the query
    pressure at which your processes start to run out of memory and/or servers
    begin to queue requests.
+  **Understand what the settings in the load balancers and web servers mean**
    and set them appropriately since default values for typical web sites and
    applications are almost always inappropriate for RTB servers. For example,
    most web servers expect to handle requests from numerous clients at
    relatively low (or bursty) rates, whereas RTB bidder frontends have to
    handle sustained high rate request traffic from a very small number of
    clients.
+  **Send small bid responses** as anything over 8KB will be considered an
    error and dropped (possibly causing reduction of QPS quota).
+  **Enable GZIP compression** to reduce the amount of payload sent across
    the API.
+  **Handle overload gracefully** by returning errors or no-bid responses when
    pressure and latencies exceed the server's ability to respond in time. The
    first strategy enables Google to throttle traffic to the bidder, which
    allows it to recover immediately when load drops to expected levels. The
    second strategy achieves the same goal as the first by reducing the
    number of bid requests that get processed, with the difference that
    overload must be absorbed by the bidder.
+  **Respond to ping requests that Google sends** to measure bidder status,
    connection close behavior, latency, and more. Do not close connections
    after responding to a ping request.

### System design

+  **Cross-region communication isn’t free, so be smart about shaping this traffic.** Understand how chatty different systems, such as a message bus
    or database, are and create a cost model.
+  **Batch events and messages into single broadcasts or API calls whenever possible.** For example, campaign budgets can be updated once per minute
    rather than on every impression event. Likewise, identify where message
    payload compression will not impact response times and use it to expedite
    processing and reduce costs. Finally, pay attention to communication and
    call failures: don’t assume every message gets delivered and every call
    succeeds. Use randomized exponential backoff retry behavior to prevent
    flooding your receiver and overburdening the sender.
