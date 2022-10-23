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

import datetime
import logging
import os

import keras_tuner
import tensorflow as tf
import tensorflow_transform as tft
import tfx.v1 as tfx
from tensorflow_cloud.tuner.tuner import DistributingCloudTuner
from tensorflow_transform import TFTransformOutput
from tfx_bsl.public import tfxio

from tensorflow_metadata.proto.v0 import schema_pb2
from tensorflow_metadata.proto.v0.schema_pb2 import Schema

LABEL_KEY = "Class"


def get_feature_keys(d: dict) -> list[str]:
    keys_to_select = [k for k in d.keys() if k.startswith("V") or k.startswith("Amount")]
    return keys_to_select


def read_using_tfx(file_pattern: list[str],
                   data_accessor: tfx.components.DataAccessor,
                   schema: schema_pb2.Schema,
                   batch_size: int) -> tf.data.Dataset:
    return data_accessor.tf_dataset_factory(
        file_pattern,
        tfxio.TensorFlowDatasetOptions(batch_size=batch_size, label_key=LABEL_KEY),
        schema=schema).repeat()


def build_model(hparams: keras_tuner.HyperParameters, feature_keys: list[str]) -> tf.keras.Model:
    inputs = [tf.keras.layers.Input(shape=(1,), name=f) for f in feature_keys]
    d = tf.keras.layers.concatenate(inputs)
    layer_size = hparams.get("num_neurons")
    d = tf.keras.layers.Dense(layer_size, activation=tf.keras.activations.relu)(d)
    outputs = tf.keras.layers.Dense(1, activation=tf.keras.activations.sigmoid)(d)
    model = tf.keras.Model(inputs=inputs, outputs=outputs)

    model.compile(
        optimizer=tf.keras.optimizers.RMSprop(),
        loss=tf.keras.losses.binary_crossentropy,
        metrics=[tf.keras.metrics.binary_accuracy])

    model.summary(print_fn=logging.info)

    return model


def _get_serve_tf_examples_fn(model, tf_transform_output):
    """Returns a function that parses a serialized tf.Example."""

    # the layer is added as an attribute to the model in order to make sure that
    # the model assets are handled correctly when exporting.
    tft_layer = tf_transform_output.transform_features_layer()

    @tf.function(input_signature=[tf.TensorSpec(shape=[None], dtype=tf.string, name='examples')])
    def serve_tf_examples_fn(serialized_tf_examples):
        """Returns the output to be used in the serving signature."""
        feature_spec = tf_transform_output.raw_feature_spec()
        if LABEL_KEY in feature_spec:
            del feature_spec[LABEL_KEY]

        parsed_features = tf.io.parse_example(serialized_tf_examples, feature_spec)

        transformed_features = tft_layer(parsed_features)

        return model(transformed_features)

    return serve_tf_examples_fn


def _get_hyperparameters() -> keras_tuner.HyperParameters:
    """Returns hyperparameters for building Keras model."""
    hp = keras_tuner.HyperParameters()
    # Defines search space.
    hp.Choice('num_neurons', [128, 256, 512, 1024, 2048], default=256)
    return hp


def run_fn(fn_args: tfx.components.FnArgs):
    tf_transform_output: TFTransformOutput = tft.TFTransformOutput(fn_args.transform_graph_path)
    schema: Schema = tf_transform_output.transformed_metadata.schema
    data_accesor = fn_args.data_accessor
    train_files = fn_args.train_files
    eval_files = fn_args.eval_files

    feature_keys = get_feature_keys(tf_transform_output.transformed_feature_spec())

    if fn_args.hyperparameters:
        hparams = keras_tuner.HyperParameters.from_config(fn_args.hyperparameters)
    else:
        # Default hyperparams if Tuner is not used or imported
        hparams = _get_hyperparameters()

    batch_size = fn_args.custom_config['batch_size']
    dataset_size = fn_args.custom_config['dataset_size']

    steps_per_epoch = (dataset_size * 2 / 3) // batch_size
    validation_steps = (dataset_size * 1 / 3) // batch_size

    train_ds = read_using_tfx(train_files, data_accesor, schema, batch_size)
    eval_ds = read_using_tfx(eval_files, data_accesor, schema, batch_size)

    tensorboard_callback = tf.keras.callbacks.TensorBoard(
        log_dir=os.environ['AIP_TENSORBOARD_LOG_DIR'],
        histogram_freq=1)

    early_stop_cb = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=3)

    model: tf.keras.Model = build_model(hparams=hparams, feature_keys=feature_keys)
    model.fit(
        data=train_ds,
        steps_per_epoch=steps_per_epoch,
        validation_data=eval_ds,
        validation_steps=validation_steps,
        callbacks=[tensorboard_callback, early_stop_cb])

    signatures = {
        'serving_default': _get_serve_tf_examples_fn(model, tf_transform_output)}

    model.save(fn_args.serving_model_dir, signatures=signatures)


def tuner_fn(fn_args: tfx.components.FnArgs) -> tfx.components.TunerFnResult:
    tuning_config = fn_args.custom_config[tfx.extensions.google_cloud_ai_platform.experimental.TUNING_ARGS_KEY]
    project_id = tuning_config['project']
    region = tuning_config['region']

    tf_transform_output: TFTransformOutput = tft.TFTransformOutput(fn_args.transform_graph_path)
    feature_keys = get_feature_keys(tf_transform_output.transformed_feature_spec())

    data_accesor = fn_args.data_accessor
    schema: Schema = tf_transform_output.transformed_metadata.schema

    train_files = fn_args.train_files
    eval_files = fn_args.eval_files
    batch_size = fn_args.custom_config['batch_size']
    dataset_size = fn_args.custom_config['dataset_size']

    steps_per_epoch = (dataset_size * 2 / 3) // batch_size
    validation_steps = (dataset_size * 1 / 3) // batch_size

    train_ds = read_using_tfx(train_files, data_accesor, schema, batch_size)
    eval_ds = read_using_tfx(eval_files, data_accesor, schema, batch_size)

    hparams = _get_hyperparameters()

    study_id = 'DistributingCloudTuner_study_{}'.format(
        datetime.datetime.now().strftime('%Y%m%d%H'))

    def hypermodel(hparams: keras_tuner.HyperParameters):
        return build_model(hparams=hparams, feature_keys=feature_keys)

    tuner: DistributingCloudTuner = DistributingCloudTuner(
        hypermodel=hypermodel,
        project_id=project_id,
        region=region,
        hyperparameters=hparams,
        objective=keras_tuner.Objective('val_binary_accuracy', 'max'),
        directory=os.path.join(tuning_config['remote_trials_working_dir'], study_id),
        study_id=study_id,
        max_trials=50,
        replica_count=5)

    early_stop_cb = tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=3)

    result = tfx.components.TunerFnResult(
        tuner=tuner,
        fit_kwargs={
            'data': train_ds,
            'steps_per_epoch': steps_per_epoch,
            'validation_data': eval_ds,
            'validation_steps': validation_steps,
            'callbacks': [early_stop_cb]
        }
    )

    return result