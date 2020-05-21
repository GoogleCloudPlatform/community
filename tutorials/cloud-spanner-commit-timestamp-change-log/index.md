---
title: Using Cloud Spanner commit timestamps to create a change log with Go
description: Learn how to use Cloud Spanner commit timestamps to create a change log.
author: jsimonweb
tags: Cloud Spanner, Go
date_published: 2018-06-06
---

When was that record changed? Use Cloud Spanner to know.

If you have a large database with lots of transactions that change records, it can be a challenge to know
which records changed most recently. Cloud Spanner commit timestamps make this easy.

This tutorial describes how to use Cloud Spanner commit timestamps to track the dates and times of when changes are made to
your database records.

This tutorial includes two approaches to using commit timestamps:

* Include a commit timestamp column when you create your table.
* Create a companion history table when you create your table.

Here are the key points:

* Use Spanner commit timestamps to simplify the tracking of changes to your database.
* If you want to track only when records change in a particular table, create the table with a commit timestamp column.
* If you want to keep a log of how records change over time, create an additional history table
  that includes a commit timestamp column. Then use transactions to update the history table when records are
  inserted or updated.

## Include a commit timestamp column when you create your table

The simplest way to incorporate timestamps into your database is to include a commit timestamp column
when you create your table. Below is an SQL statement that creates a Spanner table that includes a
timestamp column named `Timestamp`. The extra options attribute `OPTIONS(allow_commit_timestamp=true)`
makes `Timestamp` a commit timestamp column and enables it to be auto-populated with the exact transaction
timestamp for INSERT and UPDATE operations on a given table row.

```sql
CREATE TABLE DocumentsWithTimestamp(
  UserId INT64 NOT NULL,
  DocumentId INT64 NOT NULL,
  Timestamp TIMESTAMP NOT NULL OPTIONS(allow_commit_timestamp=true),
  Contents STRING(MAX) NOT NULL
) PRIMARY KEY(UserId, DocumentId)
```

You can use this SQL statement to create a documents table named `DocumentsWithTimestamp`
using the Spanner page in the Cloud Console:

