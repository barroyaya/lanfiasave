# detection/utils.py
import tensorflow as tf

import numpy as np

# Charger le modèle sauvegardé
MODELE_PATH = 'detection/modele_vulnerabilite.h5'
modele = tf.keras.models.load_model(MODELE_PATH)

def est_vulnerable(age, revenu):
    # Prépare les données pour le modèle en tant que tableau NumPy avec la bonne forme
    donnee = np.array([[age, revenu]], dtype=np.float32)
    prediction = modele.predict(donnee)
    print(prediction)
    # Renvoie True si la prédiction est supérieure à 0.5, sinon False
    return prediction[0][0] > 0.5
