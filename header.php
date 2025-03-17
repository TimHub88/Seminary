<?php
/**
 * Header principal de Seminary
 * Ce fichier contient le header réutilisable pour toutes les pages du site
 */
?>
<!-- Styles du header -->
<style>
    /* Variables CSS du header */
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

    /* Style du header */
    .new-header {
        background-color: #7E22CE; /* Violet intense comme sur l'image */
        position: sticky;
        top: 0;
        z-index: 1000;
        width: 100%;
        height: 70px;
        display: flex;
        align-items: center;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    .header-container {
        display: flex;
        justify-content: space-between; /* Garantit que le logo est à gauche et les éléments à droite */
        align-items: center;
        width: 100%;
        padding: 0 30px; /* Utiliser un padding fixe au lieu de max-width et margin */
    }

    .header-logo {
        display: flex;
        align-items: center;
        text-decoration: none;
    }

    .header-logo img {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        margin-right: 10px;
    }

    .header-logo-text {
        font-size: 24px;
        font-weight: 600;
        color: white;
    }

    .header-right {
        display: flex;
        align-items: center;
    }

    .header-nav {
        display: flex;
        gap: 24px;
    }

    .header-nav-link {
        color: white;
        text-decoration: none;
        font-size: 16px;
        font-weight: 500;
        transition: opacity 0.2s;
    }

    .header-nav-link:hover {
        opacity: 0.8;
    }

    .header-actions {
        display: flex;
        gap: 16px;
        margin-left: 30px;
    }

    .header-button {
        text-decoration: none;
        padding: 8px 16px;
        border-radius: 8px;
        font-size: 16px;
        font-weight: 500;
        transition: all 0.2s;
    }

    .header-button-primary {
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.3);
    }

    .header-button-primary:hover {
        background-color: rgba(255, 255, 255, 0.1);
    }

    .header-button-signup {
        background-color: white;
        color: #7E22CE;
    }

    .header-button-signup:hover {
        background-color: #f0f0f0;
    }

    /* Header responsive */
    @media (max-width: 768px) {
        .header-nav {
            display: none;
        }
        
        .header-actions {
            margin-left: 0;
        }
        
        .header-right {
            position: fixed;
            top: 70px;
            left: 0;
            right: 0;
            background-color: #7E22CE;
            flex-direction: column;
            align-items: center;
            padding: 1.5rem;
            transform: translateY(-100%);
            opacity: 0;
            transition: transform 0.3s ease, opacity 0.3s ease;
            z-index: 999;
            box-shadow: 0 5px 10px rgba(0,0,0,0.2);
        }
        
        .header-right.active {
            transform: translateY(0);
            opacity: 1;
        }

        .header-nav {
            display: flex;
            flex-direction: column;
            width: 100%;
            margin-bottom: 1.5rem;
        }
        
        .header-nav-link {
            padding: 0.8rem 0;
            text-align: center;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }

        .header-actions {
            flex-direction: column;
            gap: 0.8rem;
            width: 100%;
        }

        .header-button {
            display: block;
            text-align: center;
            width: 100%;
            padding: 0.8rem 1rem;
            font-size: 1rem;
        }
        
        /* Hamburger menu */
        .hamburger-menu {
            display: block;
            cursor: pointer;
        }
        
        .hamburger-icon {
            width: 30px;
            height: 24px;
            position: relative;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        
        .hamburger-icon span {
            display: block;
            height: 3px;
            width: 100%;
            background-color: white;
            border-radius: 3px;
            transition: all 0.3s ease;
        }
        
        .hamburger-icon.active span:nth-child(1) {
            transform: translateY(10px) rotate(45deg);
        }
        
        .hamburger-icon.active span:nth-child(2) {
            opacity: 0;
        }
        
        .hamburger-icon.active span:nth-child(3) {
            transform: translateY(-10px) rotate(-45deg);
        }
    }
    
    @media (min-width: 769px) {
        .hamburger-menu {
            display: none;
        }
    }
</style>

<!-- Header -->
<header class="new-header">
    <div class="header-container">
        <a href="index.html" class="header-logo">
            <img src="images/logo.png" alt="Seminary Logo">
            <span class="header-logo-text">Seminary</span>
        </a>
        
        <div class="hamburger-menu">
            <div class="hamburger-icon">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
        
        <div class="header-right">
            <nav class="header-nav">
                <a href="#" class="header-nav-link">Fonctionnalités</a>
                <a href="#" class="header-nav-link">Les prix</a>
                <a href="#" class="header-nav-link">Nous contacter</a>
            </nav>
            
            <div class="header-actions">
                <a href="#" class="header-button header-button-primary">Commencer</a>
                <a href="#" class="header-button header-button-signup">S'inscrire</a>
            </div>
        </div>
    </div>
</header>

<!-- Script pour le menu hamburger -->
<script>
    document.addEventListener('DOMContentLoaded', function() {
        const hamburgerMenu = document.querySelector('.hamburger-menu');
        const hamburgerIcon = document.querySelector('.hamburger-icon');
        const headerRight = document.querySelector('.header-right');
        
        if (hamburgerMenu && hamburgerIcon && headerRight) {
            // Attacher l'événement de clic à la zone entière du menu hamburger
            hamburgerMenu.addEventListener('click', function(event) {
                // Empêcher la propagation du clic vers le header
                event.stopPropagation();
                // Empêcher le comportement par défaut (redirection vers index.html)
                event.preventDefault();
                
                // Basculer les classes pour l'animation
                hamburgerIcon.classList.toggle('active');
                headerRight.classList.toggle('active');
            });
            
            // Ajouter z-index pour s'assurer que le menu est au-dessus des autres éléments
            hamburgerMenu.style.position = 'relative';
            hamburgerMenu.style.zIndex = '1001';
        }
    });
</script> 