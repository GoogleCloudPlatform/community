/******************************************************************************
 * Copyright 2020 Google LLC
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *****************************************************************************/
#include "include.h"

static void initialize_sntp(void) {
    ESP_LOGI(TAG, "Initializing SNTP");
    sntp_setoperatingmode(SNTP_OPMODE_POLL);
    sntp_setservername(0, "time.google.com");
    sntp_init();
}

static void obtain_time(void) {
    initialize_sntp();
    // wait for time to be set
    time_t now = 0;
    struct tm timeinfo = {0};
    while (timeinfo.tm_year < (2016 - 1900)) {
        ESP_LOGI(TAG, "Waiting for system time to be set...");
        vTaskDelay(2000 / portTICK_PERIOD_MS);
        time(&now);
        localtime_r(&now, &timeinfo);
    }
    ESP_LOGI(TAG, "Time is set...");
}

void publish_telemetry_event(iotc_context_handle_t context_handle, iotc_timed_task_handle_t timed_task, void *user_data) {
    char *publish_topic = NULL;
    asprintf(&publish_topic, PUBLISH_TOPIC_EVENT, CONFIG_GIOT_DEVICE_ID);

    char *publish_message = NULL;
    asprintf(&publish_message, TEMPERATURE_DATA, ((temprature_sens_read() - 32) / 1.8));
    ESP_LOGI(TAG, "publishing msg \"%s\" to topic: \"%s\"", publish_message, publish_topic);

    iotc_publish(context_handle, publish_topic, publish_message, iotc_example_qos, /*callback=*/NULL, /*user_data=*/NULL);

    free(publish_topic);
    free(publish_message);
}

void iotc_mqttlogic_subscribe_callback(iotc_context_handle_t in_context_handle, iotc_sub_call_type_t call_type, const iotc_sub_call_params_t *const params, iotc_state_t state, void *user_data) {
    char *sub_message = (char *)malloc(params->message.temporary_payload_data_length + 1);
    memcpy(sub_message, params->message.temporary_payload_data, params->message.temporary_payload_data_length);
    sub_message[params->message.temporary_payload_data_length] = '\0';
    ESP_LOGI(TAG, "Delegate Message Payload: %s", sub_message);
    if (strcmp(subscribe_topic_command, params->message.topic) == 0)
    {
        gpio_pad_select_gpio(BLINK_GPIO);
        /* Set the GPIO as a push/pull output */
        gpio_set_direction(BLINK_GPIO, GPIO_MODE_OUTPUT);

        int value;
        sscanf(sub_message, "light: %d", &value);
        ESP_LOGI(TAG, "value: %d\n", value);
        if (value == 1)
        {
            ESP_LOGI(TAG, "ON");
            gpio_set_level(BLINK_GPIO, 1);
        }
        else if (value == 0)
        {
            gpio_set_level(BLINK_GPIO, 0);
        }
    }
    free(sub_message);
}

void on_connection_state_changed(iotc_context_handle_t in_context_handle, void *data, iotc_state_t state) {
    iotc_connection_data_t *conn_data = (iotc_connection_data_t *)data;

    switch (conn_data->connection_state) {
    case IOTC_CONNECTION_STATE_OPENED:
        printf("connected!\n");

        asprintf(&subscribe_topic_command, SUBSCRIBE_TOPIC_COMMAND, CONFIG_GIOT_DEVICE_ID);
        printf("subscribe to topic: \"%s\"\n", subscribe_topic_command);
        iotc_subscribe(in_context_handle, subscribe_topic_command, IOTC_MQTT_QOS_AT_LEAST_ONCE, &iotc_mqttlogic_subscribe_callback, NULL);

        asprintf(&subscribe_topic_config, SUBSCRIBE_TOPIC_CONFIG, CONFIG_GIOT_DEVICE_ID);
        printf("subscribe to topic: \"%s\"\n", subscribe_topic_config);
        iotc_subscribe(in_context_handle, subscribe_topic_config, IOTC_MQTT_QOS_AT_LEAST_ONCE, &iotc_mqttlogic_subscribe_callback, NULL);

        /* Create a timed task to publish every 10 seconds. */
        delayed_publish_task = iotc_schedule_timed_task(in_context_handle, publish_telemetry_event, 10, 15, NULL);
        break;

    case IOTC_CONNECTION_STATE_OPEN_FAILED:
        printf("ERROR!\tConnection has failed reason %d\n\n", state);

        /* exit it out of the application by stopping the event loop. */
        iotc_events_stop();
        break;

    case IOTC_CONNECTION_STATE_CLOSED:
        free(subscribe_topic_command);
        free(subscribe_topic_config);

        if (IOTC_INVALID_TIMED_TASK_HANDLE != delayed_publish_task) {
            iotc_cancel_timed_task(delayed_publish_task);
            delayed_publish_task = IOTC_INVALID_TIMED_TASK_HANDLE;
        }

        if (state == IOTC_STATE_OK) {
            iotc_events_stop();
        } else {
            printf("connection closed - reason %d!\n", state);
            iotc_connect(in_context_handle, conn_data->username, conn_data->password, conn_data->client_id, conn_data->connection_timeout, conn_data->keepalive_timeout, &on_connection_state_changed);
        }
        break;

    default:
        printf("wrong value\n");
        break;
    }
}

