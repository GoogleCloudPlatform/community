---
title: Contribute a document for the Google Cloud Community site
description: Learn how to submit a tutorial or other document for the Google Cloud community site.
author: kopriva
tags: template, submit
date_published: 2020-09-21
---

We welcome the contribution of any tutorial or other document that shares knowledge about how to use Google Cloud.

The source for each document is a Markdown file in the [Google Cloud Community GitHub repository](https://github.com/GoogleCloudPlatform/community).
Each document may be accompanied by example source code and other assets alongside the document in the repository.

## Accept the Contributor License Agreement

For us to accept your contributions, we need you to sign the [Contributor License Agreement (CLA)](https://cla.developers.google.com/about):

  * If you are an individual writing original content and you own the intellectual property, then you sign an
    [individual CLA](https://developers.google.com/open-source/cla/individual).
  * If you work for a company that wants to allow you to contribute your work,
    then you sign a [corporate CLA](https://developers.google.com/open-source/cla/corporate).

## Contribute a document

1.  Read the [style guide](https://cloud.google.com/community/tutorials/styleguide) before preparing your submission.

1.  [Fork](https://docs.github.com/en/free-pro-team@latest/github/getting-started-with-github/fork-a-repo) the
    [`github.com/GoogleCloudPlatform/community`](https://github.com/GoogleCloudPlatform/community) repository.

1.  Do one of the following to add the new document file:
    
    * If you are contributing a single document file with no supporting code or image files, then create a uniquely named `.md` file at the top level of the
      `tutorials` folder.
    * If you are contributing a document with supporting code or image files, then create a new folder for your document in the `tutorials` folder and create an
      `index.md` file at the top level of that subfolder.
      
    For details, see [File organization and naming in GitHub](https://cloud.google.com/community/tutorials/styleguide#file_organization_in_github).
    
1.  Copy the [Markdown source contents](https://raw.githubusercontent.com/GoogleCloudPlatform/community/master/tutorials/tutorial-template/index.md) of the
    [tutorial template](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/tutorial-template/index.md)
    into your new Markdown file.
    
1.  Replace the template content with your own document content, following the instructions in the template and style guide.
        
1.  Commit your changes and open a [pull request](https://help.github.com/articles/using-pull-requests/).

    After you create a pull request, a reviewer reviews your submission. The reviewer will directly make some editorial and production changes to the document
    to ensure that it follows the guidelines. The reviewer may also leave comments asking for changes or clarifications. 
    
1.  Work with the reviewer to resolve any issues found during the review.

After your pull request is approved, the reviewer will merge the pull request. New documents and fixes are typically published to the
[Google Cloud Community site](https://cloud.google.com/community/tutorials) within a few days of pull requests being merged.
