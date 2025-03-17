# Seminary - Backend Flask avec intégration DeepSeek et données CSV

Ce projet met en place un backend Flask pour le site Seminary qui intègre l'API DeepSeek. Il permet aux utilisateurs de rechercher des salles de séminaires ou des activités dans les Vosges, en utilisant exclusivement les données contenues dans les fichiers CSV comme source d'information.

## Fonctionnalités

- Page d'accueil avec formulaire de recherche
- Analyse des requêtes pour déterminer si elles concernent une salle de séminaire ou une activité
- Utilisation exclusive des données CSV comme source d'information
- Intégration avec l'API DeepSeek pour générer des recommandations contextuelles
- Expérience conversationnelle personnalisée avec ton commercial et engageant
- Recommandation unique et ciblée pour chaque demande utilisateur
- Affichage des résultats dans une page de réponse formatée avec :
  - Un carrousel d'images du lieu recommandé
  - Une interface utilisateur moderne et responsive
  - Un affichage adapté aux appareils mobiles et de bureau

## Nouvelles fonctionnalités

### Préloader amélioré
- Animation plus fluide avec transition des faits "Le Saviez-vous"
- Barre de progression ralentie pour une meilleure expérience utilisateur
- Centrage parfait des éléments

### Système de logs des recherches utilisateurs
- Enregistrement automatique de chaque recherche dans un fichier CSV
- Stockage de la date/heure, de la requête et du lieu recommandé
- Données persistantes pour analyse ultérieure

### Tableau de bord de statistiques
- Visualisation des tendances de recherche via une interface graphique
- Accès sécurisé via la route `/search-stats?key=seminary_debug`
- Affichage des statistiques clés :
  - Nombre total de recherches
  - Lieux uniques recommandés
  - Pourcentage de recherches sans résultat
  - Graphique des recherches par jour
  - Top 5 des lieux les plus recommandés
  - Tableau des 10 dernières recherches

## Prérequis

- Python 3.8 ou supérieur
- Clé API DeepSeek
- Clé API Google Maps (pour les images des lieux)
- Fichiers CSV de données :
  - `salles_seminaires.csv` : Informations sur les salles de séminaires disponibles
  - `activités-vosges.csv` : Informations sur les activités disponibles dans les Vosges

## Installation locale

1. Clonez ce dépôt ou téléchargez les fichiers

2. Installez les dépendances :
   ```
   pip install -r requirements.txt
   ```

3. Configurez vos clés API :
   - Renommez le fichier `.env.example` en `.env` (ou créez-le s'il n'existe pas)
   - Ajoutez vos clés API dans le fichier .env :
     ```
     DEEPSEEK_API_KEY=votre_cle_api_ici
     GOOGLE_MAPS_API_KEY=votre_cle_google_maps_ici
     ```

4. Assurez-vous que les fichiers CSV sont présents à la racine du projet :
   - `salles_seminaires.csv`
   - `activités-vosges.csv`

5. Lancez l'application Flask :
   ```
   python app.py
   ```

6. Ouvrez votre navigateur à l'adresse [http://127.0.0.1:5000/](http://127.0.0.1:5000/)

## Déploiement sur Railway

Pour déployer cette application sur Railway, suivez les étapes ci-dessous :

