#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Application Flask pour Seminary intégrant l'API DeepSeek avec des données CSV
----------------------------------------------------
Ce script met en place un backend simple qui:
1. Sert la page d'accueil index.html
2. Récupère la description/requête soumise par l'utilisateur
3. Analyse si elle concerne une salle de séminaire ou une activité dans les Vosges
4. Utilise les données des fichiers CSV correspondants
5. Envoie cette requête à l'API DeepSeek avec les données CSV comme contexte
6. Affiche le résultat dans result.html avec un carrousel d'images du lieu recommandé
"""

import os
import csv
import re
import requests
import json
import html
import time
from datetime import datetime
import random
import pandas as pd
import numpy as np
from flask import Flask, request, send_from_directory, redirect, jsonify, render_template, url_for, session
from dotenv import load_dotenv
from collections import deque

# Charger les variables d'environnement depuis .env si présent
load_dotenv()

# Initialiser l'application Flask
app = Flask(__name__)

# Récupérer la clé API depuis les variables d'environnement
# ou utiliser une valeur par défaut pour les tests
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "votre_cle_api_par_defaut")
DEEPSEEK_API_URL = os.environ.get("DEEPSEEK_API_URL", "https://api.deepseek.com/v1/chat/completions")
# Google Maps API Key
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "AIzaSyDQrOX5SI4LLy6o4qydq5OiOifyMkXZAK4")

# Variables globales pour stocker les données CSV traitées
salles_seminaires_data = []
activites_vosges_data = {}

# Classe pour gérer les logs d'API en mémoire
class ApiLogger:
    def __init__(self, max_logs=10):
        self.logs = deque(maxlen=max_logs)  # Utilisation d'une deque avec taille maximale
        self.session_id = None
        self.reset_session()
    
    def reset_session(self):
        """Réinitialise l'ID de session avec un timestamp"""
        self.session_id = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def log_api_call(self, endpoint, input_data, output_data, status="success"):
        """
        Enregistre un appel d'API dans la mémoire
        
        Args:
            endpoint (str): Point de terminaison de l'API
            input_data (dict): Données envoyées à l'API
            output_data (dict/str): Réponse reçue de l'API
            status (str): Statut de l'appel (success/error)
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Masquer la clé API dans les logs pour des raisons de sécurité
        if isinstance(input_data, dict) and "headers" in input_data and "Authorization" in input_data["headers"]:
            input_data = input_data.copy()  # Créer une copie pour ne pas modifier l'original
            input_data["headers"] = input_data["headers"].copy()
            auth_value = input_data["headers"]["Authorization"]
            if auth_value.startswith("Bearer "):
                input_data["headers"]["Authorization"] = "Bearer [MASKED]"
        
        log_entry = {
            "timestamp": timestamp,
            "session_id": self.session_id,
            "endpoint": endpoint,
            "input": input_data,
            "output": output_data,
            "status": status
        }
        
        self.logs.append(log_entry)
        print(f"[API Log] {timestamp} - {endpoint} - {status}")
    
    def get_logs(self, count=None):
        """
        Récupère les logs stockés en mémoire
        
        Args:
            count (int, optional): Nombre de logs à récupérer (les plus récents)
            
        Returns:
            list: Liste des logs
        """
        if count is None:
            return list(self.logs)
        return list(self.logs)[-count:]
    
    def clear_logs(self):
        """Efface tous les logs en mémoire"""
        self.logs.clear()
        print("[API Log] Logs effacés")

# Initialiser le logger d'API
api_logger = ApiLogger(max_logs=20)  # Garder les 20 derniers appels API

# Dictionnaire de correspondances pour les variantes de noms de villes
city_aliases = {
    # Variantes pour les principales villes des Vosges
    'contrex': 'Contrexéville',
    'contrexeville': 'Contrexéville',
    'gerardmer': 'Gérardmer',
    'epinal': 'Épinal',
    'vittel': 'Vittel',
    'remiremont': 'Remiremont',
    'plombieres': 'Plombières-les-Bains',
    'plombieres-les-bains': 'Plombières-les-Bains',
    'saint-die': 'Saint-Dié-des-Vosges',
    'saint-die-des-vosges': 'Saint-Dié-des-Vosges',
    'la bresse': 'La Bresse',
    'labresse': 'La Bresse',
    'nancy': 'Nancy',
    'thann': 'Thann',
    'mulhouse': 'Mulhouse',
    'colmar': 'Colmar',
    'strasbourg': 'Strasbourg'
}

# Liste des villes principales pour recherche directe (noms officiels)
main_cities = set(city_aliases.values())


def parse_salles_seminaires_csv():
    """
    Lit et traite le fichier CSV des salles de séminaires.
    Retourne une liste structurée de dictionnaires contenant les informations des salles.
    """
    parsed_data = []
    
    try:
        with open('salles_seminaires.csv', 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                if row.get('COMPLET'):
                    # Extraire les informations de la colonne COMPLET
                    salle_info = row.get('COMPLET', '')
                    
                    # Initialiser un dictionnaire pour stocker les informations extraites
                    salle_dict = {
                        'nom': row.get('Nom', '').strip(),
                        'equipements': row.get('équipements', '').strip(),
                        'photo_reference': row.get('photo_reference', '').strip(),
                        'place_id': row.get('place_id', '').strip()  # Ajouter le place_id du fichier CSV
                    }
                    
                    # Extraire la capacité
                    capacite_match = re.search(r'Capacité\s*:\s*(\d+)', salle_info)
                    if capacite_match:
                        salle_dict['capacite'] = capacite_match.group(1)
                    
                    # Extraire le type
                    type_match = re.search(r'Type\s*:\s*([^\n]+)', salle_info)
                    if type_match:
                        salle_dict['type'] = type_match.group(1).strip()
                    
                    # Extraire l'adresse
                    adresse_match = re.search(r'Adresse\s*:\s*([^\n]+)', salle_info)
                    if adresse_match:
                        salle_dict['adresse'] = adresse_match.group(1).strip()
                    
                    # Extraire l'URL de l'image
                    image_match = re.search(r'[Ii]mage url\s*:\s*([^\n]+)', salle_info)
                    if image_match:
                        salle_dict['image_url'] = image_match.group(1).strip()
                    
                    # Extraire le prix
                    prix_match = re.search(r'Prix par personne\s*:\s*([^\n]+)', salle_info)
                    if prix_match:
                        salle_dict['prix'] = prix_match.group(1).strip()
                    
                    # Ajouter à la liste des salles
                    parsed_data.append(salle_dict)
        
        print(f"Chargé {len(parsed_data)} salles de séminaires depuis le fichier CSV.")
        return parsed_data
    
    except Exception as e:
        print(f"Erreur lors du parsing du fichier salles_seminaires.csv: {e}")
        return []


def parse_activites_vosges_csv():
    """
    Lit et traite le fichier CSV des activités dans les Vosges.
    Retourne un dictionnaire structuré où les clés sont les types d'activités
    et les valeurs sont des listes d'activités.
    """
    parsed_data = {}
    current_category = None
    
    try:
        with open('activités-vosges.csv', 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            
            for row in reader:
                if len(row) >= 2:
                    # Si la première colonne n'est pas vide, c'est une nouvelle catégorie
                    if row[0].strip():
                        current_category = row[0].strip()
                        parsed_data[current_category] = []
                    
                    # Si nous avons une catégorie et que la deuxième colonne n'est pas vide
                    if current_category and row[1].strip():
                        # Ajouter l'activité à la catégorie courante
                        parsed_data[current_category].append(row[1])
        
        print(f"Chargé {len(parsed_data)} catégories d'activités depuis le fichier CSV.")
        return parsed_data
    
    except Exception as e:
        print(f"Erreur lors du parsing du fichier activités-vosges.csv: {e}")
        return {}
        
@app.before_first_request
def load_csv_data():
    global salles_seminaires_data, activites_vosges_data
    salles_seminaires_data = parse_salles_seminaires_csv()
    activites_vosges_data = parse_activites_vosges_csv()


def extract_city_from_prompt(prompt):
    """
    Analyse le prompt utilisateur pour identifier si une ville y est mentionnée.
    
    Args:
        prompt (str): Le prompt fourni par l'utilisateur
        
    Returns:
        str: Le nom officiel de la ville si trouvé, None sinon
    """
    # Convertir le prompt en minuscules pour la comparaison
    prompt_lower = prompt.lower()
    
    # Vérifier d'abord les noms officiels des villes (plus rapide)
    for city in main_cities:
        if city.lower() in prompt_lower:
            print(f"Ville trouvée dans le prompt (nom officiel): {city}")
            return city
    
    # Ensuite vérifier les variantes/alias
    for alias, city in city_aliases.items():
        # Utiliser une regex pour trouver le mot complet (éviter les faux positifs)
        if re.search(r'\b' + re.escape(alias) + r'\b', prompt_lower):
            print(f"Ville trouvée dans le prompt (alias '{alias}'): {city}")
            return city
    
    print("Aucune ville n'a été trouvée dans le prompt")
    return None


def filter_venues_by_city(venues, city):
    """
    Filtre les salles de séminaires pour ne garder que celles situées dans la ville spécifiée.
    
    Args:
        venues (list): Liste des salles de séminaires
        city (str): Nom de la ville à filtrer
        
    Returns:
        list: Liste filtrée des salles de séminaires
    """
    if not city:
        return venues
    
    filtered_venues = []
    city_lower = city.lower()
    
    for venue in venues:
        # Vérifier si l'adresse contient le nom de la ville
        venue_address = venue.get('adresse', '').lower()
        
        if city_lower in venue_address:
            filtered_venues.append(venue)
    
    print(f"Filtrage par ville '{city}': {len(filtered_venues)}/{len(venues)} salles retenues")
    
    # Si aucune salle ne correspond exactement, essayer une correspondance plus souple
    if not filtered_venues:
        print("Aucune correspondance exacte, tentative de correspondance partielle...")
        
        for venue in venues:
            venue_address = venue.get('adresse', '').lower()
            
            # Vérifier si l'adresse contient au moins une partie du nom de la ville
            # (par exemple, si la ville est "Saint-Dié-des-Vosges", chercher "saint-dié")
            if any(part in venue_address for part in city_lower.split('-')):
                filtered_venues.append(venue)
        
        print(f"Correspondance partielle: {len(filtered_venues)}/{len(venues)} salles retenues")
    
    return filtered_venues if filtered_venues else venues  # Retourner toutes les salles si aucune ne correspond


def format_csv_data_for_api(query):
    """
    Formate les données CSV pour l'API DeepSeek en fonction de la requête.
    Détermine si la requête concerne une salle de séminaire ou une activité.
    Si une ville est mentionnée et que la recherche concerne une salle,
    filtre les salles pour ne garder que celles situées dans cette ville.
    
    Args:
        query (str): La requête utilisateur
        
    Returns:
        tuple: (context_data, is_venue_search)
            context_data (str): Les données formatées pour l'API
            is_venue_search (bool): True si la recherche concerne une salle, False pour une activité
    """
    # Liste de mots-clés pour identifier une recherche de salle
    venue_keywords = ['salle', 'séminaire', 'conférence', 'réunion', 'hôtel', 
                     'capacité', 'personne', 'équipement', 'projecteur', 'wifi']
    
    # Liste de mots-clés pour identifier une recherche d'activité
    activity_keywords = ['activité', 'loisir', 'sport', 'visite', 'randonnée', 'musée', 
                        'atelier', 'aventure', 'découverte', 'thermes', 'détente']
    
    # Compter les occurrences de mots-clés
    venue_count = sum(1 for keyword in venue_keywords if keyword.lower() in query.lower())
    activity_count = sum(1 for keyword in activity_keywords if keyword.lower() in query.lower())
    
    # Déterminer le type de recherche
    is_venue_search = venue_count >= activity_count
    
    # Formater les données en fonction du type de recherche
    context_data = ""
    
    if is_venue_search:
        # Essayer d'extraire une ville du prompt
        city = extract_city_from_prompt(query)
        
        # Filtrer les salles si une ville est mentionnée
        filtered_data = salles_seminaires_data
        if city:
            filtered_data = filter_venues_by_city(salles_seminaires_data, city)
        
        # Formater les données des salles de séminaires filtrées
        context_data = "SALLES DE SÉMINAIRES DISPONIBLES:\n\n"
        for i, salle in enumerate(filtered_data, 1):
            context_data += f"{i}. {salle.get('nom', 'Sans nom')}\n"
            context_data += f"   Type: {salle.get('type', 'Non spécifié')}\n"
            context_data += f"   Capacité: {salle.get('capacite', 'Non spécifiée')}\n"
            context_data += f"   Équipements: {salle.get('equipements', 'Non spécifiés')}\n"
            context_data += f"   Adresse: {salle.get('adresse', 'Non spécifiée')}\n"
            context_data += f"   Prix: {salle.get('prix', 'Non spécifié')}\n\n"
    else:
        # Formater les données des activités (inchangé)
        context_data = "ACTIVITÉS DISPONIBLES DANS LES VOSGES:\n\n"
        for category, activities in activites_vosges_data.items():
            context_data += f"CATÉGORIE: {category}\n"
            for activity in activities:
                context_data += f"- {activity}\n"
            context_data += "\n"
    
    return context_data, is_venue_search


def extract_recommended_venue(response_text):
    """
    Extrait le nom du lieu recommandé à partir de la réponse de l'API.
    
    Args:
        response_text (str): Texte de la réponse de l'API
        
    Returns:
        str: Nom du lieu recommandé ou None si aucun lieu n'est identifié
    """
    # Recherche des lieux dans les données CSV
    potential_venues = []
    
    for venue in salles_seminaires_data:
        venue_name = venue.get('nom', '')
        if venue_name and venue_name.strip() and venue_name in response_text:
            potential_venues.append((venue_name, response_text.index(venue_name)))
    
    # Trier par ordre d'apparition pour prendre le premier mentionné (généralement la recommandation)
    if potential_venues:
        sorted_venues = sorted(potential_venues, key=lambda x: x[1])
        return sorted_venues[0][0]
    
    return None


def get_venue_place_id(venue_name):
    """
    Récupère le place_id Google Maps pour un lieu donné depuis les données CSV.
    
    Args:
        venue_name (str): Nom du lieu
        
    Returns:
        str: place_id du lieu ou None s'il n'est pas trouvé
    """
    if not venue_name:
        return None
    
    for venue in salles_seminaires_data:
        if venue.get('nom') == venue_name and venue.get('place_id'):
            return venue.get('place_id')
    
    return None


def get_venue_reviews(place_id):
    """
    Récupère les avis clients pour un lieu donné via l'API Google Places.
    
    Args:
        place_id (str): Identifiant Google Places du lieu
        
    Returns:
        list: Liste des avis avec les informations nécessaires pour le carrousel
    """
    print(f"Tentative de récupération des avis pour place_id: {place_id}")
    
    if not place_id:
        print("Aucun place_id fourni, impossible de récupérer les avis")
        return []
    
    if not GOOGLE_MAPS_API_KEY:
        print("Clé API Google Maps non définie, impossible de récupérer les avis")
        return []
    
    try:
        # Construire l'URL de l'API Google Places
        url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=reviews&language=fr&key={GOOGLE_MAPS_API_KEY}"
        print(f"URL de l'API Google Places: {url}")
        
        # Effectuer la requête
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Analyser la réponse
        result = response.json()
        print(f"Statut de la réponse API: {result.get('status')}")
        
        # Extraire les avis (maximum 5)
        reviews = []
        if result.get("status") == "OK" and "result" in result and "reviews" in result["result"]:
            print(f"Nombre d'avis trouvés: {len(result['result']['reviews'])}")
            for review in result["result"]["reviews"][:5]:  # Limiter à 5 avis maximum
                reviews.append({
                    "author_name": review.get("author_name", "Anonyme"),
                    "profile_photo_url": review.get("profile_photo_url", ""),
                    "rating": review.get("rating", 0),
                    "text": review.get("text", ""),
                    "relative_time_description": review.get("relative_time_description", "")
                })
        else:
            if result.get("status") != "OK":
                print("Erreur API: " + str(result.get('status')) + " - " + 
                    str(result.get('error_message', "Pas de message d'erreur")))
            elif "result" not in result:
                print("La clé 'result' est absente de la réponse API")
            elif "reviews" not in result["result"]:
                print("La clé 'reviews' est absente du résultat API")
        
        print(f"Nombre d'avis récupérés: {len(reviews)}")
        return reviews
    except Exception as e:
        print(f"Erreur lors de la récupération des avis: {e}")
        return []


def generate_reviews_carousel_html(reviews):
    """
    Génère le HTML pour le carrousel d'avis clients.
    
    Args:
        reviews (list): Liste des avis clients
        
    Returns:
        str: HTML du carrousel d'avis
    """
    print(f"Génération du HTML pour {len(reviews)} avis")
    
    if not reviews:
        print("Aucun avis disponible, affichage du message par défaut")
        return '<div class="review-slide active"><p class="no-reviews">Aucun avis disponible pour ce lieu.</p></div>'
    
    reviews_html = []
    
    for i, review in enumerate(reviews):
        # Limiter le texte de l'avis à 150 caractères avec ellipsis si nécessaire
        review_text = review.get("text", "")
        truncated_text = review_text[:150] + "..." if len(review_text) > 150 else review_text
        
        # Générer les étoiles basées sur la note
        rating = review.get("rating", 0)
        stars_html = ""
        for star in range(5):
            if star < rating:
                stars_html += '<i class="fas fa-star"></i>'
            else:
                stars_html += '<i class="far fa-star"></i>'
        
        # Construire l'HTML pour cet avis
        active_class = " active" if i == 0 else ""
        reviews_html.append(f'''
            <div class="review-slide{active_class}">
                <div class="review-header">
                    <img src="{review.get('profile_photo_url', '')}" alt="{review.get('author_name', 'Anonyme')}" class="review-author-img">
                    <div class="review-author-info">
                        <h4 class="review-author-name">{review.get('author_name', 'Anonyme')}</h4>
                        <div class="review-rating">{stars_html}</div>
                        <span class="review-time">{review.get('relative_time_description', '')}</span>
                    </div>
                </div>
                <p class="review-text">{truncated_text}</p>
            </div>
        ''')
    
    html_result = ''.join(reviews_html)
    print(f"HTML généré pour le carrousel d'avis: {len(html_result)} caractères")
    return html_result


def get_photo_references(venue_name):
    """
    Récupère les références de photos pour un lieu donné depuis les données CSV.
    Utilise une normalisation des noms pour gérer les différences d'encodage.
    
    Args:
        venue_name (str): Nom du lieu
        
    Returns:
        list: Liste des références de photos
    """
    if not venue_name:
        return []
    
    print(f"Recherche de photos pour le lieu: '{venue_name}'")
    
    # Fonction de normalisation pour gérer différents types d'apostrophes et d'accents
    def normalize_name(name):
        if not name:
            return ""
        # Convertir en minuscules
        result = name.lower()
        # Remplacer les apostrophes et les caractères spéciaux
        result = result.replace("'", "").replace("'", "").replace("`", "")
        # Remplacer les préfixes courants
        result = result.replace("l'", "l").replace("d'", "d")
        # Remplacer les accents
        result = result.replace("é", "e").replace("è", "e").replace("ê", "e").replace("ë", "e")
        result = result.replace("à", "a").replace("â", "a").replace("ä", "a")
        result = result.replace("ô", "o").replace("ö", "o")
        result = result.replace("ù", "u").replace("û", "u").replace("ü", "u")
        result = result.replace("ç", "c")
        # Supprimer les espaces supplémentaires
        result = " ".join(result.split())
        return result
    
    # Normaliser le nom du lieu recherché
    normalized_venue_name = normalize_name(venue_name)
    print(f"Nom normalisé pour la recherche de photos: '{normalized_venue_name}'")
    
    for venue in salles_seminaires_data:
        csv_venue_name = venue.get('nom', '')
        normalized_csv_name = normalize_name(csv_venue_name)
        
        print(f"Comparaison avec: '{csv_venue_name}' (normalisé: '{normalized_csv_name}')")
        
        # Vérifier si le nom correspond exactement ou partiellement après normalisation
        if (normalized_csv_name == normalized_venue_name or 
            normalized_venue_name in normalized_csv_name or 
            normalized_csv_name in normalized_venue_name):
            if venue.get('photo_reference'):
                print(f"Photos trouvées pour le lieu: {csv_venue_name}")
                return venue.get('photo_reference').split('||||')
        
        # Vérification spécifique pour "Hôtel Restaurant L'Écho du Lac"
        if "echo du lac" in normalized_csv_name and "hotel" in normalized_csv_name:
            if "echo du lac" in normalized_venue_name and "hotel" in normalized_venue_name:
                if venue.get('photo_reference'):
                    print(f"Photos trouvées pour L'Écho du Lac via correspondance spécifique")
                    return venue.get('photo_reference').split('||||')
    
    print(f"Aucune photo trouvée pour le lieu: {venue_name}")
    return []


def generate_carousel_html(photo_references):
    """
    Génère le HTML pour le carrousel d'images.
    
    Args:
        photo_references (list): Liste des références de photos
        
    Returns:
        str: HTML du carrousel
    """
    if not photo_references or not GOOGLE_MAPS_API_KEY:
        # Image par défaut si aucune référence de photo ou pas de clé API
        default_img = '<div class="carousel-slide"><img src="https://d1muf25xaso8hp.cloudfront.net/https%3A%2F%2F11d96a0e7e946a6d02eea1b59ed8995d.cdn.bubble.io%2Ff1738937103143x452387340290872700%2FSans%2520titre-1%2520%25281%2529.png?w=64&h=64&auto=compress&dpr=1&fit=max" alt="Image par défaut"></div>'
        return default_img
    
    carousel_slides = []
    
    # Utiliser jusqu'à 5 photos
    for i, ref in enumerate(photo_references[:5]):
        if ref:  # Vérifier que la référence n'est pas vide
            # Créer l'URL de l'API Google Maps Places Photos
            photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference={ref}&key={GOOGLE_MAPS_API_KEY}"
            carousel_slides.append(f'<div class="carousel-slide"><img src="{photo_url}" alt="Photo du lieu" loading="lazy"></div>')
    
    return ''.join(carousel_slides)


def call_deepseek_api(prompt):
    """
    Appelle l'API DeepSeek avec le prompt fourni et les données CSV pertinentes.
    Inclut un mécanisme de retry et un timeout augmenté pour gérer les problèmes de connexion.
    
    Args:
        prompt (str): Description/requête fournie par l'utilisateur
        
    Returns:
        str: Réponse générée par l'API DeepSeek ou message d'erreur
    """
    # Formater les données CSV en fonction de la requête
    print(f"[DEBUG] Début de call_deepseek_api avec prompt: '{prompt}'")
    context_data, is_venue_search = format_csv_data_for_api(prompt)
    print(f"[DEBUG] Données CSV formatées, is_venue_search: {is_venue_search}")
    
    # Préparer les instructions système en fonction du type de recherche
    if is_venue_search:
        system_instruction = """Tu es Seminary, une IA spécialisée et enthousiaste qui aide les gens à trouver leur salle de séminaire idéale.

