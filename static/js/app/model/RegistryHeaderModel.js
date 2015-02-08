Ext.define('MyApp.model.RegistryHeaderModel', {
    extend: 'Ext.data.TreeModel',
    fields: [
        'year',
        'period',
        'code',
        'name',
        'status'
    ]
});