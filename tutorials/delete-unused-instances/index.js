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
const {RecommenderClient} = require('@google-cloud/recommender');
const recommender = new RecommenderClient();
const recommenderId = 'google.compute.instance.MachineTypeRecommender';
const project = 'jani-gce-test';

/**
 * List usage recommendations for a given product.
 * @param {string} project
 * @param {string} recommenderName
 */

exports.deleteUnusedInstances = async (event, context, callback) => {
  const options = _validateOptions(
    JSON.parse(Buffer.from(event.data, 'base64').toString())
  );
  const zones = await _getZonesWithVMs(options.label);
  if(zones.length == 0) {
    console.error(`No VMs matching label ${options.label} found.`);
    return;
  }
  const recommendations = await _markRecommendations(zones, options.label);
  if(options.delete == true) {
    _deleteRecommendations(recommendations);
  }
}

/**
 * Validates that a request options contains the expected fields.
 *
 * @param {!object} options the request options to validate.
 * @return {!object} the options object.
 */
function _validateOptions(options) {
  if (options.label) {
    let key, value = options.label.split('=');
    options.label.key = value;
  }
  if (!options.project) {
    throw new Error('Attribute \'project\' missing from options');
  }
  if (!options.delete) {
    options['delete'] = false;
  }
  return options;
}

// operation.resource format:
// compute.googleapis.com/projects/PROJECT/zones/ZONE/instances/NAME
function _extractZoneAndName(operation) {
  return /\/zones\/(.*)\/instances\/(.*)$/.exec(operation.resource).slice(1,3);
}

async function _getZonesWithVMs(label) {
  const options = {};
  if(label) {
    options['filter'] = `labels.${label}`;
  }
  const vms = await compute.getVMs(options);
  const zoneSet = new Set();
  for(const vm of vms[0]) {
    zoneSet.add(vm.zone.id);
  }
  return Array.from(zoneSet);
}

async function _markRecommendations(zones, label) {
  const recommendations = new Array();

  // parent = 'projects/my-project'; // Project to fetch recommendations for.
  // recommenderId = 'google.compute.instance.MachineTypeRecommender';

  for(const zone of zones) {
    const [zoneRecs] = await recommender.listRecommendations({
      parent: recommender.recommenderPath(project, zone, recommenderId),
    });
    for (const recommendation of recommendations) {
      console.info(`Recommendations from ${recommenderId} in zone ${zone}:`);
      for (const operationGroup of recommendation.content.operationGroups) {
        for (const operation of operationGroup.operations) {
          if(operation.action == 'replace') {
            const [zone, name] = _extractZoneAndName(operation)
            const [labels, fingerprint] = await compute.zone(zone).vm(name).getLabels();
            if(!label || label.key in labels) {
              console.info(`Unused instance ${name} in zone ${zone} marked for deletion`);
              await recommender.markRecommendationClaimed(recommendation);
              const data = await compute.zone(zone).vm(name).setLabels({delete: 'true'}, fingerprint);
              console.log(data);
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

async function _deleteRecommendations(recommendations) {
  for (const recommendation of recommendations) {
    if(recommendation.stateInfo.state == recommendation.stateInfo.CLAIMED) {
      for (const operationGroup of recommendation.content.operationGroups) {
        for (const operation of operationGroup.operations) {
          if(operation.action == 'replace') {
            // operation.resource format:
            // compute.googleapis.com/projects/PROJECT/zones/ZONE/instances/NAME
            const [zone, name] = extractZoneAndName(operation)
            console.info(`Tag instance ${name} in zone ${zone} for deletion`);
            await recommender.markRecommendationSucceeded(recommendation);
            const data = await compute.zone(zone).vm(name).get();
            console.log(data);
          }
        }
      }
    }
  }
}

// Stub to allow local execution with node index.js '{options}'
function main(args) {
  exports.deleteUnusedInstances({data: Buffer.from(args, 'utf-8').toString('base64')});
}
main(...process.argv.slice(2));

//main(...process.argv.slice(2)).catch(err => {
//  console.error(err);
//  process.exitCode = 1;
//});
