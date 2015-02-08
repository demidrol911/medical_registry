myCurrencyRenderer = function(v) {
    return Ext.util.Format.currency(v, ' ', 2);
};

Ext.define('MyApp.view.Main', {
    extend: 'Ext.container.Viewport',
    requires: ['Ext.grid.Panel',
               'Ext.tree.Panel',
               'MyApp.view.RegistriesTree'],
    layout: 'border',
    items: [
        {
            xtype: 'tabpanel',
            region: 'center',
            items: [
                {
                    title: 'Текущий период',
                    closable: true,
                    layout: 'fit',
                    items: [
                        {
                            xtype: 'registries-tree',
                        }
                    ]
                },
            ],          
        },
        {
            xtype: 'periodstree',
            region: 'west'
        }
    ]
});

Ext.define('PeriodsTree', {
    extend: 'Ext.tree.Panel',
    title: 'Отчётный период',
    xtype: 'periodstree',
    width: 200,
    store: 'PeriodStore',
    rootVisible: false,
    split: 'true',
    collapsible: true,
    
    columns: [
        {xtype: 'treecolumn', header: 'Период', dataIndex: 'name', flex: 1}
    ],
    listeners: {
        itemdblclick: function(record, item) {
            if (item.data.leaf) {
                var tabpanel = Ext.ComponentQuery.query('[xtype=tabpanel]')[0];
                var current_store = Ext.create('MyApp.store.RegistryHeaderStore', {
                    proxy: {extraParams: {year: item.parentNode.data.name, period: item.data.name}}
                });

                var tab = tabpanel.add({
                    title: item.parentNode.data.name + ' период ' + item.data.name,
                    layout: 'fit',
                    closable: true,
                    items: [
                        {
                            xtype: 'registries-tree',
                            store: current_store,
                        }
                    ]
                    
                });
                tabpanel.setActiveTab(tab)
                
                //current_store.load();
            }
        }
    }
});