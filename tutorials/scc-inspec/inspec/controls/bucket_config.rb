title 'Ensure that Cloud Storage buckets are configured according to policy'

project_id = input('project_id')
bucket_ignore_pattern = input('bucket_ignore_pattern')

control 'policy_bucket_config' do
  title 'Cloud Storage bucket configuration policy'
  desc 'Compliance policy checks for Cloud Storage buckets'
  impact 'medium'
  tag scc_category: 'BUCKET_CONFIG'
  tag resource_type: 'bucket'
  tag project_id: project_id

  google_storage_buckets(project: project_id).bucket_names.each do |bucket|
    describe "[#{bucket}][#{project_id}] GCS Bucket" do
      before do
        skip if bucket.match?(bucket_ignore_pattern)
      end
      subject { google_storage_bucket(name: bucket) }
      its('storage_class') { should eq 'STANDARD' }
      its('location') { should be_in ['US-CENTRAL1', 'US'] }
    end
  end
end
