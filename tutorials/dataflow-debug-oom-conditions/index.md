---
title: Debugging out-of-memory conditions in Dataflow
description: How to troubleshoot out-of-memory issues in Dataflow pipelines using Java.
author: nahuellofeudo
tags: Dataflow, Java, OutOfMemoryError
date_published: 2020-02-21
---

Nahuel Lofeudo, Google LLC

One of the most common causes of failures and slowdowns in Dataflow pipelines is workers' Java virtual machines running out
of memory. This document is a summary of the information that you need in order to detect and troubleshoot out-of-memory 
(OOM) conditions in workers, either because of bugs or memory leaks or because the workers simply need more memory than the 
system allows them to use.

## The Dataflow worker

The term *worker* is refers to Compute Engine instances that act as processing nodes for Dataflow pipelines. 

These machines run the following: 

* The *user code* that actually transforms data. This is the code that you write, and it may also
  include third-party libraries that your code uses.
* A framework (*harness*) that wraps the user code and communicates data back and forth between it and Dataflow components
  (like Shuffle) and your pipeline's sources and sinks.
* A series of monitoring agents that report statistics, progress, and worker health to the Dataflow backend. Some of this 
  information is displayed in the pipeline's view in Cloud Console.

Dataflow pipelines also run a few additional components to store the pipeline's state, such as intermediate results and
open windows. These components are referred to as *Shuffle*, and there are two versions of them:

  * The original implementation, which Dataflow has been using since the initial release of Dataflow, runs as a separate 
    process in the Compute Engine workers. 
  * A new implementation, known as *Dataflow Shuffle* (for batch pipelines) or *Streaming Engine* (for streaming pipelines),
    runs in a different set of hosts. These Shuffle hosts are in Google's infrastructure and are independent of both your
    project and Compute Engine itself.

Here is a graphical representation of the interaction between user code and Shuffle:

