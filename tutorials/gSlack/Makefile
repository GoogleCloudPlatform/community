all:

create-export:
	gcloud --project=$$PROJECT beta pubsub topics create gcp-alert-service
	
	gcloud --project=$$PROJECT beta logging sinks create gcp_alert_service \
		pubsub.googleapis.com/projects/$$PROJECT/topics/gcp-alert-service \
		--log-filter "logName=projects/$$PROJECT/logs/cloudaudit.googleapis.com%2Factivity"

	gcloud --project=$$PROJECT projects add-iam-policy-binding $$PROJECT \
		--member=$$(gcloud --project $$PROJECT --format="value(writer_identity)" beta logging sinks describe gcp_alert_service) \
		--role='roles/pubsub.publisher'

	gsutil mb -p $$PROJECT gs://$$PROJECT-gcp-alert-service

	gcloud --project=$$PROJECT beta service-management enable cloudfunctions.googleapis.com

deploy-function:
	gcloud --project=$$PROJECT beta functions deploy gcp-alert-service \
		--stage-bucket $$PROJECT-gcp-alert-service --trigger-topic gcp-alert-service \
		--entry-point=pubsubLogSink --region=us-central1
