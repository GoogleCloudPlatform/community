function runTest(test, data) {
    $ = data;
    return eval(`'use strict';(${test});`);
}

function evalMessage(message, data) {
    $ = data;
    return eval(`'use strict';\`${message}\`;`);
}

exports.pubsubLogSink = function (event, callback) {
    const base64 = require('base-64');
    let data = JSON.parse(base64.decode(event.data.data));

    Promise.all([
        getConfig(),
        getTests()
    ])
        .then(([config, tests]) => {
            return Promise.all(tests.map(test => {
                let clonedData = JSON.parse(JSON.stringify(data));
                if (runTest(test.test, clonedData)) {
                    let message = evalMessage(test.message, clonedData);
                    return sendSlack(test.slackChannel, message, config.slackAPIToken);
                }
                else {
                    return Promise.resolve();
                }
            }));
        })
        .then(() => {
            callback();
        });
};

function getConfig() {
    const Datastore = require('@google-cloud/datastore');
    const ds = Datastore();
    const query = ds.createQuery(['Config']);
    return runDSQuery(ds, query).then(configsArray => {
        return configsArray.reduce((configs, config) => {
            configs[config.name] = config.value;
            return configs;
        }, {});
    });
}

function getTests() {
    const Datastore = require('@google-cloud/datastore');
    const ds = Datastore();
    const query = ds.createQuery(['Test']);
    return runDSQuery(ds, query);
}

function runDSQuery(ds, query) {
    const Datastore = require('@google-cloud/datastore');
    return new Promise((resolve, reject) => {
        ds.runQuery(query, (err, entities, nextQuery) => {
            if (err) {
                reject(err);
            }
            const hasMore = nextQuery.moreResults !== Datastore.NO_MORE_RESULTS ? nextQuery.endCursor : false;
            if (hasMore) {
                runDSQuery(ds, nextQuery).then(moreEntities => {
                    resolve(entities.concat(moreEntities));
                });
            }
            else {
                resolve(entities);
            }
        });
    });
}

function sendSlack(channel, message, apiToken) {
    const Slack = require('slack-node');

    return new Promise((resolve, reject) => {
        const slack = new Slack(apiToken);
        slack.api('chat.postMessage', {
            text: message,
            channel: channel
        }, function (err, response) {
            if (!!err) {
                reject(err);
            }
            else {
                resolve(response);
            }
        });
    });
}
