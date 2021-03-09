---
title: Composing an infinite number of objects into one object in Cloud Storage
description: Overview of the APIs and programming techniques for being a power user of the Cloud Storage compose feature.
author: domZippilli
tags: object storage, compose, concatenate
date_published: 2021-01-06
---

Dom Zippilli | Solutions Architect | Google Cloud

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

Many people see the [`compose`](https://cloud.google.com/storage/docs/json_api/v1/objects/compose) operation in
[Cloud Storage](https://cloud.google.com/storage) and conclude that they are limited to composing 32 objects into 1. But reading the `compose`
documentation closely, you can see that there's more to the story:

<table>
  <tr>
   <td><code>sourceObjects[]</code>
   </td>
   <td>The list of source objects that will be concatenated into a single object. There is a limit of 32 components that can be composed <em>in a single operation</em>.
   </td>
  </tr>
</table>

The important details here is the phrase *in a single operation*. This implies that you can do more in multiple operations. So, how many objects can be composed 
into one? 

The answer: It's effectively unlimited. Because you can append 0-byte objects, composition can go on forever—even after it saturates the
[`componentCount`](https://cloud.google.com/storage/quotas#objects) 32-bit integer, which has a maximum value of 2,147,483,647. In practice, the number of 
objects that can be composed into a single object can be in the billions. For example, you could compose 5 billion 1KB objects into a single 5TB object. In that 
case, you would have 5 billion components. You just have to compose them 32 at a time.

This document shows you how to compose objects quickly using Python. You can translate the concepts shown here to other programming languages.

This document assumes that you have some programming experience. This document covers two techniques: one with beginner-friendly programming concepts, and one
with more intermediate concepts.

Because `compose` is a class A operation, [operations costs](https://cloud.google.com/storage/pricing#operations-pricing) apply. In general, you should
avoid using the `compose` operation in any [storage class](https://cloud.google.com/storage/docs/storage-classes) other than Standard, because storage classes
other than Standard have higher operations costs and early delete charges. It's better to compose in Standard and move objects to other classes when they're 
finalized.

## Concept

The problem of composing a large number of objects into one object fits nicely into an
[accumulator](https://runestone.academy/runestone/books/published/fopp/Iteration/TheAccumulatorPattern.html) pattern. What makes the case here slightly different
from the programming pattern is that the accumulator isn't a variable in memory, but an object in Cloud Storage.

You can think of `compose` as a function that accepts a list of up to 32 objects and accumulates them, through concatenation, into the return value. Because the
return value is just another object, and composed objects are composable, you can put the new object in a list along with 31 more and compose again, ad 
infinitum.

![drawing](https://storage.googleapis.com/gcp-community/tutorials/cloud-storage-infinite-compose/figure1.svg)

In the preceding diagram, this concept is illustrated using the final object as the accumulator. Initially, it's created as a 0-byte object, and then the 
component objects are accumulated into it 31 at a time until completion.

## Example implementation

This section demonstrates a simple implementation in Python.

### Prerequisite: Getting a list of objects

Before beginning to compose objects, you need a list of objects to compose. How you get the list of objects is up to you, since this depends on your use case.

Some examples of how you can get a list of objects to use as input:

*   Programmatically generate the names. For example, if you know the objects follow a sequential naming pattern like `[prefix]/[object]-[n]`, you can generate 
    this sequence with loops.
*   Pull the names from an external source, like a database or a file.
*   [List the objects](https://cloud.google.com/storage/docs/listing-objects#code-samples) in the bucket that you want to compose.

### Generate the composition chunks

After you get the list of objects, you need a function that iterates through the list and emits chunks of 31 objects at a time.

This Python code shows an example of how to do this:

```python
def generate_composition_chunks(slices: List,
                                chunk_size: int = 31) -> Iterable[List]:
    """Given an indefinitely long list of blobs, return the list in 31-item chunks.

    Arguments:
        slices {List} -- A list of blobs, which are slices of a desired final blob.

    Returns:
        Iterable[List] -- An iteration of 31-item chunks of the input list.

    Yields:
        Iterable[List] -- A 31-item chunk of the input list.
    """
    while len(slices):
        chunk = slices[:chunk_size]
        yield chunk
        slices = slices[chunk_size:]
```


This function requires and returns a `List` object that stores the object names in memory. A few adjustments to this function could accommodate an 
`Iterable` input that streams the names from another source (such as Cloud Storage list operation pages), if your system is memory-constrained or if you 
expect a very large number of objects. 

### Compose the chunks

This is the main function for composition, which handles creating the accumulator, reading the list in 31-object chunks, and then performing the cleanup with 
concurrent deletions. Delete operations are performed in parallel so that they don't take a long time. The accumulator (`final_blob`) is inserted at the head of
each chunk before `compose` is called.

```python
def compose(object_path: str, slices: List[storage.Blob],
            client: storage.Client, executor: Executor) -> storage.Blob:
    """Compose an object from an indefinite number of slices. Composition is
    performed single-threaded with the final object acting as an
    accumulator. Cleanup is performed concurrently using the provided
    executor.

    Arguments:
        object_path {str} -- The path for the final composed blob.
        slices {List[storage.Blob]} -- A list of the slices that should
            compose the blob, in order.
        client {storage.Client} -- A Cloud Storage client to use.
        executor {Executor} -- A concurrent.futures.Executor to use for
            cleanup execution.
    Returns:
        storage.Blob -- The composed blob.
    """
    LOG.info("Composing")
    final_blob = storage.Blob.from_string(object_path)
    final_blob.upload_from_file(io.BytesIO(b''), client=client)

    for chunk in generate_composition_chunks(slices):
        chunk.insert(0, final_blob)
        final_blob.compose(chunk, client=client)
        delete_objects_concurrent(chunk[1:], executor, client)
        sleep(1)  # can only modify object once per second  

    return final_blob
```

The `delete_objects_concurrent` function is very simple, using fire-and-forget delete tasks in an executor. A more robust implementation might check the futures
from the submitted tasks. The short sleep helps to avoid a [thundering herd](https://en.wikipedia.org/wiki/Thundering_herd_problem) and ensure that your delete 
operations aren't throttled.

```python
def delete_objects_concurrent(blobs, executor, client) -> None:
    """Delete Cloud Storage objects concurrently.

    Args:
        blobs (List[storage.Blob]): The objects to delete.
        executor (Executor): An executor to schedule the deletions in.
        client (storage.Client): Cloud Storage client to use.
    """
    for blob in blobs:
        LOG.debug("Deleting slice {}".format(blob.name))
        executor.submit(blob.delete, client=client)
        sleep(.005)  # quick and dirty ramp-up (Sorry, Dijkstra.)
```

That's it! You can test this code using [this command-line tool](https://github.com/domZippilli/gcsfast/blob/master/gcsfast/cli/upload.py).


## A more advanced approach: accumulator tree

The implementation above has one big advantage, which is that it's rather simple and safe. For many use cases, where hundreds or thousands of objects need to be
composed and time is not very critical, it will work fine. But it has two disadvantages that could cause problems as the scale increases:

*   Because there's a single accumulator, and you can only update an object in Cloud Storage [once per second](https://cloud.google.com/storage/quotas#objects),
    a lot of time is spent "cooling down" between `compose` calls.
*   Because the single accumulator must accumulate serially, operation must be single-threaded.

You can remove both of these disadvantages by using multiple accumulators across the composite objects, and then accumulating the accumulators until you get
to one. This forms a tree-like structure of accumulators:

![drawing](https://storage.googleapis.com/gcp-community/tutorials/cloud-storage-infinite-compose/figure2.svg)

This has some disadvantages, though they can be mitigated:

*   A straightforward implementation would try to store the intermediate accumulator references in memory. If you have 5 billion items to compose, that means
    approximately 156 million objects in the first iteration. Dumping the object names to disk is a good workaround, and there are certainly even better ways to
    handle it.
*   This approach creates a lot of intermediate objects. 
    *   As discussed, this would be _seriously expensive_ to do in a storage class with a minimum retention period. Each iteration of accumulators would have the
        entire file size stored. Therefore, you can only use this approach economically in the Standard storage class. Though you can mix and match 
        storage classes in a bucket, you *cannot* compose across storage classes (for example, Nearline components to a Standard composed object).
    *   Each accumulator needs a unique name. You can append a unique ID, but for larger object names with larger component counts,
        [you might run out of characters](https://cloud.google.com/storage/docs/naming-objects).

That said, for many cases this approach works fine, and it is much quicker than a single accumulator. It's a little more advanced, but having seen the simpler 
approach in action, it should be a straightforward evolution.

As before, the primary function handles reading the list chunks, composing, and cleanup, but it does things quite differently. Now, you have to create 
intermediate accumulators and schedule the work in an executor, collecting futures as the work progresses. `storage.Blob.from_string` doesn't make an empty 
object when constructed; it creates a local reference to one that doesn't exist yet, until it is uploaded or composed.

```python
def compose(object_path: str, slices: List[storage.Blob],
            client: storage.Client, executor: Executor) -> storage.Blob:
    """Compose an object from an indefinite number of slices. Composition is
    performed concurrently using a tree of accumulators. Cleanup is
    performed concurrently using the provided executor.

    Arguments:
        object_path {str} -- The path for the final composed blob.
        slices {List[storage.Blob]} -- A list of the slices that should
            compose the blob, in order.
        client {storage.Client} -- A Cloud Storage client to use.
        executor {Executor} -- A concurrent.futures.Executor to use for
            cleanup execution.

    Returns:
        storage.Blob -- The composed blob.
    """
    LOG.info("Composing")

    chunks = generate_composition_chunks(slices)
    next_chunks = []
    identifier = generate_hex_sequence()

    while len(next_chunks) > 32 or not next_chunks:  # falsey empty list is ok
        for chunk in chunks:
            # make intermediate accumulator
            intermediate_accumulator = storage.Blob.from_string(
                object_path + next(identifier))
            LOG.info("Intermediate composition: %s", intermediate_accumulator)
            future_iacc = executor.submit(compose_and_cleanup,
                                          intermediate_accumulator, chunk,
                                          client, executor)
            # store reference for next iteration
            next_chunks.append(future_iacc)
        # go again with intermediate accumulators
        chunks = generate_composition_chunks(next_chunks)

    # Now can do final compose
    final_blob = storage.Blob.from_string(object_path)
    # chunks is a list of lists, so flatten it
    final_chunk = [blob for sublist in chunks for blob in sublist]
    compose_and_cleanup(final_blob, final_chunk, client, executor)

    LOG.info("Composition complete")

    return final_blob
```

Composing and deleting is the work that you want to parallelize, so you need to move it into its own callable for the executor, `compose_and_cleanup`. This 
function gets the results of all of its assigned chunks (which have to be written in order to be composed), performs the composition, and then schedules the
cleanup. The reason for scheduling the cleanup tasks separately is so that the composed blob can be returned as soon as possible, rather than waiting for the 
cleanup.

```python
def compose_and_cleanup(blob: storage.Blob, chunk: List[storage.Blob],
                        client: storage.Client, executor: Executor):
    """Compose a blob and clean up its components. Cleanup tasks are
    scheduled in the provided executor and the composed blob immediately
    returned.

    Args:
        blob (storage.Blob): The blob to be composed.
        chunk (List[storage.Blob]): The component blobs.
        client (storage.Client): A Cloud Storage client.
        executor (Executor): An executor in which to schedule cleanup tasks.

    Returns:
        storage.Blob: The composed blob.
    """
    # wait on results if the chunk has any futures
    chunk = ensure_results(chunk)
    blob.compose(chunk, client=client)
    # clean up components, no longer need them
    delete_objects_concurrent(chunk, executor, client)
    return blob
```

As something of a stylistic choice, the `ensure_results` function accepts a list of `storage.Blob` items (which you have from the initial list), a list of
`Future[storage.Blob]` items (which you have from intermediate steps), or a mix of both, using the same code. This is what makes the `compose_and_cleanup` 
function block until its components are all complete.

```python
def ensure_results(maybe_futures: List[Any]) -> List[Any]:
    """Pass in a list that may contain futures, and if so, wait for
    the result of the future; for all other types in the list,
    simply append the value.

    Args:
        maybe_futures (List[Any]): A list which may contain futures.

    Returns:
        List[Any]: A list with the values passed in, or Future.result() values.
    """
    results = []
    for mf in maybe_futures:
        if isinstance(mf, Future):
            results.append(mf.result())
        else:
            results.append(mf)
    return results
```

Finally, this function simply gives a very long sequence of hexadecimal digits to use as identifiers for the intermediate accumulators:

```python
def generate_hex_sequence() -> Iterable[str]:
    """Generate an indefinite sequence of hexadecimal integers.

    Yields:
        Iterator[Iterable[str]]: The sequence of hex digits, as strings.
    """
    for i in count(0):
        yield hex(i)[2:]
```

This approach trades off some complexity for a great increase in speed. In
[this example command-line tool](https://github.com/domZippilli/gcsfast/blob/master/gcsfast/cli/upload_standard.py), the technique is used to upload objects 
using parallel slices.


## Conclusion

This has shown how you can use the Cloud Storage `compose` function to create single objects from very large collections of other objects. It's a great thing to
be able to do. 

There are a few caveats:

*   Though there's no limit to the number of components, the 5TB object size limit does still apply. 

*   In the very popular "colder" storage classes—like Nearline, Coldline, and Archive—programmatic composition can lead to high minimum retention charges, so 
    it's best to use Standard storage class to perform the accumulation and then change the storage class of the composite object.

*   Composite objects don't have MD5 checksums in their Cloud Storage metadata. They do have CRC32C checksums, because CRC32C is
    [commutative](https://stackoverflow.com/a/23050676) and can just be added together (componentA + componentB = objectAB), which suits the `compose` operation.
    MD5 must be calculated using the entire bitstream. Cloud Storage computes MD5 checksums during uploads, so a composed object would need to be downloaded and 
    re-uploaded to generate an MD5 checksum.

This code is offered for demonstration purposes only, and should not be considered production-ready. Applying it to your production workloads is up to you!

## What's next

*   Explore the [Google Cloud SDK](https://cloud.google.com/sdk)
*   Get started with [Google Cloud Client Libraries for your language of choice](https://cloud.google.com/apis/docs/cloud-client-libraries)
*   Learn more about [Google Cloud Storage](https://cloud.google.com/storage) features and pricing.
