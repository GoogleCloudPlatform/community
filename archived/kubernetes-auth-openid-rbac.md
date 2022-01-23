---
title: Kubernetes 1.6.1 authentication by using Google OpenID
description: A sample process that shows how to use Google Accounts with Kubernetes cluster with role-based access control (RBAC) authorization mode.
author: miry
tags: Kubernetes
date_published: 2017-06-24
---

<p style="background-color:#D9EFFC;"><i>Contributed by the Google Cloud community. Not official Google documentation.</i></p>

In this tutorial you set up authentication and authorization to your own Kubernetes cluster using your Google account with the help of role-based access control ([RBAC]) and [OpenID Connect].
RBAC was introduced in the Kubernetes 1.6 article, RBAC Support in Kubernetes, and was based on Micah Hausle's [Reduce administrative toil with Kubernetes 1.3](https://www.skuid.com/blog/reduce-administrative-toil-with-kubernetes-1-3/).

## Objectives

* Creating a Google API Console project and client ID
* Setting up a Kubernetes cluster with `kubeadm`
* Generating a local user's credentials
* Granting permissions

## Creating a Google API Console project and client ID

1. Go to https://console.developers.google.com/projectselector/apis/library.
1. From the project drop-down, select an existing project, or create a new one by selecting **Create a new project**.
1. In the sidebar under **API Manager**, select **Credentials**, then select the **OAuth consent screen** tab.
1. Choose an **Email Address**, specify a **Product Name**, and submit **Save**.
1. In the **Credentials** tab, select the **New credentials** drop-down list, and choose **OAuth client ID**.
1. Under **Application type**, select **Other**.
1. From the resulting **OAuth client dialog box**, copy the **Client ID**. The **Client ID** lets your app access enabled Google APIs.
1. Download the client secret JSON file of the credentials.

## Setting up a Kubernetes cluster

After initializing the master instance, you need to update the `kube api server` arguments in the `/etc/kubernetes/manifests/kube-apiserver.yaml`. Each argument should be on a separate line.
More information about the OIDC attributes can be found in the [Authenticating](https://kubernetes.io/docs/admin/authentication/#option-1---oidc-authenticator) reference documentation.


    sed -i "/- kube-apiserver/a\    - --oidc-issuer-url=https://accounts.google.com\n    - --oidc-username-claim=email\n    - --oidc-client-id=[YOUR_GOOGLE_CLIENT_ID]" /etc/kubernetes/manifests/kube-apiserver.yaml


Add any network CNI plugin and the cluster is ready. Copy `/etc/kubernetes/admin.conf` to local `~/.kube/config` and change the cluster ip.

    kubectl get nodes

Output appears as follows:

    NAME            STATUS    AGE       VERSION
    ip-10-9-11-30   Ready     15m       v1.6.1


## Generating local user credentials

1.  Install the helper on the client machine. Run the following command:

        go get github.com/micahhausler/k8s-oidc-helper


1.  Generate a user's credentials for `kube config`. Run the following command:

        k8s-oidc-helper -c path/to/client_secret_[CLIENT_ID].json

    This command should open the browser and ask permissions. After that, it provides you a token in the browser.
    Copy it and paste to the terminal for `k8s-oidc-helper`. The output of the command should look as follows:

        # Add the following to your ~/.kube/config

        users:
        - name: name@example.com
            user:
            auth-provider:
                config:
                client-id: 32934980234312-9ske1sskq89423480922scag3hutrv7.apps.googleusercontent.com
                client-secret: ZdyKxYW-tCzuRWwB3l665cLY
                id-token: eyJhbGciOiJSUzI19fvTKfPraZ7yzn.....HeLnf26MjA
                idp-issuer-url: https://accounts.google.com
                refresh-token: 18mxeZ5_AE.jkYklrMAf5.IMXnB_DsBY5up4WbYNF2PrY
                name: oidc

1.  Copy everything after `users:` and append it to your existing user list in the `~/.kube/config`.
    Now you have 2 users: one from the new cluster configuration and one that you added.

### Verifying the token

Test the id-token using https://jwt.io/. Be sure that you have `"email_verified": true` in the decoded message. Test connection of the new user:

    kubectl --user=name@example.com get nodes

This results in the following output:

    Error from server (Forbidden): User "name@example.com" cannot list nodes at the cluster scope. (get nodes)

This error message proves that `id-token` and api server arguments work and email is extracted from a request.

## Granting permissions

For now, grant admin rights to the user `name@example.com` with an authorization specification:

```yaml
kind: ClusterRole
apiVersion: rbac.authorization.k8s.io/v1alpha1
metadata:
    name: admin-role
rules:
    - apiGroups: ["*"]
    resources: ["*"]
    verbs: ["*"]
---
kind: ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1alpha1
metadata:
    name: admin-binding
subjects:
    - kind: User
    name: name@example.com
roleRef:
    kind: ClusterRole
    name: admin-role
```

After applying changes by using `kubectl create -f admin.yaml`,
Do the test again:

    $ kubectl --user=name@example.com get nodes

Output:

    NAME            STATUS    AGE       VERSION
    ip-10-9-11-30   Ready     20m       v1.6.1

You now have a Kubernetes cluster with authorization by email. Plus, you don't need to generate a new OpenID for new clusters.

[RBAC]: https://wikipedia.org/wiki/Role-based_access_control
[OpenID Connect]: http://openid.net/connect/
[kubeadm]: https://kubernetes.io/docs/getting-started-guides/kubeadm/
