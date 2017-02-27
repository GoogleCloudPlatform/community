---
title: Best Practices for App Engine Standard Environment Memcache
description: Learn about Best Practices for App Engine standard environment Memcache For Thread Safety, Performance, and Code Migration.
author: devlance
tags: App Engine, Memcache
date_published: 2017-02-09
---

This article outlines some best practices for using the Google App Engine
standard environment Memcache feature. The main issues discussed are
concurrency, performance, and migration. Developers using Memcache will benefit
by becoming aware of pitfalls and considerations for making code more robust.

## Introduction

Memcache is an App Engine feature that provides in-memory, temporary storage. It
is provided primarily as a cache for rapid retrieval of data that is backed by
some form of persistent storage, such as Google Cloud Datastore. Ideal use cases
for Memcache include caching published data like blogs, news feeds, and other
content that is read but not modified. Data stored in Memcache can be evicted at
any time, so applications should be structured in a way that does not depend on
the presence of entries. Memcache can serve concurrent requests to multiple,
remote clients accessing the same data. For this reason, data consistency should
be kept in mind. Memcache statistics, including hit rate, are shown on the App
Engine console and can aid in optimizing performance.

There are two classes of Memcache service, shared and dedicated. Shared Memcache
is a no-cost, best-effort service, and data stored with this service can be
evicted at any time. Dedicated Memcache is a paid service that enables you to
reserve memory for an application. This provides developers with a more
predictable level of service. However, data may still be evicted if more data
needs to be stored than space reserved in Memcache, since keys are evicted when
the cache is full. In addition, data may be evicted if the Memcache service is
restarted for planned or unplanned maintenance. The API signatures and usage are
identical for both shared and dedicated Memcache. The difference in use is a
configuration change in the App Engine Administration Console. Dedicated
Memcache allows for a specific quantity of memory to be allocated for the
application.

### Assumptions

