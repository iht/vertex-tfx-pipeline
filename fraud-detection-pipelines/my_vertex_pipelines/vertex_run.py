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

import tfx.v1 as tfx

from google.cloud import aiplatform
from google.cloud.aiplatform import Experiment


def run_in_vertex(project_id: str,
                  region: str,
                  pipeline_definition: str,
                  pipeline_name: str,
                  experiment_name: str,
                  job_id: str,
                  service_account: str):

    aiplatform.init(project=project_id, location=region, experiment=experiment_name)

    job = aiplatform.PipelineJob(template_path=pipeline_definition,
                                 display_name=pipeline_name,
                                 enable_caching=True,
                                 job_id=job_id)

    job.submit(service_account=service_account, experiment=experiment_name)


def run_locally(pipeline: tfx.dsl.Pipeline):
    tfx.orchestration.LocalDagRunner().run(pipeline)
