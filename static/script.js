// -*- coding: utf-8 -*-
// JavaScript pour l'application Crew Taxation Web

// Variables globales
let currentFilename = null;
let currentYear = new Date().getFullYear();
let selectedYearForPrices = currentYear;
let pricesData = [];
let allRotations = []; // Pour stocker toutes les rotations (utilisé pour les filtres)
let selectedPdfFile = null; // Pour stocker le fichier PDF sélectionné

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
            // Récupère le conteneur parent des onglets
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

            // Masque tous les contenus d'onglets associés
            let tabContents;
            if (tabId === 'tab-main' || tabId === 'tab-config') {
                tabContents = document.querySelectorAll('.container > .tab-content');
            } else {
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

            // Charger les données spécifiques à l'onglet Prix/Pays
            if (tabId === 'tab-prices') {
                loadAvailableYears();
            }
        }
    }

    // Ajoute les écouteurs d'événements
    document.querySelectorAll('.tabs').forEach(tabsContainer => {
        tabsContainer.addEventListener('click', handleTabClick);
    });

    // Initialiser les onglets au chargement
    const mainTabs = document.querySelector('.container > .tabs .tab-button.active');
    if (mainTabs) {
        mainTabs.click();
        if (mainTabs.getAttribute('data-tab') === 'tab-main') {
            const subTabs = document.querySelector('#tab-main .tabs .tab-button.active');
            if (subTabs) {
                subTabs.click();
            }
        }
    }

    // Initialiser les événements
    initializeEvents();
    loadConfiguration();
    loadAvailableYearsForProcessing();
});

