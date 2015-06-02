Ext.define('MyApp.view.service.ServiceWindow', { 
	extend: 'Ext.window.Window',
	
	alias: 'widget.service-window',
	
	layout: {
		type: 'vbox',
		align : 'stretch',
		pack  : 'start',
	},
	
    height: '95%',
    width: 1280,	

	requires: ['MyApp.view.service.ServiceWindowController', 'MyApp.view.service.ServiceViewModel',
			   'MyApp.view.service.AdvancedSearchWindow'],
	controller: 'servicewindow',
	
	bind: {
		title: 'Реестр {organizationListRecord.organization_name}, период: {organizationListRecord.year}-{organizationListRecord.period}'
	},
	
	listeners: {
		afterrender: 'onAfterRenderWindow'
	},
	
	items: [
		{
			xtype: 'grid',
			plugins: ['gridfilters'],
			requires: [
				'Ext.grid.column.Action',
				'Ext.grid.feature.Grouping',
				'Ext.ux.form.SearchField'
			],
			bind: {store: '{services}'},
			reference: 'service-grid',
			itemId: 'service-grid',

			listeners: {
				afterrender: 'onAfterRenderGrid',
				selectionchange: 'onServiceGridSelectionChange',
				columnshow: 'onRender',
			},

			defaults: {
				sortable: false
			},

			/*
			features: [{
				id: 'serviceGroupFeature',
				ftype: 'groupingsummary',
                groupHeaderTpl: [
                    '{children:this.getLastName} {children:this.getFirstName} {children:this.getMiddleName}, {children:this.getBirthdate}, {children:this.getGender} ',
                    {
                        getLastName: function(c) {
                            return c[0].data.last_name;
                        },
                        getFirstName: function(c) {
                            return c[0].data.first_name;
                        },
                        getMiddleName: function(c) {
                            return c[0].data.middle_name;
                        },
                        getBirthdate: function(c) {
                            return Ext.Date.format(c[0].data.birthdate, 'd-m-Y');
                        },
                        getGender: function(c) {
                            return c[0].data.gender;
                        }
						
                    }
                ],
				hideGroupedHeader: true,
				enableGroupingMenu: false
			}],
			*/
			dockedItems: [{
				xtype: 'toolbar',
				dock: 'top',
				items: [{
					xtype: 'button',
					text: 'Поиск...',
					iconCls: 'filter-icon',
					menu: [
						{text: 'Расширенный', handler: 'onAdvancedSearchClick', iconCls: 'filter-add-icon'},
						{text: 'Сбросить', iconCls: 'filter-delete-icon', handler: 'onAdvancedSearchReset'}
					]
					
				},/* {
					xtype: 'button',
					text: 'Отключить группировку',
					iconCls: '',
					handler: 'onDisableGrouping'
					
				}, */{
					xtype: 'tbfill'
				}, {
					xtype: 'button',
					text: 'Выгрузить в Excel',
					iconCls: 'export-excel-icon',
					handler: 'onExportToExcel'
				}, {
					xtype: 'component',
					itemId: 'status',
					tpl: 'Всего записей: {count}',
					style: 'margin-right:5px'					
				}]
			}],
			flex: 1,
			columns: [
				{
					menuDisabled: true,
					sortable: false,
					width: 8,					
					renderer: function(value, metaData, record) {
						if (record.get('payment_code') == 3) {
							metaData.tdAttr = 'bgcolor=#FF9999';
						} else {
							metaData.tdAttr = 'bgcolor=#B2E0C2';
						}
						
					}
				}, {
					text: 'Случай',
					dataIndex: 'event_id',
					width: 65,
					flex: 1,
				}, {
					text: 'Начало',
					dataIndex: 'start_date',
					xtype: 'datecolumn',
					format: 'd-m-Y',
					width: 100,
					//summaryType: 'min',
					//summaryRenderer: Ext.util.Format.dateRenderer('d-m-Y'),
					flex: 1,
				}, {
					text: 'Окончание',
					dataIndex: 'end_date',
					xtype: 'datecolumn',
					format: 'd-m-Y',
					width: 100,
					//summaryType: 'max',
					//summaryRenderer: Ext.util.Format.dateRenderer('d-m-Y'),					
					flex: 1,
				}, {
					text: 'Отделение',
					dataIndex: 'division_code',
					width: 80,
					flex: 1,
				}, {
					text: 'Услуга',
					dataIndex: 'service_code',
					width: 80,
					filter: {
						type: 'string',
					},
					//summaryType: 'count',
					//summaryRenderer: function(value, summaryData, dataIndex) {
					//	return  'x ' + value;	
					//}
					flex: 1,
				}, {
					text: 'Кол-во',
					dataIndex: 'quantity',
					width: 60,
					flex: 1,
				}, {
					text: 'Осн. дз',
					dataIndex: 'disease_code',
					width: 70,
					filter: {
						type: 'string'
					},
					flex: 1,
				}, {
					text: 'Сопут. дз',
					dataIndex: 'concomitant_disease',
					width: 70,
					filter: {
						type: 'string'
					},
					flex: 1,
				}, {
					text: 'Т/н врача',
					dataIndex: 'worker_code',
					width: 80,
					flex: 1,
				}, {
					text: 'Тариф',
					dataIndex: 'tariff',
					width: 70,
					summaryType: 'sum',
					flex: 1,
				}, {
					text: 'Оплачено',
					dataIndex: 'accepted',
					width: 80,
					summaryType: 'sum',
					flex: 1,
				}, {
					text: 'Комментарий',
					dataIndex: 'service_comment',
					flex: 1,
				}, {
					text: 'Ошибки',
					dataIndex: 'errors',
					width: 80,
					filter: 'list',
					flex: 1,
				}                        
			],
			
		}, {
			title: 'Случай',
			xtype: 'grid',
			store: 'MyApp.store.service.OrganizationEventStore',
			reference: 'event-grid',

			height: 94,

			columns: [
				{
					text: '№',
					dataIndex: 'event_id',
					flex: 1, //
					
				}, {
					text: 'Полис',
					dataIndex: 'policy',
					width: 200,
					tdCls: 'cell-big-font'
				}, {
					text: 'Фамилия',
					dataIndex: 'last_name',
					flex: 3, //width: 140,
					tdCls: 'cell-big-font'
				}, {
					text: 'Имя',
					dataIndex: 'first_name',
					flex: 3, //width: 140,
					tdCls: 'cell-big-font'
				}, {
					text: 'Отчество',
					dataIndex: 'middle_name',
					flex: 4, //width: 140,
					tdCls: 'cell-big-font'
				}, {
					text: 'Дата рождения',
					dataIndex: 'birthdate',
					xtype: 'datecolumn',
					format: 'd-m-Y',
					width: 125,
					tdCls: 'cell-big-font'
				}, {
					text: 'УЕТ/ЕО',
					dataIndex: 'uet',
					flex: 1, //width: 60,
					tdCls: 'cell-big-font'
				}, {
					text: '№ карты',
					dataIndex: 'anamnesis',
					tdCls: 'cell-big-font',
					flex: 2, //
				}, {
					text: 'Комментарий',
					dataIndex: 'event_comment',
					tdCls: 'cell-big-font',
					flex: 2, //
				}/* {
					text: 'Первичный д-з',
					dataIndex: 'initial_disease',
					width: 70,
				}, {
					text: 'Базовый д-з',
					dataIndex: 'basic_disease',
					width: 70,
				}, 
				
				{
					text: 'Сопутствущий д-з',
					dataIndex: 'concomitant_disease',
					width: 70,
				}, {
					text: 'Осложнённый д-з',
					dataIndex: 'complicated_disease',
					width: 70,
				}, */
				
			]/*
			xtype: 'form',
			title: 'пациент',
			reference: 'patient-info-form',
			items: [
				{
					xtype: 'fieldcontainer',
					layout: {type: 'hbox'},
					flex: 1,
					fieldDefaults: {
						margin: '0 5 0 0',
						fieldStyle: 'font-size: 16pt;'
					},					
					items: [
						{
							xtype: 'textfield',
							name: 'last_name',
							//width: 180,
							flex: 5
						}, {
							xtype: 'textfield',
							name: 'first_name',
							//width: 160,
							flex: 4
						}, {
							xtype: 'textfield',
							name: 'middle_name',
							//width: 204,
							flex: 5
						}, {
							xtype: 'datefield',
							name: 'birthdate',
							width: 125,
							format: 'd-m-Y',
							hideTrigger: true
						}, {
							xtype: 'textfield',
							name: 'gender',
							width: 100
						}, {
							xtype: 'textfield',
							name: 'policy',
							width: 205,
						}
					]
				},			
			]*/
		}, {
			xtype: 'form',
			title: 'Подробно',
			reference: 'additional-info-form',
			
			fieldDefaults: {
				labelAlign: 'right',
				editable: false,
				labelStyle: 'font-weight: bold',
			},
			
			bodyPadding: '5 5 0',
			
			defaults: {
				anchor: '100%'
			},

			items: [
				{
					xtype: 'fieldcontainer',
					layout: {type: 'hbox'},
					items: [
						{
							xtype: 'textfield',
							fieldLabel: 'Подразделение',
							name: 'department',
							flex: 1,


						},	{
							xtype: 'textfield',
							fieldLabel: 'Отделение',
							name: 'division_name',
							flex: 2,

						}				
					]
				}, {
					xtype: 'fieldcontainer',
					layout: {type: 'hbox'},
					items: [
						{
							xtype: 'textfield',
							fieldLabel: 'Условия',
							name: 'term',
							flex: 1,

							
						}, {
							xtype: 'textfield',
							fieldLabel: 'Профиль',
							name: 'profile_name',
							flex: 2,

						}					
					]
				}, 
				
				{
					xtype: 'textfield',
					fieldLabel: 'Диагноз',
					name: 'disease_name',
					flex: 1
				},

				{
					xtype: 'fieldcontainer',
					layout: {type: 'hbox'},
					items: [
						{
							xtype:'textfield',
							fieldLabel: 'Услуга',
							name: 'service_name',
							flex: 5
						},
						{
							xtype: 'textfield',
							fieldLabel: 'Результат',
							name: 'result',
							flex: 4,

						}
					]
				}, 
				/*{
					xtype: 'fieldcontainer',
					layout: {type: 'hbox'},
					items: [
						{
							xtype: 'textfield',
							fieldLabel: '№ карты',
							name: 'anamnesis',
							flex: 1
						},
						{
							xtype: 'textfield',
							fieldLabel: 'Сопут. д-з',
							name: 'concomitant_disease',
							flex: 1
						}, {
							xtype: 'textfield',
							fieldLabel: 'Осложн. д-з',
							name: 'complicated_disease',
							flex: 1
						}, {
							xtype: 'textfield',
							fieldLabel: 'Комментарий',
							name: 'event_comment',
							flex: 1							
						}
							
					]
				}*/
			]

		}
	]
	
})