This paper assumes that readers have a basic knowledge of App Engine, including
programming in one of the supported languages: Python, Java, Go, or PHP. The
examples in this paper are provided in Python. Links to the documents
introducing Memcache API for Python in other supported languages are provided in
the [Additional Resources](#additional-resources) section.

## Code Complexity and Concurrency

Memcache can be used to cache data that's persisted in storage systems like
Cloud Datastore or Google Cloud SQL. However, in some cases, writing code to
keep Memcache synchronized with application data that is written and modified in
a persistent datastore can be challenging. In this section we collect some best
practices gained from experience dealing with code complexity to avoid potential
pitfalls in concurrent access:

* It is simpler to use Memcache where data is only read because there is no risk
  of inconsistency between Memcache and the data store.
* When using Memcache for data that is both read and modified, use the Python
  NDB Client Library. This is a good practice because the NDB platform code
  handles concurrent access coordination and error conditions robustly. As a
  result, your application code will be simplified.

### Details and Discussion

Read-only data is ideal for storing in Memcache. Example use cases for this
include serving blogs, RSS feeds, and other published data that is read, but not
modified.

Memcache is a global cache service that is shared by multiple frontend instances
and requests. Concurrency control is required when application logic requires
read consistency to shared data that is updated by multiple clients.
Transactional data sources, such as relational databases or Cloud Datastore,
coordinate concurrent access by multiple clients. However, Memcache is not
transactional. This is an important point to be aware of when using Memcache.
There is a possibility that two clients will read the same data in Memcache at
the same time and modify it simultaneously. As a result, the data stored may be
incorrect. In contrast, if the application logic does not require read
consistency to shared data, there is no need for special code to coordinate
concurrent requests. An example of this is updating the timestamp for accessing
a document. If two clients try to update the last accessed date at the same time
then the last one that does the update wins. This is an expected result.

One approach to solving concurrent access to shared data within the context of a
simple, local execution environment is to synchronize threads so that only one
thread can execute at a time within a critical section. With App Engine, in the
context of code executing across multiple instances, the "compare and set"
(`Client.cas()`) function can be used to coordinate concurrent access. However,
the disadvantage of this type of function is that, if it fails, the application
must be prepared to do the error handling and retry.

Concurrency problems can be hard to detect. Problems do not usually appear until
the application is under load from many users.

### Recommendations

The `incr()` and `decr()` functions are provided for atomic execution of the
increment and decrement operations. Use the atomic Memcache functions where
possible, including `incr()`, `decr()`, and use the `cas()` function for
coordinating concurrent access. Use the Python NDB Client Library if the
application uses Memcache as a way to optimize reading and writing to Cloud
Datastore.

## Data Serialization and Migration

App Engine comes with the tools needed to seamlessly deploy upgrades to the
application without downtime or errors. However, careful planning for migration
is still needed.

The App Engine Memcache feature includes language-specific libraries that each
have a similar but slightly different flavor. In many cases, the Memcache
libraries take care of data serialization in a transparent way. Python is used
in this paper to illustrate the points about Memcache. However, Python is only
one of the four languages supported by App Engine. The Memcache APIs for the
different supported languages are similar but there are some differences.
Language-specific serialization, such as [pickling][pickle] in Python, is used
to serialize objects of most Python classes. In Java, an implementation of the
JCache API, which handles data values as byte arrays, is provided. So, it is the
responsibility of Java application developers to code for serialization and
deserialization of objects at the application level. In contrast, language
independent serialization with protobuf, is used in other cases. In particular,
protobuf is used for classes extending db.Model in Python.

[pickle]: http://docs.python.org/2/library/pickle.html

Changing the versions of the objects stored or upgrading to a new API version
may generate errors, depending on how deserialization is handled. Application
code should be ready to handle errors gracefully to give users a seamless
experience when new code is rolled out.

### Details and Discussion

When rolling out new code, deserialization of the various serialized formats of
old objects should be tested. App Engine was first released with Python 2.5 and
later upgraded to 2.7. Errors in Python object serialization, called pickling,
were a source of migration problems for applications that did not test this
point. Python 2.5 objects were stored as pickled Python objects, code was
upgraded to Python 2.7, and objects were retrieved from Memcache. However, the
Python 2.5 objects could not be unmarshalled ("unpickled") by the App Engine
Python 2.7 runtime, which generated errors. Avoiding exceptions like this has
been a frequent source of forum discussions.

Besides migration from one version of Python to the next, similar problems can
happen with serialization in other languages as well. Also, the same thing can
happen when migrating between different versions of application code. Testing is
needed whenever making changes to classes where objects are serialized with an
older structure.

There are four ways of avoiding problems like this:

1.  Make compatible changes to objects.
1.  Handle errors properly.
1.  Flush the cache before deploying new code.
1.  Use namespaces to isolate data in a multitenant-like way.

If the application uses modules developed with multiple languages, follow the
best practices for key and value compatibility discussed in the section
[Sharing memcache between different programming languages](#sharing-memcache-between-different-programming-languages).

### Recommendations

* Make compatible changes to object structures.
* Handle errors properly when reading objects from Memcache.
* Flush Memcache when deploying new code with major changes.

### Example

This example demonstrates the problems that may occur when migrating code where
objects are stored in Memcache. The code below defines the class `Person` and
the function `get_or_add_person` to retrieve or add a person with the given name
to Memcache.

[embedmd]:# (python/migration_step1/migration1.py /class Person/ /return person/)
```py
class Person(ndb.Model):
    name = ndb.StringProperty(required=True)


def get_or_add_person(name):
    person = memcache.get(name)
    if person is None:
        person = Person(name=name)
        memcache.add(name, person)
    else:
        logging.info('Found in cache: ' + name)
    return person
```

*View the code [on GitHub](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/appengine-memcache-best-practices/python/migration_step1).*

After running this code in production for some time, the new `userid` field for
class `Person` is added. The following code shows the changes made:

[embedmd]:# (python/migration_step2/migration2.py /class Person/ /return person/)
```py
class Person(ndb.Model):
    name = ndb.StringProperty(required=True)
    userid = ndb.StringProperty(required=True)


def get_or_add_person(name, userid):
    person = memcache.get(name)
    if person is None:
        person = Person(name=name, userid=userid)
        memcache.add(name, person)
    else:
        logging.info('Found in cache: ' + name + ', userid: ' + person.userid)
    return person
```

*View the code [on GitHub](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/appengine-memcache-best-practices/python/migration_step2).*

The problem created by the upgrade is that objects with the old schema were
stored in Memcache and are not compatible with the new structure of the object
that has a required `userid` field. When tested, the Memcache service
successfully unmarshalled `Person` objects with the old structure. It is
surprising that the old objects can be successfully unmarshalled because the new
`userid` field is required. In general, do not rely on this kind of behavior
when migrating code without testing. However, a problem was caused by the log
statement, which generated an error by referring to the `person.userid` field.
After flushing Memcache from the console, no more errors were generated.

Java is somewhat different, but the same principle applies. A best practice in
Java serialization is the use of a `serialVersionUID` value in the serialized
object. This gives application programmers a clean error when deserializing an
older format and provides an opportunity to customize the deserialization.

## Sharing memcache between different programming languages

An App Engine app can be factored into one or more modules and versions.
Sometimes it is convenient to write modules and versions in different
programming languages. You can share the data in your memcache between any of
your app's modules and versions. Because the memcache API serializes its
parameters, and the API may be implemented differently in different languages,
you need to code memcache keys and values carefully if you intend to share them
between langauges.

### Key Compatibility

To ensure language-independence, memcache keys should be bytes:

* In Python use plain strings (not Unicode strings)
* In Java use byte arrays (not strings)
* In Go use byte arrays
* In PHP use strings

Remember that memcache keys cannot be longer than 250 bytes, and they cannot
contain null bytes.

### Value Compatibility

For memcache values that can be written and read in all languages, these are the
types you can use:

* Byte arrays and ASCII strings.
* Unicode strings, but you must encode and decode them properly in Go and PHP.
* Integers in increment and decrement operations, but you must use 32-bit values
  in PHP.

Avoid using these types for values that you want to pass between languages:

* Integers (other than in increment and decrement operations) because Go does
  not directly support integers and PHP cannot handle 64-bit integers.
* Floating point values and complex types like lists, maps, structs, and
  classes, because each language serializes them in a different way.

To handle integers, floating point, and complex types, we recommend that you
implement your own language-independent serialization that uses a format such as
JSON or [protocol buffers](https://developers.google.com/protocol-buffers/).

### Example

The example code below operates on two memcache items in Python, Java, Go, and
PHP. It reads and writes an item with the key "who" and increments an item
with the key "count". If you create a single app with separate modules
using these four code snippets, you will see that the values set or incremented
in one language will be read by the other languages.

#### Python

[//]: # Remove extra indentation from the code below after running embedmd

[embedmd]:# (python/sharing/sharing.py /        self\.response\.headers/ /% count\)/)
```py
self.response.headers['Content-Type'] = 'text/plain'

who = memcache.get('who')
self.response.write('Previously incremented by %s\n' % who)
memcache.set('who', 'Python')

count = memcache.incr('count', 1, initial_value=0)
self.response.write('Count incremented by Python = %s\n' % count)
```

*View the code [on GitHub](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/appengine-memcache-best-practices/python/sharing).*

#### Java

[embedmd]:# (java/src/main/java/com/example/appengine/memcache/MemcacheBestPracticeServlet.java /@SuppressWarnings/ /\s+}\s}/)
```java
@SuppressWarnings("serial")
public class MemcacheBestPracticeServlet extends HttpServlet {

  @Override
  public void doGet(HttpServletRequest req, HttpServletResponse resp) throws IOException,
      ServletException {
    String path = req.getRequestURI();
    if (path.startsWith("/favicon.ico")) {
      return; // ignore the request for favicon.ico
    }

    MemcacheService syncCache = MemcacheServiceFactory.getMemcacheService();
    syncCache.setErrorHandler(ErrorHandlers.getConsistentLogAndContinue(Level.INFO));

    byte[] whoKey = "who".getBytes();
    byte[] countKey = "count".getBytes();

    byte[] who = (byte[]) syncCache.get(whoKey);
    String whoString = who == null ? "nobody" : new String(who);
    resp.getWriter().print("Previously incremented by " + whoString + "\n");
    syncCache.put(whoKey, "Java".getBytes());
    Long count = syncCache.increment(countKey, 1L, 0L);
    resp.getWriter().print("Count incremented by Java = " + count + "\n");
  }
}
```

*View the code [on GitHub](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/appengine-memcache-best-practices/java).*

#### Go

[//]: # Remove extra indentation from the code below after running embedmd

[embedmd]:# (go/app.go /\sw.Header/ /, count\)/)
```go
w.Header().Set("Content-Type", "text/plain")
c := appengine.NewContext(r)

who := "nobody"
item, err := memcache.Get(c, "who")
if err == nil {
	who = string(item.Value)
} else if err != memcache.ErrCacheMiss {
	http.Error(w, err.Error(), http.StatusInternalServerError)
	return
}

fmt.Fprintf(w, "Previously incremented by %s\n", who)
memcache.Set(c, &memcache.Item{
	Key:   "who",
	Value: []byte("Go"),
})

count, _ := memcache.Increment(c, "count", 1, 0)
fmt.Fprintf(w, "Count incremented by Go = %d\n", count)
```

*View the code [on GitHub](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/appengine-memcache-best-practices/go).*

#### PHP

```php
$memcache = new Memcached;
$memcache->set('who', $request->get('who'));
return $twig->render('memcache.html.twig', [
    'who' => $request->get('who'),
    'count' => $memcache->increment('count', 1, 0),
    'host' => $request->getHost(),
]);
```

## Other Best Practices

Several other best practices are discussed in this section.

### Handling Memcache API Failures Gracefully

Memcache errors must be handled properly for code to remain functionally
correct. While the application can fall back on data stored in the Cloud
Datastore when data is not found, it must make sure that values stored in
Memcache are correct. Failure to update Memcache successfully can result in
stale data that, if it is read later on, may result in incorrect program
behavior. The following code fragment demonstrates this concept:

[//]: # Remove extra indentation from the code below after running embedmd

[embedmd]:# (python/failure/failure.py /        if not memcache/ /handling here/)
```py
if not memcache.set('counter', value):
    logging.error("Memcache set failed")
    # Other error handling here
```

*View the code [on GitHub](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/appengine-memcache-best-practices/python/failure).*

The `set()` method returns `False` if an error is encountered when adding or
setting data in Memcache. If the value cannot be set, the application could
retry, clear the data from Memcache, flush Memcache, or raise an exception.
Retrying may be the most graceful method, but it will depend on the particular
case. In many cases, set and retry are not the correct semantics to use. The
following is simple pseudo-code for a more robust write sequence that
synchronizes Memcache and a persistent store:

[//]: # Remove extra indentation from the code below after running embedmd

[embedmd]:# (python/failure/failure.py /        memcache\.delete\(key, seconds\)/ /reader will do that/)
```py
memcache.delete(key, seconds)  # clears cache
# write to persistent datastore
# Do not attempt to put new value in cache, first reader will do that
```

*View the code [on GitHub](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/appengine-memcache-best-practices/python/failure).*

Pseudo-code for one simple read sequence is shown below.

[//]: # Remove extra indentation from the code below after running embedmd

[embedmd]:# (python/failure/failure.py /        v = memcache/ /add\(key, v\)/)
```py
v = memcache.get(key)
if v is None:
    v = read_from_persistent_store()
    memcache.add(key, v)
```

*View the code [on GitHub](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/appengine-memcache-best-practices/python/failure).*

Notice that `memcache.set()` is not used in either sequence, in order to avoid
the risk of stale data being left in the cache. However, this code has the risk
of a race condition. If a second client reads when the first client is between
the `memcache.delete()` and the completion of `write-to-persistent`, then the
second client may get the old value from the persistent store and re-cache it.
The seconds argument to `memcache.delete()`, also known as "lock duration", has
been be added here to reduce the risk of this race condition. In conclusion,
when trying to synchronize between Memcache and Cloud Datastore, it is best to
use a library like NDB, because robust handling of edge cases is required to
keep data in sync.

### Use Batch Capability when Possible

The use of batch capabilities is ideal for retrieving multiple related values.
These functions avoid retrieving inconsistent values and provide faster
performance. The following code fragment is an example of how batch capabilities
can be used:

[//]: # Remove extra indentation from the code below after running embedmd

[embedmd]:# (python/batch/batch.py /        values = {/ /\(tvalues\)/)
```py
values = {'comment': 'I did not ... ', 'comment_by': 'Bill Holiday'}
if not memcache.set_multi(values):
    logging.error('Unable to set Memcache values')
tvalues = memcache.get_multi(('comment', 'comment_by'))
self.response.write(tvalues)
```

*View the code [on GitHub](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/appengine-memcache-best-practices/python/batch).*

The code fragment demonstrates setting multiple values with the function
`set_multi()` and getting multiple values with the `get_multi()` function. Note
that when setting multiple values, if two values are intrinsically related, then
they may be best stored as a single value.

### Distribute Load Across the Keyspace

The dedicated Memcache service can handle up to 10,000 operations per second per
gigabyte. (See the [Memcache Documentation](https://cloud.google.com/appengine/docs/python/memcache/)
for details of dedicated Memcache and its limitations.) Developers may need to
be mindful of this limit for App Engine applications that handle a large number
of requests. The 10k ops/s limit may be large enough to process several hundred
HTTP requests per second, but some applications have a skewed distribution
pattern for key usage. For example, 80% of Memcache access calls may be
concentrated on only 20 keys. This may be a problem if the keys are concentrated
on particular servers due to poor key name distribution, and can lead to errors
and performance slowdowns.

To avoid performance delays, developers may spread data access across multiple
keys and aggregate the data after it is read. For instance, when writing to a
counter many times, spread the counter across many keys and then add up the
values after the counter is read from Memcache. The Memcache viewer in the
administration console displays a list of top keys, which can be used to
identify bottlenecks. A good rule of thumb is that the sum of the percentages
shown for the top 10 keys should add up to less than 5% of the total traffic.

The Memcache operation rate varies by item size approximately according to the
table on the [Memcache documentation page](https://cloud.google.com/appengine/docs/python/memcache/).
The maximum rate of operations per second drops off quickly for larger entry
sizes. The solution to this is to shard large values into multiple items or to
compress the large values.

## Additional Resources

The following links reference additional resources that may also be useful:

* [Memcache Overview](https://cloud.google.com/appengine/docs/python/memcache/)
* [Memcache API for Python](https://cloud.google.com/appengine/docs/python/memcache/using)
* [Memcache API for Java](https://cloud.google.com/appengine/docs/java/memcache/using)
* [Memcache API for Go](https://cloud.google.com/appengine/docs/go/memcache/using)
* [Memcache API for PHP](https://cloud.google.com/appengine/docs/php/memcache/using)
* [Memcache Basics Presentation Video](http://www.youtube.com/watch?feature=player_embedded&amp;v=TGl81wr8lz8)
* [Effective memcache](https://cloud.google.com/appengine/articles/scaling/memcache)
* [Compare-And-Set in Memcache](http://neopythonic.blogspot.com/2011/08/compare-and-set-in-memcache.html)
* [Migrating to Python 2.7](https://cloud.google.com/appengine/docs/python/python25/migrate27)
* [Python NDB](https://cloud.google.com/appengine/docs/python/ndb/)
* [Protocol Buffers (Protobuf)](https://github.com/google/protobuf)
* [Memcached Website](http://memcached.org/)