// Initialisation des événements
function initializeEvents() {
    // Upload de fichier
    const fileInput = document.getElementById('file-excel');
    if (fileInput) {
        fileInput.addEventListener('change', handleFileSelect);
    }

    // Bouton traiter
    const btnProcess = document.getElementById('btn-process');
    if (btnProcess) {
        btnProcess.addEventListener('click', processFile);
    }

    // Bouton exporter
    const btnExport = document.getElementById('btn-export');
    if (btnExport) {
        btnExport.addEventListener('click', exportResults);
    }

    // Bouton exporter PDF
    const btnExportPdf = document.getElementById('btn-export-pdf');
    if (btnExportPdf) {
        btnExportPdf.addEventListener('click', exportPdf);
    }

    // Bouton gérer les prix
    const btnManagePrices = document.getElementById('btn-manage-prices');
    if (btnManagePrices) {
        btnManagePrices.addEventListener('click', openPricesModal);
    }

    // Bouton sauvegarder config
    const btnSaveConfig = document.getElementById('btn-save-config');
    if (btnSaveConfig) {
        btnSaveConfig.addEventListener('click', saveConfiguration);
    }

    // Boutons pour gérer les bases
    const btnAddBase = document.getElementById('btn-add-base');
    if (btnAddBase) {
        btnAddBase.addEventListener('click', () => openAddBaseModal());
    }

    // Fermeture des modals
    const closeButtons = document.querySelectorAll('.close-modal');
    closeButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            this.closest('.modal').style.display = 'none';
        });
    });

    // Boutons dans les modals de prix
    const btnClosePrices = document.getElementById('btn-close-prices');
    if (btnClosePrices) {
        btnClosePrices.addEventListener('click', () => {
            document.getElementById('modal-prices').style.display = 'none';
        });
    }

    const btnSavePrices = document.getElementById('btn-save-prices');
    if (btnSavePrices) {
        btnSavePrices.addEventListener('click', savePrices);
    }

    // Sélecteur d'année dans le modal des prix
    const selectYearPrices = document.getElementById('select-year-prices-tab');
    if (selectYearPrices) {
        selectYearPrices.addEventListener('change', function() {
            selectedYearForPrices = parseInt(this.value);
            loadPrices(selectedYearForPrices);
        });
    }

    // Boutons modal add base
    const btnConfirmAddBase = document.getElementById('btn-confirm-add-base');
    if (btnConfirmAddBase) {
        btnConfirmAddBase.addEventListener('click', confirmAddBase);
    }

    const btnCancelAddBase = document.getElementById('btn-cancel-add-base');
    if (btnCancelAddBase) {
        btnCancelAddBase.addEventListener('click', () => {
            document.getElementById('modal-add-base').style.display = 'none';
        });
    }

    // Boutons modal edit price
    const btnConfirmEditPrice = document.getElementById('btn-confirm-edit-price');
    if (btnConfirmEditPrice) {
        btnConfirmEditPrice.addEventListener('click', confirmEditPrice);
    }

    const btnCancelEditPrice = document.getElementById('btn-cancel-edit-price');
    if (btnCancelEditPrice) {
        btnCancelEditPrice.addEventListener('click', () => {
            document.getElementById('modal-edit-price').style.display = 'none';
        });
    }

    const btnCloseDetails = document.getElementById('btn-close-details');
    if (btnCloseDetails) {
        btnCloseDetails.addEventListener('click', () => {
            document.getElementById('modal-rotation-details').style.display = 'none';
        });
    }

    // Boutons pour dupliquer année
    const btnDuplicateYear = document.getElementById('btn-duplicate-year-tab');
    if (btnDuplicateYear) {
        btnDuplicateYear.addEventListener('click', openDuplicateYearModal);
    }

    const btnConfirmDuplicate = document.getElementById('btn-confirm-duplicate');
    if (btnConfirmDuplicate) {
        btnConfirmDuplicate.addEventListener('click', confirmDuplicateYear);
    }

    const btnCancelDuplicate = document.getElementById('btn-cancel-duplicate');
    if (btnCancelDuplicate) {
        btnCancelDuplicate.addEventListener('click', () => {
            document.getElementById('modal-duplicate-year').style.display = 'none';
        });
    }

    // Boutons import/export prix
    const btnImportPrices = document.getElementById('btn-import-prices-tab');
    if (btnImportPrices) {
        btnImportPrices.addEventListener('click', () => {
            document.getElementById('file-import-prices').click();
        });
    }

    const fileImportPrices = document.getElementById('file-import-prices');
    if (fileImportPrices) {
        fileImportPrices.addEventListener('change', handleImportPrices);
    }

    const btnExportPrices = document.getElementById('btn-export-prices-tab');
    if (btnExportPrices) {
        btnExportPrices.addEventListener('click', exportPrices);
    }

    // Bouton import PDF
    const btnImportPdf = document.getElementById('btn-import-pdf-tab');
    if (btnImportPdf) {
        btnImportPdf.addEventListener('click', () => {
            document.getElementById('pdf-year').value = selectedYearForPrices;
            document.getElementById('pdf-clear-existing').checked = true;
            document.getElementById('file-import-pdf').click();
        });
    }

    const fileImportPdf = document.getElementById('file-import-pdf');
    if (fileImportPdf) {
        fileImportPdf.addEventListener('change', function(event) {
            if (event.target.files[0]) {
                // Stocker le fichier sélectionné
                selectedPdfFile = event.target.files[0];
                document.getElementById('modal-import-pdf').style.display = 'block';
            }
        });
    }

    const btnConfirmImportPdf = document.getElementById('btn-confirm-import-pdf');
    if (btnConfirmImportPdf) {
        btnConfirmImportPdf.addEventListener('click', confirmImportPdf);
    }

    const btnCancelImportPdf = document.getElementById('btn-cancel-import-pdf');
    if (btnCancelImportPdf) {
        btnCancelImportPdf.addEventListener('click', () => {
            document.getElementById('modal-import-pdf').style.display = 'none';
            document.getElementById('file-import-pdf').value = '';
        });
    }

    // Bouton ajouter période
    const btnConfirmAddPeriod = document.getElementById('btn-confirm-add-period');
    if (btnConfirmAddPeriod) {
        btnConfirmAddPeriod.addEventListener('click', confirmAddPeriod);
    }

    const btnCancelAddPeriod = document.getElementById('btn-cancel-add-period');
    if (btnCancelAddPeriod) {
        btnCancelAddPeriod.addEventListener('click', () => {
            document.getElementById('modal-add-period').style.display = 'none';
        });
    }

    // Recherche dans les prix
    const searchCountryPrice = document.getElementById('search-country-price-tab');
    if (searchCountryPrice) {
        searchCountryPrice.addEventListener('input', () => {
            if (pricesData) {
                displayPrices(pricesData);
            }
        });
    }

    // Boutons filtres
    const btnApplyFilters = document.getElementById('btn-apply-filters');
    if (btnApplyFilters) {
        btnApplyFilters.addEventListener('click', applyFilters);
    }

    const btnResetFilters = document.getElementById('btn-reset-filters');
    if (btnResetFilters) {
        btnResetFilters.addEventListener('click', resetFilters);
    }

    // Bouton pour ouvrir la modal d'import d'aéroports
    const btnImportAirportsModal = document.getElementById('btn-import-airports-modal');
    if (btnImportAirportsModal) {
        btnImportAirportsModal.addEventListener('click', () => {
            document.getElementById('modal-import-airports').style.display = 'block';
        });
    }

    // Event listener pour le fichier dans la modal d'import
    const fileAirportsImport = document.getElementById('file-airports-import');
    if (fileAirportsImport) {
        fileAirportsImport.addEventListener('change', function(event) {
            const file = event.target.files[0];
            if (file) {
                selectedAirportsNewFile = file;
                document.getElementById('file-airports-import-name').textContent = file.name;
                document.getElementById('btn-confirm-import-airports').disabled = false;
            }
        });
    }

    // Boutons de la modal d'import d'aéroports
    const btnConfirmImportAirports = document.getElementById('btn-confirm-import-airports');
    if (btnConfirmImportAirports) {
        btnConfirmImportAirports.addEventListener('click', importAirportsNew);
    }

    const btnCancelImportAirports = document.getElementById('btn-cancel-import-airports');
    if (btnCancelImportAirports) {
        btnCancelImportAirports.addEventListener('click', () => {
            document.getElementById('modal-import-airports').style.display = 'none';
        });
    }

    // Event listeners pour la recherche d'aéroports
    const btnSearchAirports = document.getElementById('btn-search-airports');
    if (btnSearchAirports) {
        btnSearchAirports.addEventListener('click', () => {
            currentAirportsPage = 1;
            searchAirports();
        });
    }

    const btnResetSearch = document.getElementById('btn-reset-search');
    if (btnResetSearch) {
        btnResetSearch.addEventListener('click', () => {
            document.getElementById('search-airport').value = '';
            document.getElementById('filter-airport-country').value = '';
            document.getElementById('filter-airport-type').value = '';
            currentAirportsPage = 1;
            searchAirports();
        });
    }

    // Recherche sur "Enter"
    const searchAirport = document.getElementById('search-airport');
    if (searchAirport) {
        searchAirport.addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                currentAirportsPage = 1;
                searchAirports();
            }
        });
    }

    const filterAirportCountry = document.getElementById('filter-airport-country');
    if (filterAirportCountry) {
        filterAirportCountry.addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                currentAirportsPage = 1;
                searchAirports();
            }
        });
    }

    // Pagination
    const btnPrevPage = document.getElementById('btn-prev-page');
    if (btnPrevPage) {
        btnPrevPage.addEventListener('click', () => {
            if (currentAirportsPage > 1) {
                currentAirportsPage--;
                searchAirports();
            }
        });
    }

    const btnNextPage = document.getElementById('btn-next-page');
    if (btnNextPage) {
        btnNextPage.addEventListener('click', () => {
            const maxPages = Math.ceil(totalAirports / airportsPerPage);
            if (currentAirportsPage < maxPages) {
                currentAirportsPage++;
                searchAirports();
            }
        });
    }

    // Charger les aéroports au chargement de l'onglet
    const airportsTabButton = document.querySelector('[data-tab="tab-airports"]');
    if (airportsTabButton) {
        airportsTabButton.addEventListener('click', function() {
            // Charger les aéroports la première fois qu'on ouvre l'onglet
            const tbody = document.getElementById('airports-table-body');
            if (tbody && tbody.children.length === 0) {
                searchAirports();
            }
        });
    }

    // ============================================================================
    // GESTION DE L'AJOUT MANUEL D'AÉROPORT
    // ============================================================================

    // Gestionnaire pour le bouton d'ajout d'aéroport
    const btnAddAirportManual = document.getElementById('btn-add-airport-manual');
    if (btnAddAirportManual) {
        btnAddAirportManual.addEventListener('click', function() {
            // Charger les pays
            loadCountriesForAirport();

            // Réinitialiser le formulaire
            document.getElementById('input-airport-icao').value = '';
            document.getElementById('input-airport-iata').value = '';
            document.getElementById('input-airport-name').value = '';
            document.getElementById('input-airport-country').value = '';
            document.getElementById('input-airport-type').value = 'AD';
            document.getElementById('input-airport-latitude').value = '';
            document.getElementById('input-airport-longitude').value = '';

            // Afficher le modal
            document.getElementById('modal-add-airport').style.display = 'block';
        });
    }

    // Gestionnaire pour le bouton de confirmation d'ajout
    const btnConfirmAddAirport = document.getElementById('btn-confirm-add-airport');
    if (btnConfirmAddAirport) {
        btnConfirmAddAirport.addEventListener('click', function() {
            const icaoCode = document.getElementById('input-airport-icao').value.trim().toUpperCase();
            const iataCode = document.getElementById('input-airport-iata').value.trim().toUpperCase();
            const name = document.getElementById('input-airport-name').value.trim().toUpperCase();
            const country = document.getElementById('input-airport-country').value.trim();
            const type = document.getElementById('input-airport-type').value.trim();
            const latitude = document.getElementById('input-airport-latitude').value.trim();
            const longitude = document.getElementById('input-airport-longitude').value.trim();

            // Validation des champs obligatoires
            if (!icaoCode) {
                showNotification('Le code ICAO est obligatoire', 'error');
                return;
            }

            if (icaoCode.length !== 4) {
                showNotification('Le code ICAO doit contenir exactement 4 caractères', 'error');
                return;
            }

            if (!iataCode) {
                showNotification('Le code IATA est obligatoire', 'error');
                return;
            }

            if (iataCode.length !== 3) {
                showNotification('Le code IATA doit contenir exactement 3 caractères', 'error');
                return;
            }

            if (!name) {
                showNotification('Le nom de l\'aéroport est obligatoire', 'error');
                return;
            }

            if (!country) {
                showNotification('Le pays est obligatoire', 'error');
                return;
            }

            // Préparer les données
            const airportData = {
                icao_code: icaoCode,
                iata_code: iataCode,
                name: name,
                country: country,
                type: type,
                latitude: latitude !== '' ? parseFloat(latitude) : null,
                longitude: longitude !== '' ? parseFloat(longitude) : null
            };

            // Envoyer la requête
            setStatus('Ajout de l\'aéroport en cours...');

            fetch('/add_airport', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(airportData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification(data.message, 'success');
                    document.getElementById('modal-add-airport').style.display = 'none';

                    // Rafraîchir la liste des aéroports
                    searchAirports();
                } else {
                    showNotification(data.message, 'error');
                }
                setStatus('Prêt');
            })
            .catch(error => {
                console.error('Erreur:', error);
                showNotification('Erreur lors de l\'ajout de l\'aéroport', 'error');
                setStatus('Prêt');
            });
        });
    }

    // Gestionnaire pour le bouton d'annulation
    const btnCancelAddAirport = document.getElementById('btn-cancel-add-airport');
    if (btnCancelAddAirport) {
        btnCancelAddAirport.addEventListener('click', function() {
            document.getElementById('modal-add-airport').style.display = 'none';
        });
    }

    // Gestionnaire pour fermer le modal avec la croix
    const modalAddAirport = document.getElementById('modal-add-airport');
    if (modalAddAirport) {
        const closeBtn = modalAddAirport.querySelector('.close-modal');
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                modalAddAirport.style.display = 'none';
            });
        }

        // Fermer le modal en cliquant en dehors
        window.addEventListener('click', function(event) {
            if (event.target === modalAddAirport) {
                modalAddAirport.style.display = 'none';
            }
        });
    }
}

