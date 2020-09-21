---
title: Contribute a tutorial for the Google Cloud Community site
description: Learn how to submit a tutorial for the Google Cloud community site.
author: kopriva
tags: template, submit
date_published: 2020-09-21
---

We welcome the contribution of any tutorial that shares knowledge about how to use Google Cloud.

The source for each tutorial is a Markdown file in the [Google Cloud Community GitHub repository](https://github.com/GoogleCloudPlatform/community).
Each tutorial may be accompanied by example source code and other assets alongside the tutorial in the repository.

## Accept the Contributor License Agreement

For us to accept your contributions, we need you to sign the [Contributor License Agreement (CLA)](https://cla.developers.google.com/about):

  * If you are an individual writing original content and you own the intellectual property, then you sign an
    [individual CLA](https://developers.google.com/open-source/cla/individual).
  * If you work for a company that wants to allow you to contribute your work,
    then you sign a [corporate CLA](https://developers.google.com/open-source/cla/corporate).

## Contribute a tutorial

1.  Read the [style guide](https://cloud.google.com/community/tutorials/styleguide) before preparing your submission.

1.  Fork the [`github.com/GoogleCloudPlatform/community`](https://github.com/GoogleCloudPlatform/community) repository.

1.  Add the new tutorial file by doing one of the following:
    
    * Create a uniquely named `.md` file at the top level of the `tutorials` folder.
    * Create a new folder for your tutorial in the `tutorials` folder and create a `.md` file at the top level of that subfolder.
    
1.  Copy the contents of the [tutorial template](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/tutorial-template/index.md)
    into your new Markdown file.
    
1.  Replace the template content with your own tutorial content, following the instructions in the template.
        
1.  Commit your changes and open a [pull request](https://help.github.com/articles/using-pull-requests/).

    After you create a pull request, a reviewer reviews your submission. The reviewer will make some editorial and production changes to the tutorial
    directly to ensure that it follows the style guide. The reviewer may also leave comments asking for changes or clarifications. 
    
1.  Work with the reviewer to resolve any issues found during the review.

After your pull request is approved, the reviewer will merge the pull request. New tutorials and fixes are typically published to the
[Google Cloud Community site](https://cloud.google.com/community/tutorials) within a few days of pull requests being merged.
