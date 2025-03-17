# Guidelines de développement - Seminary

Ce document définit les règles à suivre pour créer ou modifier des pages du site Seminary afin de garantir une expérience utilisateur cohérente et une maintenance facilitée.

## Structure de base

### Structure HTML 

Chaque nouvelle page doit suivre cette structure de base :

```html
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Seminary - [Titre de la page]</title>
    <link rel="icon" type="image/png" href="favicon.png">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        /* CSS spécifique à la page */
        /* Incluez ici les variables Seminary (voir section Couleurs ci-dessous) */
    </style>
</head>
<body>
    <?php include 'header.php'; ?>
    
    <!-- Contenu principal de la page -->
    <main>
        <!-- Votre contenu ici -->
    </main>
    
    <!-- Footer -->
    <footer>
        <!-- Contenu du footer -->
    </footer>
    
    <!-- Scripts JS -->
    <script>
        // JavaScript spécifique à la page
    </script>
</body>
</html>
```

### Extension des fichiers

- Renommez tous les fichiers `.html` en `.php` pour permettre l'inclusion du header commun
- Pour les pages statiques sans besoin de PHP, vous pouvez conserver l'extension `.html` mais vous devrez copier le header dans chaque page

## Header commun

Toutes les pages doivent utiliser le header commun :

```php
<?php include 'header.php'; ?>
```

## Couleurs

Utilisez systématiquement les variables CSS définies pour Seminary :

```css
:root {
    --primary-color: #7E22CE;
    --primary-light: #A94BE0;
    --primary-dark: #7915A9;
    --primary-transparent: rgba(126, 34, 206, 0.1);
    --white: #FFFFFF;
    --black: #222222;
    --gray-100: #F3F4F6;
    --gray-200: #E5E7EB;
    --gray-300: #D1D5DB;
    --gray-500: #6B7280;
    --gray-700: #374151;
    --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    --shadow-purple: 0 4px 14px -1px rgba(126, 34, 206, 0.3);
    --transition-fast: 0.2s ease;
    --transition-normal: 0.3s ease;
    --transition-slow: 0.5s ease;
}
```

Palette de couleurs à respecter :
- **Couleur principale** : `#7E22CE` (violet)
- **Couleur secondaire** : `#A94BE0` (violet clair)
- **Couleur tertiaire** : `#7915A9` (violet foncé)
- **Fond clair** : `#FFFFFF` ou `#F3F4F6` (blanc ou gris très clair)
- **Texte principal** : `#374151` (gris foncé)
- **Texte secondaire** : `#6B7280` (gris moyen)

## Typographie

- Police principale : `'Poppins', sans-serif`
- Hiérarchie des tailles :
  - Titres H1 : `font-size: 2.5rem; font-weight: 700;`
  - Titres H2 : `font-size: 2rem; font-weight: 700;`
  - Titres H3 : `font-size: 1.5rem; font-weight: 600;`
  - Texte normal : `font-size: 1rem; font-weight: 400;`
  - Texte petit : `font-size: 0.875rem;`
- Interlignage (line-height) : 1.5 à 1.7 pour le texte courant

## Composants UI communs

### Boutons

```css
/* Bouton primaire */
.btn-primary {
    background-color: var(--primary-color);
    color: white;
    padding: 0.75rem 1.5rem;
    border-radius: 8px;
    font-weight: 600;
    font-size: 1rem;
    border: none;
    cursor: pointer;
    transition: all var(--transition-fast);
    box-shadow: var(--shadow-md);
}

.btn-primary:hover {
    background-color: var(--primary-light);
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
}

/* Bouton secondaire */
.btn-secondary {
    background-color: white;
    color: var(--primary-color);
    padding: 0.75rem 1.5rem;
    border-radius: 8px;
    font-weight: 600;
    font-size: 1rem;
    border: 1px solid var(--primary-color);
    cursor: pointer;
    transition: all var(--transition-fast);
}

.btn-secondary:hover {
    background-color: var(--primary-transparent);
}
```

### Cartes

```css
.card {
    background-color: white;
    border-radius: 12px;
    box-shadow: var(--shadow-md);
    overflow: hidden;
    transition: all var(--transition-normal);
}

.card:hover {
    transform: translateY(-5px);
    box-shadow: var(--shadow-lg);
}

.card-content {
    padding: 1.5rem;
}

.card-title {
    font-size: 1.25rem;
    font-weight: 600;
    margin-bottom: 0.75rem;
    color: var(--gray-700);
}
```

## Responsive Design

Toutes les pages doivent être conçues avec une approche "mobile-first".

### Points de rupture (breakpoints) standards

```css
/* Mobile first - styles par défaut pour mobile */

/* Tablettes */
@media (min-width: 768px) {
    /* Styles pour tablettes */
}

/* Desktop */
@media (min-width: 1024px) {
    /* Styles pour desktop */
}

/* Grand desktop */
@media (min-width: 1280px) {
    /* Styles pour grands écrans */
}
```

### Grille flexible

Utilisez Flexbox ou CSS Grid pour les mises en page :

```css
/* Exemple de grille avec Flexbox */
.flex-container {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
}

.flex-item {
    flex: 1 1 100%; /* Full width sur mobile */
}

@media (min-width: 768px) {
    .flex-item {
        flex: 1 1 45%; /* ~2 colonnes sur tablette */
    }
}

@media (min-width: 1024px) {
    .flex-item {
        flex: 1 1 30%; /* ~3 colonnes sur desktop */
    }
}
```

