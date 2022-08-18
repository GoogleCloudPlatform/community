from flask import Flask, request, render_template, jsonify
import os, sys, json
from google.cloud import bigquery

#connection_id=os.getenv("SPANNER_BQ_CONNECTION")

app = Flask(__name__)

# main application logic
def process(input):

    # Construct a BigQuery client object.
    client = bigquery.Client()

    # with database.snapshot() as snapshot:
    #     results = snapshot.execute_sql(SPANNER_SQL_GET.format(order_id=input))

    # output=None
    # for row in results:
    #     output=row[0]

    # parameterized query doesn't seem to work inside external query
    # using traditional string substitution as long as the input data is trusted (i.e. no SQL injection)
    # query_job = client.query(
    #     f"""
    #     SELECT
    #     t1.jobExecutionId, 
    #     t1.inputIdCount,
    #     ifnull(t2.totalOutputCount,0) as totalOutputCount, 
    #     ifnull(t2.totalDistinctOutputCount,0) as totalDistinctOutputCount
    #     FROM 
    #     EXTERNAL_QUERY("us.{connection_id}", "SELECT jobExecutionId,inputIdCount FROM job_executions where jobExecutionId='{input}'") t1
    #     left outer join
    #     ( select jobExecutionId,count(1) totalOutputCount, count(distinct skuId) totalDistinctOutputCount from `web_scraping.output_records` where jobExecutionId=@jobExecutionId group by jobExecutionId) t2
    #     on t1.jobExecutionId = t2.jobExecutionId limit 1
    #     """
    #     ,job_config=bigquery.QueryJobConfig(
    #         query_parameters=[
    #             bigquery.ScalarQueryParameter("jobExecutionId", "STRING", input),
    #         ]
    #     )
    # )
    query_job = client.query(
        f"""
        select jobExecutionId,count(1) totalOutputCount, count(distinct skuId) totalDistinctOutputCount 
        from `web_scraping.output_records` where jobExecutionId=@jobExecutionId group by jobExecutionId 
        limit 1
        """
        ,job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("jobExecutionId", "STRING", input),
            ]
        )
    )
    

    output={
        #"isComplete": False,
        #"inputIdCount": -1,
        "totalOutputCount": -1,
        "totalDistinctOutputCount": -1,
    }

    for row in query_job:
      output["totalOutputCount"]=row.totalOutputCount
      output["totalDistinctOutputCount"]=row.totalDistinctOutputCount
      #output["inputIdCount"]=row.inputIdCount
      #if row.totalDistinctOutputCount >= row.inputIdCount:
        #output["isComplete"]=True

    return output

@app.route("/job/<id>", methods=["GET"])
def get_job_status(id):
    try:
        return jsonify(process(id))

    except RuntimeError:
        return f"Bad Request", 400


if __name__ == "__main__":
    PORT = int(os.getenv("PORT")) if os.getenv("PORT") else 8080

    # for local dev only
    if len(sys.argv) == 1:
        app.run(host="127.0.0.1", port=PORT, debug=True)
    elif len(sys.argv) == 2:
        print(process(sys.argv[1]))