
# Smart Outlet Example

----------------------

## Google IoT Core Setup


Follow this [getting-started-guide ](https://cloud.google.com/iot/docs/how-tos/getting-started) to do
the initial Google Cloud IoT Core setup.

### Create Public/Private Key pair

As of now, only Elliptic curve algorithm is supported for device authentication.
Navigate to `Generating an ES256 key` sub section in this [guide](https://cloud.google.com/iot/docs/how-tos/credentials/keys#generating_an_es256_key) to generate key pair.

### Create Registry and Devices

Step-by-step guide for creating Cloud IoT Core registry and devices is given [here](https://cloud.google.com/iot/docs/how-tos/devices). While creating a device, use the public key from the key pair generated in the previous step.

*NOTE: location of the registry, registry ID and device ID will be used for ESP32 configuration later on*

## Getting started with ESP32

### Setting up ESP-IDF

ESP-IDF is the official development framework for the ESP32 chip.

- Please refer [this](https://docs.espressif.com/projects/esp-idf/en/latest/get-started/index.html) for setting ESP-IDF

### Connecting ESP32 to a local network

Code snippet to connect ESP32 to a WiFi station:

```c

static esp_err_t wifi_event_handler(void *ctx, system_event_t *event)
{
    switch (event->event_id)
    {
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

static void wifi_init(void)
{
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

```

### Connecting ESP32 to Cloud IoT Core

After wifi connection is established, invoke `iotc_connect()` API in the application which initiates a connection to Cloud IoT Core.

#### Connect Callback

While making a connection request, your client application must provide a callback function, which is invoked when a connection to the Cloud IoT Core service has been established, as well as if the connection was unsuccessful.

```c
// Connection callback function signature
void on_connection_state_changed( iotc_context_handle_t in_context_handle,
                                  void* data,
                                  iotc_state_t state )
```

### Publishing data

Once a connection has been established, the client application can publish messages to the Cloud IoT Core service.

To publish a message to a topic, use either `iotc_publish()` or `iotc_publish_data()`. Each message must include the following:

- The topic name
- A message payload
- A QoS level

#### Publish callback

While invoking publish API, the client application can also supply a callback function. This callback function is optional; it is intended to notify embedded devices after the message has been fully sent/acknowledged. This callback is invoked when the client application successfully publishes to Cloud IoT Core.

```c
// Publish callback function signature

void on_publication( iotc_context_handle_t in_context_handle,
                     void* data,
                     iotc_state_t state )

```

### Subscribing to MQTT topics

To subscribe to a topic, call `iotc_subscribe()`. Subscription must include:

- The topic name
- A subscription callback function
- A QoS level.

#### Subscribe callback

The subscription callback is invoked when Cloud IoT Core sends a MQTT SUBACK response with the granted QoS level of the subscription request. This function is also invoked each time Cloud IoT Core delivers a message to the subscribed topic.

```c
// Subscribe callback function signature

void on_message( iotc_context_handle_t in_context_handle,
                 iotc_sub_call_type_t call_type,
                 const iotc_sub_call_params_t* const params,
                 iotc_state_t state,
                 void* user_data )

```

## Example Setup  

### Installing Private Key

Copy the private key created in the earlier step to `main/certs/private_key.pem` subdirectory.

*NOTE: Don't accidentally commit private key to public source*

### ESP32 Configuration

#### Wifi Setting

In the `smart-outlet` example directory, run `make menuconfig` and navigate to `Example Configuration` to set `WiFi SSID` and `WiFI Password`

#### Google IoT Core Device Setting

Set Project ID, Location, Registry ID and Device ID under `make menuconfig` -> `Component config` -> `Google IoT Core Configuration`

`project_id` of your project can be fetched from [resources page](https://console.cloud.google.com/cloud-resource-manager)

Fetch `location`, `registry_id` and `device_id` from the Google IoT Core registry.

### Flashing client application

```
    make -j8 flash monitor
```

## Example Workflow

After flashing the example to your ESP32, it should connect to Google IoT Core and start subscribing/publishing MQTT data.

### Telemetry Event

This example publishes temperature data every 10 seconds to the topic `/devices/{device-id}/events`

### Sending Device Configuration from Google IoT Core

To know more about configuring devices from Google IoT Core visit [here](https://cloud.google.com/iot/docs/how-tos/config/configuring-devices)

A subscription to the topic `/devices/{device-id}/config` is established on start-up, thus you receive configuration details in the registered subscribe callback `iotc_mqttlogic_subscribe_callback`

### Sending Device Command

A subscription to the wildcard topic `/devices/{device-id}/commands/#` is established in this example, you can send commands to the device by following instruction given [here](https://cloud.google.com/iot/docs/how-tos/commands).

- Set Output GPIO under `make menuconfig` -> `Example Configuration` -> `Output GPIO`
- Send `{"outlet": 0}` or `{"outlet": 1}` from Google Cloud IoT Core Device Console to change GPIO output.
