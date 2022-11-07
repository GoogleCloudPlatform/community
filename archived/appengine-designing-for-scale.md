---
title: Designing for scale on App Engine standard environment
description: Learn some best practices to ensure that your app will scale to high load on App Engine standard environment.
author: jmdobry
tags: App Engine
date_published: 2017-01-27
---

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

App Engine is a scalable system that automatically adds more capacity as
workloads increase.

Here are some best practices to ensure that your app will scale to high load.

## Run load tests

If you are expecting high traffic, we strongly recommend that you run load tests
to reduce the risk of hitting a bottleneck in your code or in App Engine.

Your tests should be designed to simulate real world traffic as closely as
possible. You should test at the maximum load that you expect to encounter. In
order to accurately assess demand, you can run a 1% test to determine how much
traffic will flow to your new service.

In addition, some applications will get a sudden increase in load, and you will
need to predict the rate of increase. If you are expecting spikey load, you
should also test how your application performs when traffic suddenly increases.

We also recommend that you test under various scenarios. For example, what
happens if your application moves to a new datacenter, causing a Memcache flush
and all instances to be stopped and restarted? In the Google Cloud Console, you
can [flush Memcache and stop all instances][flush_memcache] to simulate this.

[flush_memcache]: https://console.cloud.google.com/appengine/memcache

See [Netflix Chaos Monkey][chaos_monkey] for a description of this type of
testing.

[chaos_monkey]: http://techblog.netflix.com/2012/07/chaos-monkey-released-into-wild.html

