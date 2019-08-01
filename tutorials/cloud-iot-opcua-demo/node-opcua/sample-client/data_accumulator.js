/*
# Copyright Google Inc. 2019
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
*/
module.exports = class Accumulator {
  constructor(fulfillmentThreshold, onIntervalFulfill) {
    this.fulfillmentThreshold = fulfillmentThreshold;
    this.onIntervalFulfill = onIntervalFulfill;
    this.reset();
  }

  reset() {
    this.accumulator = 0;
    this.intervalStart = null;
    this.intervalEnd = null;
    this.intervalLength = 0;
    this.maxValue = Number.MIN_SAFE_INTEGER;
    this.minValue = Number.MAX_SAFE_INTEGER;
  };

  update(value, timeStamp) {
    this.accumulator += value;
    this.intervalEnd = timeStamp;
    if (!this.intervalStart) {
      this.intervalStart = timeStamp;
    }
    if (value > this.maxValue) {
      this.maxValue = value;
    }
    if (value < this.minValue) {
      this.minValue = value;
    }
    this.intervalLength = this.intervalEnd - this.intervalStart;
    if (this.intervalFulfilled()) {
      this.runFulfill();
    }
  };

  intervalFulfilled() {return this.intervalLength >= this.fulfillmentThreshold};

  hasValueStored() {return this.accumulator > 0}; 

  runFulfill() {
    if (this.hasValueStored()) {
      this.onIntervalFulfill(this.accumulator, this.maxValue, this.minValue, this.intervalEnd, this.intervalLength);
      this.reset();
    }
  };
}