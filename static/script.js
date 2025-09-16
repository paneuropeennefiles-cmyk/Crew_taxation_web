// Fonction pour afficher un message de statut
function setStatus(message) {
    document.getElementById('status-bar').textContent = message;
}

// Fonction pour afficher une notification
function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;

    // Insérer au début du contenu principal
    const mainTab = document.getElementById('tab-main');
    mainTab.insertBefore(notification, mainTab.firstChild);

    // Supprimer la notification après 5 secondes
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// Fonction pour gérer les onglets
document.addEventListener('DOMContentLoaded', function () {
    // Fonction pour gérer le clic sur les onglets
    function handleTabClick(event) {
        if (event.target.classList.contains('tab-button')) {
            // Récupère le conteneur parent des onglets (pour gérer les onglets principaux et les sous-onglets)
            const tabsContainer = event.target.closest('.tabs');
            const tabContentContainer = tabsContainer.parentElement;

            // Récupère l'ID de l'onglet à afficher
            const tabId = event.target.getAttribute('data-tab');

            // Désactive tous les onglets dans ce conteneur
            const tabButtons = tabsContainer.querySelectorAll('.tab-button');
            tabButtons.forEach(button => {
                button.classList.remove('active');
            });

            // Active l'onglet cliqué
            event.target.classList.add('active');

            // Masque tous les contenus d'onglets associés à ce groupe d'onglets
            let tabContents;

            // Pour les onglets principaux, cherche dans le conteneur principal
            if (tabId === 'tab-main' || tabId === 'tab-config') {
                tabContents = document.querySelectorAll('.container > .tab-content');
            }
            // Pour les sous-onglets, cherche dans le conteneur parent spécifique
            else {
                tabContents = tabContentContainer.querySelectorAll('.tab-content');
            }

            tabContents.forEach(content => {
                content.classList.remove('active');
            });

            // Affiche le contenu de l'onglet sélectionné
            const selectedTab = document.getElementById(tabId);
            if (selectedTab) {
                selectedTab.classList.add('active');
            }
        }
    }

    // Ajoute les écouteurs d'événements à tous les boutons d'onglets
    document.querySelectorAll('.tabs').forEach(tabsContainer => {
        tabsContainer.addEventListener('click', handleTabClick);
    });

    // Initialiser les onglets au chargement
    const mainTabs = document.querySelector('.container > .tabs .tab-button.active');
    if (mainTabs) {
        // Simule un clic sur l'onglet principal actif par défaut
        mainTabs.click();

        // Si nous sommes sur l'onglet principal, initialise aussi le sous-onglet
        if (mainTabs.getAttribute('data-tab') === 'tab-main') {
            const subTabs = document.querySelector('#tab-main .tabs .tab-button.active');
            if (subTabs) {
                subTabs.click();
            }
        }
    }
});
