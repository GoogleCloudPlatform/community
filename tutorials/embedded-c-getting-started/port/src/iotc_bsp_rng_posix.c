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

#include <iotc_bsp_rng.h>

/* No TLS option choosen */
#if !defined(IOTC_TLS_LIB_MBEDTLS) && !defined(IOTC_TLS_LIB_WOLFSSL)

#include <stdlib.h>
#include <time.h>

void iotc_bsp_rng_init() { srand(time(NULL)); }

uint32_t iotc_bsp_rng_get() {
#ifdef IOTC_BSP_RNG_16BIT_INT_PLATFORM
  const uint32_t half_a = rand();
  const uint32_t half_b = rand();

  return (half_a << 16) | (half_b & 0x0000FFFF);
#else
  return rand();
#endif
}

void iotc_bsp_rng_shutdown() { /* nothing to do here */
}

#elif defined(IOTC_TLS_LIB_MBEDTLS) /* MBEDTLS version of RNG implementation \
                                     */

#include <mbedtls/config.h>
#include <mbedtls/ctr_drbg.h>
#include <mbedtls/entropy.h>

#include <stdio.h>

static mbedtls_entropy_context entropy;
mbedtls_ctr_drbg_context ctr_drbg;

void iotc_bsp_rng_init() {
  const char personalization[] = "iotc_bsp_mbedtls_more_entropy_pls";

  mbedtls_entropy_init(&entropy);
  mbedtls_ctr_drbg_init(&ctr_drbg);

  const int ret_state = mbedtls_ctr_drbg_seed(
      &ctr_drbg, mbedtls_entropy_func, &entropy,
      (const unsigned char*)personalization, sizeof(personalization));

  if (ret_state != 0) {
    printf(" failed\n  ! mbedtls_ctr_drbg_seed returned %d\n", ret_state);
    goto exit;
  }

exit:;
}

uint32_t iotc_bsp_rng_get() {
  uint32_t random = 0;

  mbedtls_ctr_drbg_random(&ctr_drbg, (unsigned char*)&random, 4);

  return random;
}

void iotc_bsp_rng_shutdown() {
  mbedtls_ctr_drbg_free(&ctr_drbg);
  mbedtls_entropy_free(&entropy);
}

#elif defined(IOTC_TLS_LIB_WOLFSSL) /* WOLFSSL version of RNG implementation \
                                     */

#include <cyassl/ctaocrypt/memory.h>
#include <cyassl/ctaocrypt/random.h>
#include <iotc_allocator.h>

WC_RNG wolfcrypt_rng;

void iotc_bsp_rng_init() {
  /* check if already initialized */
  if (NULL == wolfcrypt_rng.drbg) {
    CyaSSL_SetAllocators(iotc_alloc_ptr, iotc_free_ptr, iotc_realloc_ptr);

    wc_InitRng(&wolfcrypt_rng);
  }
}

uint32_t iotc_bsp_rng_get() {
  uint32_t random = 0;

  wc_RNG_GenerateBlock(&wolfcrypt_rng, (byte*)&random, 4);

  return random;
}

void iotc_bsp_rng_shutdown() { wc_FreeRng(&wolfcrypt_rng); }

#endif
