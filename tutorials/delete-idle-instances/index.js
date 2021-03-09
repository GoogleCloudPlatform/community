// Copyright 2020 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//

const Compute = require('@google-cloud/compute');
const compute = new Compute();

/**
 * Mark, stop or delete idle instances.
 *
 * @param {Object} req Cloud Function request context.
 * @param {Object} res Cloud Function response context.
 */
exports.deleteIdleInstances = async (req, res) => {
  const options = _validateOptions(req.body);
  const zones = await _getZonesWithVMs(compute, options.label);
  if (zones.length === 0) {
    throw new Error(`No VMs matching label ${options.label} found.`);
  }
  await _scanRecommendations(zones, options);
  res.send(200);
  res.end();
};

/**
 * Validates that a request options contains the expected fields.
 *
 * @param {!object} options the request options to validate.
 * @return {!object} the options object.
 */
function _validateOptions (options) {
  if (options.label) {
    const parts = options.label.split('=');
    if (parts.length < 2) {
      throw new Error(`Label ${options.label} is not a key=value pair.`);
    }
    options.label.key = parts[1];
  }
  return options;
}

// operation.resource format:
// compute.googleapis.com/projects/PROJECT/zones/ZONE/instances/NAME
function _extractZoneAndName (operation) {
  return /\/zones\/(.*)\/instances\/(.*)$/.exec(operation.resource).slice(1, 3);
}

async function _getZonesWithVMs (compute, label) {
  const options = {};
  if (label) {
    options.filter = `labels.${label}`;
  }
  const vms = await compute.getVMs(options);
  const zoneSet = new Set();
  for (const vm of vms[0]) {
    zoneSet.add(vm.zone.id);
  }
  return Array.from(zoneSet);
}

async function _scanRecommendations (zones, options) {
  // Determine the current project used by Compute library
  const project = await compute.project().get();
  const projectId = project[1].name;

  const { RecommenderClient } = require('@google-cloud/recommender');
  const recommender = new RecommenderClient();
  const recommenderId = 'google.compute.instance.IdleResourceRecommender';
  const recommendations = [];
  for (const zone of zones) {
    const [zoneRecs] = await recommender.listRecommendations({
      parent: recommender.recommenderPath(projectId, zone, recommenderId)
    });
    for (const recommendation of zoneRecs) {
      console.info(`Recommendations from ${recommenderId} in zone ${zone}:`);
      for (const operationGroup of recommendation.content.operationGroups) {
        for (const operation of operationGroup.operations) {
          if (operation.action === 'replace') {
            const [zone, name] = _extractZoneAndName(operation);
            const [labels, fingerprint] = await compute.zone(zone).vm(name).getLabels();
            if (!options.label || options.label.key in labels) {
              switch (options.action) {
                case 'delete':
                  await compute.zone(zone).vm(name).delete();
                  await recommender.markRecommendationSucceeded(recommendation);
                  console.info(`Deleted instance ${name} in zone ${zone}`);
                  break;
                case 'stop':
                  await compute.zone(zone).vm(name).stop();
                  await recommender.markRecommendationSucceeded(recommendation);
                  console.info(`Stopped instance ${name} in zone ${zone}`);
                  break;
                default:
                  await compute.zone(zone).vm(name).setLabels({ delete: 'true' }, fingerprint);
                  await recommender.markRecommendationClaimed(recommendation);
                  console.info(`Unused instance ${name} in zone ${zone} marked for deletion`);
                  break;
              }
            } else {
              console.info(`Unused instance ${name} in zone ${zone} recommended for deletion but does not match label ${options.label}`);
            }
          }
        }
      }
    }
    recommendations.push(...zoneRecs);
  }
  return recommendations;
}