// Charger les années disponibles pour le sélecteur de traitement
function loadAvailableYearsForProcessing() {
    fetch('/get_available_years')
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const select = document.getElementById('select-year');
            if (!select) return;

            select.innerHTML = '';

            // Ajouter l'année courante si elle n'existe pas
            const years = data.years.includes(currentYear) ? data.years : [currentYear, ...data.years];

            years.sort((a, b) => b - a); // Tri décroissant

            years.forEach(year => {
                const option = document.createElement('option');
                option.value = year;
                option.textContent = year;
                if (year === currentYear) {
                    option.selected = true;
                }
                select.appendChild(option);
            });

            // Événement de changement
            select.addEventListener('change', function() {
                currentYear = parseInt(this.value);
            });
        }
    })
    .catch(error => {
        console.error('Erreur lors du chargement des années:', error);
    });
}

// Gestion de la sélection de fichier
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;

    const fileNameSpan = document.getElementById('file-excel-name');
    if (fileNameSpan) {
        fileNameSpan.textContent = file.name;
    }

    // Upload automatique du fichier
    uploadFile(file);
}

// Upload du fichier au serveur
function uploadFile(file) {
    const formData = new FormData();
    formData.append('excel_file', file);

    setStatus('Upload en cours...');

    fetch('/upload_excel', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            currentFilename = data.filename;
            showNotification(`Fichier chargé: ${data.filename} (${data.nb_vols} vols)`, 'success');
            setStatus(`Fichier chargé: ${data.filename}`);

            // Activer le bouton traiter
            const btnProcess = document.getElementById('btn-process');
            if (btnProcess) {
                btnProcess.disabled = false;
            }
        } else {
            showNotification(`Erreur: ${data.message}`, 'error');
            setStatus('Erreur lors du chargement');
        }
    })
    .catch(error => {
        showNotification(`Erreur réseau: ${error}`, 'error');
        setStatus('Erreur réseau');
    });
}

