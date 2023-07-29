import argparse

import google.auth
import google.auth.impersonated_credentials
from google.cloud.securitycenter_v1p1beta1 import SecurityCenterClient

parser = argparse.ArgumentParser()
parser.add_argument('--org_id', required=True)
parser.add_argument('--serviceaccount', required=True)
args = parser.parse_args()


def print_sources(scc, org_name):
  for i, source in enumerate(scc.list_sources(request={"parent": org_name}, retry=None)):
      print(i, source)


def create_inspec_source(scc, org_name):
  new_source = scc.create_source(
      request={
          "parent": org_name,
          "source": {
              "display_name": "InSpec",
              "description": "A new custom source for InSpec findings",
          },
      }
  )
  print('SOURCE_ID: %s' % new_source.name.split('/')[3])
  


def main():
  org_name = "organizations/{org_id}".format(org_id=args.org_id)
  creds, pid = google.auth.default()
  impersonated = google.auth.impersonated_credentials.Credentials(
    source_credentials=creds,
    target_principal=args.serviceaccount,
    target_scopes=['https://www.googleapis.com/auth/cloud-platform'],
  )
  scc_client = SecurityCenterClient(credentials=impersonated)
  
  # print_sources(scc_client, org_name)
  create_inspec_source(scc_client, org_name)


if __name__ == "__main__":
  main()
