i18next.init({
  lng: 'en',
  resources: {
    en: {
      translation: {
        "step": {
            "init": {
                "title": "Init",
                "description": "Vault initializing process. Vault is hit with configured number of unseal key shares, so after getting keys app performs unsealing. In the end - checks if Vault was initialized and unsealed."
            },
            "up": {
                "title": "Vault is up",
                "description": "Checking whether the Vault is running and ready to receive requests."
            },
            "auth": {
                "title": "Authentication methods setup",
                "description": "Enabling or disabling HCL configurations with described authentication methods."
            },
            "secret": {
                "title": "Enabling secrets engines",
                "description": "Enabling or disabling HCL configurations with described secret engines. Note that configured secret paths could differ from the standard ones. If you not sure which paths are used, please double-check your deployment configuration."
            },
            "policy": {
                "title": "Policies setup",
                "description": "Enabling or disabling HCL configurations with described policies."
            },
            "role": {
                "title": "Roles setup",
                "description": "Enabling or disabling HCL configurations with described roles."
            },
            "clean": {
                "title": "Clean up",
                "description": "Getting rid of unused temporary data."
            }
        }
      }
    }
  }
});