// Traitement du fichier
function processFile() {
    if (!currentFilename) {
        showNotification('Aucun fichier chargé', 'warning');
        return;
    }

    setStatus('Traitement en cours...');

    fetch('/process_file', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            filename: currentFilename,
            year: currentYear
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Traitement terminé avec succès', 'success');
            setStatus('Traitement terminé');

            // Sauvegarder les rotations pour les filtres
            allRotations = data.rotations;

            // Afficher les résultats
            displayResults(data.summary, data.rotations);

            // Activer le bouton export
            const btnExport = document.getElementById('btn-export');
            if (btnExport) {
                btnExport.disabled = false;
            }

            // Basculer automatiquement vers l'onglet "Résumé" pour afficher les résultats
            const summaryTab = document.querySelector('[data-tab="tab-summary"]');
            if (summaryTab) {
                summaryTab.click();
            }
        } else {
            showNotification(`Erreur: ${data.message}`, 'error');
            setStatus('Erreur lors du traitement');
        }
    })
    .catch(error => {
        showNotification(`Erreur réseau: ${error}`, 'error');
        setStatus('Erreur réseau');
    });
}

// Affichage des résultats
function displayResults(summary, rotations) {
    // Afficher le résumé
    const resultsText = document.getElementById('results-text');
    if (resultsText) {
        let html = '<h3>Résumé du traitement</h3>';
        html += `<p><strong>Nombre de rotations:</strong> ${summary.nb_rotations}</p>`;
        html += `<p><strong>Nombre de vols:</strong> ${summary.nb_vols}</p>`;
        html += `<p><strong>Total des indemnités:</strong> ${summary.total_indemnites.toFixed(2)} EUR</p>`;

        // Afficher le nombre de problèmes s'il y en a
        if (summary.nb_problemes && summary.nb_problemes > 0) {
            html += `<p style="color: #d32f2f; font-weight: bold; background-color: #fff3cd; padding: 10px; border-left: 3px solid #d32f2f;">⚠️ <strong>${summary.nb_problemes} indemnité(s) avec problème détecté(s)</strong><br><small>Consultez les détails des rotations ci-dessous pour voir les alertes</small></p>`;
        }

        html += '<h4>Détails par pays</h4>';
        html += '<table class="flight-table">';
        html += '<tr><th>Pays</th><th>Nb indemnités</th><th>Total (EUR)</th></tr>';

        summary.pays_details.forEach(pays => {
            html += `<tr>`;
            html += `<td>${pays.pays}</td>`;
            html += `<td>${pays.count}</td>`;
            html += `<td style="text-align:right">${pays.total.toFixed(2)}</td>`;
            html += `</tr>`;
        });

        html += '</table>';
        resultsText.innerHTML = html;
    }

    // Afficher les rotations
    displayRotations(rotations);
}

// Affichage des rotations (utilisé aussi pour les filtres)
function displayRotations(rotations) {
    const treeRotations = document.getElementById('tree-rotations');
    if (!treeRotations) return;

    treeRotations.innerHTML = '';

    if (!rotations || rotations.length === 0) {
        treeRotations.innerHTML = '<p>Aucune rotation à afficher</p>';
        return;
    }

    rotations.forEach(rotation => {
        // Vérifier si la rotation contient des problèmes
        const hasProblems = rotation.vols.some(vol => vol.diagnostic && vol.diagnostic !== '');

        // Créer l'élément parent
        const parentDiv = document.createElement('div');
        parentDiv.className = 'tree-item parent';

        // Mise en évidence visuelle si problème détecté
        if (hasProblems) {
            parentDiv.innerHTML = `⚠️ ${rotation.id} (${rotation.total.toFixed(2)} EUR) <span style="color: #d32f2f; font-size: 0.9em;">- Problème détecté</span>`;
            parentDiv.style.backgroundColor = '#ffebee';
            parentDiv.style.borderLeft = '4px solid #d32f2f';
            parentDiv.style.fontWeight = 'bold';
        } else {
            parentDiv.textContent = `${rotation.id} (${rotation.total.toFixed(2)} EUR)`;
        }

        parentDiv.style.cursor = 'pointer';

        // Créer le conteneur des vols
        const childrenDiv = document.createElement('div');
        childrenDiv.style.display = 'none';

        rotation.vols.forEach(vol => {
            const childDiv = document.createElement('div');
            childDiv.className = 'tree-item child';

            let volText = '';
            if (vol.jour_sans_vol) {
                volText = `${vol.date} - Jour sans vol - ${vol.ades} - ${vol.indemnite.toFixed(2)} EUR`;
            } else {
                volText = `${vol.date} - ${vol.flight_no} - ${vol.adep} → ${vol.ades} - ${vol.indemnite.toFixed(2)} EUR`;
            }

            // Ajouter le pays s'il existe
            if (vol.pays) {
                volText += ` (${vol.pays})`;
            }

            // Ajouter le diagnostic s'il existe
            if (vol.diagnostic && vol.diagnostic !== '') {
                childDiv.innerHTML = `<span>${volText}</span><br><span style="color: #d32f2f; font-size: 0.9em; margin-left: 20px;">${vol.diagnostic}</span>`;
                childDiv.style.backgroundColor = '#fff3cd'; // Fond jaune pour attirer l'attention
                childDiv.style.borderLeft = '3px solid #d32f2f'; // Bordure rouge
            } else {
                childDiv.textContent = volText;
            }

            childrenDiv.appendChild(childDiv);
        });

        // Toggle visibility on click
        parentDiv.addEventListener('click', () => {
            if (childrenDiv.style.display === 'none') {
                childrenDiv.style.display = 'block';
            } else {
                childrenDiv.style.display = 'none';
            }
        });

        treeRotations.appendChild(parentDiv);
        treeRotations.appendChild(childrenDiv);
    });
}

