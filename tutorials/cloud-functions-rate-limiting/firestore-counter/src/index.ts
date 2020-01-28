import { Request, Response } from "express"
import { createLogger, transports } from 'winston';
import { LoggingWinston } from '@google-cloud/logging-winston';

import admin = require('firebase-admin');
import redis = require('redis');
import rateLimiter = require('redis-rate-limiter');

const env = require('good-env');

const redisAddress = env.get('REDIS_HOST', '127.0.0.1');

// create the redis client as part of function initialization
// outside of function request scope
const client = redis.createClient(6379, redisAddress, { enable_offline_queue: true });

admin.initializeApp({
    credential: admin.credential.applicationDefault()
});

const db = admin.firestore();
db.settings({ timestampsInSnapshots: true });

const objectsRef = db.collection('demo')

// set up logging (note FUNCTION_TARGET has replaced FUNCTION_NAME as reserved env var)
const loggingWinston = new LoggingWinston({ 'logName': process.env['FUNCTION_TARGET'] });
const logger = createLogger({
    level: 'info',
    transports: [
        // goes to functions log
        new transports.Console(),
        // goes to named log, under "Global" resource
        loggingWinston,
    ],
});

export async function counterLimit(req: Request, res: Response) {
    const counterLimiter = rateLimiter.create({
        redis: client,
        key: function (x: any) { return 'counter-limit' },
        window: 3,
        limit: 1
    });
    // always increase a redis counter, then check if we are rate limited in
    // writing that value to Firestore
    client.incr('counter', (err: Error | null, counter: number) => {
        counterLimiter(req, async (cterr: Error, rate: any) => {
            if (cterr) {
                console.warn('Rate limiting not available');
                console.warn(cterr);
            } else {
                if (rate.over) {
                    res.send("counted ok");
                } else {
                    try {
                        let doc = await objectsRef.doc('counter').get();
                        let data = await doc.data();

                        if (data == undefined) {
                            data = { 'count': 0 };
                            await objectsRef.doc('counter').set(data);
                        }
                        if (data['count'] < counter) {
                            await objectsRef.doc('counter').set({ 'count': counter })
                            console.log("doc updated");
                        } else {
                            console.warn("out of order counter write");
                        }
                        res.send("ok");
                    }
                    catch (err) {
                        console.warn(err);
                        res.sendStatus(500);
                    }
                }
            }
        });
    });
}
