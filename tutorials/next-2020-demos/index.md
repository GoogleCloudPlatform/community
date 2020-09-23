# Launching code you didn't write: 
## Shipping demos at scale for Next 2020

Our biggest conference of the year can't happen in person. We're pushing everything online. That's fine, we're Google, we know how to do websites. And demos. And apps. We got this!

Turns out there were some hiccups along the way. Settle down with your favorite beverage, I'd like to tell you a story.

Back in the spring, as we were gearing up for Cloud Next 2020, Terry Ryan (@tpryan) and the Cloud Marketing team put their heads together to figure out what a fully online Next conference would be like. Demos are always a big part of Next, giving Google's product teams a chance to show off new products and features to a large audience, in person. These demos are often interactive, frequently eye-catching, and meant to both excite and educate. They include  staffers available to walk attendees through a demo and to explain the complicated bits. A lot to accomplish in person; now even harder to move them entirely online!

Terry took the lead on making this all happen, working across 27 demos to oversee building, testing and deploying these projects to the NextOnAir site in time for the summer launch. Below we'll talk through some lessons learned from that process, and some of what he built to accomplish this feat.

Each demo had an agency (or a Google team) behind it, doing the coding and visual development. Each one their own application, using whatever frontend framework that team is most comfortable with, or best fits the use case. The teams had a lot of flexibility in making their choice: in the end they just needed to deliver a web app that we would host.

For a single demo we would usually start with a core idea. Here's the thing we want to communicate, or we want to announce and show off. Then the creative team assembles a storyboard, plotting out a series of visuals and narrative. At this stage the demo is light on technical details, and more focused on how people consume and experience it.

Next we head to implementation, where the developer team works to create what the designers envisioned. Here's our first challenge, on the Google side:
##	1: How do we get code from the agencies?

In the past it was usually all over the place: an emailed .zip file, a Github repo, a Drive folder…. Almost anything you can imagine! We knew that wouldn't scale. So Terry set up a Github repo for each demo for the agencies to push code to, allowing a single control plane (and logging system) to manage all the demo code. Already a major improvement, and much simpler to manage.

Additionally, now that every demo is going through Github, we can use some existing Continuous Integration / Continuous Deployment (CICD) tools to automate. Without automation every step of the way Terry would have to manually push each build or each demo to get them published. Not a fun manual chore.. Well, let's just say we want Terry to still talk to us after this all launches.

Okay, next challenge:
##	2: How do we update these demos in production when code changes?

Lucky for us we have strong integrations between Cloud Build and Github, so we can trigger a new build each time the master branch is updated in Github (by the team making that demo). We can even automate deploying that new build to App Engine to speed things up.

All code hosted by Google is required to pass through rigorous security and privacy reviews. This is true in all cases but even more important when the code is created by a third party. However these projects frequest require multiple last minute, urgent updates in response to stakeholder requests. 
##	3: How do we control deployment so only reviewed code is pushed?

In most cases, third party code has to be pushed to Google hosted sites by a Google employee,  so Terry had to be a bottleneck there. With Github tools, he could prevent unapproved merging of pull requests, set himself up as the required reviewer, then approve the code to trigger a push to the production version  of the App Engine apps, so nothing would get into production without his express authorization. 

With this system in place Terry was able to manage a rapid flurry of updates as the deadlines approached, even if all he had was his phone! But with so much happening simultaneously, there's still another challenge:
##	4: How do we keep these systems moving forward consistently?

For that Terry made scripts. So many scripts!

He used scripts to activate individual services and service accounts. To bind Cloud Build as an App Engine admin for each project. To perform initial git commits before sharing to Github. To add functionality to Cloud Build pipelines so they could report on whether or not the builds succeeded.

Securing all these projects and apps?
A script to set up Identity-Aware Proxy for each project, to restrict access to the applications.

On the Github side, adding people to each repo and locking down the master branch - Scripts!

And then once it's all flowing:
## 5: How do I keep track of all this work?

Guess what? It's more scripts. And notifications. Terry made scripts to collect stats on the whole thing, so we know there were 281 commits, 312 code reviews, and 27 demos launched. Setting up the right set of notifications allowed a rapid response time when new code got pushed, and allowed Terry to keep the turnaround tight. When rapidly collaborating with these outside partners that speed becomes critical. These projects averaged 5 minutes from code approval to application pushed out to production. And if the new code push fails, a notification from Cloud Build tells Terry and the development team what went wrong.

This project brought together many moving parts, many access and authorization challenges, and a tricky form of remote collaboration, but with some clever process design (and a ton of scripting) Terry got it all launched in time for our big show. Congratulations!
