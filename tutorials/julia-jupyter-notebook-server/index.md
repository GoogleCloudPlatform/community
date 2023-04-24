---
title: Create a secure Jupyter Notebook server with Julia 1.0 Kernel
description: Automated creation of a secure Jupyter Notebook server with the Julia 1.0 kernel installed.
author: wardharold
tags: GCE, Jupyter, Julia, DNS
date_published: 2018-10-01
---

Ward Harold | Google

<p style="background-color:#CAFACA;"><i>Contributed by Google employees.</i></p>

This tutorial shows you how to run a secure [Jupyter Notebook server](https://jupyter-notebook.readthedocs.io/en/stable/public_server.html) with a
[Julia](https://julialang.org/) kernel installed on the Google Cloud.
It uses HashiCorp's [Terraform](https://www.terraform.io/) to acquire a
[Let's Encrypt certificate](https://letsencrypt.org/), create a Google Compute
Engine instance, and configure the necessary firewall rules and Cloud DNS
entries for the server.

Julia is a relatively new language that has emerged from MIT to address the
["two-language problem"](https://www.quora.com/What-is-the-2-language-problem-in-data-science)
in HPC, data science, ML and other compute intensive fields. The tagline "looks
like Python, feels like Lisp, runs like C" sums up Julia's goals of
simultaneously addressing *productivity*, *generality*, and *performance*
concerns in compute intensive problem domains. Jupyter notebooks are an
increasingly common mechanism for collaboration around, and delivery of,
scientific information processing solutions. While originally constructed around
Python, Jupyter now supports the installation of additional "kernels", *e.g.* R,
Scala, and Julia. While this tutorial is specific to Julia, it would be easy to
modify to add a different kernel to the resulting notebook server.

## Objectives

* Create a secure Jupyter notebook server with a Juila kernel installed
* Demonstrate acquiring a Let's Encrypt certificate via Terraform

## Before you begin

### Terraform

You need to have HashiCorp's [Terraform](https://www.terraform.io/) installed to
work through this tutorial. If you don't have it installed, the instructions can
be found [here](https://www.terraform.io/intro/getting-started/install.html).

### DNS

This tutorial assumes you have a [Cloud DNS](https://cloud.google.com/dns/)
managed zone where you can create DNS Address (`A`) records for your notebook
server.

To use Cloud DNS you need a registered domain name. If you don't have one, you
can register a domain name through [Google Domains](https://domains.google/#/)
or another domain registrar of your choice. Once you have your domain
registered, you can use this
[quickstart](https://cloud.google.com/dns/quickstart) to set up a managed zone.

You can choose to create a notebook server with a self-signed certificate, or
you can have Terraform acquire a Let's Encrypt issued certificate for your
notebook server. If you want to do the latter, you will need to enable
[DNSSEC](https://cloud.google.com/dns/dnssec) on your managed domain. Follow
[this DNSSEC tutorial](https://cloud.google.com/community/tutorials/dnssec-cloud-dns-domains)
to activate DNSSEC.

To ensure that your domain is configured properly for issuing Let's Encrypt
certificates, use the the [Let's Debug](https://letsdebug.net/) diagonistic
site. Enter the FQDN of the notebook server you're going to create, choose
DNS-01 from the validation method pull down (to the right of the input field),
and click `Run Test`. You will see a green "All OK!" message box if your
configuration is correct. If something is wrong with your configuration, the
resulting message boxes will help you debug the issue as will the
[Let's Encrypt community forum](https://community.letsencrypt.org/).

## Costs

This tutorial uses billable components of Google Cloud, including:

- Compute Engine
- Cloud DNS

Use the [Pricing Calculator](https://cloud.google.com/products/calculator/#id=cdaa96a1-84a6-468d-b5cc-493af9895149)
to generate a cost estimate based on your projected usage.

## Configure Terraform variables
The `variables.tf` file defines a collection of variables that Terraform uses
when creating a notebook server.

| Name | Default Value | Description |
| --- | --- | --- |
| acme_registration_email || Email address to be associated with the Let's Encrypt private key registration |
| manage_zone || The Cloud DNS Managed Zone that will contain the notebook server's DNS records |
| project || Name of the project that will contain the notebook server |
| servername || Name of the notebook server |
| acme_server_url | https://acme-v02.api.letsencrypt.org/directory | URL for the Let's Encrypt ACME server |
| disk_size | 16 (Gigabytes) | Size of the notebook server boot disk |
| jupyter_server_port | 8089 | Port the notebook server will listen on |
| machine_type | n1-standard-2 | Notebook server machine type |
| network | default | The Google Cloud network the notebook server will be attached to |
| region | us-central1 | The compute region the notebook server will run in |
| use_acme_cert | true | Acquire a Let's Encrypt issued certificate and install it on the notebook server |
| zone | us-central1-b | The compute zone the notebook server will run in |

You must provide values for all of the variables without default values:
project, managed_zone, acme_registration_email, and servername.

Terraform will prompt you for required values, or you can specify them in a
`terraform.tfvars` file. For example:

    project = "my-julia-jupyter-notebook-server-project"
    manage_zone = "ExampleDotCom"
    servername = "my-julia-notebook-server"
    acme_registration_email = "fred.c.dobbs@sierra.madre.net"

The default value for the acme_server_url variable is the URL of the Let's
Encrypt production environment. If you are experimenting and genterating lots of
certificates, use their staging environment to avoid hitting rate limits. The
URL for the Let's Encrypt staging environment is:
https://acme-staging-v02.api.letsencrypt.org/directory.

## Create a notebook server password

The notebook server uses a password for authentication. You must include a
hashed version of your password in the Compute Engine instance startup script
`jupyter-config.sh`. You will use the Jupyter `notebook.auth` Python module to
create a hashed version of your desired password.

Install the Jupyter Python modules if necessary.

    pip3 install jupyter

Generate a hashed version of your desired password.

    PASSWD=[YOUR DESIRED PASSWORD]
    HASHED_PASSWD=$(python3 -c "from notebook.auth import passwd; print(passwd(\"${PASSWD}\"))")

If you can't install the Jupyter Python modules you can use the hashed version
of the password: `$$nTh3b@nc`. **This is not the recommended approach. If you
use it, change the password on your notebook server when you login the first
time.**

    HASHED_PASSWD='sha1:8f334ff5f862:c19298d6e4f03fe9ec6e6a5c127927c86d47ec2a'

Update `jupyter-config.sh` with the hashed version of your password.

    sed -i 's/HASHED_PASSWD/'"${HASHED_PASSWD}"'/' jupyter-config.sh

## Verify your configuration

Generate a Terraform plan:

    terraform plan -out tf.plan -auto-approve

The terminal output describes the resources that Terraform will create/configure.

If `use_acme_cert` is true (the default), the output will include:

* acme_certificate.certificate: check that the *common_name* field contains the
  correct FQDN for your notebook server
* acme_registration.reg: check that the *email_address* field contains the
  correct email address
* google_compute_firewall.jupyter-server: check that the
  *target_tags.nnnnnnnnnn* field is set to *jupyter-server-[your server name]*
* google_compute_instance.nbs_acme_cert: check that the *tags.nnnnnnnnnn* field
  is set to *jupyter-server-[your server name]*
* google_dns_record_set.nbs_acme_cert: check that the *name* field contains the
  correct FQDN for your notebook server
* tls_private_key.private_key

If you set `use_acme_cert` to false, only these resources will be
created/configured:

* google_compute_firewall.jupyter-server: check that the
  *target_tags.nnnnnnnnnn* field is set to *jupyter-server-[your server name]*
* google_compute_instance.nbs_self_signed_cert: check that the *tags.nnnnnnnnnn*
  field is set to *jupyter-server-[your server name]*
* google_dns_record_set.nbs_self_signed_cert: check that the *name* field
  contains the correct FQDN for your notebook server

## Create the notebook server

To create the notebook server type:

    terraform apply tf.plan

The terminal output logs Terraform's progress as it executes the plan you
generated earlier. When it completes you will see:

    Apply complete! Resources: 6 added, 0 changed, 0 destroyed.

Installing the Julia kernel takes approximately 10 minutes. Therefore, even
though the Compute Engine instance is running you won't be able to immediately
connect to the notebook server. Wait 10 minutes and then proceed.

## Log into the notebook server

The URL for your notebook server has the form:
`https://[your server name].[your domain]:8089`, *e.g.*,
`https://dobbs.sierramadre.net:8089`. When you navigate there with your browser,
you should see the Jupyter login screen.

![Jupyter Login Screen](https://storage.googleapis.com/gcp-community/tutorials/julia-jupyter-notebook-server/secure-jupyter-login.png)

Note that if your notebook server has a self-signed certificate, your browser
will complain that the connection is not private because it does not recognize
the self-signed certificate. You will need to manually accept the certificate to proceed.

Enter your password and click the `Log in` button, and you should see Jupyter
interface.

![Jupyter Interface](https://storage.googleapis.com/gcp-community/tutorials/julia-jupyter-notebook-server/secure-jupyter-interface.png)

The `setup.sh` script clones a set of Julia
[tutorials](https://github.com/JuliaComputing/JuliaBoxTutorials) from the
[Julia Computing](https://juliacomputing.com/) GitHub
[repo](https://github.com/JuliaComputing) to get started.

## Clean up

When you've finished your work, teardown the notebook server, delete the
firewall rule, and remove the DNS records associated with the notebook server.

    terraform destroy
