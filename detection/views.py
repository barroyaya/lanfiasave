# detection/views.py
import tensorflow as tf

# Charger le modèle TensorFlow
model = tf.keras.models.load_model('detection/modele_vulnerabilite.h5')

def est_vulnerable(data):
    # Traitez les données avec le modèle
    prediction = model.predict(data)
    # Retournez True si la personne est vulnérable
    return prediction[0] > 0.5
from django.shortcuts import render
#
# # Create your views here.
#
# import tensorflow as tf
# import numpy as np
#
# # Charger le modèle TensorFlow une seule fois au démarrage
# MODEL_PATH = 'modele_vulnerabilite.h5'
# model = tf.keras.models.load_model(MODEL_PATH)
#
# def preprocess_data(person_data):
#     """
#     Transforme les données du recensement dans un format attendu par le modèle.
#     Cet exemple suppose que le modèle attend 2 features : l'âge et le revenu.
#     Adaptez cette fonction en fonction de votre modèle.
#     """
#     try:
#         age = float(person_data.get('age', 0))
#     except (ValueError, TypeError):
#         age = 0.0
#     try:
#         revenu = float(person_data.get('revenu', 0))
#     except (ValueError, TypeError):
#         revenu = 0.0
#     # Crée un tableau numpy de forme (1, nombre_de_features)
#     data_array = np.array([[age, revenu]])
#     return data_array
#
# def est_vulnerable(person_data):
#     """
#     Utilise le modèle TensorFlow pour déterminer si une personne est vulnérable.
#     Retourne True si la probabilité prédite est supérieure à 0.5.
#     """
#     data = preprocess_data(person_data)
#     prediction = model.predict(data)
#     # Supposons que prediction est de forme (1, 1) avec une probabilité
#     return prediction[0][0] > 0.5
