/** @odoo-module **/

odoo.define('education_mobile_and_portal_access.portal_dashboard', function (require) {
    'use strict';

    // This event listens for when the page is loaded or restored from the browser's "Back" button cache
    window.addEventListener('pageshow', function (event) {
        if (event.persisted || (window.performance && window.performance.navigation.type === 2)) {

            // 1. Find all Odoo loading spinners and forcefully hide them
            var loaders = document.querySelectorAll('.o_loading, .fa-spinner, .spinner-border, .o_portal_loader');
            loaders.forEach(function(loader) {
                loader.style.setProperty('display', 'none', 'important');

                // Hide the wrapper if Odoo put the spinner inside a div
                if (loader.parentElement && loader.parentElement.tagName === 'DIV') {
                    loader.parentElement.style.setProperty('display', 'none', 'important');
                }
            });

            // 2. Destroy any Bootstrap tooltips that got stuck on the screen
            var stuckTooltips = document.querySelectorAll('.tooltip');
            stuckTooltips.forEach(function(tooltip) {
                tooltip.remove();
            });
        }
    });

});