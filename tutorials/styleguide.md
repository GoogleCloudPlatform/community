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
[Google style guide for developer documentation](https://developers.google.com/style/).

## Caveats

Before getting into the details of how to write and structure a document, here are some basic restrictions to keep in mind:

* Don't sell or do marketing.
* Don't editorialize. Instruct.
* Don't make assumptions about your reader unless you state the assumptions up front.
* Don't use absolutes and superlatives (such as _instantaneously_, _perfectly_, _100%_, or _the best_) unless you can back up what you're saying with
  documentation.
* Don't make performance claims unless you back them up with current data. This means either external links, or links to benchmarking code.
* Don't use logos or trademarks unless you have explicit permission.
* Don't include diagrams or pictures that you have no legal rights to include.
* Don't alter, truncate, or abbreviate Google Cloud product names. For example, it’s _Cloud Storage_, not _GCS_.

## Visual assets

Google Cloud offers a set of logos and architectural diagram assets for your use:

[https://cloud.google.com/icons/](https://cloud.google.com/icons/)


## Template for writing a tutorial

A tutorial has these major sections. Items in bold below are literal heading names.

* Title
* Overview
    * First sentence tells what the page is about
    * Tell the user what they're going to learn and provide any concise background information that's helpful.
    * Don't use the heading "Overview." Just get right to it.

* **Objectives**
    * A short, bulleted list of what the tutorial teaches the reader.

* **Before you begin**
    * A numbered list of steps required to set up for the tutorial.
    * Any general prerequisites.
    * Don't assume anything about the user's environment. Assume that the user has only basic operating system installed. If doing the tutorial requires the user to have a specific environment, state what is required. For easy-to-install environment bits, just give them the instructions, such as "Run apt-get install…". For more complex setups, link to official documentation.

* **Costs** (optional)
    * Tell the reader which technologies will be used and what it costs to use them.
    * Link to the [Pricing Calculator](https://cloud.google.com/products/calculator/), preconfigured, if possible.
    * If there are no costs to be incurred, state that.

* Body
    * Use as many headings and subheadings as needed.
    * Use numbered steps in each section.
    * Start each step with the action: "Click," "Run," "Enter," and so on.
    * Keep numbered step lists to around 7 or less, if possible. If you need more steps, break it up into subheadings.
    * Provide context and explain what's going on.
    * Use screenshots when they help the reader. Don't provide a screenshot for every step.
    * Show what success looks like along the way. For example, showing console output or describing what happens helps the reader to feel like they're doing it right and help them know things are working so far.

* **Cleaning up**
    * Omit this section if you stated there are no costs in the Costs section.
    * Tell the user how to shut down what they built to avoid incurring further costs.

## File organization in GitHub

Follow these guidelines for how to organize your documents:

* Create a new folder for your document.
* Name the folder by [slugifying](http://slugify.net/) your doc's title. You can omit articles such as "and" and "the."
* Name your new doc `index.md`.
* Store images in the same folder.

For example, if you submit a tutorial named "Using Cloud SQL to Conquer the World":

* **Folder name**: `using-cloud-sql-conquer-world`
* **URL**: `https://cloud.google.com/community/tutorials/using-cloud-sql-conquer-world/`

If you don't have any additional files that go along with your tutorial, you can
simply make a top-level Markdown file within the `tutorials/` folder, e.g.
`tutorials/using-cloud-sql-conquer-world.md` instead of
`tutorials/using-cloud-sql-conquer-world/index.md`.

## Including source code

Format code, command lines, paths, and file names as code font.

If you would like to include source code within your tutorial, you have two
options:

### Embedding code in the tutorial file

Just embed the source code directly in the tutorial. Wrap the code in three
backticks or indent by four spaces to achieve proper formatting.

This option is the simplest, but offers no way to test the code, and does not
allow the user to view actual source code files as they might exist in a real
project.

For an example, see [Run Koa.js on Google App Engine Flexible Environment](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/run-koajs-on-google-app-engine.md).

### Including separate code files alongside the tutorial file

Instead of creating a Markdown file at the top level the `tutorials/` directory, create a folder for
your files. The Markdown for the tutorial should be in an `index.md` file within
the new folder, and the rest of the source code files must be in the new folder,
as well. You can use [EmbedMd](https://github.com/campoy/embedmd) to include
snippets from the source code files in the Markdown file. You should run the
`embedmd` program on  `index.md` to actually  include the code block in the
Markdown source in one of the commits for your pull request.

This option is more complicated, but it allows us to test the code, and it allows the
user to view real source code files.

For an example, see
[Webpack on App Engine flexible environment](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/appengine-nodejs-webpack).
