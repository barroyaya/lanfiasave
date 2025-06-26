# detection/prepare_data.py
import os
import pandas as pd
from sklearn.model_selection import train_test_split

def load_and_concatenate():
    # 1) Construction des chemins vers les deux fichiers
    base_dir = os.path.dirname(__file__)
    files = [
        os.path.join(base_dir, 'data', 'population_vulnerable.xlsx'),
        os.path.join(base_dir, 'data', 'population_vulnerable_score.xlsx'),
    ]

    # 2) Lecture et concaténation
    dfs = [pd.read_excel(p) for p in files]
    df = pd.concat(dfs, ignore_index=True)

    # 3) Renommage des colonnes pour matcher vos features « snake_case »
    df = df.rename(columns={
        'Âge':                          'age',
        'Nom':                          'first_name',  # si nécessaire
        'Sexe':                         'sexe',
        'Statut matrimonial':           'situation_matrimoniale',
        'Type de logement':             'logement',
        "Source d'eau":                 'source_eau',
        'Type de sanitaires':           'type_sanitaires',
        'Accès à l’électricité':        'acces_electricite',
        'Situation professionnelle':    'emploi',
        'Revenu mensuel (FCFA)':        'revenu',
        'Niveau d’éducation':           'niveau_education',
        'État de santé':                'etat_sante',
        'Handicap':                     'handicap',
        'Région':                       'region',
        'Auto-évaluation de vulnérabilité':'auto_eval_vulnerabilite',
        'Enfants non scolarisés':       'enfants_non_scolarises',
        'Nombre de personnes dans le ménage': 'nombre_personnes_menage',
        'Montant total reçu (allocations)':  'montant_total_recu',
        # pour le second fichier :
        'Score de vulnérabilité':       'vulnerability_score',
        'Catégorie de vulnérabilité':   'vulnerability_category',
    })

    return df

from sklearn.model_selection import train_test_split

import unidecode

import unidecode
import pandas as pd
from sklearn.model_selection import train_test_split

def preprocess(df):
    features = [
        'age', 'revenu', 'logement', 'type_sanitaires', 'sexe',
        'situation_matrimoniale', 'source_eau', 'acces_electricite',
        'emploi', 'niveau_education', 'etat_sante', 'handicap',
        'enfants_non_scolarises', 'nombre_personnes_menage',
        'montant_total_recu',
    ]            # vos colonnes explicatives
    raw_target = 'auto_eval_vulnerabilite'

    df = df[features + [raw_target]].copy()
    df[raw_target] = df[raw_target].astype(str).str.strip()
    df['target_norm'] = df[raw_target].str.lower().map(unidecode.unidecode)

    # Adapter ce mapping à vos 4 libellés effectivement présents
    mapping = {
        'resilient':      0,
        'stable':         1,
        'vulnerable':     2,
        'tres vulnerable':3
    }
    df['y'] = df['target_norm'].map(mapping)

    print("Après mapping, répartition de y :\n", df['y'].value_counts(dropna=False))

    df = df.dropna(subset=['y'])
    df['y'] = df['y'].astype(int)

    X = df[features]
    y = df['y']
    return train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)


if __name__ == "__main__":
    # Chargement + pré-traitement
    df = load_and_concatenate()
    X_train, X_test, y_train, y_test = preprocess(df)
    print("Données prêtes : ", X_train.shape, X_test.shape, y_train.shape)

    # Vous pouvez ensuite importer ce script depuis votre create_model.py
    # et utiliser X_train, y_train pour entraîner votre modèle.
