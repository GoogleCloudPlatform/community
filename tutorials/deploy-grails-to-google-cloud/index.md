---
title: Deploy a Grails app to App Engine flexible environment
description: Deploy a Grails 3 app to App Engine flexible environment and learn how to use Cloud Storage and Cloud SQL.
author: sdelamo
tags: Cloud SQL, App Engine, Java, Grails, Cloud Storage
date_published: 2017-08-08
---

*Sergio del Amo (Object Computing, Inc.)*

*August 2017*

*Grails Version: 3.3.0*

## Getting Started
In this guide, you deploy a Grails 3 application to
[Google App Engine flexible environment][flex], upload images to
[Google Cloud Storage][storage] and use a MySQL database provided by
[Google Cloud SQL][cloud_sql].

## Costs

This guide uses paid services. You may need to enable Billing in Google Cloud to
complete some steps in this guide.

### What you will need

To complete this guide, you need the following:

- Some time on your hands
- A decent text editor or IDE
- JDK 1.7 or greater installed with JAVA_HOME configured appropriately

### How to complete the guide

To get started do the following:

1.  [Download][download] and unzip the source or Clone the Git repository:

        git clone https://github.com/grails-guides/grails-google-cloud.git

    The Grails guides repositories contain two folders:

    - `initial`: An initial project. A Grails app with additional code to give
      you a head start.
    - `complete`: A completed example. It is the result of working through the
      steps presented by the guide and applying those changes to the `initial`
      folder.

1.  Change directory into the `initial` folder:

        cd initial

[download]: https://github.com/grails-guides/grails-google-cloud/archive/master.zip

## Writing the application

### Domain class

The `initial` project includes a Grails domain class to map `Book` instances to
a MySQL table.

A domain class fulfills the M in the Model View Controller (MVC) pattern and
represents a persistent entity that is mapped onto an underlying database
table. In Grails a domain is a class that lives in the grails-app/domain
directory.

_grails-app/domain/demo/Book.groovy_

```groovy
package demo

import grails.compiler.GrailsCompileStatic

@GrailsCompileStatic
class Book {
    String name
    String featuredImageUrl
    String fileName

    static constraints = {
        name unique: true
        featuredImageUrl nullable: true
        fileName nullable: true
    }
}
```

### Seed data

When the application starts, it loads some seed data. In particular, it loads a
list of books.

Modify `BootStrap.groovy`:

_grails-app/init/demo/BootStrap.groovy_

```groovy
package demo

import groovy.transform.CompileStatic

@CompileStatic
class BootStrap {
    def init = { servletContext ->
        Book.saveAll(
            new Book(name: 'Grails 3: A Practical Guide to Application Development'),
            new Book(name: 'Falando de Grails',),
            new Book(name: 'The Definitive Guide to Grails 2'),
            new Book(name: 'Grails in Action'),
            new Book(name: 'Grails 2: A Quick-Start Guide'),
            new Book(name: 'Programming Grails')
        )
    }
    def destroy = {
    }
}
```

### Root URL

You want to display the books persisted when the Grails app starts
(`BootStrap.groovy`) in the home page of the application.

Map the home page to be resolved by `BookController` by modifying
`UrlMappings.groovy`

Replace:

_grails-app/controllers/demo/UrlMappings.groovy_

    "/"(view:"/index")

with:

_grails-app/controllers/demo/UrlMappings.groovy_

    '/'(controller: 'book')

The `initial` project modifies slightly the output of the Grails static
scaffolding command `generate-all` to provide CRUD functionality for the domain
class `Book`.

