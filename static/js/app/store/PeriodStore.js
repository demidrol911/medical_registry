Ext.define('MyApp.store.PeriodStore', {
    extend: 'Ext.data.TreeStore',
    model: 'MyApp.model.PeriodModel',
    proxy: {
        type: 'ajax',
        url: '/viewer/json/periods/',
    },
    lazyFill: true
});