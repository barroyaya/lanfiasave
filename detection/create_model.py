import os
import joblib
import numpy as np
import pandas as pd
import tensorflow as tf
from keras.src.callbacks import EarlyStopping

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.utils.class_weight import compute_class_weight
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

import matplotlib.pyplot as plt

from detection.prepare_data import load_and_concatenate, preprocess

def build_model(input_dim: int, n_classes: int) -> tf.keras.Model:
    model = tf.keras.Sequential([
        tf.keras.layers.InputLayer(shape=(input_dim,)),
        tf.keras.layers.Dense(256, activation='relu'),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(n_classes, activation='softmax'),
    ])
    optimizer = tf.keras.optimizers.Adam(learning_rate=0.001)
    model.compile(optimizer=optimizer, loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    return model

def main():
    df = load_and_concatenate()
    X_train, X_test, y_train, y_test = preprocess(df)

    num_feats = [
        'age', 'revenu', 'enfants_non_scolarises',
        'nombre_personnes_menage', 'montant_total_recu'
    ]
    cat_feats = [c for c in X_train.columns if c not in num_feats]

    numeric_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler',  StandardScaler()),
    ])

    preprocessor = ColumnTransformer([
        ('num', numeric_pipeline, num_feats),
        ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), cat_feats),
    ], remainder='drop')

    X_train_t = preprocessor.fit_transform(X_train)
    X_test_t  = preprocessor.transform(X_test)

    print("Avant ML, shapes :", X_train.shape, X_test.shape)
    print("Après pré-trait.:", X_train_t.shape, X_test_t.shape)

    # RandomForest
    rf = RandomForestClassifier(n_estimators=200, random_state=42)
    rf.fit(X_train_t, y_train)
    print("RandomForest Accuracy:", accuracy_score(y_test, rf.predict(X_test_t)))

    # XGBoost
    xgb = XGBClassifier(n_estimators=300, max_depth=6, learning_rate=0.001, eval_metric='mlogloss')
    xgb.fit(X_train_t, y_train)
    print("XGBoost Accuracy:", accuracy_score(y_test, xgb.predict(X_test_t)))

    # Feature Importance
    feature_names = preprocessor.get_feature_names_out()
    importances = xgb.feature_importances_
    sorted_idx = np.argsort(importances)[::-1][:20]

    plt.figure(figsize=(10, 6))
    plt.barh([feature_names[i] for i in sorted_idx], importances[sorted_idx])
    plt.xlabel("Importance")
    plt.title("Top 20 Features - XGBoost")
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.savefig("top_features.png")

    n_classes = len(np.unique(y_train))
    model = build_model(input_dim=X_train_t.shape[1], n_classes=n_classes)
    model.summary()

    class_weights = compute_class_weight(class_weight='balanced', classes=np.unique(y_train), y=y_train)
    class_weights_dict = dict(enumerate(class_weights))

    early_stopping = EarlyStopping(monitor='val_loss', patience=1800, restore_best_weights=True)

    history = model.fit(
        X_train_t, y_train,
        validation_data=(X_test_t, y_test),
        epochs=1000,
        batch_size=32,
        class_weight=class_weights_dict,
        callbacks=[early_stopping],
        verbose=2
    )

    loss, acc = model.evaluate(X_test_t, y_test, verbose=0)
    print(f"\nÉval finale — loss: {loss:.4f}, accuracy: {acc:.4f}")

    base = os.path.dirname(__file__)
    model.save(os.path.join(base, 'modele_vulnerabilite.h5'))
    joblib.dump(preprocessor, os.path.join(base, 'data', 'preprocessor.pkl'))
    joblib.dump(history.history, os.path.join(base, 'history.pkl'))
    print("Modèle, pré-processeur et historique sauvegardés.")

if __name__ == "__main__":
    main()