1. Créez un compte sur [Railway](https://railway.app/) et connectez-vous

2. Depuis le tableau de bord Railway, cliquez sur "New Project"

3. Sélectionnez "Deploy from GitHub repo"

4. Connectez votre compte GitHub et sélectionnez ce dépôt

5. Railway détectera automatiquement les fichiers Procfile et requirements.txt

6. Dans l'onglet "Variables", ajoutez les variables d'environnement suivantes :
   - `DEEPSEEK_API_KEY`: Votre clé API DeepSeek
   - `DEEPSEEK_API_URL`: L'URL de l'API DeepSeek (https://api.deepseek.com/v1/chat/completions)
   - `GOOGLE_MAPS_API_KEY`: Votre clé API Google Maps
   - `FLASK_ENV`: production
   - `FLASK_DEBUG`: 0

7. Railway déploiera automatiquement l'application et vous fournira une URL pour y accéder

8. Si nécessaire, configurez un domaine personnalisé dans les paramètres du projet

## Structure des fichiers

- `app.py` : Application Flask principale avec traitement des CSV et intégration DeepSeek
- `index.html` : Page d'accueil avec le formulaire de recherche
- `result.html` : Page de résultats avec les recommandations et carrousel d'images
- `requirements.txt` : Liste des dépendances Python
- `.env` : Configuration des variables d'environnement (clés API, etc.)
- `Procfile` : Configuration pour le déploiement sur Railway
- `runtime.txt` : Version de Python à utiliser
- `salles_seminaires.csv` : Données sur les salles de séminaires disponibles
- `activités-vosges.csv` : Données sur les activités disponibles dans les Vosges

## Utilisation

1. Entrez votre requête dans le formulaire :
   - Pour rechercher une salle de séminaire, utilisez des termes comme "salle", "séminaire", "capacité", etc.
   - Pour rechercher une activité dans les Vosges, utilisez des termes comme "activité", "randonnée", "musée", etc.

2. Soumettez le formulaire pour recevoir une recommandation personnalisée basée exclusivement sur les données CSV, avec un ton commercial et engageant, accompagnée d'images du lieu recommandé.

## Fonctionnement de l'analyse des requêtes

L'application analyse la requête de l'utilisateur pour déterminer si elle concerne une salle de séminaire ou une activité dans les Vosges. Cette analyse est basée sur la présence de mots-clés spécifiques dans la requête :

- Mots-clés pour les salles : "salle", "séminaire", "conférence", "hôtel", "capacité", etc.
- Mots-clés pour les activités : "activité", "loisir", "sport", "visite", "randonnée", etc.

En fonction du résultat de cette analyse, l'application formatte les données CSV appropriées et les envoie à l'API DeepSeek avec des instructions spécifiques.

## Personnalisation de l'API DeepSeek

Le fichier `app.py` contient une implémentation de l'intégration avec l'API DeepSeek pour offrir une expérience conversationnelle plus engageante et commerciale. L'API est configurée pour :

1. Utiliser uniquement les données fournies comme source d'information
2. Adopter un ton chaleureux, commercial et personnalisé
3. Recommander UN SEUL lieu ou activité considéré comme le meilleur choix pour l'utilisateur
4. Structurer sa réponse avec une introduction personnalisée, une analyse des besoins, une présentation enthousiaste de la recommandation et une conclusion invitante
5. Communiquer directement avec l'utilisateur à la deuxième personne (vouvoiement)

Le système est conçu pour donner l'impression que Seminary est une IA passionnée et experte qui cherche personnellement la meilleure option pour l'utilisateur, tout en s'appuyant exclusivement sur les données factuelles des fichiers CSV.

## Carrousel d'images

La page de résultats a été améliorée avec un carrousel d'images moderne qui présente visuellement le lieu recommandé :

1. L'application extrait automatiquement le nom du lieu recommandé à partir de la réponse de l'API DeepSeek
2. Elle recherche ce lieu dans les données CSV pour récupérer les références de photos associées
3. Les références de photos sont utilisées pour générer des URLs d'images via l'API Google Maps Places Photos
4. Jusqu'à 5 images sont affichées dans un carrousel interactif avec :
   - Navigation par flèches gauche/droite
   - Indicateurs de position
   - Design responsive qui s'adapte aux différentes tailles d'écran
   - Chargement paresseux (lazy loading) pour optimiser les performances

## Interface utilisateur

L'interface utilisateur a été repensée pour offrir une expérience moderne et agréable :

1. Header complet avec navigation et boutons d'action
2. Menu hamburger pour les appareils mobiles
3. Mise en page responsive qui s'adapte aux écrans de toutes tailles
4. Carrousel d'images à gauche et contenu textuel à droite sur les grands écrans
5. Disposition verticale optimisée sur les petits écrans
6. Styles cohérents avec la charte graphique de Seminary
7. Animations et transitions fluides pour une expérience utilisateur améliorée 

PROMPT POUR CHAT CURSOR 
analyse bien tout ce que je t'ai dis et fais attention avant d'agir, garde toujours le code le plus optimisé possible en faisant attention à supprimer les parties devenant obsoletes ou inutiles une fois tes modifications faites et à bien modifier uniquement les parties requis pour la/les tâches, utilise sequeuntial thinking, dans tes explications soit toujours précis sur ce que tu as modifié ou tu as modifié cela pourquoi 