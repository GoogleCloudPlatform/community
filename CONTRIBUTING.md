# How do I get involved?

## Submit Feedback

We want to hear from you! Each page of official documentation on
[https://cloud.google.com]() has a "Send Feedback" link where you can submit
feedback about an individual page or about a product in general. This is the
best way to help improve the official documentation.

## Write Tutorials

Beyond the official documentation there are endless possiblities for combining
tools, platforms, languages and products. Ultimately, everything you build is
unique, but very often projects share a lot in common. By submitting a tutorial
you can share your experience and help others who are solving similar problems.

Tutorials can be short or long, but in every case they provide context for
using Google Cloud Platform in the real world and show how to solve a particular
problem that may not have been discussed in the official documentation.

Community tutorials are stored in markdown files [on GitHub][github] where they
can be reviewed and editted by the community.

To submit a tutorial:

1. Accept [the CLA][contrib]
1. Your tutorial must adhere to the styleguide to be accepted
1. Fork [github.com/GoogleCloudPlatform/community]()
1. Add a new file to the `tutorials/` folder
1. Commit your changes and open a pull request

You can fork and add a new tutorial in one step by clicking [this link][fork].

### Contributor license agreements

We'd love to accept your contributions! Before we can take them, we have to jump
over a few legal hurdles.

Please fill out either the individual or corporate Contributor License Agreement
(CLA).

  * If you are an individual writing original source code and you're sure you
    own the intellectual property, then you'll need to sign an [individual CLA][in_cla].
  * If you work for a company that wants to allow you to contribute your work,
    then you'll need to sign a [corporate CLA][corp_cla].

Follow either of the two links above to access the appropriate CLA and
instructions for how to sign and return it. Once we receive it, we'll be able to
accept your pull requests.

### Style guide

Here are some style guidelines to help make your content the best it can be.

#### Headings

Headings help give the reader a sense of how your page is organized. Use
headings to organize your page into sections and subsections. Capitalize your
headings like sentences, not like titles. That means only capitalize the first
word and any proper names, such as product names.

#### Lists

Lists help make your page scannable and more easily consumable.

##### Numbered lists

Use numbered lists for sequences, such as tutorial steps. Don't use a numbered
list as a way to count the things in the list. For example:

> 1. Do this.
> 1. Do that.
> 1. Do another thing.

Not:

> There are three colors that I like:
>
> 1. Red.
> 2. Blue.
> 3. Yellow.

##### Bulleted lists

Use bulleted lists for any lists that don't imply a sequence.

> There are three colors that I like:
>
> * Red.
> * Blue.
> * Yellow.

##### Tables

Tables are a great way to help the reader compare a set of items, such as
mutually exclusive options. Tables work especially well when there's a
consistent set of properties for each item in a list.

#### Images

A well-designed bit of artwork or a screen shot can save you a lot of writing
and help the reader to better understand a complex idea. Just make sure any
text is legible. If the image itself becomes to complex, consider breaking it up
into more than one picture.

#### Code

**Style code, command lines, paths, and file names as code**.

Use the following conventions:

* For inline text, use backticks to enclose the text, `like this`.
* For blocks of code or command lines, use indentation in markdown to create a
code block:

    print "This is a code block."
    print "It can have multiple lines."

#### Tone

**Use the right tone**. Be precise, but conversational. Keep in mind that not
everyone speaks English as a first language and many people will rely on machine
translations to understand your content.

#### Simplicity

**Keep it simple**. Don't use long words, jargon, or long sentences when short
and simple will do. The longer the sentence, the more likely that your writing
won't be clear. Don't make the reader work so hard. For example:

> To set a new owner, click Change.

Not:

> It is possible for you to set a different owner by clicking the Change button.

That goes for paragraphs, too. Don't be afraid to keep your paragraphs short and
to the point. For some reason this is more important on the web. People read
differently on the web than when they read books.

#### Voice

**Keep to active voice**. Active voice makes it obvious who is performing the
action, which makes your writing clearer and stronger. For example:

> "The agent writes a line to the log file."

Not:

> "A line is written in the log file by the agent."

It's okay to use passive voice when you'd have to go out of your way to use
active voice. Sometimes the actor isn't entirely clear, so don't try to invent
one; just use passive voice. For example:

> "Your project is created in just a few minutes."

Not:

> "Google Cloud Platform creates a project in just a few minutes."

#### Be direct

**Speak to the reader**. Tutorials just read better if you speak directly to the
reader in the second person. That means use "you" a lot more then "I" or "we".

#### Ordering

**Think about the order**. Write in the order the reader needs to follow, not
the other way around. For example:

> "In the Cloud Console, in the Compute Engine section, on the VM instances page..."

Not:

> "On the VM instances page in the Compute Engine section of the Cloud Console..."

## Publish Datasets

TODO

## Contribute on GitHub

The [github.com/GoogleCloudPlatform]() organization houses open source Google
Cloud Platform projects such as [datalab][datalab],
[gcloud-python][gcloud_python], [DataflowJavaSDK][df_sdk],
[PerfKitBenchmarker][perfkit] and many more. We welcome contributions from the
community.

## Ask and answer on Stack Overflow

Many users ask questions on [Stack Overflow][so], and it's great when community
members who've been in the same situation can share their experience. Keep in
mind that Stack Overflow does not replace official documentation, so when you
answer a question on Stack Overflow, provide links to the relevant documentation
when you can. If the question revealed a gap in the offical
documentation, please click **Send feedback** on
the documentation page and let us know what's misisng or wrong, so we can improve the page.

Many Google Cloud Platform products have their own tags on Stack Overflow, and
you can also find a general [google-cloud-platform][gcp] tag. Most tags are have
the following format: `google-cloud-<product>`. You can find links to the Stack
Overflow channels for various Google Cloud Platform products on the
[Community Support][support] page.

## Discuss on Slack

TODO

[datalab]: https://github.com/GoogleCloudPlatform/datalab
[gcloud_python]: https://github.com/GoogleCloudPlatform/gcloud-python
[df_sdk]: https://github.com/GoogleCloudPlatform/DataflowJavaSDK
[perfkit]: https://github.com/GoogleCloudPlatform/PerfKitBenchmarker
[github]: https://github.com/GoogleCloudPlatform/community
[contrib]: https://github.com/GoogleCloudPlatform/community/blob/master/CONTRIBUTING.md
[fork]: https://github.com/GoogleCloudPlatform/community/new/master/tutorials
[in_cla]: https://developers.google.com/open-source/cla/individual
[corp_cla]: https://developers.google.com/open-source/cla/corporate
[so]: http://stackoverflow.com/
[gcp]: http://stackoverflow.com/questions/tagged/google-cloud-platform
[support]: https://cloud.google.com/support/#community
