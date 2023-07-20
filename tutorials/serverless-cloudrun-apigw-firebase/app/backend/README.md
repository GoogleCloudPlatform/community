# Employees API 

Open API Specifications: api-gateway--espv2-definition.yaml

Cloud API Gateway

1. Create a service account that will be used by OpenAPI configurations to invoke Cloud Run Executions

gcloud iam service-accounts create api-gateway-sa --display-name="API Gateway Service Account" --description="Service Account to Deploy OpenAPI configs to the API Gateway"

assuming that this is the Service Account: api-gateway-sa@PROJECT_ID.iam.gserviceaccount.com
api-gateway-sa@gp-service-project.iam.gserviceaccount.com

2. Grant the Service Account the roles/run.invoker role so that it can invoke Cloud Run services. 

gcloud projects add-iam-policy-binding PROJECT_NUMBER --member='serviceAccount:api-gateway-sa@PROJECT_ID.iam.gserviceaccount.com'  --role='roles/run.invoker'
gcloud projects add-iam-policy-binding 1036905305322 --member='serviceAccount:api-gateway-sa@gp-service-project.iam.gserviceaccount.com'  --role='roles/run.invoker'

3. create the API

gcloud api-gateway apis create amazing-employees-api 

4. Upload an OpenAPI configuration for the API we just created

gcloud api-gateway api-configs create amazing-employees-api-config --api=amazing-employees-api --backend-auth-service-account=api-gateway-sa@PROJECT_ID.iam.gserviceaccount.com --openapi-spec=openapi-spec.yaml
gcloud api-gateway api-configs create amazing-employees-api-config --api=amazing-employees-api --backend-auth-service-account=api-gateway-sa@gp-service-project.iam.gserviceaccount.com --openapi-spec=api-gateway--espv2-definition.yaml

5. Enable the API from gcloud … 

gcloud services list --available | grep amazing
gcloud services enable amazing-employees-api-2r9pl0cajhcvj.apigateway.gp-service-project.cloud.goog

6. (OPTIONAL) create an api key and then restrict it to the service just enabled (Remove the security components from the Open API specification if the KEY is not needed)

7 . deploy the API and its configuration to a gateway

gcloud api-gateway gateways create amazing-employees-api \
  --api=amazing-employees-api --api-config=amazing-employees-api-config \
  --location=us-east1





