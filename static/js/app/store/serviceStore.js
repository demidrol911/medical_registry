Ext.define('MyApp.store.serviceStore', {
    extend: 'Ext.data.Store',
    model: 'MyApp.model.serviceModel',
    autoLoad: true,
    totalProperty: 'totalCounf',
    sorters: {property: 'event_id', direction: 'ASC'},

    proxy: {
        type: 'ajax',
        url: '/viewer/json/services/',
        timeout: 260000,
        reader: {
            type: 'json',
            rootProperty: 'services'
        }
    }
});
