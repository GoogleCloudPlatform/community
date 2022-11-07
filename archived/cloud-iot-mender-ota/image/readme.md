# Build a Mender Yocto project OS image for the Raspberry Pi3 device

These steps outline how to build a Yocto Project image for the Raspberry Pi3 device. 

The [Yocto Project](https://www.yoctoproject.org/) is an open source collaboration project that helps developers create custom Linux-based systems for embedded products, regardless of the hardware architecture. 

The build output includes a file that can be flashed to the device storage during initial provisioning; it has suffix `.sdimg`. Additionally copies of the same image with `.img` and `.bmap` suffix are uploaded to Cloud Storage bucket.

Yocto image builds generally take a while to complete. Generally instances with high CPU cores and memory along with faster disks such as SSD will help speed up the overall build process. Additionally, there are pre-built images for quick testing available in the Cloud Storage bucket which you can download and proceed directly to "Working with pre-built Mender Yocto Images" section

Below are the instructions to build a custom Mender Yocto image for the Raspberry Pi3 device. This image will have a number of requirements needed to communicate with Cloud IoT Core built in.

Use the *"cloud api shell" environment you used earlier.*

## Create a Compute Engine instance for Mender Yocto Project OS builds

```
gcloud beta compute instances create "mender-ota-build" --project $PROJECT --zone "us-central1-c" --machine-type "n1-standard-16" --subnet "default" --maintenance-policy "MIGRATE" --scopes "https://www.googleapis.com/auth/cloud-platform" --min-cpu-platform "Automatic" --tags "https-server" --image "ubuntu-1604-xenial-v20180405" --image-project "ubuntu-os-cloud" --boot-disk-size "150" --boot-disk-type=pd-ssd --boot-disk-device-name "mender-ota-build"
```


## SSH into the image and install the necessary updates required for the Yocto project builds

```
gcloud compute --project $PROJECT ssh --zone "us-central1-c" "mender-ota-build"
```


## Install the Mender Yocto custom image build including dependencies by downloading script from the below github repo and executing on the build server 

This step initially builds a custom image for the Raspberry Pi device as well as Mender artifact update which can be used to test the OTA feature of Mender. All images after the completion of the build are automatically uploaded into Cloud Storage bucket.

Note that you are now switching to the "build server shell" environment, and not in the "cloud api shell" environment.

```
export GCP_IOT_MENDER_DEMO_HOST_IP_ADDRESS=$(gcloud compute instances describe mender-ota-demo --format="value(networkInterfaces.accessConfigs[0].natIP)")
```

```
wget https://raw.githubusercontent.com/GoogleCloudPlatform/community/master/tutorials/cloud-iot-mender-ota/image/mender-gcp-build.sh
```

```
chmod +x ./mender-gcp-build.sh
```

```
. ./mender-gcp-build.sh
```

**Note:** *The build process will generally take anywhere from **45 minutes to 60 minutes** and will create custom embedded Linux image with all the necessary packages and dependencies to be able to connect to Cloud IoT Core. The output of the build will be (2) files which will be uploaded into Cloud Storage Bucket.*

1. *`gcp-mender-demo-image-raspberrypi3.sdimg` - This will be the core image file which will be used by the client to connect to GCP IoT core and Mender Server. Copies of the same image file with `.bmap` and `.img` are also generated and uploaded to Cloud Storage bucket.*

2. *`gcp-mender-demo-image-raspberrypi3.mender` - This will be the Mender artifact file which you will upload to the mender server and deploy on the client as part of the OTA update process.*

4. This completes the build process, the next step is to provision the build to a [new device](https://docs.mender.io/artifacts/provisioning-a-new-device) (Raspberry Pi3). The build image was copied automatically to the Cloud Storage bucket which was created earlier. 

You can now download the newly built image or artifact to your local PC where you can write the image to an SD card or upload the artifact as outlined in the main tutorial.

