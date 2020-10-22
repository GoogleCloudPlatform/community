---
title: Google Cloud Community tutorial style guide
description: Learn about style guidelines for writing Google Cloud community tutorials.
author: kopriva,jimtravis
tags: write, edit, review, template
date_published: 2020-09-21
---

This document provides guidance for contributors to the Google Cloud Community site.

The [Google Cloud Community site](https://cloud.google.com/community/tutorials) includes a wide range of documents that show people how to use Google Cloud in
various scenarios and with various tools and resources. To make it easier for you to write documents and to make it easier for your readers to use the documents,
we provide some basic guidelines that documents on this site must follow.

Much of the material in this style guide is derived from the more comprehensive
[Google developer documentation style guide](https://developers.google.com/style/). For general style matters—such as capitalization, tone, voice, and
punctuation—see the main developer documentation style guide.

## Voice, tone, and general guidance

Here are some general guidelines to keep in mind:

* Instruct the reader. Don't sell, market, or editorialize.
* Tell the reader at the beginning what assumptions you're making in the tutorial.
* Don't use absolutes and superlatives (such as _instantaneously_, _perfectly_, _100%_, or _the best_) unless you can back up what you're saying with
  documentation.
* Only make performance claims that you can back up with current data.
* Only use logos, diagram, images, and trademarks for which you have explicit permission.
* Don't alter, truncate, or abbreviate Google Cloud product names. For example, it’s _Cloud Storage_, not _GCS_.

## Visual assets

Google Cloud offers a [library of logos, icons, and architectural diagram assets](https://cloud.google.com/icons/) for your use.

## File organization and naming in GitHub

How you name and organize your files in GitHub depends on whether you are submitting
a single standalone tutorial file or submitting a tutorial file with a set of supporting
files, such as images and source code.

### Contribute supporting files with the tutorial

If you have additional image or source code files that go along with your tutorial,
do the following in GitHub:

1.  Create a new folder for your document.
1.  Name the folder with key words from your title, separated by hyphens,
    omitting words like *and* and *the*.

    For example, if you submit a tutorial named "Using Cloud SQL to conquer
    the world", name your folder `using-cloud-sql-conquer-world`.

1.  Name your new document file `index.md`.
1.  Store images and source code in the same folder.
1.  (Optional) Use [EmbedMd](https://github.com/campoy/embedmd) to include
    snippets from the source code files in the `index.md` Markdown file.

### Contribute a single standalone tutorial file

If you don't have additional files that go along with your tutorial, do the
following in GitHub:

1.  Make a single Markdown file at the top level of the `tutorials/` folder.

1.  Name your new document file with key words from your title, separated by
    hyphens, omitting words like *and* and *the*.

    For example, if you submit a tutorial named "Using Cloud SQL to conquer
    the world", name your file `using-cloud-sql-conquer-world.md`.

## Follow the tutorial template

We provide a tutorial template that explains and demonstrates each part of a tutorial document.

1.  Copy the [Markdown source contents](https://raw.githubusercontent.com/GoogleCloudPlatform/community/master/tutorials/tutorial-template/index.md)
    of the [tutorial template](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/tutorial-template/index.md) file into
    your new Markdown file.

1.  Replace the explanations and examples in the template with your tutorial content.