## Images

- Toutes les images doivent être responsive
- Utilisez des images optimisées pour le web (formats WebP si possible, sinon JPG/PNG compressés)
- Toujours spécifier une alternative textuelle avec l'attribut `alt`

```css
img {
    max-width: 100%;
    height: auto;
}
```

## Navigation et liens

- Les liens actifs doivent être visuellement distingués
- Tous les liens doivent avoir un état hover
- Navigation principale toujours accessible

## Bonnes pratiques

### Performance

- Minimisez le nombre de requêtes HTTP
- Optimisez les images
- Placez le CSS critique inline dans le `<head>`
- Chargez les scripts JavaScript non critiques en bas de page ou avec `defer`

### Accessibilité

- Structure sémantique avec des balises HTML5 appropriées (`<header>`, `<main>`, `<footer>`, etc.)
- Contraste suffisant entre le texte et l'arrière-plan
- Éléments interactifs accessibles au clavier
- Textes alternatifs pour les images

### Conventions de nommage CSS

Utilisez une approche BEM simplifiée :
- `.block` pour le composant principal
- `.block__element` pour les éléments à l'intérieur du bloc
- `.block--modifier` pour les variations du bloc

Exemple :
```css
.card /* Bloc */
.card__title /* Élément */
.card--featured /* Modificateur */
```

## Exemple de mise en œuvre

Voici un exemple simple d'une nouvelle page respectant ces guidelines :

```html
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Seminary - Nos services</title>
    <link rel="icon" type="image/png" href="favicon.png">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        :root {
            --primary-color: #7E22CE;
            --primary-light: #A94BE0;
            --primary-dark: #7915A9;
            --primary-transparent: rgba(126, 34, 206, 0.1);
            --white: #FFFFFF;
            --black: #222222;
            --gray-100: #F3F4F6;
            --gray-200: #E5E7EB;
            --gray-300: #D1D5DB;
            --gray-500: #6B7280;
            --gray-700: #374151;
            --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
            --shadow-purple: 0 4px 14px -1px rgba(126, 34, 206, 0.3);
            --transition-fast: 0.2s ease;
            --transition-normal: 0.3s ease;
            --transition-slow: 0.5s ease;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Poppins', sans-serif;
        }
        
        body {
            color: var(--gray-700);
            background-color: var(--white);
            line-height: 1.6;
        }
        
        /* Page spécifique */
        .hero-section {
            padding: 4rem 2rem;
            text-align: center;
            background-color: var(--gray-100);
        }
        
        .hero-title {
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--primary-color);
            margin-bottom: 1rem;
        }
        
        .hero-subtitle {
            font-size: 1.25rem;
            color: var(--gray-500);
            max-width: 800px;
            margin: 0 auto 2rem;
        }
        
        .services-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 2rem;
            max-width: 1200px;
            margin: 3rem auto;
            padding: 0 2rem;
        }
        
        .service-card {
            flex: 1 1 100%;
            background-color: var(--white);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: var(--shadow-md);
            transition: all var(--transition-normal);
        }
        
        .service-card:hover {
            transform: translateY(-5px);
            box-shadow: var(--shadow-lg);
        }
        
        .service-image {
            width: 100%;
            height: 200px;
            object-fit: cover;
        }
        
        .service-content {
            padding: 1.5rem;
        }
        
        .service-title {
            font-size: 1.25rem;
            font-weight: 600;
            color: var(--primary-color);
            margin-bottom: 0.75rem;
        }
        
        .service-description {
            color: var(--gray-500);
            margin-bottom: 1.5rem;
        }
        
        .service-link {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            color: var(--primary-color);
            text-decoration: none;
            font-weight: 600;
            font-size: 0.875rem;
            transition: all var(--transition-fast);
        }
        
        .service-link:hover {
            color: var(--primary-light);
        }
        
        .service-link i {
            transition: transform var(--transition-fast);
        }
        
        .service-link:hover i {
            transform: translateX(3px);
        }
        
        @media (min-width: 768px) {
            .service-card {
                flex: 1 1 calc(50% - 1rem);
            }
        }
        
        @media (min-width: 1024px) {
            .service-card {
                flex: 1 1 calc(33.333% - 1.35rem);
            }
        }
    </style>
</head>
<body>
    <?php include 'header.php'; ?>
    
    <section class="hero-section">
        <h1 class="hero-title">Nos services</h1>
        <p class="hero-subtitle">Découvrez notre gamme complète de services pour rendre votre séminaire d'entreprise inoubliable.</p>
        <a href="#" class="btn-primary">Nous contacter</a>
    </section>
    
    <div class="services-grid">
        <div class="service-card">
            <img src="images/service1.jpg" alt="Recherche de lieux" class="service-image">
            <div class="service-content">
                <h3 class="service-title">Recherche de lieux</h3>
                <p class="service-description">Nous trouvons pour vous le lieu idéal adapté à vos besoins spécifiques et votre budget.</p>
                <a href="#" class="service-link">En savoir plus <i class="fas fa-arrow-right"></i></a>
            </div>
        </div>
        
        <!-- Ajoutez d'autres cartes de services selon le même modèle -->
    </div>
    
    <footer style="background-color: var(--gray-700); color: white; padding: 3rem 2rem; text-align: center;">
        <div style="max-width: 1200px; margin: 0 auto;">
            <p>&copy; 2024 Seminary. Tous droits réservés.</p>
        </div>
    </footer>
</body>
</html>
``` 