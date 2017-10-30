# Using Cloud Spanner in ASP.NET

[Cloud Spanner](https://cloud.google.com/spanner/) is a hosted SQL database by Google. It offers planet-scale support, and nearly infinite scaling. It also requires zero maintenance downtime. With the new Cloud Spanner ADO.NET provider you can take advantage of Spanner in your existing C# applications.This tutorial describes how to use our new C# Cloud Spanner ADO.NET library to build a simple REST API for Books.  We will use the asynchronous API of Cloud Spanner to store and query books. The Cloud Spanner ADO.NET library is fully asynchronous down to the network level to provide the best performance.

What we’ll use in this blog post:

* [Visual Studio 2017](https://www.visualstudio.com/vs/community/).  You can download the community edition for free from Microsoft.

* [Cloud Spanner nuget package](https://github.com/GoogleCloudPlatform/google-cloud-dotnet).  You’ll add this to your project.

### **Creating your Spanner Instance**

In order to use Google Cloud Spanner, you'll first need to create a cloud project and download the Cloud SDK. The information on doing that can be found [here](https://cloud.google.com/spanner/docs/getting-started/set-up).

Once you have a project,

* Visit [https://](https://console.cloud.google.com/spanner/instances?project=)[console.cloud](https://console.cloud.google.com/spanner/instances?project=)[.google.com/spanner/instances?project=](https://console.cloud.google.com/spanner/instances?project=).

* Create a new Spanner instance called "myspanner"

* Create a database called "books" and then a new table called “bookTable”

* Define the schema as below and set the primary key to "ID"

![image alt text](image_0.png)

### **Set up Default Application Credentials**

### You need proper credentials to call Cloud Spanner, otherwise it will not know who is making the request. This sample uses Google Default Application Credentials to access your data.  Follow the steps online [here](https://developers.google.com/identity/protocols/application-default-credentials#howtheywork) to set up application credentials on your development machine.

## **Cloud Spanner with ASP.NET**

The first project we will create is an ASP.NET Core WebAPI application.  This REST API will provide basic CRUD operations on the bookTable created above. After we are done, you will be able to create, read, update and delete books.

Create a new ASP.NET project via the menu **File**** ->** **New Project** -> **C#** -> **Web****->** **ASP.NET Core Web Application (.NET Core)**.

Choose "Web API" and call the project “SpannerTest”.

![image alt text](image_1.png)

### **Add the nuget package for Spanner**

The C# Spanner library for ADO.NET is available [on nuget] as "Google.Cloud.Spanner.Data". Add a reference to the Cloud Spanner nuget using the **Manage Nuget Packages** dialog.

![image alt text](image_2.png)

### **Model and Controller Class**

The first code we need to write is a Model class for a Book.  Add a new folder called "Models" in the project and then a class called Book to that folder with the following content:

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

We also need a Controller class to handle the http requests.  Under the "Controllers" folder add a new “Web API Controller class” item named **BooksController**.  Erase the contents of this controller.  We’ll start filling it in below.

### **Inserting **

This sample will be pretty basic and will not have everything you would normally see in an ASP.NET application, but does show how to use Cloud Spanner.

Add the following code to BooksController. Be sure to replace {myProject} with your own project id.

    namespace SpannerTest.Controllers    {        [Route("api/[controller]/")]        public class BooksController : Controller        {            [HttpPost]            public async Task<IActionResult> Create([FromBody] Book item)            {                // Insert a new item.                using (var connection =                    new SpannerConnection(                        $"Data Source=projects/{_myProject}/instances/myspanner/databases/books"))                {                    await connection.OpenAsync();                         item.Id = Guid.NewGuid().ToString("N");                    var cmd = connection.CreateInsertCommand(                        "bookTable", new SpannerParameterCollection                        {                            {"ID", SpannerDbType.String, item.Id},                            {"Title", SpannerDbType.String, item.Title},                            {"Author", SpannerDbType.String, item.Author},                            {"PublishDate", SpannerDbType.Date, item.PublishDate}                        });                         await cmd.ExecuteNonQueryAsync();                }                     return Ok();            }
        }
    }


When you run the application, use a utility to send different REST requests to test your API.  I like using [Postman](https://chrome.google.com/webstore/detail/postman/fhbjgbiflinjbdggehcddcbncdddomop), which is a Chrome extension but you can use something else like curl.  Use Postman to add a new book to the database as below.  Note: replace the port number to match your server.  So, the ‘56777’ in [http://localhost:56777](http://localhost:56777) should be replaced with the port your local server is running on.

![image alt text](image_3.png)

### **Getting Books.**

Now that we have code to insert records, we can add more code to list all books or a single book.

Add the following methods to your controller.

    . . .
    [HttpGet]    public async Task<IActionResult> GetAll()    {        var result = new List<Book>();             using (var connection = new SpannerConnection(            $"Data Source=projects/{_myProject}/instances/myspanner/databases/books"))        {            var selectCmd = connection.CreateSelectCommand("SELECT * FROM bookTable");            using (var reader = await selectCmd.ExecuteReaderAsync())            {                while (await reader.ReadAsync())                {                    result.Add(new Book                    {                        Id = reader.GetFieldValue<string>("ID"),                        Title = reader.GetFieldValue<string>("Title"),                        Author = reader.GetFieldValue<string>("Author"),                        PublishDate = reader.GetFieldValue<DateTime>("PublishDate")                    });                }            }        }             return Ok(result);    }         [HttpGet]    [Route("{id}", Name="GetBookById")]    public async Task<IActionResult> Get(string id)    {        using (var connection = new SpannerConnection(            $"Data Source=projects/{_myProject}/instances/myspanner/databases/books"))        {            var selectCommand =connection.CreateSelectCommand($"SELECT * FROM bookTable WHERE ID='{id}'");            using (var reader = await selectCommand.ExecuteReaderAsync())            {                while (await reader.ReadAsync())                {                    return Ok(new Book                    {                        Id = reader.GetFieldValue<string>("ID"),                        Title = reader.GetFieldValue<string>("Title"),                        Author = reader.GetFieldValue<string>("Author"),                        PublishDate = reader.GetFieldValue<DateTime>("PublishDate")                    });                }            }        }             return NotFound();    }
    . . .


Now, run your program.  Using Postman, perform an HTTP GET on [http://localhost:56777/api/books](http://localhost:56777/api/books) to return all books or [http://localhost:56777/api/books/[ID](http://localhost:56777/api/books/[ID)] to retrieve a single book.

### **[Optional] Deploy to Google App Engine Flex**

You can deploy this Web API project to Google’s App Engine Flex environment and get automatic scaling and management.

Download and install the [Google Cloud Tools for Visual studio extension](https://cloud.google.com/tools/visual-studio/docs/quickstart#install_cloud_tools_for_visual_studio). Then from the main menu, select **Tools**->**Google Cloud** -> **Publish to Google Cloud**.

![image alt text](image_4.png)

Then click **App Engine Flex**, click **Publish** and your website will now be live at [https://YOUR_PROJECT_ID.appspot.com](https://YOUR_PROJECT_ID.appspot.com)!

### **Summary**

That’s it!  Now you can insert and list books in a spanner database!

Of course, for enterprise-grade software you'll need to consider transactions, transient faults, and exponential backoff. The Spanner library for ADO.NET supports handling these issues  like you would expect. You can read more about this in our [getting started documentation](https://cloud.google.com/spanner/docs/getting-started/csharp/).The library is in Beta, and so if you do stumble over a bug please be sure to log it on our[ issue tracker](https://github.com/GoogleCloudPlatform/google-cloud-dotnet/issues).