In addition to measuring performance during load tests, you should also measure
the [increase in costs as the number of users of your service increases](#understand-how-costs-change-as usage-of-your-service-increases).

You should allow sufficient time in your schedule to resolve problems that might
arise in load testing.

## A single entity group in the Datastore should not be updated too rapidly

If you are using the Datastore, Google recommends that you design your
application so that it will [not need to update an entity group more than once per second for a sustained period of time][errors]. Remember that an entity with no parent and no children
is its own entity group. If you update an entity group too rapidly then your
Datastore writes will have higher latency, timeouts, and other types of error.
This is known as contention.

[errors]: https://cloud.google.com/appengine/articles/handling_datastore_errors

Datastore write rates to a single entity group can exceed the one per second
limit so load tests might not show this problem.

## Avoid high write rates to Datastore keys that are lexicographically close

The Datastore is built on top of Google’s NoSQL database, [Bigtable][bigtable],
and is subject to Bigtable's performance characteristics. Bigtable scales by
sharding rows onto separate tablet servers, and these rows are lexicographically
ordered by key. If you are using the Datastore, you can get slow writes due to a
hot tablet server if you have a write rate to a small range of keys that exceeds
the capacity of a single tablet server.

[bigtable]: https://research.google.com/archive/bigtable.html

By default, App Engine allocates keys using a scattered algorithm. Thus you will
not normally encounter this problem if you create new entities at a high write
rate using the default ID allocation policy. There are some corner cases where
you can hit this problem:

* If you create new entities at a very high rate using the legacy sequential ID
  allocation policy.

* If you create new entities at a very high rate and you are allocating your own
  IDs which are monotonically increasing.

* If you create new entities at a very high rate for a kind which previously had
  very few existing entities. Bigtable will start off with all entities on the
  same tablet server and will take some time to split the range of keys onto
  separate tablet servers.

* You will also see this problem if you create new entities at a high rate with
  a monotonically increasing indexed property like a timestamp, because these
  properties are the keys for rows in the index tables in Bigtable.

## Do not set a spending limit that could be exceeded

You can [configure a daily spending limit][billing] for your application if you
are paying online. You can [view the spending limit][settings] in the Cloud
Console. Your application will serve errors if your spending limit is exceeded,
so ensure that your limit is sufficient to handle the maximum possible daily
usage. You should not wait until the last minute to try to increase your
spending limit, because Google needs an approval from your credit card issuer.
If there are problems getting this approval then your spending limit increase
will be delayed.

[billing]: https://cloud.google.com/appengine/docs/python/console#billing
[settings]: https://console.cloud.google.com/appengine/settings

## Ensure that you will not hit quota limits on API calls

Some API calls have per-minute and per-day quota limits in order to prevent a
single application from using up more than its share of available resources. In
the Cloud Console, you can [view your quota details][quotas] for all API calls.
You will get a quota denied error if you exceed quota limits.

[quotas]: https://console.cloud.google.com/project/_/appengine/quotas

APIs that are not yet generally available are usually subject to strict quota
limits. You can visit the [App Engine features page][standard_env] to find out
which APIs are generally available, and which are still in preview or
experimental stages.

[standard_env]: https://cloud.google.com/appengine/docs/about-the-standard-environment

In addition, there are some APIs that have relatively strict quotas, despite
being generally available. APIs in this category include [URL Fetch][urlfetch],
[Sockets][sockets], and [Channels][channels]. If you are using these APIs, you
should pay particular attention to quota limits.

[urlfetch]: https://cloud.google.com/appengine/docs/about-the-standard-environment#urlfetch
[sockets]: https://cloud.google.com/appengine/docs/about-the-standard-environment#sockets
[channels]: https://cloud.google.com/appengine/docs/about-the-standard-environment#channel

The per-minute quota limits are not shown in the Cloud Console. Your application
will not hit a per-minute quota unless you have an unexpected usage pattern.
Load testing can be used to determine whether you would hit a per-minute quota
limit.

## Shard task queues if high throughput is needed

You can shard task queues if you want higher throughput than is possible with a
single queue. You can use the same principles described in the
[sharding counters article][counters] to do this. Your application should not
depend on tasks executing immediately after creation so that you can handle a
short term backlog in the task queues without affecting the experience of your
end users.

[counters]: https://cloud.google.com/appengine/articles/sharding_counters

## Use the default performance settings unless you have tested the impact of changes

We recommend that you use the default settings for [automatic scaling][auto_scaling]
for max idle instances and min/max pending latency on automatic unless you have
done load testing with other settings to verify their effects. The default
performance settings will, in most cases, enable the lowest possible latency. A
trade-off for low latency is usually higher costs due to having additional idle
instances that can handle temporary spikes in load.

[auto_scaling]: https://cloud.google.com/appengine/docs/standard/python/how-instances-are-managed#scaling_types

You should set [min_idle_instances][idle] if you want to minimize latency,
particularly if you expect sudden spikes in traffic. The number of idle
instances that are needed will depend on your traffic and it is best to do load
tests to determine the optimal number.

[idle]: https://cloud.google.com/appengine/docs/python/config/appref#min_idle_instances

You should use the default value for [max_concurrent_requests][concurrent].
Increasing this value might cause a performance penalty that can manifest as
requests waiting longer for API calls to return. You should run load tests to
determine impact before making changes.

[concurrent]: https://cloud.google.com/appengine/docs/python/config/appref#max_concurrent_requests

## Use traffic migration or splitting when switching to a new default version

A high traffic application might get errors or higher latency when
updating to a new version in the following scenarios:

* Complete update of a new default version
* Set the default version

Once the update is complete, App Engine will send requests to the
new version. However, the new version can take some time to spin up
enough instances to handle all traffic. During this period, requests
can potentially sit on the pending queue and can time out.

Therefore, in order to minimize latency and errors, we recommend that customers
use [traffic migration][traffic] or [traffic splitting][split-traffic] to move
traffic gradually to a new version before making it the default.

[traffic]: https://cloud.google.com/appengine/docs/python/migrating-traffic
[split-traffic]: https://cloud.google.com/appengine/docs/python/splitting-traffic

An application can serve requests from both versions while you are
moving traffic to the new version. In most cases, this will not cause
any problems. However, if you have an incompatibility in the cached
objects used by an application then you will need to ensure that users
go to the same version of an application during their session. You
will need to code this into your application logic.

## Do not exceed Memcache rated operations per second

You can use [Dedicated Memcache][dedicated_memcache] in order to get guaranteed
capacity and more consistent performance. You must ensure that you do not exceed
the rated operations per second.

[dedicated_memcache]: https://cloud.google.com/appengine/docs/python/memcache/

The rated operations per second of Dedicated Memcache is disproportionately
lower for items larger than 1 KB. One strategy for reducing item size is to
compress large values before storing in Memcache.

Note that the Memcache graphs in the App Engine Admin Console dashboard show
average operations per second aggregated over a time period. Thus these graphs
might not show very short term spikes in usage, which could impact performance.

If your load is unevenly distributed across the Memcache keyspace then you might
not see the expected performance from Dedicated Memcache.

## Avoid Memcache hot keys

Hot keys are a common anti-pattern that can cause Memcache capacity to be
exceeded.

For Dedicated Memcache, we recommend that the peak access rate on a single key
should be 1-2 orders of magnitude less than the per-GB rating. For example, the
rating for 1 KB sized items is 10,000 operations per second per GB of Dedicated
Memcache. Therefore, the load on a single key should not be higher than
100 - 1,000 operations per second for items that are 1 KB in size.

Memcache hashes keys so that keys that are lexicographically close will not
cause hotspots.

In load tests, you might see better performance. However, you should design your
code so that it complies with the published ratings because the performance of
Dedicated Memcache can change.

The Cloud Console displays Memcache hot keys.

Here are some strategies for reducing the operations per second on
frequently-used keys:

* Organize data per user so that a single HTTP request only hits that user's
  data. Avoid storing global data which must be accessed from all HTTP requests.

* Shard your frequently-used keys to keep under the per-key guideline. You
  should create enough keys so that none appear in the Memcache Viewer's list of
  top keys. Even if all of these keys are on the same Memcache backend, it will
  generally not cause a hot key issue.

* Cache frequently-used keys in your instances' global memory not in Memcache.
  Note that you would lose the consistency of Memcache if you stored data in
  instance memory, because one instance might have different data than another.

## Test third-party dependencies

If you depend on a system outside App Engine for handling requests then you
should ensure that this system has been tested to handle high load. For example,
if you are using URL Fetch to get data from a third-party web server then you
can determine the impact of various load testing scenarios on the third party
web server's throughput and latency.

## Implement backoff on retry

Your code can retry on failure, whether calling an App Engine service such as
the Datastore or an external service using URL Fetch or the Socket API. In these
cases, you should always implement a randomized exponential backoff policy in
order to avoid the [thundering herd problem][herd]. You should also limit the
total number of retries and handle failures after the maximum retry limit is
reached.

[herd]: https://wikipedia.org/wiki/Thundering_herd_problem

An example implementation for backoff on retry is in the [Cloud Storage client library][gcs_client]:

* [RetryHelper.java][retry_java]
* [Python RetryParams class][utils_py]

[gcs_client]: https://github.com/GoogleCloudPlatform/appengine-gcs-client/
[retry_java]: https://github.com/GoogleCloudPlatform/appengine-gcs-client/blob/master/java/src/main/java/com/google/appengine/tools/cloudstorage/RetryHelper.java
[utils_py]: https://github.com/GoogleCloudPlatform/appengine-gcs-client/blob/master/python/src/cloudstorage/api_utils.py

You should also implement backoff on retry on automated clients that call your
App Engine application.

## Understand how costs change as usage of your service increases

During the initial design of a new service, the developers can choose to
trade-off the efficiency of their code for reduced complexity, in order to build
features more quickly. However, this trade-off might lead to significantly
higher costs, if the service gets a significant increase in usage.

Below are some examples of ways in which you can reduce costs by making changes
in your application's design. This list is by-no-means exhaustive, but it
reflects the experiences of some App Engine customers who have had significant
increases in traffic.

### Inefficient use of APIs

App Engine's backend services, such as Memcache and Datastore, will generally
scale, even if you use these APIs inefficiently. But you would be reducing
performance and increasing costs. The additional costs can be significant for
some applications. The tips below can also apply when calling a third party API
from your application.

* Use asynchronous API calls, when available, so that your application can do
  other work while waiting for the call to return.

* Set an API call deadline, when possible, so that your application is not
  blocked indefinitely if there is a spike in latency.

* Avoid noop writes to storage systems, such as Memcache or the Datastore. These
  will increase latency, and in the case of the Datastore, also increase costs.
  You should refactor your code if you are doing this.

* Consider using batch API calls, when available, that can offer improvements in
  performance. You should ensure that you eliminate duplicate calls from a
  batch, in order to avoid unnecessary work.

* [Task names][task] are unique per queue. You can ensure that you are not
  creating duplicate tasks, by setting a meaningful task name.

* Avoid unnecessary indexed fields for your Datastore kinds which adds
  additional costs. It might be more cost efficient to run a Mapreduce job to
  create your own index, than to update the indexed fields on each write.

[task]: https://cloud.google.com/appengine/docs/python/taskqueue/tasks#Task_name

### Polling

You can implement polling in various scenarios. For example:

* Mobile clients poll your application for updates.
* Your application makes API calls to third party sites to get updated
  information on each user in your system.

In many cases, the polling requests consume resources unnecessarily, because
there has been no change to the user's data. You can poll less frequently in
order to reduce costs, but that can lead to reduced freshness. Instead, you can
use a different method to push updates to clients, such as [Websockets][websocket].
However, Websockets cannot be implemented on App Engine, so would require some
additional complexity in your implementation.

[websocket]: http://en.wikipedia.org/wiki/WebSocket

### Using backend services outside App Engine

You have a small corpus that fits in a single machine's memory. You can use the
Datastore for this use case. It is quick to get started using App Engine and
Datastore, and it will scale to high IOPS. However, if you have very high IOPS,
it might be less expensive to run your own replicated cache on a quorum of
machines.

### Caching

Adding caching layers will improve your application's performance, thereby
reducing costs. An App Engine application can easily cache data in an instance's
global memory and in [Memcache][memcache_how].

[memcache_how]: https://cloud.google.com/appengine/articles/scaling/memcache#how

In some cases, you will benefit from more aggressive caching strategies. For
example, you can cache data on your mobile clients, which then update your
application asynchronously.

The design of an application can depend on caching working correctly in order to
scale. Your load tests should include a scenario in which you simulate a failure
of the caching layer to verify that your application will continue to scale in
this situation.

## Related links

* Five-part series on effectively [scaling your App Engine-based applications][scaling_overview]

* [App Engine Load Testing and Performance Tips][appengine_load] (YouTube video)

* [Building scalable applications with Google App Engine][building_apps]
  presentation from Google I/O 2008.

[scaling_overview]: https://cloud.google.com/appengine/articles/scaling/overview
[appengine_load]: https://www.youtube.com/watch?v=T_BQevqRp44
[building_apps]: https://sites.google.com/site/io/building-scalable-web-applications-with-google-app-engine
