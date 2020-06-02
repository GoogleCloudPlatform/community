/* Copyright 2018-2019 Google LLC
 *
 * This is part of the Google Cloud IoT Device SDK for Embedded C,
 * it is licensed under the BSD 3-Clause license; you may not use this file
 * except in compliance with the License.
 *
 * You may obtain a copy of the License at:
 *  https://opensource.org/licenses/BSD-3-Clause
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include <iotc_bsp_time.h>

#include <stddef.h>
#include <sys/time.h>

void iotc_bsp_time_init() { /* empty */
}

iotc_time_t iotc_bsp_time_getcurrenttime_seconds() {
  struct timeval current_time;
  gettimeofday(&current_time, NULL);
  return (iotc_time_t)((current_time.tv_sec) +
                       (current_time.tv_usec + 500000) /
                           1000000); /* round the microseconds to seconds */
}

iotc_time_t iotc_bsp_time_getcurrenttime_milliseconds() {
  struct timeval current_time;
  gettimeofday(&current_time, NULL);
  return (iotc_time_t)((current_time.tv_sec * 1000) +
                       (current_time.tv_usec + 500) /
                           1000); /* round the microseconds to milliseconds */
}