1.  Go to the [**Spanner** page](https://console.cloud.google.com/spanner) in the Cloud Console.
1.  Create a new Cloud Spanner instance named `spanner-sample`.
1.  Select the **Create Database** button.
1.  Enter the Database name as `sample-db` and click the **Continue** button.
1.  Click the **Edit as text** option to activate it and enter the SQL statement above as the DDL statement

When inserting records, use a method like the following Go sample code to
insert a timestamp in the commit timestamp column. This code snippet inserts the
`spanner.CommitTimestamp` constant, which populates the `Timestamp` column
with the exact timestamp of when each record was inserted:

```go
func writeToDocumentsTable(ctx context.Context, w io.Writer, client *spanner.Client) error {
	documentsColumns := []string{"UserId", "DocumentId", "Timestamp", "Contents"}
	m := []*spanner.Mutation{
		spanner.InsertOrUpdate("DocumentsWithTimestamp", documentsColumns,
			[]interface{}{1, 1, spanner.CommitTimestamp, "Hello World 1"}),
		spanner.InsertOrUpdate("DocumentsWithTimestamp", documentsColumns,
			[]interface{}{1, 2, spanner.CommitTimestamp, "Hello World 2"}),
		spanner.InsertOrUpdate("DocumentsWithTimestamp", documentsColumns,
			[]interface{}{1, 3, spanner.CommitTimestamp, "Hello World 3"}),
			...
```

When updating records, use a method like the following Go sample code to update the commit timestamp column.
This code updates five records and uses the **spanner.CommitTimestamp** constant which populates the **Timestamp** column
with the exact timestamp of when each record was updated:

```go
func updateDocumentsTable(ctx context.Context, w io.Writer, client *spanner.Client) error {
	cols := []string{"UserId", "DocumentId", "Timestamp", "Contents"}
	_, err := client.Apply(ctx, []*spanner.Mutation{
		spanner.Update("DocumentsWithTimestamp", cols,
			[]interface{}{1, 1, spanner.CommitTimestamp, "Hello World 1 Updated"}),
		spanner.Update("DocumentsWithTimestamp", cols,
			[]interface{}{1, 3, spanner.CommitTimestamp, "Hello World 3 Updated"}),
		spanner.Update("DocumentsWithTimestamp", cols,
			[]interface{}{2, 5, spanner.CommitTimestamp, "Hello World 5 Updated"}),
		spanner.Update("DocumentsWithTimestamp", cols,
			[]interface{}{3, 7, spanner.CommitTimestamp, "Hello World 7 Updated"}),
		spanner.Update("DocumentsWithTimestamp", cols,
			[]interface{}{3, 9, spanner.CommitTimestamp, "Hello World 9 Updated"}),
	})
	return err
}
```

If you want to find the last 5 records that were updated in the table,
the commit timestamp column allows you to use a query like the following:

```sql
SELECT UserId, DocumentId, Timestamp, Contents
FROM DocumentsWithTimestamp
ORDER BY Timestamp DESC Limit 5
```

This query returns the last 5 rows that were updated, in order from newest to oldest.

You can run this SQL statement to query the `DocumentsWithTimestamp`
table from the [**Cloud Spanner**](https://console.cloud.google.com/spanner) page in the Cloud Console.

## Create a companion history table when you create your table

As an alternative to adding timestamp columns to your table, if you would like to more
thoroughly track changes to your records over time, you can create a companion history table
when you create your table.

The following SQL statements create two tables: `Documents` and `DocumentHistory`:

```sql
CREATE TABLE Documents(
  UserId INT64 NOT NULL,
  DocumentId INT64 NOT NULL,
  Contents STRING(MAX) NOT NULL
) PRIMARY KEY(UserId, DocumentId)

CREATE TABLE DocumentHistory(
  UserId INT64 NOT NULL,
  DocumentId INT64 NOT NULL,
  Timestamp TIMESTAMP NOT NULL OPTIONS(allow_commit_timestamp=true),
  PreviousContents STRING(MAX)
) PRIMARY KEY(UserId, DocumentId, Timestamp), INTERLEAVE IN PARENT Documents ON DELETE NO ACTION
```

The `DocumentHistory` table stores a transaction timestamp along with a copy
of the `Documents` table's `Contents` column as it changes.

The `DocumentHistory` table's `PreviousContents` column is initially populated with the original value
inserted into the `Documents` table's `Contents` column. When a transaction updates a given row in the
`Documents` table before the the `Contents` column's value is changed, its current value is first saved in the 
`DocumentHistory` table's `PreviousContents` column along with a transaction timestamp in the `Timestamp` column.

The following Go code inserts 5 records into each of the tables as a transaction with commit timestamps:

```go
func writeWithHistory(ctx context.Context, w io.Writer, client *spanner.Client) error {
	_, err := client.ReadWriteTransaction(ctx, func(ctx context.Context, txn *spanner.ReadWriteTransaction) error {
		documentsColumns := []string{"UserId", "DocumentId", "Contents"}
		documentHistoryColumns := []string{"UserId", "DocumentId", "Timestamp", "PreviousContents"}
		txn.BufferWrite([]*spanner.Mutation{
			spanner.InsertOrUpdate("Documents", documentsColumns,
				[]interface{}{1, 1, "Hello World 1"}),
			spanner.InsertOrUpdate("Documents", documentsColumns,
				[]interface{}{1, 2, "Hello World 2"}),
			spanner.InsertOrUpdate("Documents", documentsColumns,
				[]interface{}{1, 3, "Hello World 3"}),
			spanner.InsertOrUpdate("Documents", documentsColumns,
				[]interface{}{2, 4, "Hello World 4"}),
			spanner.InsertOrUpdate("Documents", documentsColumns,
				[]interface{}{2, 5, "Hello World 5"}),
			spanner.InsertOrUpdate("DocumentHistory", documentHistoryColumns,
				[]interface{}{1, 1, spanner.CommitTimestamp, "Hello World 1"}),
			spanner.InsertOrUpdate("DocumentHistory", documentHistoryColumns,
				[]interface{}{1, 2, spanner.CommitTimestamp, "Hello World 2"}),
			spanner.InsertOrUpdate("DocumentHistory", documentHistoryColumns,
				[]interface{}{1, 3, spanner.CommitTimestamp, "Hello World 3"}),
			spanner.InsertOrUpdate("DocumentHistory", documentHistoryColumns,
				[]interface{}{2, 4, spanner.CommitTimestamp, "Hello World 4"}),
			spanner.InsertOrUpdate("DocumentHistory", documentHistoryColumns,
				[]interface{}{2, 5, spanner.CommitTimestamp, "Hello World 5"}),
		})
		return nil
	})
	return err
}
```

The following Go code updates 3 records in each table as a transaction with commit timestamps:

```go
func updateWithHistory(ctx context.Context, w io.Writer, client *spanner.Client) error {
	_, err := client.ReadWriteTransaction(ctx, func(ctx context.Context, txn *spanner.ReadWriteTransaction) error {
		// Create anonymous function "getContents" to read the current value of the Contents column for a given row.
		getContents := func(key spanner.Key) (string, error) {
			row, err := txn.ReadRow(ctx, "Documents", key, []string{"Contents"})
			if err != nil {
				return "", err
			}
			var content string
			if err := row.Column(0, &content); err != nil {
				return "", err
			}
			return content, nil
		}
		// Create two string arrays corresponding to the columns in each table.
		documentsColumns := []string{"UserId", "DocumentId", "Contents"}
		documentHistoryColumns := []string{"UserId", "DocumentId", "Timestamp", "PreviousContents"}
		// Get row's Contents before updating.
		previousContents, err := getContents(spanner.Key{1, 1})
		if err != nil {
			return err
		}
		// Update row's Contents while saving previous Contents in DocumentHistory table.
		txn.BufferWrite([]*spanner.Mutation{
			spanner.InsertOrUpdate("Documents", documentsColumns,
				[]interface{}{1, 1, "Hello World 1 Updated"}),
			spanner.InsertOrUpdate("DocumentHistory", documentHistoryColumns,
				[]interface{}{1, 1, spanner.CommitTimestamp, previousContents}),
		})
		previousContents, err = getContents(spanner.Key{1, 3})
		if err != nil {
			return err
		}
		txn.BufferWrite([]*spanner.Mutation{
			spanner.InsertOrUpdate("Documents", documentsColumns,
				[]interface{}{1, 3, "Hello World 3 Updated"}),
			spanner.InsertOrUpdate("DocumentHistory", documentHistoryColumns,
				[]interface{}{1, 3, spanner.CommitTimestamp, previousContents}),
		})
		previousContents, err = getContents(spanner.Key{2, 5})
		if err != nil {
			return err
		}
		txn.BufferWrite([]*spanner.Mutation{
			spanner.InsertOrUpdate("Documents", documentsColumns,
				[]interface{}{2, 5, "Hello World 5 Updated"}),
			spanner.InsertOrUpdate("DocumentHistory", documentHistoryColumns,
				[]interface{}{2, 5, spanner.CommitTimestamp, previousContents}),
		})
		return nil
	})
	return err
}
```

Now you can execute a query like the following that returns the last 3 documents that were updated
together with the previous versions of those 3 documents.

```sql
SELECT d.UserId, d.DocumentId, d.Contents, dh.Timestamp, dh.PreviousContents
FROM Documents d JOIN DocumentHistory dh
ON dh.UserId = d.UserId AND dh.DocumentId = d.DocumentId
ORDER BY dh.Timestamp DESC LIMIT 3
```

You can run this SQL statement to query the `Documents` and `DocumentHistory`
tables from the [**Cloud Spanner**](https://console.cloud.google.com/spanner) page in the Cloud Console.

## Next steps

* Explore [the runnable code sample](https://github.com/GoogleCloudPlatform/golang-samples/blob/master/spanner/spanner_snippets/snippet.go) that contains the code snippets included in this document.
* For a tutorial that shows how to use Java to create a change log, see [Creating a change log with JDBC using the commit timestamp feature of Cloud Spanner](https://cloud.google.com/solutions/using-spanner-commit-timestamp).
* See [the Cloud Spanner commit timestamp documentation](https://cloud.google.com/spanner/docs/commit-timestamp).
