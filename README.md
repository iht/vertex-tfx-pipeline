# TFX pipelines with Vertex AI

## Setup

This project can be run from the Cloud Shell of your Google Cloud project.

You will need a Google Cloud project with owner permissions, and you also need 
to have the [Google Cloud SDK configured to use that project](https://cloud.google.com/sdk/docs/install-sdk).
For instance, you could use the [Cloud Shell in your Google Cloud project](https://cloud.google.com/shell/docs), 
which is configured by default with the Google Cloud SDK.

### Setup Google Cloud project

This repository contains some Terraform code in the `terraform` directory to setup 
Vertex AI and all the required APIs and permissions in the Google Cloud project.

Please check the README.md in the [terraform/](terraform/) directory for more details. 
You only need to run the Terraform code once.

## Running the pipeline

### Python version

Please don't use Python < 3.7 (e.g. 3.6) or Python > 3.9 (e.g. 3.10), they will 
not work with TFX. For more details, please check:

* https://www.tensorflow.org/tfx
* https://github.com/tensorflow/tfx

At the moment of writing this, the Cloud Shell has Python 3.9. You can check your 
Python version by running the following command:

```shell
python --version
```

Once you have made sure you have the correct Python version, create a virtualenv: 

```shell
python -m venv tfxenv
```

Activate it:

```shell
source ./tfxenv/bin/activate
```

And install the dependencies in the file `requirements.txt`, by running:

```shell
pip install -r requirements.txt
```

### Run the pipeline

Edit the scripts in the directory `scripts` to point to your project id and region 
of choice.

The `playground` branch of this repository contains incomplete code that you need to
finish, as an exercise to learn the ropes of TFX pipelines.

To run the pipeline in Google Cloud, you need to run the provided scripts from the 
top level directory of the repository:

```shell
./scripts/launch_google_cloud.sh
```