// Appliquer les filtres
function applyFilters() {
    const rotationFilter = document.getElementById('filter-rotation').value.trim().toUpperCase();
    const dateFromFilter = document.getElementById('filter-date-from').value;
    const dateToFilter = document.getElementById('filter-date-to').value;
    const baseFilter = document.getElementById('filter-base').value.trim().toUpperCase();
    const minAmountFilter = parseFloat(document.getElementById('filter-min-amount').value) || 0;

    // Filtrer les rotations
    const filteredRotations = allRotations.filter(rotation => {
        // Filtre par ID de rotation
        if (rotationFilter && !rotation.id.includes(rotationFilter)) {
            return false;
        }

        // Filtre par montant
        if (rotation.total < minAmountFilter) {
            return false;
        }

        // Filtre par base (vérifie ADEP du premier vol et ADES du dernier)
        if (baseFilter) {
            const firstVol = rotation.vols[0];
            const lastVol = rotation.vols[rotation.vols.length - 1];
            if (!firstVol.adep.includes(baseFilter) && !lastVol.ades.includes(baseFilter)) {
                return false;
            }
        }

        // Filtre par date
        if (dateFromFilter || dateToFilter) {
            const rotationDates = rotation.vols.map(v => {
                // Convertir date format DD-MM-YYYY en YYYY-MM-DD pour comparaison
                const parts = v.date.split('-');
                if (parts.length === 3) {
                    return `${parts[2]}-${parts[1]}-${parts[0]}`;
                }
                return v.date;
            });

            if (dateFromFilter) {
                const hasDateAfterOrEqual = rotationDates.some(d => d >= dateFromFilter);
                if (!hasDateAfterOrEqual) return false;
            }

            if (dateToFilter) {
                const hasDateBeforeOrEqual = rotationDates.some(d => d <= dateToFilter);
                if (!hasDateBeforeOrEqual) return false;
            }
        }

        return true;
    });

    displayRotations(filteredRotations);
    showNotification(`${filteredRotations.length} rotation(s) trouvée(s)`, 'success');
}

// Réinitialiser les filtres
function resetFilters() {
    document.getElementById('filter-rotation').value = '';
    document.getElementById('filter-date-from').value = '';
    document.getElementById('filter-date-to').value = '';
    document.getElementById('filter-base').value = '';
    document.getElementById('filter-min-amount').value = '';

    displayRotations(allRotations);
    showNotification('Filtres réinitialisés', 'success');
}

// Export des résultats
function exportResults() {
    setStatus('Export en cours...');

    fetch('/export_results', {
        method: 'POST'
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.message);
            });
        }
        return response.blob();
    })
    .then(blob => {
        // Créer un lien de téléchargement
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `export_indemnites_${new Date().getTime()}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();

        showNotification('Export réussi', 'success');
        setStatus('Export terminé');
    })
    .catch(error => {
        showNotification(`Erreur: ${error.message}`, 'error');
        setStatus('Erreur lors de l\'export');
    });
}

// Fonction pour exporter en PDF
function exportPdf() {
    setStatus('Génération du PDF en cours...');

    // Récupérer l'année sélectionnée
    const selectYear = document.getElementById('select-year');
    const year = selectYear ? selectYear.value : new Date().getFullYear();

    fetch('/export_pdf', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ year: parseInt(year) })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.message);
            });
        }
        return response.blob();
    })
    .then(blob => {
        // Créer un lien de téléchargement
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `rapport_indemnites_${new Date().getTime()}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();

        showNotification('Rapport PDF généré avec succès', 'success');
        setStatus('PDF généré');
    })
    .catch(error => {
        showNotification(`Erreur: ${error.message}`, 'error');
        setStatus('Erreur lors de la génération du PDF');
    });
}

// Charger la configuration
function loadConfiguration() {
    fetch('/get_config')
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Afficher les bases
            const basesText = document.getElementById('bases-text');
            if (basesText) {
                basesText.value = data.bases.join(', ');
            }
        }
    })
    .catch(error => {
        console.error('Erreur lors du chargement de la configuration:', error);
    });
}

// Sauvegarder la configuration
function saveConfiguration() {
    const basesText = document.getElementById('bases-text');
    if (!basesText) return;

    const basesStr = basesText.value;
    const bases = basesStr.split(',').map(b => b.trim().toUpperCase()).filter(b => b);

    fetch('/save_config', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ bases })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Configuration sauvegardée', 'success');
        } else {
            showNotification(`Erreur: ${data.message}`, 'error');
        }
    })
    .catch(error => {
        showNotification(`Erreur réseau: ${error}`, 'error');
    });
}

// Ouvrir le modal de gestion des prix
function openPricesModal() {
    const modal = document.getElementById('modal-prices');
    modal.style.display = 'block';

    // Charger les années disponibles
    loadAvailableYears();
}

// Charger les années disponibles
function loadAvailableYears() {
    fetch('/get_available_years')
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const select = document.getElementById('select-year-prices-tab');
            if (!select) return;

            select.innerHTML = '';

            // Ajouter l'année courante si elle n'existe pas
            const years = data.years.includes(currentYear) ? data.years : [currentYear, ...data.years];

            years.sort((a, b) => b - a); // Tri décroissant

            years.forEach(year => {
                const option = document.createElement('option');
                option.value = year;
                option.textContent = year;
                select.appendChild(option);
            });

            // Sélectionner la première année ou l'année courante
            selectedYearForPrices = years[0] || currentYear;
            select.value = selectedYearForPrices;

            loadPrices(selectedYearForPrices);
        }
    })
    .catch(error => {
        console.error('Erreur lors du chargement des années:', error);
        loadPrices(currentYear);
    });
}

