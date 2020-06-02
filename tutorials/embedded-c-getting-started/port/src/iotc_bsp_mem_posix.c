// Copyright 2018-2019 Espressif Systems (Shanghai) PTE LTD
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include <iotc_bsp_mem.h>
#include <stdlib.h>
#include <esp_attr.h>
#include <esp_heap_caps.h>
#include <sdkconfig.h>

IRAM_ATTR void *iotc_bsp_mem_alloc(size_t byte_count)
{
#if (CONFIG_SPIRAM_SUPPORT && (CONFIG_SPIRAM_USE_CAPS_ALLOC || CONFIG_SPIRAM_USE_MALLOC))
    return heap_caps_malloc(byte_count, MALLOC_CAP_SPIRAM|MALLOC_CAP_8BIT);
#else
    return malloc(byte_count);
#endif
}

IRAM_ATTR void *iotc_bsp_mem_realloc(void* ptr, size_t byte_count)
{
#if (CONFIG_SPIRAM_SUPPORT && (CONFIG_SPIRAM_USE_CAPS_ALLOC || CONFIG_SPIRAM_USE_MALLOC))
    return heap_caps_realloc(ptr, byte_count, MALLOC_CAP_SPIRAM|MALLOC_CAP_8BIT);
#else
    return realloc(ptr, byte_count);
#endif
}

IRAM_ATTR void iotc_bsp_mem_free(void* ptr)
{
    heap_caps_free(ptr);
}
