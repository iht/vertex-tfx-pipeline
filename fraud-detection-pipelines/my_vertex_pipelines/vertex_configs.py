#  Copyright 2023 Google LLC
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
from typing import Dict, List

import tfx.v1 as tfx

BATCH_SIZE = 4096
DATASET_SIZE = 284807

METADATA_PATH = '/tmp/tfx_metadata.db'
SERVING_MODEL_DIR = '/tmp/tfx_model/'


def get_beam_args_for_dataflow(project: str,
                               temp_location_gcs: str,
                               region: str,
                               service_account_dataflow: str,
                               dataflow_network: str):
    beam_args = [f"--project={project}",
                 f"--temp_location={temp_location_gcs}",
                 f"--region={region}",
                 "--runner=DataflowRunner",
                 f"--service_account_email={service_account_dataflow}",
                 f"--no_use_public_ips",
                 f"--subnetwork={dataflow_network}"]

    return beam_args


def get_beam_args_for_local(project: str, temp_location_gcs: str, region: str) -> List[str]:
    beam_args = [f"--project={project}",
                 f"--temp_location={temp_location_gcs}",
                 f"--region={region}",
                 "--runner=DirectRunner"]

    return beam_args


def get_vertex_tuner_config(project_id: str, region: str, service_account: str) -> Dict[str, str]:
    vertex_tuner_config = {'project': project_id,
                           'region': region,
                           'service_account': service_account}
    return vertex_tuner_config


def get_vertex_training_config(project_id: str,
                               service_account: str) -> Dict[str, str]:
    vertex_job_spec = {
        'project': project_id,
        'service_account': service_account,
        'worker_pool_specs': [{'machine_spec': {'machine_type': 'e2-standard-4'},
                               'replica_count': 1,
                               'container_spec': {'image_uri': 'gcr.io/tfx-oss-public/tfx:{}'.format(tfx.__version__)}
                               }]
    }

    return vertex_job_spec


def get_vertex_endpoint_config(project_id: str, endpoint_name: str) -> Dict[str, str]:
    vertex_serving_spec = {
        'project_id': project_id,
        'endpoint_name': endpoint_name,
        # Remaining argument is passed to aiplatform.Model.deploy()
        # See https://cloud.google.com/vertex-ai/docs/predictions/deploy-model-api#deploy_the_model
        # for the detail.
        #
        # Machine type is the compute resource to serve prediction requests.
        # See https://cloud.google.com/vertex-ai/docs/predictions/configure-compute#machine-types
        # for available machine types and acccerators.
        'machine_type': 'e2-standard-4',
    }

    return vertex_serving_spec