static esp_err_t wifi_event_handler(void *ctx, system_event_t *event) {
    switch (event->event_id) {
    case SYSTEM_EVENT_STA_START:
        esp_wifi_connect();
        break;
    case SYSTEM_EVENT_STA_GOT_IP:
        xEventGroupSetBits(wifi_event_group, CONNECTED_BIT);
        break;
    case SYSTEM_EVENT_STA_DISCONNECTED:
        esp_wifi_connect();
        xEventGroupClearBits(wifi_event_group, CONNECTED_BIT);
        break;
    default:
        break;
    }
    return ESP_OK;
}

static void wifi_init(void) {
    tcpip_adapter_init();
    wifi_event_group = xEventGroupCreate();
    ESP_ERROR_CHECK(esp_event_loop_init(wifi_event_handler, NULL));
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));
    ESP_ERROR_CHECK(esp_wifi_set_storage(WIFI_STORAGE_RAM));
    wifi_config_t wifi_config = {
        .sta = {
            .ssid = CONFIG_ESP_WIFI_SSID,
            .password = CONFIG_ESP_WIFI_PASSWORD,
        },
    };
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(ESP_IF_WIFI_STA, &wifi_config));
    ESP_LOGI(TAG, "start the WIFI SSID:[%s]", CONFIG_ESP_WIFI_SSID);
    ESP_ERROR_CHECK(esp_wifi_start());
    ESP_LOGI(TAG, "Waiting for wifi");
    xEventGroupWaitBits(wifi_event_group, CONNECTED_BIT, false, true, portMAX_DELAY);
}

static void mqtt_task(void *pvParameters) {
    iotc_crypto_key_data_t iotc_connect_private_key_data;
    iotc_connect_private_key_data.crypto_key_signature_algorithm = IOTC_CRYPTO_KEY_SIGNATURE_ALGORITHM_ES256;
    iotc_connect_private_key_data.crypto_key_union_type = IOTC_CRYPTO_KEY_UNION_TYPE_PEM;
    iotc_connect_private_key_data.crypto_key_union.key_pem.key = (char *) ec_pv_key_start;

    /* initialize iotc library and create a context to use to connect to the
    * GCP IoT Core Service. */
    const iotc_state_t error_init = iotc_initialize();

    if (IOTC_STATE_OK != error_init) {
        printf(" iotc failed to initialize, error: %d\n", error_init);
        vTaskDelete(NULL);
    }

    iotc_context = iotc_create_context();
    if (IOTC_INVALID_CONTEXT_HANDLE >= iotc_context) {
        printf(" iotc failed to create context, error: %d\n", -iotc_context);
        vTaskDelete(NULL);
    }

    const uint16_t connection_timeout = 0;
    const uint16_t keepalive_timeout = 20;

    char jwt[IOTC_JWT_SIZE] = {0};
    size_t bytes_written = 0;
    iotc_state_t state = iotc_create_iotcore_jwt(CONFIG_GIOT_PROJECT_ID, 3600, &iotc_connect_private_key_data, jwt, IOTC_JWT_SIZE, &bytes_written);

    if (IOTC_STATE_OK != state) {
        printf("iotc_create_iotcore_jwt returned with error: %ul", state);
        vTaskDelete(NULL);
    }

    char *device_path = NULL;
    asprintf(&device_path, DEVICE_PATH, CONFIG_GIOT_PROJECT_ID, CONFIG_GIOT_LOCATION, CONFIG_GIOT_REGISTRY_ID, CONFIG_GIOT_DEVICE_ID);
    iotc_connect(iotc_context, NULL, jwt, device_path, connection_timeout, keepalive_timeout, &on_connection_state_changed);
    free(device_path);

    iotc_events_process_blocking();

    iotc_delete_context(iotc_context);

    iotc_shutdown();

    vTaskDelete(NULL);
}

void app_main() {
    //Initialize NVS
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);
    ESP_LOGI(TAG, "ESP_WIFI_MODE_STA");
    wifi_init();
    obtain_time();
    xTaskCreate(&mqtt_task, "mqtt_task", 8192, NULL, 5, NULL);
}
