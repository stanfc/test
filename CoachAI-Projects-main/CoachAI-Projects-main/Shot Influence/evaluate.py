import time
import numpy as np
import pandas as pd
import tensorflow as tf
import rally_classifier as rc
import train
import util
from sklearn.metrics import brier_score_loss


timestr = time.strftime("%Y%m%d-%H%M%S")
dataset = pd.read_csv('new_data/dataset.csv')

test_mask = (dataset['match_id'] == 30) | (dataset['match_id'] == 34)
val_ratio = 0.3
encode_columns = []
shot_predictors = ['is_target_turn', 'aroundhead', 'backhand', 'time_proportion']
rally_predictors = ['roundscore_diff', 'continuous_score']
target = 'is_target_win'

seq_len = dataset.groupby('rally_id').size().max()
seq_len += 1 if seq_len % 2 == 1 else 2

encoded = pd.get_dummies(dataset, columns=encode_columns)
codes_type, uniques_type = pd.factorize(encoded['type'])
encoded['type'] = codes_type + 1  # Reserve code 0 for paddings

shot_predictors = [c for c in encoded.columns if any(c.startswith(f'{p}_')for p in shot_predictors) or c in shot_predictors]
train_data, val_data, test_data = train.split_data(encoded, val_ratio=val_ratio, test_mask=test_mask)

(train_shots, train_shot_types), (train_rallies, train_target, train_rally_id) = train.prepare_data(train_data, [shot_predictors, ['hit_area', 'player_location_area', 'opponent_location_area', 'type']], [rally_predictors, target, 'rally_id'], pad_to=seq_len)

(test_shots, test_shot_types), (test_rallies, test_target, test_rally_id) = train.prepare_data(test_data, [shot_predictors, ['hit_area', 'player_location_area', 'opponent_location_area', 'type']], [rally_predictors, target, 'rally_id'], pad_to=seq_len)
seq_len = train_shots.shape[1]

train_hit_area_encoded = train_shot_types[:, :, 0].copy()
train_player_area_encoded = train_shot_types[:, :, 1].copy()
train_opponent_area_encoded = train_shot_types[:, :, 2].copy()
train_shot_types = train_shot_types[:, :, 3].copy()
train_time_proportion = train_shots[:, :, 2].copy()             # time proportion
train_shots = np.delete(train_shots, 2, axis=2)

test_hit_area_encoded = test_shot_types[:, :, 0].copy()
test_player_area_encoded = test_shot_types[:, :, 1].copy()
test_opponent_area_encoded = test_shot_types[:, :, 2].copy()
test_shot_types = test_shot_types[:, :, 3].copy()
test_time_proportion = test_shots[:, :, 2].copy()             # time proportion
test_shots = np.delete(test_shots, 2, axis=2)

shot_predictors.remove('time_proportion')


regularizer = tf.keras.regularizers.l2(0.01)
optimizer = 'adam'
loss = 'binary_crossentropy'
metrics = ['AUC', 'binary_accuracy']
epochs = 100

callbacks = tf.keras.callbacks.EarlyStopping(min_delta=0.002, patience=15, restore_best_weights=True)
tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir='./history/', histogram_freq=1)

n_shot_types = len(uniques_type) + 1
n_area_types = encoded['player_location_area'].nunique() + 1
cnn_kwargs = {'filters': 32, 'kernel_size': 3, 'kernel_regularizer': regularizer,
              'activation': 'relu'}
rnn_kwargs = {'units': 32, 'kernel_regularizer': regularizer}
dense_kwargs = {'kernel_regularizer': regularizer}

batch_size = 32
MODEL_NAME = 'SPECIFY_NAME'


# Avoid tensorflow use full memory
physical_devices = tf.config.experimental.list_physical_devices('GPU')
try:
    tf.config.experimental.set_memory_growth(physical_devices[0], True)
except:
    # Invalid device or cannot modify virtual devices once initialized.
    pass

prediction_model, attention_model = rc.bad_net((seq_len, len(shot_predictors)),
                                               embed_types_size=n_shot_types,
                                               embed_area_size=n_area_types,
                                               rally_info_shape=len(rally_predictors),
                                               cnn_kwargs=cnn_kwargs,
                                               rnn_kwargs=rnn_kwargs,
                                               dense_kwargs=dense_kwargs)
prediction_model.load_weight(MODEL_NAME)


train_x = [train_hit_area_encoded, train_player_area_encoded, train_opponent_area_encoded, train_shots, train_shot_types, train_time_proportion, train_rallies]
test_x = [test_hit_area_encoded, test_player_area_encoded, test_opponent_area_encoded, test_shots, test_shot_types, test_time_proportion, test_rallies]

test_results = prediction_model.evaluate(test_x, test_target)
y_pred = prediction_model.predict(test_x)
br_score = brier_score_loss(test_target, y_pred)

# write test AUC and accuracy into csv
log_file = './record/' + MODEL_NAME + '.csv'
auc = str(test_results[1])
acc = str(test_results[2])
with open(log_file, 'a') as log:
    log.write(timestr + ', ' + auc + ', ' + acc + '\n')