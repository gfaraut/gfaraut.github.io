(function() {
    // Cette fonction sera exécutée une fois que le DOM est chargé
    function removeSearchElements() {
      // Liste de tous les sélecteurs possibles pour les éléments de recherche
      const searchSelectors = [
        '.bd-search',
        '.search-input',
        '.search-input__wrapper',
        '.search-input__outer',
        'div[role="search"]',
        '.sd-fs-5',
        '.bd-sidebar-primary .sd-input-group',
        '.bd-sidebar-primary form[role="search"]',
        '.bd-search-container',
        'form.bd-search',
        '.search-button',
        '.btn-search',
        '.bd-toc-nav form',
        '.sidebar-search-container',
        '.search-box',
        '#searchbox',
        '.search-field'
      ];
      
      // Supprimer tous les éléments correspondant aux sélecteurs
      searchSelectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        elements.forEach(el => {
          if (el && el.parentNode) {
            el.parentNode.removeChild(el);
          }
        });
      });
    }
    
    // Exécuter au chargement
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', removeSearchElements);
    } else {
      removeSearchElements();
    }
    
    // Exécuter également après un court délai pour gérer les éléments ajoutés dynamiquement
    setTimeout(removeSearchElements, 500);
    setTimeout(removeSearchElements, 1500);
  })();