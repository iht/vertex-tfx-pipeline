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

from typing import Optional, List

import tfx.v1 as tfx
from tfx.components import StatisticsGen, SchemaGen, Transform, ExampleValidator, Trainer, Evaluator, Pusher
from tfx.extensions.google_cloud_big_query.example_gen.component import BigQueryExampleGen

import tensorflow_model_analysis as tfma

from my_vertex_pipelines import vertex_configs


def create_pipeline(pipeline_name: str,
                    experiment_name: str,
                    experiment_run_name: str,
                    pipeline_root: str,
                    query: str,
                    transform_fn_file: str,
                    trainer_fn_file: str,
                    beam_pipeline_args: Optional[List[str]],
                    region: str,
                    project_id: str,
                    service_account: str,
                    local_connection_config: Optional[str]) -> tfx.dsl.Pipeline:
    ## -----
    ## Input
    ## -----
    # Get data from BigQuery
    example_gen: BigQueryExampleGen = None  # TODO: read from BigQuery using the query

    ## ---------------
    ## Data validation
    ## ---------------
    # Computes statistics over data for visualization and example validation.
    statistics_gen: StatisticsGen = None  # TODO

    # Schema inferred from stats
    schema_gen: SchemaGen = None  # TODO (use schema inference for simplicity, rather than writing the schema)

    # Q: What if we don't want to infer the schema but check if the data complies with a certain schema?
    # A: We can use the ImportSchemaGen component, from a schema specified in some location (e.g. GCS)
    # schema_gen = tfx.components.ImportSchemaGen(
    #     schema_file='/some/path/schema.pbtxt')

    # Performs anomaly detection based on statistics and data schema.
    # The output contains anomalies info (data drift, skew training-test)
    example_validator: ExampleValidator = None  # TODO

    # See https://www.tensorflow.org/tfx/data_validation/get_started
    # Q: What are the thresholds used to decide if an anomaly should stop the pipeline?
    # A: Those are encoded in the schema, see an example at https://www.tensorflow.org/tfx/tutorials/tfx/penguin_tfdv
    # See all the annotations/thresholds you can set at:
    # https://github.com/tensorflow/metadata/blob/master/tensorflow_metadata/proto/v0/schema.proto

    # These are the types of anomalies that are detected:
    # https://github.com/tensorflow/metadata/blob/master/tensorflow_metadata/proto/v0/anomalies.proto

    ## -------------------
    ## Feature engineering
    ## -------------------
    transform: Transform = None  # TODO. See feature_engineering_fn.py

    ## --------
    ## Training
    ## --------
    if local_connection_config:
        custom_config = {
            'batch_size': vertex_configs.BATCH_SIZE,
            'dataset_size': vertex_configs.DATASET_SIZE
        }

        trainer: Trainer = None  # TODO: Use tfx.components.Trainer
    else:  # We are training in Vertex
        vertex_job_spec = vertex_configs.get_vertex_training_config(project_id=project_id,
                                                                    service_account=service_account)

        custom_config = {
            tfx.extensions.google_cloud_ai_platform.ENABLE_VERTEX_KEY:
                True,
            tfx.extensions.google_cloud_ai_platform.VERTEX_REGION_KEY:
                region,
            tfx.extensions.google_cloud_ai_platform.TRAINING_ARGS_KEY:
                vertex_job_spec,
            'batch_size': vertex_configs.BATCH_SIZE,
            'dataset_size': vertex_configs.DATASET_SIZE,
            'experiment_name': experiment_name,
            'experiment_run_name': experiment_run_name,
            'project_id': project_id,
            'location': region
        }

        trainer: Trainer = None  # TODO. Use tfx.extensions.google_cloud_ai_platform.Trainer
    ## ---------------------------------
    ## Evaluate model (against baseline)
    ## ---------------------------------
    model_resolver = tfx.dsl.Resolver(
        strategy_class=tfx.dsl.experimental.LatestBlessedModelStrategy,
        model=tfx.dsl.Channel(type=tfx.types.standard_artifacts.Model),
        model_blessing=tfx.dsl.Channel(
            type=tfx.types.standard_artifacts.ModelBlessing)).with_id(
        'latest_blessed_model_resolver')

    # Metrics to be checked
    eval_config = tfma.EvalConfig(
        model_specs=[tfma.ModelSpec(label_key='Class')],
        slicing_specs=[tfma.SlicingSpec()],
        metrics_specs=[
            tfma.MetricsSpec(per_slice_thresholds={
                'binary_accuracy':
                    tfma.PerSliceMetricThresholds(thresholds=[
                        tfma.PerSliceMetricThreshold(
                            slicing_specs=[tfma.SlicingSpec()],
                            threshold=tfma.MetricThreshold(
                                value_threshold=tfma.GenericValueThreshold(
                                    lower_bound={'value': 0.6}))
                        )]),
            })])

    evaluator: Evaluator = tfx.components.Evaluator(
        examples=transform.outputs['transformed_examples'],
        model=trainer.outputs['model'],
        baseline_model=model_resolver.outputs['model'],
        eval_config=eval_config)

    ## --------------------------------------------------------------------------
    ## Push to endpoint (and publish in model registry if this is the first time)
    ## --------------------------------------------------------------------------
    if local_connection_config:
        push_destination = tfx.proto.PushDestination(
            filesystem=tfx.proto.PushDestination.Filesystem(
                base_directory=vertex_configs.SERVING_MODEL_DIR))

        pusher: Pusher = None  # TODO. Use tfx.components.Pusher
    else:
        serving_image = 'europe-docker.pkg.dev/vertex-ai/prediction/tf2-cpu.2-9:latest'

        vertex_serving_spec = vertex_configs.get_vertex_endpoint_config(
            project_id,
            endpoint_name="fraud-detection")

        custom_config = {
            tfx.extensions.google_cloud_ai_platform.ENABLE_VERTEX_KEY:
                True,
            tfx.extensions.google_cloud_ai_platform.VERTEX_REGION_KEY:
                region,
            tfx.extensions.google_cloud_ai_platform.VERTEX_CONTAINER_IMAGE_URI_KEY:
                serving_image,
            tfx.extensions.google_cloud_ai_platform.SERVING_ARGS_KEY:
                vertex_serving_spec,
        }

        pusher: Pusher = None  # TODO. Use tfx.extensions.google_cloud_ai_platform.Pusher

    components = [example_gen,
                  statistics_gen,
                  schema_gen,
                  example_validator,
                  transform,
                  trainer,
                  pusher,
                  model_resolver,
                  evaluator]

    pipeline = tfx.dsl.Pipeline(pipeline_name=pipeline_name,
                                pipeline_root=pipeline_root,
                                components=components,
                                beam_pipeline_args=beam_pipeline_args,
                                metadata_connection_config=local_connection_config,
                                enable_cache=True)

    return pipeline
