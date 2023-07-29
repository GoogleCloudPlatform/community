"use strict";
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : new P(function (resolve) { resolve(result.value); }).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
Object.defineProperty(exports, "__esModule", { value: true });
const winston_1 = require("winston");
const logging_winston_1 = require("@google-cloud/logging-winston");
const admin = require("firebase-admin");
const redis = require("redis");
const rateLimiter = require("redis-rate-limiter");
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
const objectsRef = db.collection('demo');
// set up logging (note FUNCTION_TARGET has replaced FUNCTION_NAME as reserved env var)
const loggingWinston = new logging_winston_1.LoggingWinston({ 'logName': process.env['FUNCTION_TARGET'] });
const logger = winston_1.createLogger({
    level: 'info',
    transports: [
        // goes to functions log
        new winston_1.transports.Console(),
        // goes to named log, under "Global" resource
        loggingWinston,
    ],
});
function counterLimit(req, res) {
    return __awaiter(this, void 0, void 0, function* () {
        const counterLimiter = rateLimiter.create({
            redis: client,
            key: function (x) { return 'counter-limit'; },
            window: 3,
            limit: 1
        });
        // always increase a redis counter, then check if we are rate limited in
        // writing that value to Firestore
        client.incr('counter', (err, counter) => {
            counterLimiter(req, (cterr, rate) => __awaiter(this, void 0, void 0, function* () {
                if (cterr) {
                    console.warn('Rate limiting not available');
                    console.warn(cterr);
                }
                else {
                    if (rate.over) {
                        res.send("counted ok");
                    }
                    else {
                        try {
                            let doc = yield objectsRef.doc('counter').get();
                            let data = yield doc.data();
                            if (data == undefined) {
                                data = { 'count': 0 };
                                yield objectsRef.doc('counter').set(data);
                            }
                            if (data['count'] < counter) {
                                yield objectsRef.doc('counter').set({ 'count': counter });
                                console.log("doc updated");
                            }
                            else {
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
            }));
        });
    });
}
exports.counterLimit = counterLimit;
//# sourceMappingURL=index.js.map