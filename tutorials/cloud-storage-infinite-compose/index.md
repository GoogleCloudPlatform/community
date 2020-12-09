---
title: How to compose an infinite number of objects into one in GCS
description: Overview of the APIs and appropriate programming techniques for being a power-user of the GCS compose feature.
author: domZippilli
tags: object storage, compose, concatenate, 
date_published: 2020-12-09
---

Dom Zippilli | Solutions Architect | Google Cloud

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

A lot of customers take a look at the [compose](https://cloud.google.com/storage/docs/json_api/v1/objects/compose) operation in GCS and conclude that they are limited to composing 32 objects into one. But reading the compose documentation closely, you can see there's more to the story:


<table>
  <tr>
   <td><code>sourceObjects[]</code>
   </td>
   <td>The list of source objects that will be concatenated into a single object. There is a limit of 32 components that can be composed <strong>in a single operation</strong>.
   </td>
  </tr>
</table>


The key here is the phrase "in a single operation." This implies you could do more in multiple operations. So how many objects can be composed into one? 

The answer is: it's unlimited. Since, technically, you can append zero-byte objects, composition can go on forever (even after it saturates the [component-count](https://cloud.google.com/storage/quotas#objects) INT32). In practice, it can be a very high number. For example, say you were to compose 5 billion 1KB objects, making a single 5TB object. In that case, you would have 5 billion components. You just have to compose them 32 at a time.

This might seem like a use case that would never come up, but it does. An example might be an IoT or similar system where sensor data is uploaded into object storage, and you later want to concatenate this collection into a single large file. Logs, similarly, could be concatenated from hundreds of thousands of files.

In this article, I'll show you how to compose objects quickly and easily using simple Python code. The concepts shown here can easily translate to other programming languages.


## Before you begin

Note that compose is a class A operation, so [operations costs](https://cloud.google.com/storage/pricing#operations-pricing) will apply. We'll cover this in more detail later, but in general you will want to avoid doing compose in any storage class besides standard, as you'll have higher operations costs as well as early delete charges. It's better to compose in Standard, and move objects to other classes when they're finalized.


## Concept

The problem we have here can fit nicely into an [accumulator](https://runestone.academy/runestone/books/published/fopp/Iteration/TheAccumulatorPattern.html) pattern. What makes the case here very slightly different from the programming pattern is that our accumulator will not be a variable in memory, but an object in GCS.

If we think of compose as a function, it accepts a list up to 32 objects and "accumulates" them, through concatenation, into the return value. Since the return value is just another object, and composed objects are composable, we can put the new object in a list along with 31 more, and compose again, ad infinitum.

![drawing](./figure1.svg)

In the above diagram, this concept is illustrated using the final object as the accumulator. Initially, it's created as a 0-byte object, and then the composite objects are accumulated into it 31 at a time until completion. 


## Example implementation

Next, we'll go over a simple implementation of this in Python.


### Prerequisite: Getting a list of objects

Before beginning the composition code, note that there's an input we need: a list of objects to compose. Exactly how to get this is best left as an exercise for the reader, as it depends on the case. Some ways you could get this input are:



*   Programmatically generate the names. For example, if you know the objects follow a sequential naming pattern like [prefix]/[collection]-[n], you can generate this sequence with trivial loops.
*   Pull the names from an external source, like a database or a file.
*   [List the objects](https://cloud.google.com/storage/docs/listing-objects#code-samples) in the bucket you want to compose.


### Generate the compose chunks

Once you have the list of objects, you need a function that iterates through the list and emits chunks of 31 at a time. This is pretty simple:


```
def generate_composition_chunks(slices: List,
                                chunk_size: int = 31) -> Iterable[List]:
    """Given an indefinitely long list of blobs, return the list in 31 item chunks.

    Arguments:
        slices {List} -- A list of blobs which are slices of a desired final
            blob.

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


Note that this function requires and returns a List object, which will store the object names in memory. A few adjustments to this function could accommodate an Iterable input which streams the names from another source (such as GCS list operation pages), if you're memory constrained or expect a very large number of objects. 


### Compose the chunks

Now, you simply need to:



*   Create the accumulator
*   Compose chunks into the accumulator until finished
*   Perform cleanup

The following example uses a bit of concurrency to perform the cleanup, as deletes are trivially parallelized and would take a long time otherwise. 


```
def compose(object_path: str, slices: List[storage.Blob],
            client: storage.Client, executor: Executor) -> storage.Blob:
    """Compose an object from an indefinite number of slices. Composition will
    be performed single-threaded with the final object acting as an
    "accumulator." Cleanup will be performed concurrently using the provided
    executor.

    Arguments:
        object_path {str} -- The path for the final composed blob.
        slices {List[storage.Blob]} -- A list of the slices which should
            compose the blob, in order.
        client {storage.Client} -- A GCS client to use.
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
        sleep(1)  # can only modify object once per second

    LOG.info("Cleanup")
    delete_objects_concurrent(slices, executor, client)

    return final_blob
This is our main function for composition. It handles creating the accumulator, reading the list in 31-object chunks, and then performing the cleanup with concurrent deletes. Note that the accumulator (final_blob) is inserted at the head of each chunk before compose is called.

def delete_objects_concurrent(blobs, executor, client) -> None:
    """Delete GCS objects concurrently.

    Args:
        blobs (List[storage.Blob]): The objects to delete.
        executor (Executor): An executor to schedule the deletions in.
        client (storage.Client): GCS client to use.
    """
    for blob in blobs:
        LOG.debug("Deleting slice {}".format(blob.name))
        executor.submit(blob.delete, client=client)
        sleep(.005)  # quick and dirty ramp-up, sorry Dijkstra
```


This function is pretty trivial, using fire-and-forget delete tasks in an executor. A more robust implementation might check the Futures from the submitted tasks, though the Python storage library has retries built in, and component names are usually easily recreated if something goes really wrong, so fire-and-forget is OK. The short sleep helps to avoid a [thundering herd](https://en.wikipedia.org/wiki/Thundering_herd_problem) and ensure that we don't get our deletes throttled.

That's it! You can test this code using [this command line tool](https://github.com/domZippilli/gcsfast/blob/master/gcsfast/cli/upload.py).


## A more advanced approach: "accumulator tree"

The implementation above has one big advantage, which is that it's pretty simple and safe. For many use cases, where hundreds or thousands of objects need to be composed and time is not very critical, it will work fine. But it has two disadvantages that could start to hurt as the scale increases:



*   Since there's a single accumulator, and we can only update an object in GCS [once per second](https://cloud.google.com/storage/quotas#objects), we spend a lot of time "cooling down" between compose calls.
*   The single accumulator also locks us into single-threaded operation, since we have to accumulate serially.

We could remove both of these disadvantages by using multiple accumulators across the composite objects, then accumulating the accumulators, until we get down to one. This would form a tree-like structure of accumulators:

![drawing](./figure2.svg)

This has some disadvantages, though they can be mitigated:



*   A straightforward implementation would try to store the intermediate accumulator references in memory. If you have 5 billion items to compose, that means ~156 million objects in the first iteration. Dumping the object names to disk is a good workaround, and there are certainly even slicker ways to handle it.
*   You'll be creating a lot of intermediate objects. 
    *   As discussed, this would be _seriously expensive_ to do in a storage class with a minimum retention period. Each iteration of accumulators will have the entire file size stored. Thus, you can only do this approach economically in the Standard storage class. While you can mix and match storage classes in a bucket, you **cannot** compose across storage classes (e.g., Nearline components to a Standard composed object).
    *   Each accumulator will need a unique name. Appending a unique ID is easy enough, but for larger object names with larger component counts, [you might run out of characters](https://cloud.google.com/storage/docs/naming-objects).

That said, for many cases this will work just fine, and will be much quicker than a single accumulator. It's a little more advanced, but having seen the simpler approach in action, it should be a straightforward evolution.


```
def compose(object_path: str, slices: List[storage.Blob],
            client: storage.Client, executor: Executor) -> storage.Blob:
    """Compose an object from an indefinite number of slices. Composition will
    be performed concurrently using a tree of accumulators. Cleanup will be
    performed concurrently using the provided executor.

    Arguments:
        object_path {str} -- The path for the final composed blob.
        slices {List[storage.Blob]} -- A list of the slices which should
            compose the blob, in order.
        client {storage.Client} -- A GCS client to use.
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
        # let intermediate accumulators finish and go again
        chunks = generate_composition_chunks(next_chunks)

    # Now can do final compose
    final_blob = storage.Blob.from_string(object_path)
    final_chunk = [blob for sublist in chunks for blob in sublist]
    compose_and_cleanup(final_blob, final_chunk, client, executor)

    LOG.info("Composition complete")

    return final_blob
As before, this primary function handles reading the list chunks, composing, and cleanup, but it does things quite differently. Now, we have to create intermediate accumulators, and schedule our work in an Executor, collecting Futures as we go.

def compose_and_cleanup(blob: storage.Blob, chunk: List[storage.Blob],
                        client: storage.Client, executor: Executor):
    """Compose a blob and clean up its components. Cleanup tasks will be
    scheduled in the provided executor and the composed blob immediately
    returned.

    Args:
        blob (storage.Blob): The blob to be composed.
        chunk (List[storage.Blob]): The component blobs.
        client (storage.Client): A GCS client.
        executor (Executor): An executor in which to schedule cleanup tasks.

    Returns:
        storage.Blob: The composed blob.
    """
    # wait on results if the chunk is full of futures
    chunk = ensure_results(chunk)
    blob.compose(chunk, client=client)
    # cleanup components, no longer need them
    delete_objects_concurrent(chunk, executor, client)
    return blob

This is the work we want to parallelize, so we need to move it into its own callable for the Executor. This function gets the results of all its assigned chunks (they have to be written in order to be composed), performs the compose, and then schedules the cleanup. The reason for scheduling the cleanup tasks separately is so that we can return the composed blob as soon as possible, rather than waiting on the cleanup before we do so.

def ensure_results(maybe_futures: List[Any]) -> List[Any]:
    """Pass in a list that may contain a Future(s), and if so, wait for
    the result of the Future and append it; for all other types in the list,
    simply append the value.

    Args:
        maybe_futures (List[Any]): A list which may contain Futures.

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

Something of a stylistic choice, this function serves to let us accept either a list of storage.Blob (which we have from our initial list) or a list of Future[storage.Blob] (which we have from intermediate steps) using the same code. This is what makes our compose_and_cleanup function block until its components are all complete.

def delete_objects_concurrent(blobs, executor, client) -> None:
[...]

def generate_composition_chunks(slices: List,
                                chunk_size: int = 32) -> Iterable[List]:
[...]

def generate_hex_sequence() -> Iterable[str]:
    """Generate an indefinite sequence of hexadecimal integers.

    Yields:
        Iterator[Iterable[str]]: The sequence of hex digits, as strings.
    """
    for i in count(0):
        yield hex(i)[2:]

```


This function simply gives us a very long sequence of hexadecimal digits to use as identifiers for our intermediate accumulators.

This approach trades off some complexity for a great increase in speed. In [this example command line tool](https://github.com/domZippilli/gcsfast/blob/master/gcsfast/cli/upload_standard.py), the technique is used to upload objects using parallel slices.


## Conclusion

Hopefully, this article has shown you how you can use the GCS compose function to create single objects from very large collections of other objects. It's a great thing to be able to do. I want to leave you with a few caveats:

Remember that while there's no limit to the number of components, the 5TB object size limit does still apply. 

It's worth repeating that in the very popular "colder" storage classes, like Nearline, Coldline, and Archive, programmatic composition can lead to unpleasant minimum retention charges, so it's best to use Standard storage class to perform the accumulation and then change the storage class of the composite object.

Finally, note that composite objects do not have MD5 checksums in their GCS metadata. They do have CRC32C checksums, as CRC32C is [commutative](https://stackoverflow.com/a/23050676) and can just be added together (componentA + componentB = objectAB), which suits the compose operation. MD5 has to be calculated using the entire bitstream. GCS computes MD5s during uploads, so a composed object would have to be downloaded and re-uploaded to generate an MD5.

And as always, this code is offered for demonstration purposes only, and should not be considered production-ready. Applying it to your production workloads is up to you!