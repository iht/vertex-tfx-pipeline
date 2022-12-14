#  Copyright 2022 Google LLC
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

import tfx.v1 as tfx

from my_vertex_pipelines import fraud_detection_pipeline
from my_vertex_pipelines import vertex_configs
from my_vertex_pipelines import vertex_run


def main(running_locally: bool,
         enable_cloud_tuner: bool,
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
         tensorboard: str,
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
        beam_args = vertex_configs.get_beam_args_for_dataflow(project=project_id,
                                                              region=region,
                                                              temp_location_gcs=temp_location,
                                                              service_account_dataflow=service_account_dataflow,
                                                              dataflow_network=dataflow_network)

    pipeline: tfx.dsl.Pipeline = fraud_detection_pipeline.create_pipeline(
        pipeline_name=pipeline_name,
        pipeline_root=pipeline_root,
        query=query,
        beam_pipeline_args=beam_args,
        transform_fn_file=transform_fn_file,
        region=region,
        trainer_fn_file=trainer_fn_file,
        project_id=project_id,
        tensorboard=tensorboard,
        service_account=service_account_dataflow,
        temp_location=temp_location,
        local_connection_config=metadata_connection,
        enable_cloud_tuner=enable_cloud_tuner)

    runner.run(pipeline)  # Creates pipeline definition

    logging.getLogger().setLevel(logging.INFO)

    if running_locally:
        vertex_run.run_locally(pipeline)
    else:
        vertex_run.run_in_vertex(project_id=project_id,
                                 region=region,
                                 pipeline_definition=pipeline_definition,
                                 pipeline_name=pipeline_name,
                                 service_account=service_account,
                                 tensorboard_instance=tensorboard)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("--run-locally", action="store_true", default=False)
    parser.add_argument("--enable-cloud-tuner", action="store_true", default=False)
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--region", required=True)
    parser.add_argument("--temp-location", required=True)
    parser.add_argument("--service-account", required=True)
    parser.add_argument("--service-account-dataflow", required=True)
    parser.add_argument("--dataflow-network", required=True)
    parser.add_argument("--pipeline-root", required=True)
    parser.add_argument("--pipeline-name", required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--transform-fn-path", required=True)
    parser.add_argument("--trainer-fn-path", required=True)
    parser.add_argument("--tensorboard", required=True)

    args = parser.parse_args()

    project = args.project_id
    temp_location_gcs = args.temp_location
    region = args.region

    main(running_locally=args.run_locally,
         enable_cloud_tuner=args.enable_cloud_tuner,
         pipeline_name=args.pipeline_name,
         pipeline_root=args.pipeline_root,
         query=args.query,
         project_id=project,
         region=region,
         service_account=args.service_account,
         service_account_dataflow=args.service_account_dataflow,
         dataflow_network=args.dataflow_network,
         transform_fn_file=args.transform_fn_path,
         trainer_fn_file=args.trainer_fn_path,
         tensorboard=args.tensorboard,
         temp_location=temp_location_gcs)
