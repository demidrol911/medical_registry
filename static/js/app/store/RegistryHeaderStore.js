Ext.define('MyApp.store.RegistryHeaderStore', {
    extend: 'Ext.data.TreeStore',
    storeId: 'registriesStore',
    model: 'MyApp.model.RegistryHeaderModel',
    autoLoad: true,
    proxy: {
        type: 'ajax',
        url: '/viewer/json/registries/',
        timeout: 260000,
    }
});