# import os
# import joblib
# import numpy as np
# import pandas as pd
# import tensorflow as tf
# from keras.src.callbacks import EarlyStopping
#
# from sklearn.pipeline import Pipeline
# from sklearn.compose import ColumnTransformer
# from sklearn.impute import SimpleImputer
# from sklearn.preprocessing import StandardScaler, OneHotEncoder
# from sklearn.utils.class_weight import compute_class_weight
# from sklearn.ensemble import RandomForestClassifier
# from xgboost import XGBClassifier
# from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
#
# import matplotlib.pyplot as plt
#
#
# from detection.prepare_data import load_and_concatenate, preprocess
#
# def build_model(input_dim: int, n_classes: int) -> tf.keras.Model:
#     model = tf.keras.Sequential([
#         tf.keras.layers.InputLayer(shape=(input_dim,)),
#         tf.keras.layers.Dense(256, activation='relu'),
#         tf.keras.layers.BatchNormalization(),
#         tf.keras.layers.Dropout(0.3),
#         tf.keras.layers.Dense(128, activation='relu'),
#         tf.keras.layers.BatchNormalization(),
#         tf.keras.layers.Dropout(0.3),
#         tf.keras.layers.Dense(64, activation='relu'),
#         tf.keras.layers.BatchNormalization(),
#         tf.keras.layers.Dropout(0.3),
#         tf.keras.layers.Dense(n_classes, activation='softmax'),
#     ])
#     optimizer = tf.keras.optimizers.Adam(learning_rate=0.001)
#     model.compile(optimizer=optimizer, loss='sparse_categorical_crossentropy', metrics=['accuracy'])
#     return model
#
# def main():
#     df = load_and_concatenate()
#     X_train, X_test, y_train, y_test = preprocess(df)
#
#     num_feats = [
#         'age', 'revenu', 'enfants_non_scolarises',
#         'nombre_personnes_menage', 'montant_total_recu'
#     ]
#     cat_feats = [c for c in X_train.columns if c not in num_feats]
#
#     numeric_pipeline = Pipeline([
#         ('imputer', SimpleImputer(strategy='median')),
#         ('scaler',  StandardScaler()),
#     ])
#
#     preprocessor = ColumnTransformer([
#         ('num', numeric_pipeline, num_feats),
#         ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), cat_feats),
#     ], remainder='drop')
#
#     X_train_t = preprocessor.fit_transform(X_train)
#     X_test_t  = preprocessor.transform(X_test)
#
#     print("Avant ML, shapes :", X_train.shape, X_test.shape)
#     print("Après pré-trait.:", X_train_t.shape, X_test_t.shape)
#
#     # RandomForest
#     rf = RandomForestClassifier(n_estimators=200, random_state=42)
#     rf.fit(X_train_t, y_train)
#     print("RandomForest Accuracy:", accuracy_score(y_test, rf.predict(X_test_t)))
#
#     # XGBoost
#     xgb = XGBClassifier(n_estimators=300, max_depth=6, learning_rate=0.001, eval_metric='mlogloss')
#     xgb.fit(X_train_t, y_train)
#     print("XGBoost Accuracy:", accuracy_score(y_test, xgb.predict(X_test_t)))
#
#     # Feature Importance
#     feature_names = preprocessor.get_feature_names_out()
#     importances = xgb.feature_importances_
#     sorted_idx = np.argsort(importances)[::-1][:20]
#
#     plt.figure(figsize=(10, 6))
#     plt.barh([feature_names[i] for i in sorted_idx], importances[sorted_idx])
#     plt.xlabel("Importance")
#     plt.title("Top 20 Features - XGBoost")
#     plt.gca().invert_yaxis()
#     plt.tight_layout()
#     plt.savefig("top_features.png")
#
#     n_classes = len(np.unique(y_train))
#     model = build_model(input_dim=X_train_t.shape[1], n_classes=n_classes)
#     model.summary()
#
#     class_weights = compute_class_weight(class_weight='balanced', classes=np.unique(y_train), y=y_train)
#     class_weights_dict = dict(enumerate(class_weights))
#
#     early_stopping = EarlyStopping(monitor='val_loss', patience=1800, restore_best_weights=True)
#
#     history = model.fit(
#         X_train_t, y_train,
#         validation_data=(X_test_t, y_test),
#         epochs=1000,
#         batch_size=32,
#         class_weight=class_weights_dict,
#         callbacks=[early_stopping],
#         verbose=2
#     )
#
#     loss, acc = model.evaluate(X_test_t, y_test, verbose=0)
#     print(f"\nÉval finale — loss: {loss:.4f}, accuracy: {acc:.4f}")
#
#     base = os.path.dirname(__file__)
#     model.save(os.path.join(base, 'modele_vulnerabilite.h5'))
#     joblib.dump(preprocessor, os.path.join(base, 'data', 'preprocessor.pkl'))
#     joblib.dump(history.history, os.path.join(base, 'history.pkl'))
#     print("Modèle, pré-processeur et historique sauvegardés.")
#
# if __name__ == "__main__":
#     main()