// Charger les prix pour une année (avec périodes)
function loadPrices(year) {
    fetch(`/get_prices_periods/${year}`)
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            pricesData = data.prices;
            displayPrices(data.prices);
        }
    })
    .catch(error => {
        console.error('Erreur lors du chargement des prix:', error);
        // Fallback sur l'ancienne API
        fetch(`/get_prices/${year}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                pricesData = data.prices;
                displayPricesLegacy(data.prices);
            }
        });
    });
}

// Afficher les prix avec périodes
function displayPrices(prices) {
    const tbody = document.querySelector('#countries-table-tab tbody');
    if (!tbody) return;

    tbody.innerHTML = '';
    const searchTerm = (document.getElementById('search-country-price-tab')?.value || '').toLowerCase();

    prices.forEach(item => {
        // Filtre de recherche
        if (searchTerm && !item.country?.toLowerCase().includes(searchTerm) &&
            !item.icao_prefix?.toLowerCase().includes(searchTerm)) {
            return;
        }

        const tr = document.createElement('tr');

        // Formater les périodes
        let periodsHtml = '';
        if (item.periods && item.periods.length > 0) {
            item.periods.forEach(period => {
                const dateStr = period.valid_from ?
                    `à partir du ${formatDate(period.valid_from)}` :
                    'Prix par défaut';
                periodsHtml += `
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 2px 0; border-bottom: 1px solid #eee;">
                        <span style="font-size: 11px; color: #666;">${dateStr}</span>
                        <span style="font-weight: bold;">${period.price.toFixed(0)} €</span>
                        <button class="btn-icon" onclick="deletePricePeriod('${item.icao_prefix}', '${period.valid_from || ''}', ${period.price})" title="Supprimer">🗑️</button>
                    </div>
                `;
            });
        } else {
            periodsHtml = '<span style="color: #999;">Aucun prix défini</span>';
        }

        tr.innerHTML = `
            <td><strong>${item.country || 'N/A'}</strong></td>
            <td>${item.icao_prefix}</td>
            <td>${item.zone || ''}</td>
            <td style="min-width: 200px;">${periodsHtml}</td>
            <td>
                <button class="btn btn-secondary btn-sm" onclick="openAddPeriodModal('${item.icao_prefix}', '${item.country}')">
                    ➕ Période
                </button>
            </td>
        `;

        tbody.appendChild(tr);
    });
}

// Formater une date
function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('fr-FR');
}

// Afficher les prix (ancienne version sans périodes)
function displayPricesLegacy(prices) {
    const tbody = document.querySelector('#countries-table tbody');
    if (!tbody) return;

    tbody.innerHTML = '';

    prices.forEach(item => {
        const tr = document.createElement('tr');

        tr.innerHTML = `
            <td>${item.country}</td>
            <td>${item.icao_prefix}</td>
            <td>${item.zone || ''}</td>
            <td style="text-align:right">${item.price.toFixed(2)} €</td>
            <td>
                <button class="btn btn-secondary" onclick="editPrice('${item.icao_prefix}', '${item.country}', ${item.price})">
                    Modifier
                </button>
            </td>
        `;

        tbody.appendChild(tr);
    });
}

// Ouvrir le modal pour ajouter une période
function openAddPeriodModal(icaoPrefix, country) {
    document.getElementById('period-icao-prefix').value = icaoPrefix;
    document.getElementById('period-country').value = country;
    document.getElementById('period-valid-from').value = '';
    document.getElementById('period-price').value = '';
    document.getElementById('modal-add-period').style.display = 'block';
}

// Supprimer une période de prix
function deletePricePeriod(icaoPrefix, validFrom, price) {
    if (!confirm(`Supprimer le prix de ${price}€ ?`)) return;

    fetch('/delete_price_period', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            icao_prefix: icaoPrefix,
            year: selectedYearForPrices,
            valid_from: validFrom || null
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Prix supprimé', 'success');
            loadPrices(selectedYearForPrices);
        } else {
            showNotification(`Erreur: ${data.message}`, 'error');
        }
    });
}

// Confirmer l'import du PDF
function confirmImportPdf() {
    if (!selectedPdfFile) {
        showNotification('Aucun fichier sélectionné', 'error');
        return;
    }

    const year = parseInt(document.getElementById('pdf-year').value);
    const clearExisting = document.getElementById('pdf-clear-existing').checked;

    const formData = new FormData();
    formData.append('pdf_file', selectedPdfFile);
    formData.append('year', year);
    formData.append('clear_existing', clearExisting);

    setStatus('Import des barèmes en cours...');

    fetch('/import_pdf_baremes', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            let message = data.message;
            if (data.missing_countries && data.missing_countries.length > 0) {
                message += ` - Pays non trouvés: ${data.missing_countries.slice(0, 5).join(', ')}`;
                if (data.missing_countries.length > 5) {
                    message += ` ... et ${data.missing_countries.length - 5} autres`;
                }
            }
            showNotification(message, 'success');
            document.getElementById('modal-import-pdf').style.display = 'none';
            loadPrices(selectedYearForPrices);
            loadAvailableYears();
            setStatus('Import terminé');
        } else {
            showNotification(`Erreur: ${data.message}`, 'error');
            setStatus('Erreur lors de l\'import');
        }
    })
    .catch(error => {
        showNotification(`Erreur réseau: ${error}`, 'error');
        setStatus('Erreur réseau');
    })
    .finally(() => {
        selectedPdfFile = null;
        document.getElementById('file-import-pdf').value = '';
    });
}

// Confirmer l'ajout d'une période
function confirmAddPeriod() {
    const icaoPrefix = document.getElementById('period-icao-prefix').value;
    const validFrom = document.getElementById('period-valid-from').value || null;
    const price = parseFloat(document.getElementById('period-price').value);

    if (isNaN(price) || price < 0) {
        showNotification('Prix invalide', 'error');
        return;
    }

    fetch('/add_price_period', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            icao_prefix: icaoPrefix,
            year: selectedYearForPrices,
            price: price,
            valid_from: validFrom
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Période ajoutée', 'success');
            document.getElementById('modal-add-period').style.display = 'none';
            loadPrices(selectedYearForPrices);
        } else {
            showNotification(`Erreur: ${data.message}`, 'error');
        }
    })
    .catch(error => {
        showNotification(`Erreur réseau: ${error}`, 'error');
    });
}

// Éditer un prix
function editPrice(icaoPrefix, country, currentPrice) {
    document.getElementById('input-country-name').value = country;
    document.getElementById('input-price').value = currentPrice;
    document.getElementById('input-price').dataset.icaoPrefix = icaoPrefix;

    document.getElementById('modal-edit-price').style.display = 'block';
}

// Confirmer la modification du prix
function confirmEditPrice() {
    const priceInput = document.getElementById('input-price');
    const icaoPrefix = priceInput.dataset.icaoPrefix;
    const newPrice = parseFloat(priceInput.value);

    if (isNaN(newPrice) || newPrice < 0) {
        showNotification('Prix invalide', 'error');
        return;
    }

    fetch('/update_price', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            icao_prefix: icaoPrefix,
            year: selectedYearForPrices,
            price: newPrice
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Prix mis à jour', 'success');
            document.getElementById('modal-edit-price').style.display = 'none';
            loadPrices(selectedYearForPrices);
        } else {
            showNotification(`Erreur: ${data.message}`, 'error');
        }
    })
    .catch(error => {
        showNotification(`Erreur réseau: ${error}`, 'error');
    });
}

// Sauvegarder les prix
function savePrices() {
    showNotification('Prix sauvegardés', 'success');
    document.getElementById('modal-prices').style.display = 'none';
}

// Ouvrir le modal d'ajout de base
function openAddBaseModal() {
    document.getElementById('input-base-code').value = '';
    document.getElementById('modal-add-base').style.display = 'block';
}

// Confirmer l'ajout de base
function confirmAddBase() {
    const input = document.getElementById('input-base-code');
    const code = input.value.trim().toUpperCase();

    if (code.length !== 4 || !/^[A-Z]{4}$/.test(code)) {
        showNotification('Code OACI invalide (4 lettres)', 'error');
        return;
    }

    const basesText = document.getElementById('bases-text');
    const currentBases = basesText.value.split(',').map(b => b.trim()).filter(b => b);

    if (currentBases.includes(code)) {
        showNotification('Cette base existe déjà', 'warning');
        return;
    }

    currentBases.push(code);
    basesText.value = currentBases.join(', ');

    document.getElementById('modal-add-base').style.display = 'none';
    showNotification(`Base ${code} ajoutée`, 'success');
}

// Ouvrir le modal de duplication d'année
function openDuplicateYearModal() {
    const targetYear = selectedYearForPrices + 1;
    document.getElementById('input-target-year').value = targetYear;
    document.getElementById('modal-duplicate-year').style.display = 'block';
}

// Confirmer la duplication d'année
function confirmDuplicateYear() {
    const targetYear = parseInt(document.getElementById('input-target-year').value);

    if (!targetYear || targetYear < 2020 || targetYear > 2100) {
        showNotification('Année invalide', 'error');
        return;
    }

    fetch('/duplicate_year', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            source_year: selectedYearForPrices,
            target_year: targetYear
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            document.getElementById('modal-duplicate-year').style.display = 'none';
            // Recharger les années disponibles
            loadAvailableYears();
        } else {
            showNotification(`Erreur: ${data.message}`, 'error');
        }
    })
    .catch(error => {
        showNotification(`Erreur réseau: ${error}`, 'error');
    });
}

// Import de prix depuis Excel
function handleImportPrices(event) {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('prices_file', file);
    formData.append('year', selectedYearForPrices);

    setStatus('Import en cours...');

    fetch('/import_prices', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            loadPrices(selectedYearForPrices);
            setStatus('Import terminé');
        } else {
            showNotification(`Erreur: ${data.message}`, 'error');
            setStatus('Erreur lors de l\'import');
        }

        // Réinitialiser l'input file
        event.target.value = '';
    })
    .catch(error => {
        showNotification(`Erreur réseau: ${error}`, 'error');
        setStatus('Erreur réseau');
        event.target.value = '';
    });
}

// Export de prix vers Excel
function exportPrices() {
    setStatus('Export des prix en cours...');

    window.location.href = `/export_prices/${selectedYearForPrices}`;

    showNotification('Export des prix réussi', 'success');
    setStatus('Export terminé');
}

// Fermer les modals en cliquant en dehors
window.onclick = function(event) {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
}

// ============================================================================
// GESTION DES AÉROPORTS
// ============================================================================

let selectedAirportsNewFile = null;
let currentAirportsPage = 1;
const airportsPerPage = 100;
let totalAirports = 0;
let currentAirportsFilters = {};

// Import des aéroports NEW (format tab-delimited, uniquement type AD/AH)
function importAirportsNew() {
    if (!selectedAirportsNewFile) {
        showNotification('Aucun fichier sélectionné', 'error');
        return;
    }

    const clearExisting = document.getElementById('clear-airports-before-import').checked;

    let confirmMessage;
    if (clearExisting) {
        confirmMessage = '⚠️ Cette action va SUPPRIMER TOUS les aéroports existants et les remplacer par le nouveau fichier. Continuer ?';
    } else {
        confirmMessage = '💡 Les aéroports seront ajoutés ou mis à jour sans supprimer les existants. Continuer ?';
    }

    if (!confirm(confirmMessage)) {
        return;
    }

    setStatus('Import des aéroports en cours...');
    document.getElementById('btn-confirm-import-airports').disabled = true;

    const formData = new FormData();
    formData.append('airports_file', selectedAirportsNewFile);
    formData.append('clear_existing', clearExisting.toString());

    fetch('/import_airports_new', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message, 'success');
            setStatus('Import terminé');
            document.getElementById('file-airports-import-name').textContent = 'Aucun fichier sélectionné';
            selectedAirportsNewFile = null;
            document.getElementById('file-airports-import').value = '';
            document.getElementById('modal-import-airports').style.display = 'none';

            // Recharger les aéroports
            searchAirports();
        } else {
            showNotification(`Erreur: ${data.message}`, 'error');
            setStatus('Erreur lors de l\'import');
            document.getElementById('btn-confirm-import-airports').disabled = false;
        }
    })
    .catch(error => {
        showNotification(`Erreur réseau: ${error}`, 'error');
        setStatus('Erreur réseau');
        document.getElementById('btn-confirm-import-airports').disabled = false;
    });
}

// Event listeners pour la recherche d'aéroports
document.getElementById('btn-search-airports').addEventListener('click', () => {
    currentAirportsPage = 1;
    searchAirports();
});

document.getElementById('btn-reset-search').addEventListener('click', () => {
    document.getElementById('search-airport').value = '';
    document.getElementById('filter-airport-country').value = '';
    document.getElementById('filter-airport-type').value = '';
    currentAirportsPage = 1;
    searchAirports();
});

// Recherche sur "Enter"
document.getElementById('search-airport').addEventListener('keypress', function(event) {
    if (event.key === 'Enter') {
        currentAirportsPage = 1;
        searchAirports();
    }
});

document.getElementById('filter-airport-country').addEventListener('keypress', function(event) {
    if (event.key === 'Enter') {
        currentAirportsPage = 1;
        searchAirports();
    }
});

// Pagination
document.getElementById('btn-prev-page').addEventListener('click', () => {
    if (currentAirportsPage > 1) {
        currentAirportsPage--;
        searchAirports();
    }
});

document.getElementById('btn-next-page').addEventListener('click', () => {
    const maxPages = Math.ceil(totalAirports / airportsPerPage);
    if (currentAirportsPage < maxPages) {
        currentAirportsPage++;
        searchAirports();
    }
});

// Rechercher les aéroports
function searchAirports() {
    const searchTerm = document.getElementById('search-airport').value.trim();
    const country = document.getElementById('filter-airport-country').value.trim();
    const type = document.getElementById('filter-airport-type').value;

    currentAirportsFilters = {
        search: searchTerm,
        country: country,
        type: type,
        limit: airportsPerPage,
        offset: (currentAirportsPage - 1) * airportsPerPage
    };

    setStatus('Recherche en cours...');

    const params = new URLSearchParams();
    if (searchTerm) params.append('search', searchTerm);
    if (country) params.append('country', country);
    if (type) params.append('type', type);
    params.append('limit', airportsPerPage);
    params.append('offset', currentAirportsFilters.offset);

    fetch(`/search_airports?${params.toString()}`)
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            totalAirports = data.total;
            displayAirports(data.airports);
            updatePagination();
            setStatus('Recherche terminée');
        } else {
            showNotification(`Erreur: ${data.message}`, 'error');
            setStatus('Erreur lors de la recherche');
        }
    })
    .catch(error => {
        showNotification(`Erreur réseau: ${error}`, 'error');
        setStatus('Erreur réseau');
    });
}

// Afficher les aéroports dans la table
function displayAirports(airports) {
    const tbody = document.getElementById('airports-table-body');
    tbody.innerHTML = '';

    if (airports.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 20px; color: #666;">Aucun aéroport trouvé</td></tr>';
        document.getElementById('airports-count').textContent = '';
        return;
    }

    airports.forEach(airport => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>${airport.icao_code}</strong></td>
            <td>${airport.iata_code || '-'}</td>
            <td>${airport.name}</td>
            <td>${airport.country_name || airport.country}</td>
            <td><span class="badge">${airport.type}</span></td>
            <td>${airport.latitude.toFixed(4)}</td>
            <td>${airport.longitude.toFixed(4)}</td>
        `;
        tbody.appendChild(row);
    });

    document.getElementById('airports-count').textContent = `(${totalAirports} aéroport${totalAirports > 1 ? 's' : ''})`;
}

