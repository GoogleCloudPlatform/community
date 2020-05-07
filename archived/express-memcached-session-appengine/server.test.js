'use strict';

const assert = require(`assert`);
const express = require(`express`);
const session = require(`express-session`);
const proxyquire = require(`proxyquire`).noPreserveCache();
const sinon = require(`sinon`);
const request = require(`supertest`);

function getSample () {
  const testApp = express();
  sinon.stub(testApp, `listen`).callsArg(1);

  const storeMock = session.MemoryStore;
  const expressMock = sinon.stub().returns(testApp);
  const memcachedMock = sinon.stub().returns(storeMock);
  const publicIpMock = {
    v4: sinon.stub().yields(null, `123.45.67.890`)
  };

  const app = proxyquire(`./server.js`, {
    publicIp: publicIpMock,
    'connect-memjs': memcachedMock,
    express: expressMock
  });

  return {
    app: app,
    mocks: {
      express: expressMock,
      store: storeMock,
      'connect-memjs': memcachedMock,
      publicIp: publicIpMock
    }
  };
}

it(`sets up the sample`, () => {
  const sample = getSample();

  assert.equal(sample.mocks.express.callCount, 1);
  assert.equal(sample.app.listen.callCount, 1);
  assert.equal(sample.app.listen.firstCall.args[0], process.env.PORT || 8080);
});

it(`should respond with visit count`, (done) => {
  const sample = getSample();
  const expectedResult = `Viewed <strong>1</strong> times.`;

  request(sample.app)
    .get(`/`)
    .expect(200)
    .expect((response) => {
      assert.equal(response.text.includes(expectedResult), true);
    })
    .end(done);
});
