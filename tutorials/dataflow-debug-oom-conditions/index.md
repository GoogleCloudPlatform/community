---
title: Debugging out-of-memory conditions in Dataflow
description: How to troubleshoot out-of-memory issues in Dataflow pipelines using Java.
author: nahuellofeudo
tags: Dataflow, Java, OutOfMemoryError
date_published: 2020-02-28
---

Nahuel Lofeudo, Google LLC

One of the most common causes of failures and slowdowns in Dataflow pipelines is workers' Java virtual machines running out
of memory. This document is a summary of the information that you need in order to detect and troubleshoot out-of-memory 
(OOM) conditions in workers, either because of bugs or memory leaks or because the workers need more memory than the 
system allows them to use.

## The Dataflow worker

The term *worker* refers to Compute Engine instances that act as processing nodes for Dataflow pipelines. 

These machines run the following: 

* The *user code* that actually transforms data. This is the code that you write, and it may also
  include third-party libraries that your code uses.
* A framework (*harness*) that wraps the user code and communicates data between it and Dataflow components (like Shuffle)
  and your pipeline's sources and sinks.
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
account for every single kilobyte of memory use, you only need to consider the process threads (as many as CPU cores, by 
default).

## Determining whether you are having out-of-memory issues

Pipelines having out-of-memory issues will often get stuck, or fail with no obvious symptoms (for example, few if any
errors logged in the job's view in Cloud Console).

To confirm that your job is failing because of memory issues, do the following:

1.  Open the [Cloud Console](https://console.cloud.google.com/logs/viewer) to the **Logs viewer** page.
1.  On the right side of the text field that says **Filter by label or text search**, click the downward-pointing arrow
    and select **Convert to advanced filter**.
1.  Enter the following filter:

        resource.type="dataflow_step"
        resource.labels.job_id="[YOUR_JOB_ID]"
        ("thrashing=true" OR "OutOfMemoryError" OR "Out of memory" OR "Shutting down JVM")

1.  Click **Submit filter**.

    In some cases, you might need to click **Load older logs** to search all logs from the start of the job.

If you get any results back, then your job is running out of memory.

The messages `"thrashing=true"` and `"OutOfMemoryError"` come from the JVM. Generally, these messages mean that the Java
code is exhausting the JVM's heap. Later sections of this document explain how to troubleshoot these errors. Note that some 
classes throw `OutOfMemoryError` even if they have enough heap memory. For example,
[ByteArrayOutputStream](https://github.com/openjdk/jdk/blob/jdk8-b120/jdk/src/share/classes/java/io/ByteArrayOutputStream.java#L110) cannot grow over 2GB. Check the stacktrace of 
`OutOfMemoryError` to see if your job has hit this case.

The message `"Out of memory: kill process [PID] ([PROCESS_NAME]) score [NUMBER] or sacrifice child"` means that some other
process in the worker is causing the Compute Engine machine itself to run out of RAM. Dataflow workers don't have swap 
space, so when the RAM is all used, there is nothing else left. This message means that the Linux kernel itself has 
started killing processes that threatened the stability of the entire system. If you see this error message, 
[contact Google support](https://console.cloud.google.com/support). 
 
Other memory-related messages may sound scary but are actually harmless. For example: 

    [GC (Allocation Failure) [PSYoungGen: <n>K -> <n>K (<n>K)], <n> secs] [Times: user=<n> sys=<n>, real=<n> secs]

This message simply means that the JVM needed to run a garbage collection cycle and freed up some memory. The message also
explains how much time (the `real` time) the garbage collection took to run.

## Obtaining a heap dump

If you find that your job is failing due to the JVM running out of memory, take a heap dump to determine what is causing
the out-of-memory (OOM) condition.

There are three main ways of obtaining a heap dump from JVMs running in Dataflow workers. In order of preference:
 
* Instruct the pipeline's JVMs to automatically dump their heap when out of memory.
* Connect to the worker machine and download the heap through a browser.
* Connect directly to a JVM through JMX.

Each of these options has advantages and disadvantages, as discussed in the following sections.

### Instruct the pipeline to dump heap on OOM

The best way to obtain heap dumps is to re-run the jobs with these flags:

    --dumpHeapOnOOM
    --saveHeapDumpsToGcsPath=gs://[PATH_TO_A_STORAGE_BUCKET]

Running a job with these flags automatically saves heap dumps to the specified location when the out-of-memory condition
happens, without any manual intervention. 

Your Cloud Storage bucket will have as many heap dump (`.hprof`) files as JVMs that have run out of memory.
 
The heap dump is saved to the Compute Engine machine's boot disk before being uploaded to Cloud Storage. For jobs running on
Dataflow Shuffle or Streaming Engine, the root disks are generally too small to store dumps for machines larger than
n1-standard-2. Therefore, if your job uses Dataflow Shuffle or Streaming Engine, use `--diskSizeGb` to increase the size of
the workers' disks to hold the memory dump; set the disk size to at least 30 GB + *the amount of RAM of the machine*. 
Otherwise, the heap dump might fail.

Make sure that the account that the job is running under (normally the Dataflow service account) has write permissions on 
the bucket.

### Connect to the worker machine and download the heap

Connecting to the worker and downloading the heap is easier to carry out but involves manually triggering the memory dump, 
which means that you would need to keep track of the performance of your pipeline in order to dump the memory when it's 
about to cause problems.

To create a heap dump, first find the name of the worker for which you want the heap dump and then connect to it using SSH
by running the following command on your local workstation:

    gcloud compute ssh --project=$PROJECT --zone=$ZONE \
      $WORKER_NAME --ssh-flag "-L 8081:127.0.0.1:8081"

Replace `$PROJECT`, `$ZONE` and `$WORKER_NAME` with the appropriate values.

The SSH command opens a tunnel from the computer where it's run to the cloud host and forwards port 8081 through it.

After the `ssh` command completes and shows you the remote shell, open a browser and navigate to this URL:

    http://127.0.0.1:8081/heapz

You will see a link to download the worker's heap dump. After downloading the heap dump, you can exit the SSH session.

The heap dump is saved to the Compute Engine machine's boot disk before being uploaded to Cloud Storage. For jobs running on
Dataflow Shuffle or Streaming Engine, the root disks are generally too small to store dumps for machines larger than
n1-standard-2. Therefore, if your job uses Dataflow Shuffle or Streaming Engine, use `--diskSizeGb` to increase the size of
the workers' disks to hold the memory dump; set the disk size to at least 30 GB + *the amount of RAM of the machine*. 
Otherwise, the heap dump might fail.

### Connect directly to a JVM through JMX

Every version of Oracle JDK and OpenJDK since 1.6 has included VisualVM, which can connect to a running JVM running locally
or in a remote machine through the JMX (Java Management Extensions) protocol, monitor its state, and extract information 
live. VisualVM is in the `bin/` directory of your Java home directory.
 
You can use the following command on your local computer to examine the state of the JVM running on any Dataflow worker:

    gcloud compute ssh --project=$PROJECT --zone=$ZONE \
      $WORKER_NAME --ssh-flag "-L 5555:127.0.0.1:5555"

Replace `$PROJECT`, `$ZONE` and `$WORKER_NAME` with the appropriate values.

After the `ssh` command completes and shows you the remote shell, start VisualVM and follow these steps:

1.  In the **File** menu, select **Add a JMX connection**.
1.  Enter `localhost:5555` for the hostname.
1.  Select **Do not require SSL connection**.
1.  Click **OK**.
1.  Select the tab created for the connection **localhost:5555**.

VisualVM starts showing telemetry from the remote worker. You can see CPU and memory utilization, threads, and more detailed
information. To learn more, see [VisualVM Documentation and Resources](https://visualvm.github.io/documentation.html).

To create a heap dump with VisualVM, go to the **Monitor** tab and click the **Heap Dump** button. 

The JVM is paused while the memory dump is captured and transferred to your computer. So, if your connection is not fast 
enough to transfer the entire content of your heap in five minutes or less, the Dataflow backend could assume that the 
worker is dead and restart it. In that case, all contents of the JVM's memory would be lost.

## Analyzing the memory dump

After you have gotten a memory dump, it's time to find which objects in the heap are the ones responsible for taking the 
largest portions of the available memory. One of the easiest tools to use for this purpose is VisualVM.

### View the memory dump

1.  Open VisualVM, which is in the `bin/` directory of your Java home directory.

    ![VisualVM main window](https://storage.googleapis.com/gcp-community/tutorials/dataflow-debug-oom-conditions/visualvm_main.png)

1.  Select **File** → **Load** and choose your heap dump (`.hprof`) file.

    The first time that you load a large heap dump file (e.g., larger than a gigabyte), it can take a long time. VisualVM
    needs to parse the entire memory map and generate a graph of all of the references between objects. This information is
    cached on disk, so loading the same file again is faster.

1.  After the heap dump has been loaded, switch to the memory view by opening the **Summary** menu and selecting
    **Objects**.

    ![Select Objects in the drop-down](https://storage.googleapis.com/gcp-community/tutorials/dataflow-debug-oom-conditions/summary_objects.png)

    By default, VisualVM shows all objects by class, sorted by the total amount of memory used. To search for causes of
    out-of-memory conditions, it's best to start with the list of *dominators*. A dominator is an object that directly
    or transitively retains in memory a large number of other objects.
    
    For a graphical example of object references and dominators, see the
    [Eclipse Platform documentation](https://help.eclipse.org/2019-12/topic/org.eclipse.mat.ui.help/concepts/dominatortree.html?cp=60_2_3).

1.  Select **Preset: Dominators** and click **Retained** to show the largest dominators and sort by the amount of memory 
    retained.

### Understanding the memory dump and memory usage

When VisualVM calculates and shows the largest dominators, see if there is a single object or a single class that can
account for a large fraction (over 70%) of the memory used. If so, chances are that any code that deals with that object
or that class is what's causing the out-of-memory condition. 

If you don't recognize the name of the class, you can see which other objects reference the dominator objects by   
selecting them in the list and clicking the button labeled **References**. This opens a separate pane with the list of 
objects that reference the selected object. You can then navigate the chain of references to understand where the
dominator objects are created and referenced (and, therefore, what keeps them in memory).

When you have found your dominator objects, ask yourself "Are these dominator objects expected to be this size?"

It's normal for some objects to be relatively large, such as caches and read/write buffers. Understand what the dominator
object is, and how large it needs to be. 

If the objects are bigger than you think they should be, the next thing to do is to look at the source code for signs of
bugs. To do that, you need to know where to look: Are they part of the Apache Beam codebase, the Google codebase, the 
codebase of some third party, or some custom code written by you? A good indicator is the package name of the object: If you 
are unsure, doing a public internet search for the full class name usually points to whatever the code belongs to. With this
information, your next step should be to debug the code that manages these objects, if it's custom code, or to contact
Google if the objects are from Google or Apache Beam. 

Using larger machines does not necessarily solve out-of-memory problems. Larger machines that come with more memory also 
have more CPU cores, so the ratio of RAM to cores remains the same, regardless of machine size; n1-standard machines have
3.75GB of RAM per core, and n1-highmem machines have 7.5GB of RAM per core. 

Dataflow starts as many threads to process data (the threads that run the code in your DoFn methods) as there are CPU cores
in the worker. Therefore, on average, a DoFn should never use more than one core's worth of RAM. For example,
for n1-standard workers, your code should never use more than 3.75GB of memory (actually less than that, since other pieces
of the worker also need some memory). If your code needs more than one core's worth of RAM, you need to tell Dataflow to use 
fewer threads; you do this by running your job with the parameter `--numberOfWorkerHarnessThreads=[n]` (replacing `[n]` with 
the number of threads to use. The lower the number of threads, the larger the amount of RAM each one will be able to use.

## Takeaways

* Just because your Dataflow workers have a certain amount of RAM installed, that doesn't mean that your code can use all 
  of that memory. There are many other things going on in the worker machines.

  * If your pipeline *doesn't* use Dataflow Shuffle (batch) or Streaming Engine (streaming), then the heap available to your 
    code is roughly 40% of the total memory.
  * If your pipeline *does* use Dataflow Shuffle or Streaming Engine, then the heap available to your code is roughly 80% of 
    the total memory.

* The Java heap is shared across all Java threads and all instances of your DoFns.

* Make sure that each DoFn never uses more than a fraction of the total memory. 

* Don't cache or buffer data. Dataflow takes care of that for you. Keep as little state in RAM as possible.

* If you run out of memory, then try the following:
  * Use highmem workers.
  * Use fewer threads.
  
* If everything else fails, obtain a heap dump and track down the source of the out-of-memory condition.