// Mettre à jour la pagination
function updatePagination() {
    const maxPages = Math.ceil(totalAirports / airportsPerPage);
    document.getElementById('page-info').textContent = `Page ${currentAirportsPage} / ${maxPages}`;
    document.getElementById('btn-prev-page').disabled = currentAirportsPage === 1;
    document.getElementById('btn-next-page').disabled = currentAirportsPage >= maxPages;
}

// Charger les aéroports au chargement de l'onglet
const airportsTabButton = document.querySelector('[data-tab="tab-airports"]');
if (airportsTabButton) {
    airportsTabButton.addEventListener('click', function() {
        // Charger les aéroports la première fois qu'on ouvre l'onglet
        const tbody = document.getElementById('airports-table-body');
        if (tbody.children.length === 0) {
            searchAirports();
        }
    });
}

// ============================================================================
// GESTION DE L'AJOUT MANUEL D'AÉROPORT
// ============================================================================

// Fonction pour charger la liste des pays
function loadCountriesForAirport() {
    fetch('/get_countries')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const select = document.getElementById('input-airport-country');
                // Vider le select sauf la première option
                select.innerHTML = '<option value="">-- Sélectionner un pays --</option>';

                // Ajouter les pays
                data.countries.forEach(country => {
                    const option = document.createElement('option');
                    option.value = country.icao_prefix;
                    option.textContent = `${country.country_name} (${country.icao_prefix})`;
                    select.appendChild(option);
                });
            } else {
                showNotification('Erreur lors du chargement des pays', 'error');
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            showNotification('Erreur lors du chargement des pays', 'error');
        });
}
