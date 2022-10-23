#
# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

PROJECT=ihr-vertex-pipelines
REGION=europe-west4
QUERY="SELECT * FROM data_playground.transactions"

PIPELINE_ROOT=gs://ihr-live-workshop/pipeline_local
PIPELINE_NAME=fraud-detect-pipeline
TRANSFORM_FN=./fraud-detection-pipelines/feature_engineering_fn.py
TRAINER_FN=./fraud-detection-pipelines/trainer_fn.py

TEMP_LOCATION=gs://ihr-live-workshop/tmp/

SERVICE_ACCOUNT=ml-in-prod-vertex-sa@ihr-vertex-pipelines.iam.gserviceaccount.com
SERVICE_ACCOUNT_DATAFLOW=ml-in-prod-dataflow-sa@ihr-vertex-pipelines.iam.gserviceaccount.com
SUBNETWORK=regions/$REGION/subnetworks/default

TENSORBOARD=projects/237148598933/locations/europe-west4/tensorboards/5315267907087761408

cd fraud-detection-pipelines || exit

VERSION=$(python setup.py --version)
LOCAL_PACKAGE=dist/fraud-detection-pipelines-$VERSION.tar.gz

python setup.py sdist

pip install $LOCAL_PACKAGE

python -m my_vertex_pipelines.fraud_detection_main --project-id=$PROJECT \
  --region=$REGION \
  --query="$QUERY" \
  --pipeline-roo=$PIPELINE_ROOT \
  --pipeline-name=$PIPELINE_NAME \
  --transform-fn-path=$TRANSFORM_FN \
  --trainer-fn-path=$TRAINER_FN \
  --service-account=$SERVICE_ACCOUNT \
  --service-account-dataflow=$SERVICE_ACCOUNT_DATAFLOW \
  --dataflow-network=$SUBNETWORK \
  --tensorboard=$TENSORBOARD \
  --temp-location=$TEMP_LOCATION \
  --run-locally