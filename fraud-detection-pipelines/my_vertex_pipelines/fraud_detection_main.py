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

import argparse
import logging

from datetime import datetime

import tfx.v1 as tfx

from my_vertex_pipelines import fraud_detection_pipeline
from my_vertex_pipelines import vertex_configs
from my_vertex_pipelines import vertex_run


def main(running_locally: bool,
         use_dataflow: bool,
         pipeline_name: str,
         pipeline_root: str,
         query: str,
         project_id: str,
         region: str,
         service_account: str,
         service_account_dataflow: str,
         dataflow_network: str,
         transform_fn_file: str,
         trainer_fn_file: str,
         temp_location: str):
    pipeline_definition = pipeline_name + "_pipeline.json"
    runner = tfx.orchestration.experimental.KubeflowV2DagRunner(
        config=tfx.orchestration.experimental.KubeflowV2DagRunnerConfig(),
        output_filename=pipeline_definition)

    if running_locally:
        metadata_connection = tfx.orchestration.metadata.sqlite_metadata_connection_config(vertex_configs.METADATA_PATH)
        beam_args = vertex_configs.get_beam_args_for_local(project=project_id,
                                                           region=region,
                                                           temp_location_gcs=temp_location)
    else:
        metadata_connection = None
        if use_dataflow:
            beam_args = vertex_configs.get_beam_args_for_dataflow(project=project_id,
                                                                  region=region,
                                                                  temp_location_gcs=temp_location,
                                                                  service_account_dataflow=service_account_dataflow,
                                                                  dataflow_network=dataflow_network)
        else:
            beam_args = vertex_configs.get_beam_args_for_local(project=project_id,
                                                               region=region,
                                                               temp_location_gcs=temp_location)

    # Use a custom job id to register params and metrics in the same experiment run id
    this_moment: str = datetime.now().strftime("%Y%m%d%H%M%S")
    job_id = f"{pipeline_name}-{this_moment}"
    experiment_name = f"{pipeline_name}-experiment"

    pipeline: tfx.dsl.Pipeline = fraud_detection_pipeline.create_pipeline(
        pipeline_name=pipeline_name,
        experiment_name=experiment_name,
        experiment_run_name=job_id,
        pipeline_root=pipeline_root,
        query=query,
        beam_pipeline_args=beam_args,
        transform_fn_file=transform_fn_file,
        region=region,
        trainer_fn_file=trainer_fn_file,
        project_id=project_id,
        service_account=service_account,
        local_connection_config=metadata_connection)

    runner.run(pipeline)  # Creates pipeline definition

    logging.getLogger().setLevel(logging.INFO)

    if running_locally:
        vertex_run.run_locally(pipeline)
    else:
        vertex_run.run_in_vertex(project_id=project_id,
                                 region=region,
                                 pipeline_definition=pipeline_definition,
                                 pipeline_name=pipeline_name,
                                 experiment_name=experiment_name,
                                 job_id=job_id,
                                 service_account=service_account)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("--run-locally", action="store_true", default=False)
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--region", required=True)
    parser.add_argument("--temp-location", required=True)

    parser.add_argument("--service-account", required=False, help="Mandatory if running in Vertex")

    parser.add_argument("--use-dataflow", required=False, action="store_true", default=False)
    parser.add_argument("--service-account-dataflow", required=False,
                        help="Mandatory if running in Vertex with Dataflow enabled")
    parser.add_argument("--dataflow-network", required=False,
                        help="Mandatory if running in Vertex with Dataflow enabled")

    parser.add_argument("--pipeline-root", required=True)
    parser.add_argument("--pipeline-name", required=True)

    parser.add_argument("--query", required=True)

    parser.add_argument("--transform-fn-path", required=True)
    parser.add_argument("--trainer-fn-path", required=True)

    args = parser.parse_args()

    main(running_locally=args.run_locally,
         use_dataflow=args.use_dataflow,
         pipeline_name=args.pipeline_name,
         pipeline_root=args.pipeline_root,
         query=args.query,
         project_id=args.project_id,
         region=args.region,
         service_account=args.service_account,
         service_account_dataflow=args.service_account_dataflow,
         dataflow_network=args.dataflow_network,
         transform_fn_file=args.transform_fn_path,
         trainer_fn_file=args.trainer_fn_path,
         temp_location=args.temp_location)
