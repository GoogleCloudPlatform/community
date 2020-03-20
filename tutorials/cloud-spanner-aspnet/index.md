---
title: Using Cloud Spanner in ASP.NET
description: Learn how to use Cloud Spanner with ASP.NET using C#.
author: benwulfe
tags: Cloud Spanner, C#, SQL, ASP.NET, ADO.NET
date_published: 2017-11-03
---

This tutorial describes how to use the
[C# Google Cloud Spanner ADO.NET library][ado] to build a simple REST API for
books and use the API to store and query books.

[Cloud Spanner][spanner] is a hosted SQL database, and the Cloud Spanner ADO.NET
provider lets you take advantage of Cloud Spanner in your C# applications. The
Cloud Spanner ADO.NET library is fully asynchronous to the network level and is
the recommended way to integrate Cloud Spanner APIs into your .NET applications.

What you’ll use in this tutorial:

* [Visual Studio 2017][studio]. You can download the community edition for free
  from Microsoft.
* [Cloud Spanner nuget package][repo]. You’ll add this to your project.

[ado]: https://cloud.google.com/spanner/docs/getting-started/csharp/
[spanner]: https://cloud.google.com/spanner/
[repo]: https://github.com/GoogleCloudPlatform/google-cloud-dotnet

## Cost

Cloud Spanner charges based on the number of nodes, storage and bandwidth used.
See [Cloud Spanner detailed pricing][pricing] for more information.

[pricing]: https://cloud.google.com/spanner/pricing

## Before you begin

1.  Set up the following on your development machine:

    1.  Set up the [Cloud SDK](https://cloud.google.com/sdk/).
    1.  Set up authentication and authorization for the Cloud SDK. This tutorial
        uses the [Google Default Application Credentials][adc] when calling
        Google APIs to access your data.
    1.  [Install Microsoft Visual Studio 2017][studio]. The community edition is
        free.

1.  Go to the [Spanner page in the Cloud Platform Console][instances] and create
    or select a project to use for this tutorial.

[adc]: https://developers.google.com/identity/protocols/application-default-credentials#howtheywork
[instances]: https://console.cloud.google.com/spanner/instances

### Creating a Cloud Spanner database

1.  Go to the [**Spanner** page][spanner_console] in the Cloud Platform Console.
1.  Create a new Cloud Spanner instance named **myspanner**.
1.  Create a new database named **books**.
1.  Add a table named **bookTable**.
1.  Define the schema for **bookTable** as shown and set the primary key to
    **ID**.

![image alt text](https://storage.googleapis.com/gcp-community/tutorials/cloud-spanner-aspnet/image_0.png)

[spanner_console]: https://console.cloud.google.com/spanner

## Creating an ASP.NET Core Web API application

This REST API provides basic create, read, update, and delete (CRUD) operations
on books in the **bookTable** database.

**Note**: You can download a completed version of the application [here][app].

[app]: https://github.com/GoogleCloudPlatform/community/tree/master/tutorials/cloud-spanner-aspnet/BookWebApi

1.  To create the application:

    1.  From the menu, click **File > New Project > C# > Web > ASP.NET Core Web
        Application (.NET Core)**.
    1. Choose **Web API**.

    ![image alt text](https://storage.googleapis.com/gcp-community/tutorials/cloud-spanner-aspnet/image_1.png)

    1. For the project name, enter **SpannerTest**.

1.  Using the Manage Nuget Packages dialog, add a reference to the Cloud Spanner nuget.

    ![image alt text](https://storage.googleapis.com/gcp-community/tutorials/cloud-spanner-aspnet/image_2.png)

1.  To create a Model class for a book:

    1.  Add a new folder named **Models** in the project.
    1.  In the **Models** folder, add a class named **Book** with the following
        content:

        ```cs
        namespace SpannerTest.Models
        {
            public class Book
            {
                public string Id { get; set; }
                public string Author { get; set; }
                public string Title { get; set; }
                public DateTime PublishDate { get; set; }
            }
        }
        ```

1.  To create a Controller class to handle the HTTP requests:

    1.  In the Controllers folder, add a new Web API Controller class item named
        **BooksController**.
    1.  Delete the contents of the controller.
    1.  To list all books, add a `GetAll` method to **BooksController** and
        replace *myProject* with your project ID.

        See the [example `GetAll` method](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/cloud-spanner-aspnet/BookWebApi/BookWebApi/Controllers/BookController.cs#L36).

    1.  To get a single book, add a `Get` method to **BooksController** and
        replace *myProject* with your project ID.

        See the [example `Get` method](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/cloud-spanner-aspnet/BookWebApi/BookWebApi/Controllers/BookController.cs#L62).

    1.  To insert records, add a `Create` method to **BooksController** and
        replace *myProject* with your project ID.

        See the [example `Create` method](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/cloud-spanner-aspnet/BookWebApi/BookWebApi/Controllers/BookController.cs#L85).

## Adding books and testing the application

To run the application, use a utility to send REST requests to test the API.
This example shows [Postman][postman], a Chrome extension, but you can use
`curl` or another utility.

[postman]: https://chrome.google.com/webstore/detail/postman/fhbjgbiflinjbdggehcddcbncdddomop

1.  To add a book to the database, perform an `HTTP POST` with the port that
    your local server is running on. For example, replace port `56777` in
    `http://localhost:56777`.
1.  To test the application, perform an HTTP GET:

    * To return all books, enter: `http://localhost:PORT_NUMBER/api/books`
    * To return a single book, enter: `http://localhost:PORT_NUMBER/api/books/ID`

![image alt text](https://storage.googleapis.com/gcp-community/tutorials/cloud-spanner-aspnet/image_3.png)

### [Optional] Deploy to Google App Engine Flex

For automatic scaling and management, you can deploy your Web API project to the
App Engine flexible environment.

1.  Download and install [Google Cloud Tools for Visual Studio][install_studio].
1.  In the main menu, select **Tools** > **Google Cloud** >
    **Publish to Google Cloud**.
1.  In the Publish dialog box, choose **App Engine Flex**.

    ![image alt text](https://storage.googleapis.com/gcp-community/tutorials/cloud-spanner-aspnet/image_4.png)

1.  Click **Publish**. After publishing completes, the application is live at
    `[https://YOUR_PROJECT_ID.appspot.com](https://YOUR_PROJECT_ID.appspot.com)`.

[install_studio]: https://cloud.google.com/tools/visual-studio/docs/quickstart#install_cloud_tools_for_visual_studio

## Cleaning Up

Once you are done, you should delete your database to avoid unnecessary charges.

1.  Navigate to the [Spanner page](https://console.cloud.google.com/spanner).
1.  Select the instance you created.
1.  Choose **Delete Instance**.

## What's next

This basic tutorial does not have everything in a typical ASP.NET application.
For enterprise-grade software you'll need to consider transactions, transient
faults, and exponential backoff. The Cloud Spanner library for ADO.NET supports
handling these issues, and you can read more about this in
[Getting Started with Cloud Spanner in C#][getting_started].

If you find a bug please log it on the [issue tracker][issues].

[studio]: https://www.visualstudio.com/vs/community/
[getting_started]: https://cloud.google.com/spanner/docs/getting-started/csharp/
[issues]: https://github.com/GoogleCloudPlatform/google-cloud-dotnet/issues