You can find the code: `BookController`, `BookGormService` and GSP views in the
\§ 21`
`initial` project.

## Google Cloud SDK

1.  Signup for [Google Cloud Platform](https://console.cloud.google.com/) and
    create a new project:

    ![Create Project](https://storage.googleapis.com/gcp-community/tutorials/deploy-grails-to-google-cloud/create-project.png)

    ![Create Project](https://storage.googleapis.com/gcp-community/tutorials/deploy-grails-to-google-cloud/create-project-2.png)

    The previous image shows a project named **grailsgooglecloud**.

1.  Install [Cloud SDK](https://cloud.google.com/sdk/downloads) for your
    operating system.

1.  After you have installed the SDK, run the `init` command in your terminal:

        gcloud init

    It prompts you to select the Google account and the project which you want
    to use.

## App Engine

This guide deploys a Grails application to
[App Engine flexible environment][flex].

App Engine allows developers to focus on doing what they do best: writing
code. Based on Compute Engine, the App Engine flexible environment
automatically scales your app up and down while balancing the load.
Microservices, authorization, SQL and NoSQL databases, traffic splitting,
logging, versioning, security scanning, and content delivery networks are all
supported natively.

Run the command:

    gcloud app create

to initialize an App Engine application within the current Google Cloud project.

NOTE: You need to choose the region where you want your App Engine application
located.

### Google App Engine Gradle plugin

To deploy to App Engine, add the [Google App Engine Gradle plugin][plugin] to
your project.

1.  Add the plugin as a `buildscript` dependency.

    _build.gradle_

        buildscript {
            repositories {
                mavenLocal()
                maven { url "https://repo.grails.org/grails/core" }
            }
            dependencies {
                classpath "org.grails:grails-gradle-plugin:$grailsVersion"
                classpath "com.bertramlabs.plugins:asset-pipeline-gradle:2.14.1"
                classpath "org.grails.plugins:hibernate5:${gormVersion-".RELEASE"}"
                classpath 'com.google.cloud.tools:appengine-gradle-plugin:1.3.2'
            }
        }

1.  Apply the plugin:

    _build.gradle_

        apply plugin:"eclipse"
        apply plugin:"idea"
        apply plugin:"war"
        apply plugin:"org.grails.grails-web"
        apply plugin:"org.grails.grails-gsp"
        apply plugin:"asset-pipeline"
        apply plugin:"codenarc"
        apply plugin: 'com.google.cloud.tools.appengine'

[plugin]: https://github.com/GoogleCloudPlatform/app-gradle-plugin

### Application deployment configuration

To deploy to Google App Engine, add the file `src/main/appengine/app.yaml`.

It describes the application’s deployment configuration:

_src/main/appengine/app.yaml_

```yaml
runtime: java
env: flex

runtime_config:
    jdk: openjdk8
    server: jetty9

resources:
    cpu: 1
    memory_gb: 2.3

manual_scaling:
    instances: 1
