Ext.define('MyApp.store.RegistryHeaderStore', {
    extend: 'Ext.data.Store',
    requires: ['MyApp.model.RegistryHeaderModel'],
    storeId: 'registriesStore',
    model: 'RegistriesModel',
    autoLoad: true,
    proxy: {
        type: 'ajax',
        url: '/viewer/json/registries/',
        totalProperty: 'total',
        timeout: 260000,
        reader: {
            type: 'json',
            root: 'registries'
        }
    }
    
});
