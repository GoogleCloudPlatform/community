import datetime
import hashlib
import json
import os
import sys

from google.cloud.securitycenter_v1p1beta1 import CreateFindingRequest, ListFindingsRequest, UpdateFindingRequest, Finding, SecurityCenterClient
from google.cloud import storage


# tag that maps to the SCC finding category
tag_scc_category = 'scc_category'
tag_resource_type = 'resource_type'

# API clients
gcs = None
scc = None


def on_finalize(event, context):
  """Function entry point, triggered by creation of object in a Cloud Storage bucket"""
  global gcs
  if not gcs:
    gcs = storage.Client()

  print('Processing InSpec report: %s' % event['name'])
  bucket = storage.Bucket(name=event['bucket'], client=gcs)
  blob = bucket.blob(event['name'])
  report_str = blob.download_as_string()
  report = json.loads(report_str)

  scc_source = os.environ.get('SCC_SOURCE',
      'SCC_SOURCE environment variable is not set.')
  _inspec_report_to_scc(report, scc_source)


def _inspec_report_to_scc(report, scc_source):
  """Creates/updates SCC findings based on supplied InSpec JSON report"""
  global scc
  if not scc:
    scc = SecurityCenterClient()

  # get the set of existing SCC Findings for this source
  current_findings = _get_findings(scc, scc_source)

  # InSpec tests are grouped into profiles and controls
  for prof in report['profiles']:
    controls = prof['controls']
    for control in controls:
      _add_control_findings(scc, scc_source, control, current_findings)


def _add_control_findings(scc, scc_source, control, current_findings):
  """Creates/updates SCC findings for InSpec test results"""
  results = control['results']
  if not results:
    return

  # extract details from InSpec control, converting to SCC types where necessary
  severity = _impact_to_severity(control['impact'])
  tags = control['tags']
  category = tags[tag_scc_category]
  resource_type = tags[tag_resource_type]
  control_id = control['id']
  print("\nInSpec Control '%s' has %d test results" % (control_id, len(results)))

  created_count = 0
  updated_count = 0
  # add/update SCC Findings per InSpect test result
  for result in results:
    finding_state = _status_to_state(result['status'])
    event_time = datetime.datetime.strptime(
      result['start_time'], '%Y-%m-%dT%H:%M:%S%z')
    resource_name = _parse_code_desc(result['code_desc'])
    finding_id = _create_finding_id(control_id, resource_name)

    # This InSpec test does not exist in SCC, and the InSpec test passed or skipped.
    # We don't need to add/update SCC
    if finding_id not in current_findings and finding_state != Finding.State.ACTIVE:
      continue

    # if we haven't seen this failed test before, create a new finding
    if finding_id not in current_findings:
      finding = Finding(
        state=finding_state,
        resource_name=resource_name,
        category=category,
        event_time=event_time,
        severity=severity
      )
      created = scc.create_finding(
        parent=scc_source,
        finding_id=finding_id,
        finding=finding
      )
      created_count += 1
      print('Created Finding:%s for %s violation for resource: %s/%s' % (
        finding_id, category, resource_type, resource_name))

    # otherwise, update existing SCC finding state
    else:
      fq_finding_name = '{source_name}/findings/{finding_id}'.format(
          source_name=scc_source, finding_id=finding_id)
      updated = scc.set_finding_state(
        name=fq_finding_name,
        state=finding_state,
        start_time=event_time
      )
      updated_count += 1
      print('Updated Finding:%s state:%s for %s violation for resource: %s/%s'
        % (finding_id, finding_state, category, resource_type, resource_name))
  print('Created %d new Findings, updated %d Findings' % (created_count, updated_count))


def _get_findings(scc, source):
  """Retrieves SCC Finding IDs for the supplied Source"""
  request = ListFindingsRequest(
    parent=source,
  )
  findings_response = scc.list_findings(request=request)
  findings_dict = {}
  for fr in findings_response:
    finding = fr.finding
    finding_id = finding.name.split('/')[5]
    findings_dict[finding_id] = finding
  return findings_dict


def _parse_code_desc(code_desc):
  """code_desc report field contains resource info.

  Depends upon a consistent naming convention for InSpec tests.
  For example: "[resource_name][project_id] Test details..."
  """
  close_index = code_desc.find(']')
  return code_desc[1:close_index]


def _create_finding_id(control_id, resource_name, length=20):
  """Hash the control and resource; repeatable (tho not strictly unique).

  Needs to be repeatable such that the same control/test maps to the
  same SCC Finding over multiple runs.
  """
  input = control_id + resource_name
  hex = hashlib.sha256(input.encode('UTF-8')).hexdigest()
  result = int(hex, 16) % (10 ** length)
  return str(result)


def _status_to_state(status):
  """Translates an InSpec status to an SCC Finding State"""
  if status == 'failed':
    return Finding.State.ACTIVE
  elif status == 'passed' or status == 'skipped':
    return Finding.State.INACTIVE
  else:
    return Finding.State.STATE_UNSPECIFIED


def _impact_to_severity(impact):
  """Translates an InSpec impact to an SCC Severity"""
  if impact >= 0.9:
    return Finding.Severity.CRITICAL
  elif impact >= 0.7:
    return Finding.Severity.HIGH
  elif impact >= 0.4:
    return Finding.Severity.MEDIUM
  elif impact >= 0.01:
    return Finding.Severity.LOW
  else:
    return Finding.Severity.SEVERITY_UNSPECIFIED


def main():
  """For local testing"""
  args = sys.argv[1:]
  if len(args) != 3:
    print('Incorrect args')
    return

  report_file = args[0]
  org_id = args[1]
  source_id = args[2]
  # fully qualified source name
  scc_source = "organizations/{org_id}/sources/{src_id}".format(
    org_id=org_id, src_id=source_id)

  with open(report_file) as f:
    report = json.load(f)
    _inspec_report_to_scc(report, scc_source)


if __name__ == "__main__":
  main()
