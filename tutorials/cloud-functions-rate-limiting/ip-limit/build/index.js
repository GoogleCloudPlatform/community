"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const redis = require("redis");
const rateLimiter = require("redis-rate-limiter");
const env = require('good-env');
const redisAddress = env.get('REDIS_HOST', '127.0.0.1');
// create the redis client as part of function initialization
// outside of function request scope
const client = redis.createClient(6379, redisAddress, { enable_offline_queue: true });
function IPRateDemo(req, res) {
    const limit = rateLimiter.create({
        redis: client,
        key: function (requestObj) { return requestObj.ip; },
        rate: '10/second'
    });
    limit(req, function (err, rate) {
        if (err) {
            console.warn('Rate limiting not available');
            // fail open
            res.send("OK\n");
        }
        else {
            if (rate.over) {
                console.error('Over the limit for ' + req.ip);
                res.send(429);
            }
            else {
                res.send("OK\n");
            }
        }
    });
}
exports.IPRateDemo = IPRateDemo;
//# sourceMappingURL=index.js.map