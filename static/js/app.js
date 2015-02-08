Ext.application({
    name: 'MyApp',
    appFolder: '/static/js/app/',

    views: ['Main'],
    stores: ['PeriodStore', 'RegistryHeaderStore', 'serviceStore'],
    
    autoCreateViewport: 'MyApp.view.Main',
    launch: function () {
    }
    
});