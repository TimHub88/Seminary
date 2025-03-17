# Guide de conversion des pages HTML en PHP avec header commun

Ce guide explique comment convertir les pages HTML existantes de Seminary pour utiliser le header commun. Suivez ces étapes pour assurer une transition en douceur.

## Étape 1 : Préparer les fichiers

1. Renommez le fichier HTML en PHP
   ```
   index.html → index.php
   search.html → search.php
   contact.html → contact.php
   etc.
   ```

2. Assurez-vous que le fichier `header.php` est bien placé à la racine du site

## Étape 2 : Modifier la structure du fichier

Pour chaque page à convertir :

1. Ouvrez le fichier .php

2. Localisez la section du header :
   ```html
   <!-- Nouveau header -->
   <header class="new-header">
       <!-- ... tout le contenu du header ... -->
   </header>

   <!-- Script pour le menu hamburger -->
   <script>
       <!-- ... le script du menu hamburger ... -->
   </script>
   ```

3. Supprimez tout ce bloc et remplacez-le par :
   ```php
   <?php include 'header.php'; ?>
   ```

4. Supprimez également les styles CSS spécifiques au header dans la section `<style>` :
   ```css
   /* Nouveau header styles */
   .new-header { ... }
   .header-container { ... }
   /* ... tous les styles liés au header ... */
   ```

## Étape 3 : Vérification et test

1. Ouvrez la page dans un navigateur (via un serveur PHP local)
2. Vérifiez que :
   - Le header s'affiche correctement
   - Le menu hamburger fonctionne sur mobile
   - Les liens du header fonctionnent
   - Le style global est cohérent

## Exemple concret

### Avant (page.html) :

```html
<!DOCTYPE html>
<html lang="fr">
<head>
    <!-- ... meta, title, links ... -->
    <style>
        /* ... styles généraux ... */

        /* Nouveau header styles */
        .new-header {
            background-color: #7E22CE;
            position: sticky;
            top: 0;
            z-index: 1000;
            /* ... autres styles ... */
        }
        /* ... tous les autres styles liés au header ... */

        /* Styles spécifiques à la page */
        .page-content {
            /* ... styles du contenu ... */
        }
    </style>
</head>
<body>
    <!-- Nouveau header -->
    <header class="new-header">
        <div class="header-container">
            <!-- ... contenu du header ... -->
        </div>
    </header>

    <!-- Script pour le menu hamburger -->
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            /* ... code du menu hamburger ... */
        });
    </script>
    
    <!-- Contenu de la page -->
    <div class="page-content">
        <!-- ... contenu spécifique ... -->
    </div>
    
    <!-- Footer -->
    <footer>
        <!-- ... contenu du footer ... -->
    </footer>
</body>
</html>
```

### Après (page.php) :

```html
<!DOCTYPE html>
<html lang="fr">
<head>
    <!-- ... meta, title, links ... -->
    <style>
        /* ... styles généraux ... */

        /* Les styles du header ont été supprimés car ils sont dans header.php */

        /* Styles spécifiques à la page */
        .page-content {
            /* ... styles du contenu ... */
        }
    </style>
</head>
<body>
    <?php include 'header.php'; ?>
    
    <!-- Contenu de la page -->
    <div class="page-content">
        <!-- ... contenu spécifique ... -->
    </div>
    
    <!-- Footer -->
    <footer>
        <!-- ... contenu du footer ... -->
    </footer>
</body>
</html>
```

## Résolution des problèmes courants

### Le header ne s'affiche pas

- Vérifiez que le chemin vers `header.php` est correct
- Assurez-vous que PHP est correctement configuré sur votre serveur
- Consultez les logs d'erreur PHP

### Les styles sont en conflit

- Assurez-vous d'avoir supprimé tous les styles dupliqués liés au header
- En cas de conflit, vérifiez la spécificité CSS

### Le menu hamburger ne fonctionne pas

- Vérifiez que le script est bien chargé
- Ouvrez la console du navigateur pour détecter d'éventuelles erreurs JavaScript

## Conseil pour faciliter la maintenance future

À l'avenir, envisagez de créer également un fichier `footer.php` réutilisable pour standardiser le pied de page sur toutes les pages du site.

```php
<!-- À la fin de votre page -->
<?php include 'footer.php'; ?>
```

Cela permettra d'avoir une structure cohérente et facilitera les mises à jour futures. 