![Diagrams of the interaction between user code and Shuffle](https://storage.googleapis.com/gcp-community/tutorials/dataflow-debug-oom-conditions/worker_shuffle_modes.png)

This diagram simplifies things a little. The implementations of Shuffle for batch and streaming pipelines are different from
each other, but the idea is the same: There is more going on in worker machines than simply running your code.

Inside the Java virtual machine (JVM), the situation is similar: A single memory space (the JVM heap) is used by multiple
threads (one processing thread per CPU core, plus many others) to store information. 

If any of the user code needs to use more than its proportional amount of memory (total size of memory divided by number of
process threads), the JVM could run out of free space and into an out-of-memory condition.

Even though there are hundreds of threads running in worker JVMs, most use a negligible amount of memory. Unless you need to
account for every single kilobyte of memory use, you only need to worry about the process threads (as many as CPU cores, by 
default).

## Signs that you are having out-of-memory issues

Pipelines having out-of-memory issues will often get stuck, or fail with no obvious symptoms (for example, few if any
errors logged in the job's view in Cloud Console).

To confirm that your job is failing because of memory issues, open Cloud Console and go to **Logs** → **Logging** and on the
right side of the text field that says **Filter by label or text search** click the downward-pointing arrow and select
**Convert to advanced filter**.

Use the following filter:

    resource.type="dataflow_step"
    resource.labels.job_id="[YOUR_JOB_ID]"
    ("thrashing=true" OR "OutOfMemoryError" OR "Out of memory" OR "Shutting down JVM")

Click **Submit filter**. (You may also need to click **Load older logs** to search all the logs from the start of the job.)

If you get any results back, then your job is running out of memory.

The messages `"thrashing=true"` and `"OutOfMemoryError"` come from the JVM. They mean that the Java code is exhausting the 
JVM's heap. Later sections of this document explain how to troubleshoot these errors.

The message `"Out of memory: kill process [PID] ([PROCESS_NAME]) score [NUMBER] or sacrifice child"` means that some other
process in the worker is causing the Compute Engine machine itself to run out of RAM. Dataflow workers don't have swap 
space, so once the RAM is all used, there is nothing else left. This message means that the Linux kernel itself has 
started killing processes that threatened the stability of the entire system. If you see this error message, open a support 
ticket or report it to Google. 
 
Other memory-related messages may sound scary but are actually harmless. For example: 

    [GC (Allocation Failure) [PSYoungGen: <n>K -> <n>K (<n>K)], <n> secs] [Times: user=<n> sys=<n>, real=<n> secs]

This message simply means that the JVM needed to run a garbage collection cycle and freed up some memory. The message also
explains how much time (the `real` time) the garbage collection took to run.

## Obtaining a heap dump

If you find that your job is failing due to the JVM running out of memory, you will need to take a heap dump to find out
what is causing the OOM condition.

There are three main ways of obtaining a heap dump from JVMs running in Dataflow workers. In order of preference:
 
* Instruct the pipeline's JVMs to automatically dump their heap on OOM.
* Connect to the worker machine and download the heap through a browser.
* Connect directly to a JVM through JMX.

All options have advantages and disadvantages. Let's go one by one:

### Instructing the pipeline to dump heap on OOM

The best way to obtain heap dumps is to re-run the jobs with these flags:

    --dumpHeapOnOOM
    
    --saveHeapDumpsToGcsPath=gs://[PATH_TO_A_STORAGE_BUCKET]


This will automatically save heap dumps to the specified location when the OOM happens, without any manual intervention. 
Your GCS bucket will have as many .hprof files as JVMs OOM'd (e.g.: if two workers have memory issues, you will have one or more heap dumps for each of the workers).
 
>**Caveat:** the heap dump is saved to the GCE machine's boot disk before being uploaded to GCS, and in jobs running on Dataflow Shuffle or Streaming Engine the root disks are generally too small to store dumps for machines larger than n1-standard-2.
If your job uses Dataflow Shuffle or Streaming Engine,  you will need to use **--diskSizeGb** to increase the size of the workers' disks to hold the memory dump and set it to at least 30GB + the amount of RAM of the machine. Otherwise the heap dump might fail.

>**NOTE:** Make sure that the account the job is running under (normally the Dataflow service account) has write permissions on the bucket.

### Connecting to the worker machine and downloading the heap
This method is easier to carry out but involves manually triggering the memory dump, which means that you will need to keep track of the performance of your pipeline in order to dump the memory when it's about to cause issues.

To create a heap dump, first find the name of the worker of which you want the heap dump and then *SSH into it* by running the following command on your local workstation:

	gcloud compute ssh --project=$PROJECT --zone=$ZONE \
	  $WORKER_NAME --ssh-flag "-L 8081:127.0.0.1:8081"
  
(Replace $PROJECT, $ZONE and $WORKER_NAME with the appropriate values)

The SSH command will open a tunnel from the computer where it's run to the cloud host, and forward port 8081 through it.
Once the ssh command connects and shows you the remote shell, open a browser and navigate to this url:

	http://127.0.0.1:8081/heapz

You will see a link to download the worker's heap dump. After downloading the heap dump you can exit the SSH session.

	**Caveat:** the heap dump is saved to the GCE machine's boot disk before being uploaded to GCS, and in jobs running on Dataflow Shuffle or Streaming Engine the root disks are generally too small to store dumps for machines larger than n1-standard-2.
	If your job uses Dataflow Shuffle or Streaming Engine,  you will need to use --diskSizeGb to increase the size of the workers' disks to hold the memory dump and set it to at least 30GB + the amount of RAM of the machine. Otherwise the heap dump might fail.

### Connecting directly to a JVM through JMX

Every version of Oracle JDK and OpenJDK since 1.6 has included a tool named **VisualVM** which can connect to a running JVM (running locally or in a remote machine through the JMX protocol), monitor its state and extract information live. It should be in the **bin/** directory of your Java home directory.
 
You can use the following command on your local computer to examine the state of the JVM running on any Dataflow worker::

	gcloud compute ssh --project=$PROJECT --zone=$ZONE \
	  $WORKER_NAME --ssh-flag "-L 5555:127.0.0.1:5555"

(remember to replace $PROJECT, $ZONE and $WORKER_NAME with the appropriate values)

Once the ssh command connects and shows you the remote shell, start VisualVM and follow these steps:

1. From the **File** menu, select **Add a JMX connection**.
1. Enter "**localhost:5555**" for the hostname and select "**Do not require SSL connection**"
1. Click on **Ok** and select the tab created for the connection "**localhost:5555**".

At this point VisualVM will start showing telemetry from the remote worker. You will be able to see CPU and memory utilization, threads, and more detailed information. To learn more about VisualVM you can read its official documentation[official documentation](https://visualvm.github.io/documentation.html) .

To create a heap dump through VisualVM, navigate to the **Monitor** tab and click on the **Heap Dump** button. 

The caveat of this method is that the JVM is paused while the memory dump is captured and transferred to your computer. So if your connection is not fast enough to transfer the entire content of your heap in five minutes or less, the Dataflow backend could assume that the worker is dead and restart it. In that case all contents of the JVM's memory would be lost.

## Analyzing the memory dump

Once you have a memory dump it's time to find which objects in the heap are the ones responsible for taking the largest portions of the available memory. One of the easiest tools to use for this purpose is VisualVM.

The first step is to open VisualVM, which should be in the `bin/` directory of your java home directory.


![VisualVM main window](https://storage.googleapis.com/gcp-community/tutorials/dataflow-debug-oom-conditions/visualvm_main.png)

Then use **File** → **Load** and open your HPROF file.

Loading an HPROF file larger than a gigabyte can take some time, as VisualVM needs to parse the entire memory map and generate a graph of all the references between objects. The good news is that all this information is cached on disk so the next time you open the same file it will be much faster.
Once the heap dump has been loaded, switch to the memory view by opening the drop-down labeled **Summary** and selecting **Objects**.

![Select Objects in the drop-down](https://storage.googleapis.com/gcp-community/tutorials/dataflow-debug-oom-conditions/summary_objects.png  "Select Objects in the drop-down")

By default, VisualVM shows all objects by class, sorted by total amount of memory used. To search for causes of OOMs, it's best to start with the list of **Dominators**. A **Dominator** is an object that directly or transitively retains in memory a large number of other objects.
For example, the following is a graph of objects. The arrows represent references from one object to another:

![Object graph](https://storage.googleapis.com/gcp-community/tutorials/dataflow-debug-oom-conditions/object_graph.png  "Graph of objects")
*Object C is a Dominator because it references, and therefore keeps in memory, objects D to H. Source: [help.eclipse.org](https://help.eclipse.org)*

Select **Preset: Dominators** and click on "**Retained**" to show the largest dominators and sort by the amount of memory retained.

Once VisualVM calculates and shows the largest Dominators, see if there is a single object or a single class that can account for a large fraction (over 70%) of the memory used. If so, chances are that any code that deals with that object or that class is what's causing the OOM. 

If you don't recognize the name of the class, you can see which other objects reference the Dominator objects by selecting them on the list and clicking on the button labeled **References**.
That will open a separate pane with the list of objects that reference the object selected above. You will then be able to navigate the chain of references to understand where the Dominator objects are created and referenced (and, therefore, what keeps them in memory).

Once you have found your dominator objects, ask yourself: *Are these dominator objects expected to be this size*?
It's normal for some objects to be relatively large; some examples would be caches and read/write buffers. Understand what the dominator object is, and how large it needs to be. 

But if the objects are in fact too big, the next thing you will need to do is look at source code for signs of bugs. In order to do that, you will need to know where to look: are they part of Apache Beam's codebase, Google's codebase, a third party, or is it part of custom code written by you? 
A good indicator is the package name of the object. If you are unsure, googling the full class name usually points to whatever the code belongs to. With this information, your final step should be to debug the code that manages these objects, if it's custom code, or to contact Google if the objects are from Google or Apache Beam. 

Note: Using larger machines does not necessarily solve Out-Of-Memory problems. Larger machines that come with more memory also have more CPU cores, so the ratio of RAM to cores remains the same, regardless of machine size. N1-standard machines 
have 3.75GB of RAM per core, and n1-highmem machines have 7.5GB of RAM per core. 
 
Dataflow starts as many threads to process data (the threads that run the code in your DoFn's) as there are CPU cores in the worker. Therefore, by default and on average, a DoFn should never use more than one core's worth of RAM. 
For example, for n1-standard workers, your code should never use more than 3.75GB of memory (actually less than that, since other pieces of the worker also need some memory). 
If your code needs more than one core's worth of RAM, you will need to tell Dataflow to use **fewer threads**, running your job with the parameter **--numberOfWorkerHarnessThreads=<n>**. The lower the number of threads, the larger the amount of RAM each one will be able to use.

## Takeaways

Just because your Dataflow workers have a certain amount of RAM installed, that doesn't mean that your code can use all 
of that memory. There are many other things going on in the worker machines.

  * If your pipeline *doesn't* use Dataflow Shuffle (batch) or Streaming Engine (streaming), then the heap available to your 
    code is roughly 40% of the total memory.
  * If your pipeline *does* use Dataflow Shuffle or Streaming Engine, then the heap available to your code is roughly 80% of 
    the total memory.

The java heap is shared across all Java threads and all instances of your DoFn's.

Make sure that each DoFn never uses more than a fraction of the total memory. 

Don't cache or buffer data. Dataflow takes care of that for you. Keep as little state in RAM as possible.

If you run out of memory...
  * Try using highmem workers.
  * Try using fewer threads.
  
If everything else fails, obtain a heap dump and track down the source of the out-of-memory error.
