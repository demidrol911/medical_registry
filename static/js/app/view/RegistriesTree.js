Ext.define('MyApp.view.RegistriesTree', {
    extend: 'Ext.tree.Panel',
    xtype: 'registries-tree',
    store: 'RegistryHeaderStore',
    rootVisible: false,
    
    columns: [
        {
            xtype: 'treecolumn',
            text: 'Наименование',
            dataIndex: 'name',
            width: 350,
        }, {
            text: 'Код',
            dataIndex: 'code',
        }, {
            text: 'Статус',
            dataIndex: 'status',
            width: 150,
        }
    ],
    listeners: {
        beforeload: function (store, operation, eOpts) {            
            if(store.isLoading()) return false;        
        },
        itemdblclick: function(record, item) {
            if (item.data.leaf) {
                var current_store = Ext.create('MyApp.store.serviceStore', {
                    proxy: {extraParams: {year: item.data.year, period: item.data.period,
                                          organization: item.parentNode.data.code, department: item.data.code}}
                });
                
                var service_window = Ext.create('Ext.window.Window', {
                    title: 'Реестр ' + item.data.name + ' - ' + item.data.year + ' период ' + item.data.period,
                    layout: {
                        type: 'border'
                    },
                    width: 1000,
                    height: 600,
                    
                    viewModel: {
                        stores: {
                            services: current_store
                        }
                    },
                    
                    items: [
                        {
                            region: 'center',
                            xtype: 'grid',
                            requires: [
                                'Ext.grid.filters.Filters',
                                'Ext.grid.feature.Grouping'
                            ],
                            plugins: ['gridfilters'],
                            
                            bind: '{services}',
                            
                            reference: 'allServices',

                            dockedItems: [{
                                xtype: 'toolbar',
                                dock: 'top',
                                items: [{
                                    xtype: 'button',
                                    text: 'Расширенный поиск...'
                                }, {
                                    xtype: 'tbfill'
                                }]
                            }],
                            columns: [
                                {
                                    text: 'Полис', 
                                    dataIndex: 'policy',
                                    width: 120,
                                    filter: {
                                        type: 'string',
                                    }
                                }, {
                                    text: 'Случай №',
                                    dataIndex: 'event_id',
                                    width: 80
                                }, {
                                    text: 'Дата',
                                    dataIndex: 'end_date',
                                    width: 80
                                }, {
                                    text: 'Отделение',
                                    dataIndex: 'division_code',
                                    width: 80
                                }, {
                                    text: 'Услуга',
                                    dataIndex: 'service_code',
                                    width: 80,
                                    filter: {
                                        type: 'string',
                                    }
                                }, {
                                    text: 'Кол-во',
                                    dataIndex: 'quantity',
                                    width: 80
                                }, {
                                    text: 'Диагноз',
                                    dataIndex: 'disease_code',
                                    width: 80,
                                    filter: {
                                        type: 'string'
                                    }
                                }, {
                                    text: 'Номер истории',
                                    dataIndex: 'anamnesis_number',
                                    width: 80
                                }, {
                                    text: 'Т/н врача',
                                    dataIndex: 'worker_code',
                                    width: 80
                                }, {
                                    text: 'Оплачено',
                                    dataIndex: 'accepted_payment',
                                    width: 80
                                }, {
                                    text: 'Ошибки',
                                    dataIndex: 'errors',
                                    width: 80
                                }                          
                            ],
                            listeners: {
                                'render': function(component) {
                                    current_grid = this;
                                    this.setLoading(true);
                                    current_store.load({
                                        callback: function() {
                                            current_grid.setLoading(false);
                                        }
                                    });
                                    
                                }
                                
                            }
                        },
                        {

                            xtype: 'form',
                            region: 'south',
                            bodyPadding: '0 5 0 5',
                            
                            layout: {
                                type: 'vbox',
                                align: 'stretch'
                            },
                            
                            fieldDefaults: {
                                labelWidth: 150,
                            },
                            
                            items: [
                                {
                                    xtype: 'fieldset',
                                    title: 'Пациент',
                                    layout: 'hbox',
                                    defaultType: 'textfield',
                                    
                                    fieldDefaults: {
                                        labelAlign: 'top'
                                    },
                                    
                                    items: [
                                        {
                                            fieldLabel: 'ФИО',
                                            bind: '{allServices.selection.last_name} {allServices.selection.first_name} {allServices.selection.middle_name}',
                                            width: 250,
                                            margin: '0 0 10 5'
                                        },
                                        {
                                            fieldLabel: 'Полис',
                                            bind: '{allServices.selection.policy}',
                                            width: 150,
                                            margin: '0 0 10 5'
                                        },
                                        {
                                            fieldLabel: 'История болезни',
                                            bind: '{allServices.selection.anamnesis_number}',
                                            width: 150,
                                            margin: '0 0 10 5'
                                        },
                                    ]
                                    
                                },
                                {
                                    xtype: 'fieldset',
                                    title: 'Услуга',
                                    layout: {
                                        type: 'vbox',
                                        align: 'stretch'
                                    },
                                    defaultType: 'textfield',
                                    
                                    items: [
                                        {
                                            fieldLabel: 'Наименование услуги',
                                            bind: '{allServices.selection.service_name}',
                                            margin: '0 0 5 5'
                                        }, {
                                            fieldLabel: 'Наименование диагноза',
                                            bind: '{allServices.selection.disease_name}',
                                            margin: '0 0 10 5'
                                        }
                                    ]                                    
                                }


                            ]

                        }
                    ]
                });
                service_window.show();
            } else {
                
            }
        }
    }
});