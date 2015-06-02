Ext.define('MyApp.view.main.Main', {
    extend: 'Ext.container.Container',

    xtype: 'app-main',

	requires: ['MyApp.view.main.MainController', 'MyApp.view.main.MainViewModel'],
	
	controller: 'main',

	viewModel: {
		type: 'main-viewmodel'
	},
	
	id: 'MainView',
	
	layout: 'border',
	
    items: [
		{
			xtype: 'tabpanel',
			plain: true,
			region: 'center',
			title: 'Счета медицинских организаций',
			requires: ['Ext.grid.filters.Filters', 'Ext.grid.plugin.CellEditing'],					
			
			reference: 'RegistryTabPanel',
			
			items: [
				{
					xtype: 'grid',
					title: 'Юр. лица',
					plugins: [
						'gridfilters', 
						{ptype: 'cellediting', clicksToEdit: 1}
					],
					
					reference: 'OrganizationRegistryGrid',
					store: 'MyApp.store.main.RegistryListStore',

					columns: [
						{text: 'Код', dataIndex: 'organization_code', filter: 'string', width: 140},
						{text: 'Наименование МО', dataIndex: 'organization_name', filter: 'string', width: 440},
						{
							text: 'Статус', 
							dataIndex: 'organization_status', 
							width: 260, 
							filter: 'list',
			
							editor: {
								xtype: 'combobox',
								editable: false,
								store: 'MyApp.store.main.RegistryStatusStore',
								queryMode: 'local',
								displayField: 'name',
								valueField: 'name',
								listeners: {
									change: 'onRegistryListChange'
								},
							},								
						},
						{text: 'Дата загрузки', dataIndex: 'organization_timestamp', xtype: 'datecolumn', filter: true, width: 120, format: 'd-m-Y'},
					],
					
					listeners: {
						itemkeydown: 'onOrganizationListKeyDown',
						itemdblclick: 'onOrganizationListDblClick'
					}
										
				},
				{
					title: 'Подразделения',
					xtype: 'grid',
					plugins: 'gridfilters',		
					reference: 'DepartmentRegistryGrid',
					store: 'MyApp.store.main.DepartmentListStore', 
					columns: [
						{text: 'Код подразделения', dataIndex: 'department_code', filter: 'string', width: 140},
						{text: 'Наименование подразделения', dataIndex: 'department_name', width: 440, filter: 'string'},
						{text: 'Статус', dataIndex: 'department_status', width: 260, filter: 'list'},
						{text: 'Дата загрузки', xtype: 'datecolumn', dataIndex: 'department_timestamp', filter: true, width: 120, format: 'm-d-Y'},
					],
					listeners: {
						itemdblclick: 'onDepartmentListDblClick'
					}
				}
			],
			
			dockedItems: [
				{
					xtype: 'toolbar',
					dock: 'top',
					items: [
						{	
							text: 'Задать период',
							xtype: 'button',
							iconCls: 'select-period-icon',
							scale: 'medium',
							handler: 'onSelectPeriodClick'
						}, {
							text: 'Фильтры',
							xtype: 'button',
							scale: 'medium',
							iconCls: 'filter-icon',
							menu: [
								{text: 'Отобрать подразделения', iconCls: 'filter-add-icon', handler: 'onDepartmentFastFilter'},
								{text: 'Убрать фильтры', iconCls: 'filter-delete-icon', handler: 'onResetFastFilter'}
							]
						}, '->', {

							xtype: 'component',
							itemId: 'current_period',
							tpl: 'Выбранный период: {period}',
							style: 'margin-right:5px; font-weight:bold;'					
					
						}
					]
				},
				{
					xtype: 'toolbar',
					dock: 'bottom',
					items: [
						{
							iconCls: 'accept-icon',
							xtype: 'button',
							id: 'btnAcceptRegistryList',
							text: 'Сохранить', 
							scale: 'medium',
							disabled: true,
							handler: 'onSaveRegistryList'
							
						}, {
							iconCls: 'decline-icon',
							xtype: 'button',
							id: 'btnCancelRegistryList',
							text: 'Отменить', 
							scale: 'medium',
							disabled: true,
							handler: 'onCancelRegistryList'
						}
					]
				}				
				
			],
		},
		{
			title: 'Сводка',
			height: 250
		}
	]
});