import { Request, Response } from "express"

import redis = require('redis');
import rateLimiter = require('redis-rate-limiter');

const env = require('good-env');

const redisAddress = env.get('REDIS_HOST', '127.0.0.1');

// create the redis client as part of function initialization
// outside of function request scope
const client = redis.createClient(6379, redisAddress, { enable_offline_queue: true });


export function basicRateDemo(req: Request, res: Response) {
    // const client = redis.createClient(6379, redisAddress, {enable_offline_queue: true});
    const limit = rateLimiter.create({
        redis: client,
        key: function (requestObj: any) { return 'basicRate' },
        rate: '10/second'
    });
    limit(req, function (err: Error, rate: any) {
        if (err) {
            console.warn('Rate limiting not available');
            // fail open
            res.send("OK\n");
        } else {
            if (rate.over) {
                console.error('Over the limit!');
                res.send(429);
            } else {
                res.send("OK\n");
            }
        }
    });
}

