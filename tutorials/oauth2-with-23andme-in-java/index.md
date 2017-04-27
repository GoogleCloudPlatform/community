---
title: Authenticating to the 23andMe API with the Google Java OAuth 2.0 Client
description: Authenticate to the 23andMe API with the Google Java OAuth 2.0 client and pull a single genotype for i3003137, a SNP associated with Sickle Cell Anemia.
author: dennisbyrne
tags: OAuth, OAuth2, Java, 23andMe, genomics
date_published: 2017-04-26
---

This sample app uses Google's OAuth 2.0 java lib to authenticate with 23andMe. Once authenticated the app pulls a single genotype for i3003137, a SNP associated with Sickle Cell Anemia.
 
## Create a 23andMe client

Follow the instructions at [https://api.23andme.com/apply/](https://api.23andme.com/apply/) to create a 23andMe Oauth client. Make sure to set your `redirect_uri` to [http://127.0.0.1:8080/Callback](http://127.0.0.1:8080/Callback). You will be given a `client_id` and a `client_secret`.

## Clone the community repo

      git clone https://github.com/GoogleCloudPlatform/community.git

## Run the sample app

      cd community/tutorials/oauth2-with-23andMe-in-java/java/

Make sure you have [maven installed][install_maven], then run the app:
    
      mvn compile && mvn -q exec:java -Dexec.args="`client_id` `client_secret`"

[install_maven]: https://maven.apache.org/install.html

## Example output

`Genotype @ i3003137, a SNP associated with Sickle Cell Anemia: TT`
