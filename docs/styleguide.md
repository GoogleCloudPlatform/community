This document provides guidance for contributors to the Google Cloud Platform (GCP) Community site.

## Types of documentation

Documentation submitted by contributors is usually one of two types:

+  **Concept**: Helps the user gain deeper understanding of a product or architecture. Concept docs answer questions such as "What is X?" and "How does X work?" They don't provide specific walkthroughs. They might contain numbered steps as generic examples, but this is rare.

  **Example**: [Building Scalable and Resilient Apps](https://cloud.google.com/solutions/scalable-and-resilient-apps)


+  **Tutorial**: Walks a user through a real-world, industry-specific, or end-to-end development scenario that uses your product. Tutorials teach, "How to do Y in the context of ABC." Tutorials contain numbered steps that prescribe what to do. They can have enough supporting conceptual information, interspersed among the steps, to help the reader understand what they're doing, why they're doing it, and how and why it works. The end result is a working example. Usually, code on GitHub supports the document.

  **Example**: [Setting Up PostgreSQL](https://cloud.google.com/solutions/set-up-postgres)


## Designing a doc

Just as you design an app before you start coding, designing how your doc works before you write saves you writing time, helps focus your document, and helps to make sure you're giving the reader the right information. [A good way to design your document is by outlining](https://owl.english.purdue.edu/owl/resource/544/02/). 

As you develop your outline, ask yourself:

+  In one sentence, what is my doc about? You can reuse a version of this sentence as the opener in the doc.
+  What does my reader need to know before they can understand the contents? This question can lead to a set of prerequisites.
+  Why does the reader care? This information will be part of your introduction.
+  Am I building concepts for the reader from most general to most specific?
+  Am I introducing ideas in the right order?
+  Is there anything I can remove?
+  Is there anything missing?
+  Have I made the right assumptions about my audience?

The following sections show the main, top-level organization for the concept and tutorial doc types. Use these sections to start your outlines.


### Writing a Concept doc

A Concept doc has these major sections:

+  Title
+  Overview
   +  Don't use the heading "Overview" or any other heading. Just start at the first sentence.
+  Body
   +  Provides the details.
   +  Contains headings and subheadings as needed to make the content easy to skim.

### Writing a Tutorial

A Tutorial doc has these major sections. Items in bold below are literal heading names:

+  Title
+  Overview
   +  First sentence tells what the page is about
   +  Tell the user what they're going to learn and provide any concise background information that's helpful.
   +  Don't use the heading "Overview." Just get right to it.

+  **Objectives**
   +  A short, bulleted list of what the tutorial teaches the reader.

+  **Before you begin**
   +  A numbered list of steps required to set up for the tutorial.
   +  Any general prerequisites.
   +  Don't assume anything about the user's environment. Assume that the user has only basic operating system installed. If doing the tutorial requires the user to have a specific environment, state what is required. For easy-to-install environment bits, just give them the instructions, such as "Run apt-get install…". For more-complex setups, link to official documentation.

+  **Costs** (optional)
   +  Tell the reader which technologies will be used and what it costs to use them.
   +  Link to the [Pricing Calculator](https://cloud.google.com/products/calculator/), preconfigured, if possible.
   +  If there are no costs to be incurred, state that.

+  Body
   +  Use as many headings and subheadings as needed.
   +  Use numbered steps in each section.
   +  Start each step with the action: "Click", "Run", "Enter", and so on.
   +  Keep numbered step lists to around 7 or less, if possible. If you need more steps, break it up into subheadings.
   +  Provide context and explain what's going on.
   +  Use screenshots when they help the reader. Don't provide a screenshot for every step.
   +  Show what success looks like along the way. For example, showing console output or describing what happens helps the reader to feel like they're doing it right and help them know things are working so far.

+  **Cleaning up**
   +  Omit this section if you stated there are no costs in the Costs section.
   +  Tell the user how to shut down what they built to avoid incurring further costs.


## General content guidelines

This site seeks technical content. While it's fine and often appropriate to point out the advantages of a particular product or Cloud Platform, don't give sales pitches in the document. Here are some guidelines:

+  Write for a technical audience.
+  If the document looks like a sales brochure, it's not appropriate as GCP content.
+  Avoid superlatives. Don't say "the best", "amazing", "fantastic", and so on. No exclamation points.

### Ambiguity

Ambiguity is the enemy of technical content. Re-read what you've written to check whether it can be read to mean more than one thing.

### Repetition

Avoid needless repetition. Telling the reader a fact one time usually suffices. 

## General style guidelines

Here are style guidelines to help you craft a great article.

### Headings

Use headings to organize your page into sections and subsections. Headings make it easier for readers to skim and understand what the article is about. Capitalize only the first word and product names in your headings.

**For example:**

Creating a new object

**Not:**

Creating a New Object


### Lists

Lists help make your page more scannable.


### Numbered lists

Use numbered lists when it’s essential that the items be done in a specific order. Otherwise, use a bulleted list. Don't use a numbered list as a way to count the things in the list.

**For example:**

1. Do this.
1. Do that.
1. Do another thing.

**Not:**

There are three colors that I like:

1. Red
1. Blue
1. Yellow

**Think about the order**. When writing instructions, give the reader orientation cues in the proper order. Think about moving someone's eyes around the screen.

**For example:**

"Click the OK button in the Cloud Console, on the VM instances page, in the Compute Engine section."

**Not this**, because it causes someone to visually search backwards:

"Click the OK button in the Compute Engine section of the VM instances page of the Cloud Console."


### Bulleted lists

Use bulleted lists for lists that don't imply a sequence. End each item with a period if the item is a sentence or a phrase. Don't use periods for lists of single words or if the list contains only product names.

**For example:**

I have three favorite colors:

+  Red
+  Blue
+  Yellow


### Parallelism

Try to keep your language across list items in a similar format. For example, start each item with a noun or a verb, but don't mix the formats.

**For example:**

+  Write the docs.
+  Write them well.
+  Enjoy the process.

**Not:**

+  Write the docs.
+  The docs should be great.
+  You can have fun writing the docs.


### Tables

Tables are a great way to help the reader compare a set of items, such as mutually exclusive options. Tables work well when there's a consistent set of properties for each item in a list.

Use the parallelism principle previously described for table headings and the first column.


### Images

A well-designed diagram or a screen shot can save you a lot of writing and help the reader better understand a complex idea. Make sure any text is legible at the display size in the doc (800 pixels wide or less). If the image itself becomes too complex, consider breaking it up into more than one picture.


### Code

Format code, command lines, paths, and file names as code font.


## Voice and tone

### Active voice

**Use active voice**. Active voice makes it obvious who is performing the action, which makes your writing clearer and stronger.

**For example**:

"The logging agent writes a line to the log file."

**Not**:

"A line is written in the log file by the logging agent."

It's okay to use passive voice when you'd have to go out of your way to use active voice. For example, sometimes you don't need to include the actor in the sentence because the actor isn't relevant. Just use passive voice, instead.

**For example:**

"RFID tag readers are typically positioned in multiple locations in a retail store."

**Not:**

"System engineers typically place RFID tag readers in multiple locations in a retail store."


### Direct

**Speak to the reader**. Documentation reads better if you speak to the reader in the second person. That means use "you" and avoid "I" or "we".

**For example:**

"Now load your data into BigQuery. Follow these steps: ..."

**Not:**

"Now we'll load the data into BigQuery."


### Present tense

**Keep to present tense**. Avoid using future or past tenses.

**For example:**

"The Cloud Console downloads a JSON file to your computer."

**Not:**

"The Cloud Console will download a JSON file to your computer."


### Simple

**Keep it simple**. Use short, simple sentences. They are easier for readers to parse and understand. Omit unnecessary words.

**For example:**

"Click Change to set a new owner."

**Not:**

"It is possible for you to set a different owner by clicking the Change button."
Also keep your paragraphs short and to the point. On the web, people skim more and expect shorter content than when they read books. Five sentences or less per paragraph is a good guideline.

If a sentence is long, even with  straightforward word choices, break it up into multiple, shorter sentences.

Re-read what you wrote and then eliminate all the unnecessary words.


## Linking

Provide inline links to relevant information, where appropriate. For example, link to:

+  "One source of truth" content.
+  Anything that's likely to go out of date quickly if you copied it into your article.
+  Information that gives more depth than is appropriate for the current context.

Provide direct links to pages in the Google Cloud Console when you give Cloud Console-based instructions. These _deep links_ save the reader time spent looking for the right page and can save you time writing descriptions of how to find the page. Deep links open the page with the project set to the user's last-used project.


## What’s next

Learn more about strong writing.

+  [What is plain language?](http://plainlanguagenetwork.org/plain-language/what-is-plain-language/#.V1HvQXUrLOF)
+  [Purdue Online Writing Lab](https://owl.english.purdue.edu/sitemap/) (OWL)
+  [Grammar Girl](http://www.quickanddirtytips.com/grammar-girl)
+  [The Elements of Style](http://www.amazon.com/Elements-Style-Fourth-William-Strunk/dp/020530902X/ref=sr_1_1?ie=UTF8&qid=1463012361&sr=8-1&keywords=the+elements+of+style+book) (book by Strunk and White)
+  [The Deluxe, Transitive Vampire](http://www.amazon.com/Deluxe-Transitive-Vampire-Ultimate-Handbook/dp/0679418601) (book by Karen Elizabeth Gordon)