IMPORTANT:
- Utilise UNIQUEMENT les informations fournies dans la liste des salles ci-dessous pour répondre
- Adopte un ton chaleureux, commercial et personnalisé comme si tu parlais directement à l'utilisateur
- Après analyse, recommande UN SEUL lieu que tu considères vraiment comme le meilleur choix pour cette personne
- Explique pourquoi ce lieu est parfait pour ses besoins spécifiques
- À la fin de ta réponse, ajoute une liste de 3 avantages clés du lieu sous forme de liste à puces, chaque avantage doit être concis et convaincant

Structure ta réponse ainsi:
1. Une introduction chaleureuse et personnalisée (utilise "vous" pour t'adresser à l'utilisateur)
2. Une brève analyse de ce que tu as compris de leurs besoins
3. Une présentation enthousiaste sous le format **Recommandation Unique** : [Description courte et persuasive du lieu en 3 phrases maximum qui explique pourquoi ce lieu est parfait pour leurs besoins]
4. Une conclusion invitante qui encourage l'utilisateur à réserver ou demander plus d'informations
5. Une liste de 3 avantages clés sous ce format exact:
   AVANTAGES:
   - **[Titre court et percutant du premier avantage]** [Description détaillée du premier avantage spécifique au lieu et aux besoins du client]
   - **[Titre court et percutant du deuxième avantage]** [Description détaillée du deuxième avantage spécifique au lieu et aux besoins du client]
   - **[Titre court et percutant du troisième avantage]** [Description détaillée du troisième avantage spécifique au lieu et aux besoins du client]