```

Here, `app.yaml` specifies the runtime used by the app, and sets `env: flex`,
specifying that the app uses the [flexible environment][flex].

The minimal `app.yaml` application configuration file shown above is
sufficient for a simple Grails application. Depending on the size, complexity,
and features that your application uses, you may need to change and extend
this basic configuration file. For more information on what can be configured
via `app.yaml`, please see the [Configuring Your App with app.yaml][configure]
guide.

For more information on how the Java runtime works, see
[Java 8 / Jetty 9.3 Runtime][jetty].

[configure]: https://cloud.google.com/appengine/docs/flexible/java/configuring-your-app-with-app-yaml
[jetty]: https://cloud.google.com/appengine/docs/flexible/java/dev-jetty9

### SpringBoot Jetty

As shown in the previous app engine configuration file, the app uses Jetty.

Grails is built on top of SpringBoot. Following SpringBoot’s documentation, you
need to do the following changes to [deploy to Jetty instead of Tomcat][boot].

1.  Replace:

    _build.gradle_

        compile "org.springframework.boot:spring-boot-starter-tomcat"

    with:

    _build.gradle_

        provided "org.springframework.boot:spring-boot-starter-jetty"

1.  Exclude the tomcat-juli other dependency as well:

    _build.gradle_

        configurations {
            compile.exclude module: "tomcat-juli"
            compile.exclude module: "spring-boot-starter-tomcat"
        }

[boot]: https://docs.spring.io/spring-boot/docs/current/reference/html/howto-embedded-servlet-containers.html

## Cloud SQL

This guide’s Grails application uses a MySQL database created with
[Cloud SQL][cloud_sql].

Cloud SQL is a fully-managed database service that makes it easy to set up,
maintain, manage, and administer your relational PostgreSQL BETA and MySQL
databases in the cloud. Cloud SQL offers high performance, scalability, and
convenience. Hosted on Google Cloud Platform, Cloud SQL provides a database
infrastructure for applications running anywhere.

### Enable the Cloud SQL API

If you have not enabled Cloud SQL and the Cloud SQL API already, go to your
project dashboard and enable them:

![](https://storage.googleapis.com/gcp-community/tutorials/deploy-grails-to-google-cloud/cloudsql-1.png)

![](https://storage.googleapis.com/gcp-community/tutorials/deploy-grails-to-google-cloud/cloudsql-2.png)

![](https://storage.googleapis.com/gcp-community/tutorials/deploy-grails-to-google-cloud/cloudsql-3.png)

![](https://storage.googleapis.com/gcp-community/tutorials/deploy-grails-to-google-cloud/cloudsql-4.png)

![](https://storage.googleapis.com/gcp-community/tutorials/deploy-grails-to-google-cloud/cloudsqlapi-1.png)

### Create a Cloud SQL Instance

[Create a new instance of Cloud SQL](https://console.cloud.google.com/sql)
associated to the same project which you created before:

1.  Go to the Cloud SQL section of the console:

    ![](https://storage.googleapis.com/gcp-community/tutorials/deploy-grails-to-google-cloud/cloudsql-5.png)

1.  The next screenshots illustrate the process:

    ![](https://storage.googleapis.com/gcp-community/tutorials/deploy-grails-to-google-cloud/cloudsql-6.png)

    ![](https://storage.googleapis.com/gcp-community/tutorials/deploy-grails-to-google-cloud/cloudsql-7.png)

    ![](https://storage.googleapis.com/gcp-community/tutorials/deploy-grails-to-google-cloud/cloudsql-8.png)

    ![](https://storage.googleapis.com/gcp-community/tutorials/deploy-grails-to-google-cloud/cloudsql-9.png)

1.  Once the instance is ready, create a database:

    ![](https://storage.googleapis.com/gcp-community/tutorials/deploy-grails-to-google-cloud/cloudsql-10.png)

    ![](https://storage.googleapis.com/gcp-community/tutorials/deploy-grails-to-google-cloud/cloudsql-11.png)

    ![](https://storage.googleapis.com/gcp-community/tutorials/deploy-grails-to-google-cloud/cloudsql-12.png)

### Datasource using Cloud SQL

As described in [Using Cloud SQL with a flexible environment][flex_cloud_sql]
documentation, you need to add several runtime dependencies and configure the
production URL to use the Cloud SQL MySQL database which you created before.

1.  Add the MySQL dependencies JDBC library and Cloud SQL MySQL Socket Factory:

    _build.gradle_
    
        runtime 'mysql:mysql-connector-java:8.0.16'
        runtime 'com.google.cloud.sql:mysql-socket-factory-connector-j-8:1.0.14'

1.  Replace the `production` environment `datasource` configuration to point to the
    Cloud SQL MySQL database in `application.yml`:

    _grails-app/conf/application.yml_

        production:
            dataSource:
                dialect: org.hibernate.dialect.MySQL5InnoDBDialect
                driverClassName: com.mysql.cj.jdbc.Driver
                dbCreate: update
                url: jdbc:mysql://google/grailsgooglecloud?socketFactory=com.google.cloud.sql.mysql.SocketFactory&cloudSqlInstance=inner-topic-174815:us-central1:grailsgooglecloud&useSSL=true
                username: root
                password: grailsgooglecloud

The production datasource URL uses a custom URL which is built with several components:

    jdbc:mysql://google/[DATABASE_NAME]?socketFactory=com.google.cloud.sql.mysql.SocketFactory&cloudSqlInstance=[INSTANCE_NAME]&useSSL=true

- For `[DATABASE_NAME]`, use the database name you used when you created the
  database.
- For `[INSTANCE_NAME]`, use your instance name, which is visible in your Cloud
  SQL instance details:

  ![](https://storage.googleapis.com/gcp-community/tutorials/deploy-grails-to-google-cloud/cloudsql-13.png)

- For this guide, use username `root`, and use the password which you entered when you created the SQL instance; see previous sections.

The [Cloud SQL Socket Factory for JDBC drivers Github Repository][factory]
contains a tool in `examples/getting-started` that can help generate the JDBC
URL and verify that connectivity can be established.

[flex_cloud_sql]: https://cloud.google.com/appengine/docs/flexible/java/using-cloud-sql
[factory]: https://github.com/GoogleCloudPlatform/cloud-sql-jdbc-socket-factory

## Cloud Storage

The app allows users to upload a book cover image. To store the images in GCP, use [Cloud Storage][storage].

Cloud Storage is unified object storage for developers and enterprises,
from live data serving to data analytics/ML to data archiving.

[Enable the Cloud Storage API](https://console.cloud.google.com/flows/enableapi?apiid=storage_api,logging,sqladmin.googleapis.com&redirect=https://console.cloud.google.com&_ga=1.20629880.1963584502.1488379440) for the project, if you have not enabled it already.

![Screenshot showing how to locate API Manager](https://storage.googleapis.com/gcp-community/tutorials/deploy-grails-to-google-cloud/cloudstorage-1.png)

![Screenshot showing how to search for Cloud Storage](https://storage.googleapis.com/gcp-community/tutorials/deploy-grails-to-google-cloud/cloudstorage-2.png)

![Screenshot showing Enable button](https://storage.googleapis.com/gcp-community/tutorials/deploy-grails-to-google-cloud/cloudstorage-3.png)

1.  You can create a Cloud Storage Bucket as illustrated in the images below.
    Name the bucket **grailsbucket**:

    ![Screenshot showing the Storage menu](https://storage.googleapis.com/gcp-community/tutorials/deploy-grails-to-google-cloud/cloudstorage-4.png)

    ![Screenshot showing the create bucket option](https://storage.googleapis.com/gcp-community/tutorials/deploy-grails-to-google-cloud/cloudstorage-5.png)

    ![Screenshot showing how to name and create a bucket](https://storage.googleapis.com/gcp-community/tutorials/deploy-grails-to-google-cloud/cloudstorage-6.png)

1.  Add Cloud Storage dependency to your project dependencies:

    _build.gradle_

        compile 'com.google.cloud:google-cloud-storage:1.84.0'

1.  Exclude `com.google.guava:guava-jdk5` too:

    _build.gradle_

        configurations {
            compile.exclude module: "tomcat-juli"
            compile.exclude module: "spring-boot-starter-tomcat"
            compile.exclude(group: "com.google.guava", module: "guava-jdk5")
        }

1.  Append these configuration (Cloud Storage Bucket and Project id) parameters
    to `application.yml`:

    _grails-app/conf/application.yml_

        ---
        googlecloud:
            projectid: grailsgooglecloud
            cloudStorage:
                bucket: grailsbucket

    These configuration parameters are used by the services described below.

1.  Create a Grails command object to manage file upload parameters.

    _grails-app/controllers/demo/FeaturedImageCommand.groovy_

        package demo

        import grails.compiler.GrailsCompileStatic
        import grails.validation.Validateable
        import org.springframework.web.multipart.MultipartFile

        @GrailsCompileStatic
        class FeaturedImageCommand implements Validateable {
            MultipartFile featuredImageFile
            Long id
            Long version

            static constraints = {
                id nullable: false
                version nullable: false
                featuredImageFile  validator: { MultipartFile val, FeaturedImageCommand obj ->
                    if ( val == null ) {
                        return false
                    }
                    if ( val.empty ) {
                        return false
                    }

                    ['jpeg', 'jpg', 'png'].any { String extension ->
                        val.originalFilename?.toLowerCase()?.endsWith(extension)
                    }
                }
            }
        }

1.  Add two controller actions to `BookController`:

    _grails-app/controllers/demo/BookController.groovy_

        UploadBookFeaturedImageService uploadBookFeaturedImageService

        @Transactional(readOnly = true)
        def editFeaturedImage(Book book) {
            respond book
        }
        @CompileDynamic
        def uploadFeaturedImage(FeaturedImageCommand cmd) {

            if (cmd.hasErrors()) {
                respond(cmd.errors, model: [book: cmd], view: 'editFeaturedImage')
                return
            }

            def book = uploadBookFeaturedImageService.uploadFeaturedImage(cmd)
            if (book == null) {
                notFound()
                return
            }

            if (book.hasErrors()) {
                respond(book.errors, model: [book: book], view: 'editFeaturedImage')
                return
            }

            request.withFormat {
                form multipartForm {
                    flash.message = message(code: 'default.updated.message', args: [message(code: 'book.label', default: 'Book'), book.id])
                    redirect book
                }
                '*' { respond book, [status: OK] }
            }
        }

1.  The previous controller actions use a service to manage the business logic.
    Create `UploadBookFeaturedImageService.groovy`:

    _grails-app/services/demo/UploadBookFeaturedImageService.groovy_

        package demo

        import groovy.util.logging.Slf4j
        import groovy.transform.CompileStatic

        @Slf4j
        @CompileStatic
        class UploadBookFeaturedImageService {

            BookGormService bookGormService

            GoogleCloudStorageService googleCloudStorageService

            private static String fileSuffix() {
                new Date().format('-YYYY-MM-dd-HHmmssSSS')
            }

            Book uploadFeaturedImage(FeaturedImageCommand cmd) {
                String fileName = "${cmd.featuredImageFile.originalFilename}${fileSuffix()}"

                log.info "cloud storage file name $fileName"

                String fileUrl = googleCloudStorageService.storeMultipartFile(fileName, cmd.featuredImageFile)

                log.info "cloud storage media url $fileUrl"

                def book = bookGormService.updateFeaturedImageUrl(cmd.id, cmd.version, fileName, fileUrl)
                if ( !book || book.hasErrors() ) {
                    googleCloudStorageService.deleteFile(fileName)
                }
                book
            }
        }

1.  Encapsulate the code which interacts with Cloud Storage in a service:

    _grails-app/services/demo/GoogleCloudStorageService.groovy_

        package demo

        import com.google.cloud.storage.Acl
        import com.google.cloud.storage.BlobId
        import com.google.cloud.storage.BlobInfo
        import com.google.cloud.storage.Storage
        import com.google.cloud.storage.StorageOptions
        import grails.config.Config
        import grails.core.support.GrailsConfigurationAware
        import org.springframework.web.multipart.MultipartFile
        import groovy.transform.CompileStatic

        @SuppressWarnings('GrailsStatelessService')
        @CompileStatic
        class GoogleCloudStorageService implements GrailsConfigurationAware {

            Storage storage = StorageOptions.defaultInstance.service

            // Google Cloud Platform project ID.
            String projectId

            // Cloud Storage Bucket
            String bucket

            @Override
            void setConfiguration(Config co) {
                projectId = co.getRequiredProperty('googlecloud.projectid', String)
                bucket = co.getProperty('googlecloud.cloudStorage.bucket', String, projectId)
            }

            String storeMultipartFile(String fileName, MultipartFile multipartFile) {
                storeInputStream(fileName, multipartFile.inputStream)
            }

            String storeInputStream(String fileName, InputStream inputStream) {
               BlobInfo blobInfo = storage.create(readableBlobInfo(bucket, fileName), inputStream)
                blobInfo.mediaLink
            }

            String storeBytes(String fileName, byte[] bytes) {
                BlobInfo blobInfo = storage.create(readableBlobInfo(bucket, fileName), bytes)
                blobInfo.mediaLink
            }

            private static BlobInfo readableBlobInfo(String bucket, String fileName) {
                BlobInfo.newBuilder(bucket, fileName)
                        // Modify access list to allow all users with link to read file
                        .setAcl([Acl.of(Acl.User.ofAllUsers(), Acl.Role.READER)])
                        .build()
            }

            boolean deleteFile(String fileName) {
                BlobId blobId = BlobId.of(bucket, fileName)
                storage.delete(blobId)
            }
        }

1.  If the upload of an image to Google Cloud is successful, save the reference
    to the media URL in our domain class. Add this method to the
    `BookGormService` class:

    _grails-app/services/demo/BookGormService.groovy_

        @SuppressWarnings('LineLength')
        Book updateFeaturedImageUrl(Long id, Long version, String fileName, String featuredImageUrl, boolean flush = false) {
            Book book = Book.get(id)
            if ( !book ) {
                return null
            }
            book.version = version
            book.fileName = fileName
            book.featuredImageUrl = featuredImageUrl
            book.save(flush: flush)
            book
        }

1.  Create a file named `grails-app/views/book/editFeaturedImage.gsp` from the
    content found in [editFeaturedImage.gsp](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/deploy-grails-to-google-cloud/editFeaturedImage.gsp).

## Deploying the App

To deploy the app to Google App Engine run:

    ./gradlew appengineDeploy

Initial deployment may take a while. When finished, you can access your app:

![Grails app deployed in Google Cloud](https://storage.googleapis.com/gcp-community/tutorials/deploy-grails-to-google-cloud/welcometograils.png)

Go to the [Versions](https://console.cloud.google.com/appengine/versions) section in the App Engine administration panel and see the deployed app.

## Logging

For the version which you would like to inspect, select **Logs** in the diagnose dropdown:

![Logs dropdown](https://storage.googleapis.com/gcp-community/tutorials/deploy-grails-to-google-cloud/logs.png)

Application log messages written to stdout and stderr are automatically collected and can be viewed in the Logs Viewer.

1.  Create a controller and log with level INFO and verify the log statement is
    visible in the Log Viewer:

    _grails-app/controllers/demo/LegalController.groovy_

        package demo

        import groovy.transform.CompileStatic
        import groovy.util.logging.Slf4j

        @CompileStatic
        @Slf4j
        class LegalController {
            def index() {
                log.info 'inside legal controller'
                render 'Legal Terms'
            }
        }

1.  Add the next line to `grails-app/conf/logback.groovy`:

        logger 'demo', INFO, ['STDOUT'], false

    to log `INFO` statements of classes under package `demo` to `STDOUT`
    appender with additivity `false`.

If you redeploy the app to App Engine and access the `/legal` end point, you
will see the logging statements in Log Viewer.

Check the [Writing Application Logs](https://cloud.google.com/appengine/docs/flexible/java/writing-application-logs) documentation to read more about logs in the flexible environment.

Write your application logs using stdout for output and stderr for errors. Note
that this does not provide log levels that you can use for filtering in the Logs
Viewer; however, the Logs Viewer does provide other filtering, such as text,
timestamp, etc.

## Cleaning up

When you finish this guide, clean up the resources you created on Google Cloud
Platform so you won't be billed for them in the future. The following sections
describe how to delete or turn off these resources.

### Deleting the project

The easiest way to eliminate billing is to delete the project you created for
the tutorial.

To delete the project:

Deleting a project has the following consequences:

- If you used an existing project, you'll also delete any other work you've done
  in the project.
- You can't reuse the project ID of a deleted project. If you created a custom
  project ID that you plan to use in the future, you should delete the resources
  inside the project instead. This ensures that URLs that use the project ID,
  such as an appspot.com URL, remain available.
- If you are exploring multiple tutorials and quickstarts, reusing projects
  instead of deleting them prevents you from exceeding project quota limits.

1.  In the Cloud Platform Console, go to the Projects page.

    [GO TO THE PROJECTS PAGE](https://console.cloud.google.com/iam-admin/projects)

1.  In the project list, select the project you want to delete and click
    **Delete project**. After selecting the checkbox next to the project name,
    click **Delete project**.

1.  In the dialog, type the project ID, and then click Shut down to delete the
    project.

**Deleting or turning off specific resources**

You can individually delete or turn off some of the resources that you created
during the tutorial.

### Deleting app versions

To delete an app version:

1.  In the Cloud Platform Console, go to the App Engine Versions page.

    [GO TO THE VERSIONS PAGE](https://console.cloud.google.com/appengine/versions)

1.  Click the checkbox next to the non-default app version you want to delete.

    Note: The only way you can delete the default version of your App Engine app
    is by deleting your project. However, you can stop the default version in
    the Cloud Platform Console. This action shuts down all instances associated
    with the version. You can restart these instances later if needed.

    In the App Engine standard environment, you can stop the default version
    only if your app has manual or basic scaling.

1.  Click the **Delete** button at the top of the page to delete the app version.

### Deleting Cloud SQL instances

To delete a Cloud SQL instance:

1.  In the Cloud Platform Console, go to the SQL Instances page.

    [GO TO THE SQL INSTANCES PAGE](https://console.cloud.google.com/sql/instances)

1.  Click the name of the SQL instance you want to delete.
1.  Click the **Delete** button at the top of the page to delete the instance.

### Deleting Cloud Storage buckets

To delete a Cloud Storage bucket:

1.  In the Cloud Platform Console, go to the Cloud Storage browser.

    [GO TO THE CLOUD STORAGE BROWSER](https://console.cloud.google.com/storage/browser)

1.  Click the checkbox next to the bucket you want to delete.
1.  Click the **Delete** button at the top of the page to delete the bucket.

## Learn More

Visit [Grails Guides](http://guides.grails.org) to learn more.

Moreover, if you want to learn more about Google Cloud and Grails integration,
checkout a more complete sample app.

The [Google Cloud Bookshelf with Grails](https://grails-samples.github.io/google-bookshelf/)
application shows how to use a variety of Google Cloud Platform products,
including some of the services described in this guides and other services such
as:

- Google [Cloud Vision API](https://cloud.google.com/vision/)
- Google [Cloud Translation API](https://cloud.google.com/translate)
- Authentication using [Google Identity Platform](https://developers.google.com/identity/)

[flex]: https://cloud.google.com/appengine/docs/flexible/
[storage]: https://cloud.google.com/storage/
[cloud_sql]: https://cloud.google.com/sql/