Ton objectif est de convaincre l'utilisateur que tu as trouvé LA salle parfaite pour son événement!
"""
    else:
        system_instruction = """Tu es Seminary, une IA passionnée et experte qui aide les gens à découvrir l'activité parfaite dans les Vosges.

IMPORTANT:
- Utilise UNIQUEMENT les informations fournies dans la liste des activités ci-dessous pour répondre
- Adopte un ton enthousiaste, inspirant et personnel comme si tu parlais directement à l'utilisateur
- Après analyse, recommande UNE SEULE activité que tu considères vraiment comme le meilleur choix pour cette personne
- Explique pourquoi cette activité correspond parfaitement à leurs attentes
- À la fin de ta réponse, ajoute une liste de 3 avantages clés de l'activité sous forme de liste à puces, chaque avantage doit être concis et convaincant

Structure ta réponse ainsi:
1. Une introduction chaleureuse et personnalisée (utilise "vous" pour t'adresser à l'utilisateur)
2. Une brève analyse de ce que tu as compris de leurs envies
3. Une présentation enthousiaste sous le format **Recommandation Unique** : [Description courte et persuasive de l'activité en 3 phrases maximum qui explique pourquoi cette activité est parfaite pour leurs besoins]
4. Une conclusion inspirante qui donne envie à l'utilisateur de vivre cette expérience
5. Une liste de 3 avantages clés sous ce format exact:
   AVANTAGES:
   - **[Titre court et percutant du premier avantage]** [Description détaillée du premier avantage spécifique à l'activité et aux besoins du client]
   - **[Titre court et percutant du deuxième avantage]** [Description détaillée du deuxième avantage spécifique à l'activité et aux besoins du client]
   - **[Titre court et percutant du troisième avantage]** [Description détaillée du troisième avantage spécifique à l'activité et aux besoins du client]

Ton objectif est de convaincre l'utilisateur que tu as trouvé L'activité parfaite pour lui dans les Vosges!
"""
    
    # Configuration de l'appel à l'API DeepSeek
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    
    # Vérifier si la clé API est définie
    if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY == "votre_cle_api_par_defaut":
        print("[DEBUG] ERREUR: Clé API DeepSeek non définie ou valeur par défaut")
        return "Désolé, je ne peux pas traiter votre demande car la clé API DeepSeek n'est pas configurée. Veuillez contacter l'administrateur."
    
    # Préparation des données pour l'API
    # À adapter selon la documentation officielle de l'API DeepSeek
    data = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "system",
                "content": system_instruction
            },
            {
                "role": "user",
                "content": f"Voici les données sur lesquelles tu dois te baser:\n\n{context_data}\n\nRequête de l'utilisateur: {prompt}"
            }
        ]
    }
    
    print(f"[DEBUG] Données préparées pour l'API DeepSeek")
    
    # Paramètres pour le mécanisme de retry
    max_retries = 3
    timeout_seconds = 90  # Augmentation du timeout à 90 secondes
    
    # Préparer les données d'entrée pour le log (sans la clé API)
    log_input = {
        "headers": {"Content-Type": "application/json", "Authorization": "Bearer [MASKED]"},
        "data": data,
        "prompt": prompt,
        "is_venue_search": is_venue_search
    }
    
    # Tentatives d'appel à l'API avec retry
    for attempt in range(1, max_retries + 1):
        try:
            print(f"[DEBUG] Tentative d'appel à l'API DeepSeek ({attempt}/{max_retries}, timeout: {timeout_seconds}s)...")
            
            # Appel à l'API DeepSeek avec timeout augmenté
            response = requests.post(
                DEEPSEEK_API_URL, 
                headers=headers, 
                json=data, 
                timeout=timeout_seconds
            )
            
            # Vérifier si la requête a réussi
            response.raise_for_status()
            
            # Récupérer la réponse
            result = response.json()
            
            # Extraire le contenu de la réponse
            response_content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            print(f"[DEBUG] Réponse reçue de l'API DeepSeek, longueur: {len(response_content)} caractères")
            
            # Enregistrer l'appel API réussi dans les logs
            api_logger.log_api_call(
                endpoint="DeepSeek API",
                input_data=log_input,
                output_data=result,
                status="success"
            )
            
            return response_content
            
        except requests.exceptions.Timeout:
            # Gestion spécifique des erreurs de timeout
            print(f"[DEBUG] Timeout lors de l'appel à l'API DeepSeek (tentative {attempt}/{max_retries})")
            
            if attempt < max_retries:
                # Calculer le temps d'attente avant la prochaine tentative (backoff exponentiel)
                wait_time = 2 ** attempt
                print(f"[DEBUG] Nouvelle tentative dans {wait_time} secondes...")
                time.sleep(wait_time)
            else:
                # Enregistrer l'erreur de timeout dans les logs
                api_logger.log_api_call(
                    endpoint="DeepSeek API",
                    input_data=log_input,
                    output_data={"error": "Timeout lors de l'appel à l'API"},
                    status="error"
                )
                
                return "Désolé, je n'ai pas pu obtenir une réponse de l'API DeepSeek dans le délai imparti. Veuillez réessayer plus tard."
                
        except requests.exceptions.RequestException as e:
            # Gestion des autres erreurs de requête
            error_message = f"Erreur lors de l'appel à l'API DeepSeek: {str(e)}"
            print(f"[DEBUG] {error_message}")
            
            if attempt < max_retries:
                # Calculer le temps d'attente avant la prochaine tentative (backoff exponentiel)
                wait_time = 2 ** attempt
                print(f"[DEBUG] Nouvelle tentative dans {wait_time} secondes...")
                time.sleep(wait_time)
            else:
                # Enregistrer l'erreur dans les logs
                api_logger.log_api_call(
                    endpoint="DeepSeek API",
                    input_data=log_input,
                    output_data={"error": str(e)},
                    status="error"
                )
                
                return f"Désolé, une erreur s'est produite lors de l'appel à l'API DeepSeek: {str(e)}"
        
        except Exception as e:
            # Gestion des erreurs inattendues
            error_message = f"Erreur inattendue lors de l'appel à l'API DeepSeek: {str(e)}"
            print(f"[DEBUG] {error_message}")
            
            # Enregistrer l'erreur dans les logs
            api_logger.log_api_call(
                endpoint="DeepSeek API",
                input_data=log_input,
                output_data={"error": str(e)},
                status="error"
            )
            
            return f"Désolé, une erreur inattendue s'est produite: {str(e)}"


def generate_advantage_cards_html(prompt, venue_name=None, response_text=None):
    """
    Génère le HTML pour les cartes d'avantages en fonction du prompt utilisateur et de la réponse de DeepSeek.
    
    Args:
        prompt (str): La requête de l'utilisateur
        venue_name (str, optional): Nom du lieu recommandé
        response_text (str, optional): Texte de réponse de DeepSeek contenant les avantages
        
    Returns:
        str: HTML des cartes d'avantages
    """
    # Essayer d'extraire les avantages de la réponse de DeepSeek
    extracted_advantages = []
    
    if response_text:
        # Déboguer: afficher le début de la réponse pour vérifier le format
        print(f"Débogage: Extrait de la réponse DeepSeek (premiers 200 caractères): {response_text[:200]}...")
        
        # Rechercher la section AVANTAGES dans la réponse avec une expression régulière améliorée
        # Prend en compte différentes formatations possibles: numéros, astérisques, etc.
        avantages_section = re.search(r'(?:\d+\.)?(?:\s*\*{1,2})?\s*AVANTAGES\s*(?:\*{1,2})?\s*:+\s*((?:-\s*.*(?:\n|$))+)', response_text, re.IGNORECASE | re.DOTALL)
        
        if avantages_section:
            # Extraire tous les avantages listés
            avantages_text = avantages_section.group(1)
            print(f"Débogage: Section AVANTAGES trouvée, contenu: {avantages_text}")
            
            # Expression régulière améliorée pour extraire chaque élément de la liste
            avantages_items = re.findall(r'-\s*(.*?)(?=\n\s*-|\n\n|$)', avantages_text, re.DOTALL)
            
            print(f"Avantages trouvés: {len(avantages_items)}")
            
            for advantage_text in avantages_items[:3]:  # Limiter à 3 avantages
                advantage_text = advantage_text.strip()
                print(f"Débogage: Traitement de l'avantage: {advantage_text}")
                
                # Expression régulière améliorée pour extraire le titre entre ** ** et la description
                # Prend en compte les deux-points qui peuvent séparer le titre et la description
                title_match = re.search(r'\*\*(.*?)\*\*\s*:?\s*(.*)', advantage_text, re.DOTALL)
                
                if title_match:
                    title = title_match.group(1).strip()
                    description = title_match.group(2).strip()
                    
                    print(f"Débogage: Titre extrait: '{title}', Description: '{description}'")
                    
                    # Supprimer la ponctuation au début de la description si présente
                    if description and description[0] in [',', '.', ':', ';']:
                        description = description[1:].strip()
                    
                    # Déterminer l'icône en fonction du contenu du titre et de la description
                    icon = determine_icon_for_advantage(title + " " + description)
                    
                    extracted_advantages.append({
                        'icon': icon,
                        'title': title,
                        'text': description
                    })
                    print(f"Avantage extrait - Titre: {title}, Description: {description}")
                else:
                    # Si le format ** ** n'est pas trouvé, utiliser la méthode précédente
                    print(f"Débogage: Format titre** **description non trouvé pour: {advantage_text}")
                    icon = determine_icon_for_advantage(advantage_text)
                    extracted_advantages.append({
                        'icon': icon,
                        'title': get_title_for_advantage(advantage_text),
                        'text': advantage_text
                    })
        else:
            print(f"Débogage: Aucune section AVANTAGES trouvée dans la réponse. Expression régulière utilisée: r'(?:\\d+\\.)?(?:\\s*\\*{{1,2}})?\\s*AVANTAGES\\s*(?:\\*{{1,2}})?\\s*:+\\s*((?:-\\s*.*(?:\\n|$))+)'")
    
    # Si nous avons extrait des avantages, les utiliser
    if len(extracted_advantages) >= 1:
        # S'assurer d'avoir exactement 3 cartes
        if len(extracted_advantages) > 3:
            advantages_to_show = extracted_advantages[:3]
        elif len(extracted_advantages) < 3:
            # Compléter avec des avantages par défaut
            advantages_to_show = extracted_advantages[:]
            
            # Valeurs par défaut si aucun mot-clé n'est trouvé
            default_advantages = [
                {
                    'icon': 'fa-map-marker-alt',
                    'title': 'Emplacement idéal',
                    'text': 'Facilement accessible et situé dans un cadre privilégié'
                },
                {
                    'icon': 'fa-laptop',
                    'title': 'Équipement complet',
                    'text': 'Toutes les technologies nécessaires pour votre événement'
                },
                {
                    'icon': 'fa-concierge-bell',
                    'title': 'Service personnalisé',
                    'text': 'Un accompagnement sur mesure pour votre séminaire'
                }
            ]
            
            # Compléter avec des avantages par défaut qui ne sont pas déjà présents
            default_index = 0
            while len(advantages_to_show) < 3 and default_index < len(default_advantages):
                default_adv = default_advantages[default_index]
                # Vérifier si ce titre d'avantage n'est pas déjà utilisé
                if not any(adv['title'] == default_adv['title'] for adv in advantages_to_show):
                    advantages_to_show.append(default_adv)
                default_index += 1
        else:
            # Exactement 3 avantages trouvés
            advantages_to_show = extracted_advantages
            
        print("Utilisation des avantages extraits de la réponse DeepSeek")
    else:
        print(f"Impossible d'extraire les avantages de la réponse DeepSeek, utilisation de la méthode par mots-clés")
        # Liste de mots-clés et leurs icônes/titres/descriptions associés
        advantage_keywords = {
            # Emplacement et accessibilité
            'accessible': {
                'icon': 'fa-map-marker-alt',
                'title': 'Facilement accessible',
                'text': 'Emplacement stratégique avec accès facile par différents moyens de transport'
            },
            'central': {
                'icon': 'fa-map-marker-alt',
                'title': 'Emplacement central',
                'text': 'Situé au cœur de la région, à proximité des points d\'intérêt'
            },
            'proche': {
                'icon': 'fa-map-marker-alt',
                'title': 'Proximité idéale',
                'text': 'À quelques minutes des principales attractions et commodités'
            },
            'parking': {
                'icon': 'fa-car',
                'title': 'Parking disponible',
                'text': 'Stationnement facile et sécurisé pour tous les participants'
            },
            'gare': {
                'icon': 'fa-train',
                'title': 'Proche des transports',
                'text': 'Facilement accessible en train et autres transports en commun'
            },
            
            # Équipements et technologie
            'équipement': {
                'icon': 'fa-laptop',
                'title': 'Équipement complet',
                'text': 'Toutes les technologies nécessaires pour votre événement professionnel'
            },
            'technologie': {
                'icon': 'fa-laptop',
                'title': 'Technologie avancée',
                'text': 'Systèmes audiovisuels modernes et connexion internet haut débit'
            },
            'wifi': {
                'icon': 'fa-wifi',
                'title': 'WiFi haut débit',
                'text': 'Connexion internet rapide et fiable dans tout l\'établissement'
            },
            'projecteur': {
                'icon': 'fa-tv',
                'title': 'Équipement audiovisuel',
                'text': 'Projecteurs HD, écrans et systèmes sonores professionnels'
            },
            'visioconférence': {
                'icon': 'fa-video',
                'title': 'Visioconférence',
                'text': 'Équipement pour réunions hybrides et connexions à distance'
            },
            
            # Services et personnel
            'service': {
                'icon': 'fa-concierge-bell',
                'title': 'Service personnalisé',
                'text': 'Un accompagnement sur mesure pour votre séminaire'
            },
            'personnel': {
                'icon': 'fa-user-tie',
                'title': 'Personnel attentif',
                'text': 'Équipe professionnelle dédiée à la réussite de votre événement'
            },
            'restauration': {
                'icon': 'fa-utensils',
                'title': 'Restauration sur place',
                'text': 'Options de restauration de qualité adaptées à vos besoins'
            },
            'traiteur': {
                'icon': 'fa-utensils',
                'title': 'Service traiteur',
                'text': 'Repas et pauses gourmandes préparés par des professionnels'
            },
            
            # Environnement et ambiance
            'calme': {
                'icon': 'fa-leaf',
                'title': 'Environnement calme',
                'text': 'Cadre serein propice à la concentration et aux échanges'
            },
            'nature': {
                'icon': 'fa-tree',
                'title': 'Cadre naturel',
                'text': 'Environnement verdoyant pour un séminaire ressourçant'
            },
            'vue': {
                'icon': 'fa-mountain',
                'title': 'Vue panoramique',
                'text': 'Paysages exceptionnels pour inspirer vos équipes'
            },
            'luxe': {
                'icon': 'fa-gem',
                'title': 'Prestations haut de gamme',
                'text': 'Confort et élégance pour un séminaire prestigieux'
            },
            
            # Capacité et configuration
            'grand': {
                'icon': 'fa-users',
                'title': 'Grande capacité',
                'text': 'Espace adapté pour accueillir des groupes importants'
            },
            'modulable': {
                'icon': 'fa-th-large',
                'title': 'Espaces modulables',
                'text': 'Configuration flexible selon vos besoins spécifiques'
            },
            'intime': {
                'icon': 'fa-user-friends',
                'title': 'Cadre intimiste',
                'text': 'Parfait pour les petits groupes et les réunions privées'
            },
            
            # Activités et détente
            'activité': {
                'icon': 'fa-hiking',
                'title': 'Activités team building',
                'text': 'Options variées pour renforcer la cohésion d\'équipe'
            },
            'détente': {
                'icon': 'fa-spa',
                'title': 'Espaces de détente',
                'text': 'Zones de relaxation pour des pauses bien méritées'
            },
            'sport': {
                'icon': 'fa-dumbbell',
                'title': 'Installations sportives',
                'text': 'Équipements pour rester actif pendant votre séjour'
            },
            'spa': {
                'icon': 'fa-spa',
                'title': 'Spa intégré',
                'text': 'Espace bien-être pour se détendre après les réunions'
            }
        }
        
        # Valeurs par défaut si aucun mot-clé n'est trouvé
        default_advantages = [
            {
                'icon': 'fa-map-marker-alt',
                'title': 'Emplacement idéal',
                'text': 'Facilement accessible et situé dans un cadre privilégié'
            },
            {
                'icon': 'fa-laptop',
                'title': 'Équipement complet',
                'text': 'Toutes les technologies nécessaires pour votre événement'
            },
            {
                'icon': 'fa-concierge-bell',
                'title': 'Service personnalisé',
                'text': 'Un accompagnement sur mesure pour votre séminaire'
            }
        ]
        
        # Normaliser le prompt (minuscules, sans accents)
        prompt_lower = prompt.lower()
        
        # Rechercher les mots-clés dans le prompt
        found_advantages = []
        for keyword, advantage in advantage_keywords.items():
            if keyword.lower() in prompt_lower:
                found_advantages.append(advantage)
        
        # Si un lieu est spécifié, ajouter un avantage spécifique au lieu
        if venue_name:
            venue_advantage = {
                'icon': 'fa-building',
                'title': f'Lieu recommandé',
                'text': f'{venue_name} - Parfaitement adapté à vos besoins spécifiques'
            }
            # Vérifier si l'avantage du lieu n'est pas déjà dans la liste
            if not any(adv['title'] == 'Lieu recommandé' for adv in found_advantages):
                found_advantages.append(venue_advantage)
        
        # S'assurer d'avoir exactement 3 cartes
        if len(found_advantages) > 3:
            # Si plus de 3 avantages trouvés, prendre les 3 premiers
            advantages_to_show = found_advantages[:3]
        elif len(found_advantages) < 3:
            # Si moins de 3 avantages trouvés, compléter avec des avantages par défaut
            advantages_to_show = found_advantages[:]
            
            # Compléter avec des avantages par défaut qui ne sont pas déjà présents
            default_index = 0
            while len(advantages_to_show) < 3 and default_index < len(default_advantages):
                default_adv = default_advantages[default_index]
                # Vérifier si ce titre d'avantage n'est pas déjà utilisé
                if not any(adv['title'] == default_adv['title'] for adv in advantages_to_show):
                    advantages_to_show.append(default_adv)
                default_index += 1
        else:
            # Exactement 3 avantages trouvés
            advantages_to_show = found_advantages
    
    # Déboguer le nombre de cartes générées
    print(f"Nombre de cartes d'avantages générées: {len(advantages_to_show)}")
    
    # Générer le HTML
    html = '<div class="advantage-cards-section"><h3 class="advantage-cards-title">Pourquoi choisir ce lieu ?</h3><div class="advantage-cards-container">'
    for advantage in advantages_to_show:
        html += f"""
        <div class="advantage-card">
            <div class="advantage-logo">
                <i class="fas {advantage['icon']}"></i>
            </div>
            <div class="advantage-content">
                <h3 class="advantage-title">{advantage['title']}</h3>
                <p class="advantage-text">{advantage['text']}</p>
            </div>
        </div>
        """
    html += '</div></div>'
    
    return html


def determine_icon_for_advantage(text):
    """
    Détermine l'icône appropriée en fonction du contenu du texte d'avantage.
    
    Args:
        text (str): Le texte de l'avantage
        
    Returns:
        str: Classe d'icône FontAwesome
    """
    text_lower = text.lower()
    
    # Emplacement et accessibilité
    if any(keyword in text_lower for keyword in ['emplacement', 'accès', 'accessible', 'proximité', 'proche', 'central']):
        return 'fa-map-marker-alt'
    
    # Transport et parking
    if any(keyword in text_lower for keyword in ['parking', 'stationnement', 'voiture']):
        return 'fa-car'
    if any(keyword in text_lower for keyword in ['gare', 'train', 'transport']):
        return 'fa-train'
    
    # Technologie et équipement
    if any(keyword in text_lower for keyword in ['équipement', 'technologie', 'technique', 'matériel']):
        return 'fa-laptop'
    if any(keyword in text_lower for keyword in ['wifi', 'internet', 'connexion']):
        return 'fa-wifi'
    if any(keyword in text_lower for keyword in ['projecteur', 'écran', 'vidéo', 'projection']):
        return 'fa-tv'
    if any(keyword in text_lower for keyword in ['visioconférence', 'visio', 'conférence']):
        return 'fa-video'
    
    # Services et personnel
    if any(keyword in text_lower for keyword in ['service', 'assistance', 'accompagnement']):
        return 'fa-concierge-bell'
    if any(keyword in text_lower for keyword in ['personnel', 'équipe', 'staff']):
        return 'fa-user-tie'
    if any(keyword in text_lower for keyword in ['restauration', 'repas', 'nourriture', 'cuisine']):
        return 'fa-utensils'
    
    # Environnement et ambiance
    if any(keyword in text_lower for keyword in ['calme', 'tranquille', 'silencieux', 'paisible']):
        return 'fa-leaf'
    if any(keyword in text_lower for keyword in ['nature', 'vert', 'jardin', 'parc']):
        return 'fa-tree'
    if any(keyword in text_lower for keyword in ['vue', 'panorama', 'paysage']):
        return 'fa-mountain'
    if any(keyword in text_lower for keyword in ['luxe', 'prestige', 'élégant', 'haut de gamme']):
        return 'fa-gem'
    
    # Capacité et configuration
    if any(keyword in text_lower for keyword in ['grand', 'spacieux', 'vaste', 'capacité']):
        return 'fa-users'
    if any(keyword in text_lower for keyword in ['modulable', 'flexible', 'adaptable']):
        return 'fa-th-large'
    if any(keyword in text_lower for keyword in ['intime', 'petit', 'privé']):
        return 'fa-user-friends'
    
    # Activités et détente
    if any(keyword in text_lower for keyword in ['activité', 'animation', 'team building']):
        return 'fa-hiking'
    if any(keyword in text_lower for keyword in ['détente', 'relaxation', 'spa', 'bien-être']):
        return 'fa-spa'
    if any(keyword in text_lower for keyword in ['sport', 'fitness', 'exercice']):
        return 'fa-dumbbell'
    
    # Valeur par défaut
    return 'fa-star'


def get_title_for_advantage(text):
    """
    Génère un titre court pour l'avantage basé sur son contenu.
    
    Args:
        text (str): Le texte de l'avantage
        
    Returns:
        str: Titre court pour l'avantage
    """
    # Limiter à 5 mots maximum
    words = text.split()
    if len(words) <= 5:
        return text
    
    # Extraire les 5 premiers mots et ajouter des points de suspension
    short_title = ' '.join(words[:5])
    
    # S'assurer que le titre se termine par un point ou une virgule
    if short_title[-1] in ['.', ',', '!', '?', ';', ':']:
        short_title = short_title[:-1]
    
    return short_title + '...'


def generate_google_maps_script(place_id):
    """
    Génère le script JavaScript pour afficher une carte Google Maps avec un marqueur personnalisé
    pointant sur le lieu spécifié par son place_id.
    
    Args:
        place_id (str): L'identifiant Google Maps du lieu
        
    Returns:
        str: Le script HTML/JavaScript pour la carte Google Maps
    """
    if not place_id:
        # Si aucun place_id n'est fourni, retourner un message d'erreur
        return """
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                const mapContainer = document.getElementById('map');
                if (mapContainer) {
                    mapContainer.innerHTML = '<div style="display: flex; justify-content: center; align-items: center; height: 100%; background-color: #f3f4f6;"><p>Carte non disponible</p></div>';
                }
            });
        </script>
        """
    
    # Script pour initialiser la carte Google Maps avec le place_id
    return f"""
    <script>
        // Fonction d'initialisation de la carte Google Maps
        function initMap() {{
            // Créer une nouvelle instance de la carte
            const map = new google.maps.Map(document.getElementById('map'), {{
                // Options de la carte
                zoom: 15,
                mapId: 'seminary_map',
                mapTypeControl: false,
                streetViewControl: false,
                fullscreenControl: true,
                zoomControl: true,
                // Options supplémentaires pour masquer les POI et activer le zoom à la molette
                gestureHandling: 'greedy', // Permet de zoomer avec la molette sans la touche Ctrl
                styles: [
                    {{
                        featureType: 'poi',
                        elementType: 'labels',
                        stylers: [{{ visibility: 'off' }}] // Masquer les étiquettes des points d'intérêt
                    }},
                    {{
                        featureType: 'transit',
                        elementType: 'labels',
                        stylers: [{{ visibility: 'off' }}] // Masquer les étiquettes de transport
                    }},
                    {{
                        featureType: 'road',
                        elementType: 'labels.icon',
                        stylers: [{{ visibility: 'off' }}] // Masquer les icônes des routes
                    }}
                ]
            }});
            
            // Créer un service de géocodage pour convertir le place_id en coordonnées
            const geocoder = new google.maps.Geocoder();
            
            // Géocoder le place_id
            geocoder.geocode({{ placeId: '{place_id}' }})
                .then(response => {{
                    if (response.results.length > 0) {{
                        // Récupérer la position du lieu
                        const location = response.results[0].geometry.location;
                        
                        // Centrer la carte sur le lieu
                        map.setCenter(location);
                        
                        // Créer un élément HTML pour le marqueur personnalisé
                        const markerElement = document.createElement('div');
                        markerElement.className = 'custom-marker';
                        markerElement.innerHTML = '<i class="fas fa-map-marker-alt"></i>';
                        
                        // Créer un marqueur avancé avec l'élément HTML personnalisé
                        const marker = new google.maps.marker.AdvancedMarkerElement({{
                            map,
                            position: location,
                            content: markerElement,
                            title: '{{address}}'
                        }});
                        
                        // Remarque : Nous ne définissons plus d'événement de clic pour le marqueur
                        // car nous ne voulons pas afficher la card d'information
                    }} else {{
                        console.error('Aucun résultat trouvé pour ce place_id');
                    }}
                }})
                .catch(error => {{
                    console.error('Erreur lors du géocodage:', error);
                }});
        }}
    </script>
    
    <!-- Chargement de l'API Google Maps avec les bibliothèques nécessaires -->
    <script 
        src="https://maps.googleapis.com/maps/api/js?key={GOOGLE_MAPS_API_KEY}&callback=initMap&libraries=marker&v=beta"
        defer
    ></script>
    """

def extract_recommendation_description(response_text):
    """
    Extrait la description de la recommandation unique de la réponse de l'API DeepSeek.
    
    Args:
        response_text (str): La réponse complète de l'API DeepSeek
        
    Returns:
        str: La description extraite ou une description par défaut si non trouvée
    """
    # Pattern pour trouver la section "Recommandation Unique"
    pattern = r'\*\*Recommandation Unique\*\* : ([^\n]+)'
    
    # Patterns alternatifs
    # 1. Chercher une description dans une section d'avantages
    alt_pattern1 = r'\*\*(Cadre|Confort|Accessibilité|Localisation)[^\*]+\*\* : ([^\n]+)'
    # 2. Extraire le premier paragraphe après "Bonjour" qui décrit souvent le lieu
    alt_pattern2 = r'Bonjour[^!]+!([^!\.]+\.[^\.]+)'
    # 3. Chercher une description générale dans l'introduction
    alt_pattern3 = r'(idéal pour votre séminaire[^\.]+\.[^\.]+)'
    
    # Chercher la correspondance avec le pattern principal
    match = re.search(pattern, response_text)
    
    if match:
        # Extraire et retourner la description
        description = match.group(1).strip()
        print(f"[DEBUG] Description de recommandation unique trouvée: '{description}'")
        return description
    else:
        # Essayer avec le premier pattern alternatif (avantages)
        alt_match1 = re.search(alt_pattern1, response_text)
        if alt_match1:
            title = alt_match1.group(1).strip()
            content = alt_match1.group(2).strip()
            description = f"{content}"
            print(f"[DEBUG] Description extraite de la section '{title}': '{description}'")
            return description
            
        # Essayer avec le deuxième pattern alternatif (intro après bonjour)
        alt_match2 = re.search(alt_pattern2, response_text)
        if alt_match2 and len(alt_match2.group(1).strip()) > 20:
            description = alt_match2.group(1).strip()
            print(f"[DEBUG] Description extraite de l'introduction: '{description}'")
            return description
            
        # Essayer avec le troisième pattern alternatif (mention "idéal pour séminaire")
        alt_match3 = re.search(alt_pattern3, response_text)
        if alt_match3:
            description = alt_match3.group(1).strip()
            print(f"[DEBUG] Description générale extraite: '{description}'")
            return description
            
        # Si aucun pattern ne fonctionne, utiliser une description par défaut
        default_description = "Un lieu idéal pour vos événements professionnels, offrant un cadre à la fois fonctionnel et agréable. Parfaitement situé et équipé pour répondre à tous vos besoins."
        print(f"[DEBUG] Aucune description trouvée, utilisation de la description par défaut.")
        return default_description

@app.route('/')
def home():
    """
    Route principale qui sert la page d'accueil (index.html).
    Modifie le formulaire pour qu'il pointe vers la route '/result' en méthode POST.
    """
    try:
        # Lire le fichier index.html
        with open('index.html', 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Modifier l'action du formulaire et la méthode
        # Remplacer action="creer-seminaire.html" method="get" par action="/result" method="post"
        content = content.replace('action="creer-seminaire.html"', 'action="/result"')
        content = content.replace('method="get"', 'method="post"')
        
        return content
    
    except FileNotFoundError:
        return "Le fichier index.html est introuvable.", 404


@app.route('/result', methods=['POST'])
def result():
    """
    Route qui traite la soumission du formulaire et affiche les résultats.
    1. Récupère la requête de l'utilisateur
    2. Appelle l'API DeepSeek avec les données CSV pertinentes
    3. Extrait le lieu recommandé, recherche ses images et avis
    4. Injecte les résultats, images et avis dans result.html
    5. Retourne la page HTML modifiée
    """
    try:
        # Réinitialiser l'ID de session pour cette nouvelle requête
        api_logger.reset_session()
        
        # Récupérer la requête de l'utilisateur
        prompt = request.form.get('description', '').strip()
        
        # Log pour déboguer la valeur du prompt
        print(f"[DEBUG] Prompt reçu: '{prompt}'")
        
        # Si la requête est vide, rediriger vers la page d'accueil
        if not prompt:
            print("[DEBUG] Prompt vide, redirection vers la page d'accueil")
            return redirect('/')
        
        # Log avant l'appel à l'API
        print("[DEBUG] Appel à l'API DeepSeek avec le prompt:", prompt)
        
        try:
            # Appeler l'API DeepSeek avec la requête de l'utilisateur
            generated_response = call_deepseek_api(prompt)
            
            # Debug: Afficher la réponse générée
            print(f"Longueur de la réponse: {len(generated_response)}")
            print(f"Début de la réponse: {generated_response[:100]}...")
            
            # Si l'API renvoie une erreur, définir recommended_venue à None
            if "ERROR" in generated_response or "Je ne peux pas recommander" in generated_response:
                recommended_venue = None
            else:
                # Extraire le lieu recommandé de la réponse
                recommended_venue = extract_recommended_venue(generated_response)
            
            # Enregistrer la recherche de l'utilisateur
            log_user_search(prompt, recommended_venue)
            
            # Si aucun lieu n'est recommandé, afficher un message d'erreur
            if not recommended_venue:
                return render_template('error.html', 
                                      error_message="Désolé, je n'ai pas pu trouver de lieu correspondant à votre demande. Veuillez essayer une autre requête.")
            
            # Extraire la description de recommandation unique
            recommendation_description = extract_recommendation_description(generated_response)
            
            # Variables par défaut
            venue_address = "Adresse non disponible"
            place_id = None
            
            # Extraire le place_id et l'adresse du lieu recommandé si un lieu a été recommandé
            if recommended_venue:
                print(f"[DEBUG] Recherche des détails pour le lieu recommandé: '{recommended_venue}'")
                for venue in salles_seminaires_data:
                    if venue.get('nom') == recommended_venue:
                        if venue.get('adresse'):
                            venue_address = venue.get('adresse')
                        
                        # Extraction et vérification du place_id
                        venue_place_id = venue.get('place_id')
                        if venue_place_id and venue_place_id.strip():
                            place_id = venue_place_id.strip()
                            print(f"[DEBUG] Place ID trouvé pour {recommended_venue}: {place_id}")
                        else:
                            print(f"[DEBUG] Aucun place_id trouvé pour {recommended_venue} dans le CSV")
                        
                        break
                
                if not place_id:
                    print(f"[DEBUG] Tentative de récupération du place_id via get_venue_place_id pour: {recommended_venue}")
                    # Essayer d'utiliser la fonction dédiée comme fallback
                    place_id = get_venue_place_id(recommended_venue)
                    if place_id:
                        print(f"[DEBUG] Place ID trouvé via get_venue_place_id: {place_id}")
            else:
                print("[DEBUG] Aucun lieu n'a été recommandé par DeepSeek")
            
            # Récupérer les références de photos pour ce lieu
            photo_references = get_photo_references(recommended_venue) if recommended_venue else []
            print(f"Nombre de références de photos trouvées: {len(photo_references)}")
            
            # Générer le HTML du carrousel d'images
            carousel_html = generate_carousel_html(photo_references)
            
            # Récupérer les avis pour ce lieu
            reviews = get_venue_reviews(place_id)
            
            # Générer le HTML du carrousel d'avis
            reviews_carousel_html = generate_reviews_carousel_html(reviews)
            print(f"HTML du carrousel d'avis généré ({len(reviews)} avis)")
            
            # Générer les cartes d'avantages dynamiques en fonction du prompt et de la réponse DeepSeek
            advantage_cards_html = generate_advantage_cards_html(prompt, recommended_venue, generated_response)
            print("Cartes d'avantages dynamiques générées en fonction du prompt et de la réponse DeepSeek")
            
            # Générer le script Google Maps avec le marqueur personnalisé
            google_maps_script = generate_google_maps_script(place_id)
            print("Script Google Maps généré avec le marqueur personnalisé")
            
            # Lire le fichier result.html
            with open('result.html', 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Remplacer les placeholders par les valeurs réelles
            content = content.replace('{{ prompt }}', html.escape(prompt))
            content = content.replace('{{ description }}', generated_response)
            content = content.replace('{{ carousel_images }}', carousel_html)
            content = content.replace('{{ advantage_cards }}', advantage_cards_html)
            content = content.replace('{{ google_maps_script }}', google_maps_script)
            content = content.replace('{{ venue_description }}', recommendation_description)
            
            # Gérer le cas où aucun lieu n'a été recommandé
            if recommended_venue:
                content = content.replace('{{ venue_name }}', recommended_venue)
            else:
                # Si c'est une erreur de l'API, afficher un message approprié
                if "ERROR" in generated_response or "Je ne peux pas recommander" in generated_response:
                    content = content.replace('{{ venue_name }}', "Recommandation temporairement indisponible")
                else:
                    content = content.replace('{{ venue_name }}', "Lieu recommandé")
            
            content = content.replace('{{ venue_address }}', venue_address)  # Garder pour compatibilité
            content = content.replace('{{ reviews_carousel }}', reviews_carousel_html)
            
            return content
        
        except Exception as e:
            print(f"Erreur lors du traitement de la demande: {e}")
            return "Une erreur est survenue lors du traitement de votre demande.", 500
    
    except FileNotFoundError:
        return "Le fichier result.html est introuvable.", 404


@app.route('/venue-details')
def venue_details():
    """
    Route qui affiche les détails d'un lieu spécifique sans passer par l'API DeepSeek.
    1. Récupère le nom du lieu depuis le paramètre 'venue' de l'URL
    2. Recherche ce lieu dans les données CSV
    3. Génère une réponse similaire à celle de l'API DeepSeek
    4. Utilise les mêmes fonctions que la route "/result" pour générer la page de résultats
    """
    try:
        # Récupérer le nom du lieu depuis le paramètre 'venue' de l'URL
        venue_name = request.args.get('venue', '')
        
        print(f"Recherche du lieu: '{venue_name}'")
        
        if not venue_name:
            return redirect('/')
        
        # Rechercher le lieu dans les données CSV avec une comparaison plus flexible
        venue_data = None
        
        # Fonction de normalisation améliorée pour gérer différents types d'apostrophes et d'accents
        def normalize_name(name):
            if not name:
                return ""
            # Convertir en minuscules
            result = name.lower()
            # Remplacer les apostrophes et les caractères spéciaux
            result = result.replace("'", "").replace("'", "").replace("`", "")
            # Remplacer les préfixes courants
            result = result.replace("l'", "l").replace("d'", "d")
            # Remplacer les accents
            result = result.replace("é", "e").replace("è", "e").replace("ê", "e").replace("ë", "e")
            result = result.replace("à", "a").replace("â", "a").replace("ä", "a")
            result = result.replace("ô", "o").replace("ö", "o")
            result = result.replace("ù", "u").replace("û", "u").replace("ü", "u")
            result = result.replace("ç", "c")
            # Supprimer les espaces supplémentaires
            result = " ".join(result.split())
            return result
        
        # Normaliser le nom du lieu recherché
        normalized_venue_name = normalize_name(venue_name)
        print(f"Nom normalisé pour la recherche: '{normalized_venue_name}'")
        
        # Vérifier chaque lieu dans les données CSV
        for venue in salles_seminaires_data:
            csv_venue_name = venue.get('nom', '')
            normalized_csv_name = normalize_name(csv_venue_name)
            
            print(f"Comparaison avec: '{csv_venue_name}' (normalisé: '{normalized_csv_name}')")
            
            # Vérifier si le nom correspond exactement ou partiellement
            if (normalized_csv_name == normalized_venue_name or 
                normalized_venue_name in normalized_csv_name or 
                normalized_csv_name in normalized_venue_name):
                venue_data = venue
                print(f"Lieu trouvé par correspondance de nom: {venue.get('nom')}")
                break
            
            # Vérifier également dans le place_id qui contient souvent le nom complet
            if venue.get('place_id') and normalize_name(venue.get('place_id', '')).find(normalized_venue_name) != -1:
                venue_data = venue
                print(f"Lieu trouvé via place_id: {venue.get('nom')}")
                break
            
            # Vérification spécifique pour "Hôtel Restaurant L'Écho du Lac"
            if "echo du lac" in normalized_csv_name and "hotel" in normalized_csv_name:
                if "echo du lac" in normalized_venue_name and "hotel" in normalized_venue_name:
                    venue_data = venue
                    print(f"Lieu trouvé par correspondance spécifique pour L'Écho du Lac: {venue.get('nom')}")
                    break
        
        # Si le lieu n'est pas trouvé, rediriger vers la page d'accueil
        if not venue_data:
            print(f"Lieu non trouvé: {venue_name}")
            return redirect('/')
        
        # Extraire uniquement l'adresse physique du lieu
        physical_address = venue_data.get('adresse', '')
        
        # Si l'adresse contient trop d'informations, essayer d'extraire uniquement l'adresse physique
        if len(physical_address) > 100 or "Équipements" in physical_address or "Tarifs" in physical_address:
            # Essayer d'extraire l'adresse du champ COMPLET
            complet = venue_data.get('COMPLET', '')
            address_match = re.search(r'Adresse\s*:\s*([^,]+(?:,\s*[^,]+){1,3})', complet)
            if address_match:
                physical_address = address_match.group(1).strip()
            else:
                # Fallback: prendre juste la première partie de l'adresse
                physical_address = physical_address.split(',')[0] if ',' in physical_address else physical_address
        
        # Générer une réponse similaire à celle de l'API DeepSeek
        generated_response = f"""Bonjour ! Je suis ravi de vous présenter {venue_data.get('nom')}, un lieu parfait pour votre séminaire.

Après analyse de vos besoins, je vous recommande vivement {venue_data.get('nom')} qui offre un cadre idéal pour votre événement. 

{venue_data.get('nom')} est un {venue_data.get('type', 'établissement')} situé à {physical_address}. Il peut accueillir jusqu'à {venue_data.get('capacite', 'plusieurs')} personnes et dispose de {venue_data.get('equipements', 'tous les équipements nécessaires')}.

Je vous invite à découvrir ce lieu exceptionnel qui saura répondre à toutes vos attentes. N'hésitez pas à nous contacter pour plus d'informations ou pour réserver dès maintenant.

AVANTAGES:
- **Emplacement stratégique** : Situé à {physical_address}, facilement accessible pour tous vos participants.
- **Équipements professionnels** : {venue_data.get('equipements', 'Tous les équipements nécessaires')} pour garantir le succès de votre événement.
- **Capacité adaptée** : Espace pouvant accueillir jusqu'à {venue_data.get('capacite', 'plusieurs')} personnes, parfait pour votre séminaire.
"""
        
        # Variables par défaut
        venue_address = physical_address
        place_id = venue_data.get('place_id')
        
        # Récupérer les références de photos pour ce lieu
        photo_references = get_photo_references(venue_name)
        print(f"Nombre de références de photos trouvées: {len(photo_references)}")
        
        # Générer le HTML du carrousel d'images
        carousel_html = generate_carousel_html(photo_references)
        
        # Récupérer les avis pour ce lieu
        reviews = get_venue_reviews(place_id)
        
        # Générer le HTML du carrousel d'avis
        reviews_carousel_html = generate_reviews_carousel_html(reviews)
        print(f"HTML du carrousel d'avis généré ({len(reviews)} avis)")
        
        # Générer les cartes d'avantages dynamiques en fonction de la réponse générée
        advantage_cards_html = generate_advantage_cards_html(f"Je cherche {venue_name}", venue_name, generated_response)
        print("Cartes d'avantages dynamiques générées")
        
        # Générer le script Google Maps avec le marqueur personnalisé
        google_maps_script = generate_google_maps_script(place_id)
        print("Script Google Maps généré avec le marqueur personnalisé")
        
        # Lire le fichier result.html
        with open('result.html', 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Remplacer les placeholders par les valeurs réelles
        content = content.replace('{{ prompt }}', html.escape(f"Détails de {venue_name}"))
        content = content.replace('{{ description }}', generated_response)
        content = content.replace('{{ carousel_images }}', carousel_html)
        content = content.replace('{{ advantage_cards }}', advantage_cards_html)
        content = content.replace('{{ venue_name }}', venue_name)
        content = content.replace('{{ venue_address }}', venue_address)
        content = content.replace('{{ reviews_carousel }}', reviews_carousel_html)
        content = content.replace('{{ google_maps_script }}', google_maps_script)
        
        return content
    
    except FileNotFoundError:
        return "Le fichier result.html est introuvable.", 404
    except Exception as e:
        print(f"Erreur lors du traitement de la demande: {e}")
        return "Une erreur est survenue lors du traitement de votre demande.", 500


# Routes pour servir les ressources statiques si nécessaire
@app.route('/<path:filename>')
def serve_static(filename):
    """
    Sert les fichiers statiques (CSS, JavaScript, images, etc.)
    """
    return send_from_directory('.', filename)


# Ajouter une route pour accéder aux logs API (protégée par un mot de passe simple)
@app.route('/api-logs', methods=['GET'])
def view_api_logs():
    """
    Route pour visualiser les logs d'API en mémoire.
    Protégée par un paramètre de requête 'key' pour un accès simple.
    """
    # Clé d'accès simple (à remplacer par une authentification plus robuste en production)
    access_key = request.args.get('key', '')
    debug_key = "seminary_debug"  # Clé simple pour le débogage
    
    if access_key != debug_key:
        return jsonify({"error": "Accès non autorisé"}), 403
    
    # Récupérer le nombre de logs à afficher (par défaut tous)
    count = request.args.get('count')
    if count:
        try:
            count = int(count)
        except ValueError:
            count = None
    
    # Option pour effacer les logs après consultation
    clear_after = request.args.get('clear', 'false').lower() == 'true'
    
    # Récupérer les logs
    logs = api_logger.get_logs(count)
    
    # Effacer les logs si demandé
    if clear_after:
        api_logger.clear_logs()
    
    return jsonify({
        "count": len(logs),
        "session_id": api_logger.session_id,
        "logs": logs
    })

@app.route('/clear-api-logs', methods=['POST'])
def clear_api_logs():
    """
    Route pour effacer les logs d'API en mémoire.
    Protégée par un paramètre de requête 'key' pour un accès simple.
    """
    # Clé d'accès simple (à remplacer par une authentification plus robuste en production)
    access_key = request.args.get('key', '')
    debug_key = "seminary_debug"  # Clé simple pour le débogage
    
    if access_key != debug_key:
        return jsonify({"error": "Accès non autorisé"}), 403
    
    # Effacer les logs
    api_logger.clear_logs()
    
    return jsonify({
        "status": "success",
        "message": "Logs API effacés avec succès"
    })


# Fonction pour enregistrer les recherches des utilisateurs
def log_user_search(prompt, recommended_venue=None):
    """
    Enregistre les recherches des utilisateurs dans un fichier CSV.
    
    Args:
        prompt (str): La requête de l'utilisateur
        recommended_venue (str, optional): Le lieu recommandé par l'IA
    """
    try:
        # Créer le dossier logs s'il n'existe pas
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        # Chemin du fichier CSV
        log_file = 'logs/user_searches.csv'
        
        # Vérifier si le fichier existe déjà
        file_exists = os.path.isfile(log_file)
        
        # Préparer les données à enregistrer
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data = {
            'timestamp': [timestamp],
            'prompt': [prompt],
            'recommended_venue': [recommended_venue if recommended_venue else 'Aucun']
        }
        
        # Créer un DataFrame
        df = pd.DataFrame(data)
        
        # Enregistrer dans le fichier CSV
        if file_exists:
            df.to_csv(log_file, mode='a', header=False, index=False)
        else:
            df.to_csv(log_file, mode='w', header=True, index=False)
            
        print(f"[LOG] Recherche enregistrée: {prompt} -> {recommended_venue}")
    except Exception as e:
        print(f"[ERROR] Impossible d'enregistrer la recherche: {str(e)}")


# Route pour visualiser les statistiques des recherches utilisateurs
@app.route('/search-stats', methods=['GET'])
def search_stats():
    """
    Affiche les statistiques des recherches utilisateurs.
    Nécessite une clé d'accès pour des raisons de sécurité.
    """
    # Vérifier la clé d'accès
    access_key = request.args.get('key', '')
    if access_key != 'seminary_debug':
        return jsonify({"error": "Accès non autorisé"}), 403
    
    try:
        # Vérifier si le fichier de logs existe
        log_file = 'logs/user_searches.csv'
        if not os.path.exists(log_file):
            return jsonify({"message": "Aucune recherche enregistrée"}), 200
        
        # Charger les données
        df = pd.read_csv(log_file)
        
        # Convertir la colonne timestamp en datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Statistiques générales
        total_searches = len(df)
        unique_venues = df['recommended_venue'].nunique()
        searches_without_result = len(df[df['recommended_venue'] == 'Aucun'])
        
        # Statistiques par jour
        df['date'] = df['timestamp'].dt.date
        searches_by_day = df.groupby('date').size().reset_index(name='count')
        searches_by_day['date'] = searches_by_day['date'].astype(str)
        
        # Top 5 des lieux recommandés
        top_venues = df['recommended_venue'].value_counts().head(5).reset_index()
        top_venues.columns = ['venue', 'count']
        
        # Préparer les données pour le graphique
        dates = searches_by_day['date'].tolist()
        counts = searches_by_day['count'].tolist()
        
        # Créer le HTML pour la page de statistiques
        html = f"""
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Statistiques des recherches - Seminary</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body {{ padding: 20px; background-color: #f8f9fa; }}
                .stats-card {{ margin-bottom: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .card-header {{ background-color: #8c1dcb; color: white; border-radius: 10px 10px 0 0 !important; }}
                h1 {{ color: #8c1dcb; }}
                .chart-container {{ height: 300px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="text-center my-4">Statistiques des recherches utilisateurs</h1>
                
                <div class="row">
                    <div class="col-md-4">
                        <div class="card stats-card">
                            <div class="card-header">Total des recherches</div>
                            <div class="card-body">
                                <h2 class="card-title">{total_searches}</h2>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card stats-card">
                            <div class="card-header">Lieux uniques recommandés</div>
                            <div class="card-body">
                                <h2 class="card-title">{unique_venues}</h2>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card stats-card">
                            <div class="card-header">Recherches sans résultat</div>
                            <div class="card-body">
                                <h2 class="card-title">{searches_without_result}</h2>
                                <p class="card-text">({round(searches_without_result/total_searches*100, 1)}% du total)</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row mt-4">
                    <div class="col-md-8">
                        <div class="card stats-card">
                            <div class="card-header">Recherches par jour</div>
                            <div class="card-body">
                                <div class="chart-container">
                                    <canvas id="searchesChart"></canvas>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card stats-card">
                            <div class="card-header">Top 5 des lieux recommandés</div>
                            <div class="card-body">
                                <ul class="list-group">
                                    {''.join([f'<li class="list-group-item d-flex justify-content-between align-items-center">{venue}<span class="badge bg-primary rounded-pill">{count}</span></li>' for venue, count in zip(top_venues['venue'], top_venues['count'])])}
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row mt-4">
                    <div class="col-12">
                        <div class="card stats-card">
                            <div class="card-header">Dernières recherches</div>
                            <div class="card-body">
                                <div class="table-responsive">
                                    <table class="table table-striped">
                                        <thead>
                                            <tr>
                                                <th>Date et heure</th>
                                                <th>Requête</th>
                                                <th>Lieu recommandé</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {''.join([f'<tr><td>{row["timestamp"]}</td><td>{row["prompt"]}</td><td>{row["recommended_venue"]}</td></tr>' for _, row in df.sort_values('timestamp', ascending=False).head(10).iterrows()])}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <script>
                // Graphique des recherches par jour
                const ctx = document.getElementById('searchesChart').getContext('2d');
                const searchesChart = new Chart(ctx, {{
                    type: 'line',
                    data: {{
                        labels: {dates},
                        datasets: [{{
                            label: 'Nombre de recherches',
                            data: {counts},
                            backgroundColor: 'rgba(140, 29, 203, 0.2)',
                            borderColor: 'rgba(140, 29, 203, 1)',
                            borderWidth: 2,
                            tension: 0.1
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {{
                            y: {{
                                beginAtZero: true,
                                ticks: {{
                                    precision: 0
                                }}
                            }}
                        }}
                    }}
                }});
            </script>
        </body>
        </html>
        """
        
        return html
    except Exception as e:
        print(f"[ERROR] Erreur lors de la génération des statistiques: {str(e)}")
        return jsonify({"error": f"Erreur lors de la génération des statistiques: {str(e)}"}), 500


if __name__ == '__main__':
    # Charger les données CSV avant de démarrer le serveur
    print("Chargement initial des données CSV...")
    salles_seminaires_data = parse_salles_seminaires_csv()
    activites_vosges_data = parse_activites_vosges_csv()
    print("Chargement initial des données CSV terminé.")
    
    print("Démarrage du serveur Seminary...")
    print("Accédez à l'application via: http://127.0.0.1:5000/")
    app.run(debug=True) 
