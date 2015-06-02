Ext.define('MyApp.view.service.AdvancedSearchWindow', { 
	extend: 'Ext.window.Window',
	
	alias: 'widget.advanced-search-service-window',
	
	layout: {
		type: 'vbox',
		align : 'stretch',
		pack  : 'start',
	},
	title: 'Расширенный поиск',
	requires: ['MyApp.view.service.AdvancedSearchWindowController'],
	
	controller: 'advanced-search-window-controller',
	
	listeners: {
		afterrender: 'onAfterRender'
	},
	
	items: [
		{
			xtype: 'form',
			bodyPadding: 5,
			
			defaults: {
				anchor: '100%'
			},
			reference: 'advanced-search-form',
			width: 500,
			height: 600,
			defaultType: 'textfield',
			
			items: [{
				fieldLabel: 'Полис',
				name: 'policy',
			}, {
				fieldLabel: 'Фамилия',
				name: 'last_name',
			}, {
				fieldLabel: 'Имя',
				name: 'first_name',
			}, {
				fieldLabel: 'Отчество',
				name: 'middle_name',
			}, {
				xtype: 'datefield',
				fieldLabel: 'Дата рождения',
				name: 'birthdate',
				format: 'd-m-Y',
			}, {
				xtype: 'combobox',
				fieldLabel: 'Условия оказания',
				displayField: 'name',
				valueField: 'name',
				name: 'term',
				store: 'MyApp.store.service.ServiceTermStore',
				queryMode: 'local',
				typeAhead: true,
				anyMatch: true
			}, {
				xtype: 'fieldcontainer',
				layout: {type: 'hbox'},
				fieldLabel: 'Код диагноза',
				combineErrors: true,
				items: [
					{	
						xtype: 'textfield',
						name: 'disease_1',
						margin: '0 5 0 0',
						flex: 1
					}, {
						xtype: 'textfield',
						name: 'disease_2',
						flex: 1
					}
				]
			}, {
				xtype: 'fieldcontainer',
				layout: {type: 'hbox', align: 'stretch'},
				msgTarget: 'side',
				combineErrors: true,
				fieldLabel: 'Код услуги',
				items: [
					{
						xtype: 'textfield',
						name: 'service_1',
						margin: '0 5 0 0',
						format: 'd-m-Y',
						flex: 1
					}, { 
						xtype: 'textfield',
						name: 'service_2',
						format: 'd-m-Y',
						flex: 1
					}, 				
				]
			}, {
				xtype: 'fieldcontainer',
				layout: {type: 'hbox', align: 'stretch'},
				combineErrors: true,
				fieldLabel: 'Дата начала',
				items: [
					{
						xtype: 'datefield',
						name: 'start_date_1',
						margin: '0 5 0 0',
						format: 'd-m-Y',
						flex: 1
					}, { 
						xtype: 'datefield',
						name: 'start_date_2',
						format: 'd-m-Y',
						flex: 1
					}, 				
				]
			}, {
				xtype: 'fieldcontainer',
				layout: {type: 'hbox', align: 'stretch'},
				combineErrors: true,
				fieldLabel: 'Дата окончания',
				items: [
					{
						xtype: 'datefield',
						name: 'end_date_1',
						margin: '0 5 0 0',
						format: 'd-m-Y',
						flex: 1
					}, { 
						xtype: 'datefield',
						name: 'end_date_2',
						format: 'd-m-Y',
						flex: 1
					}, 				
				]
			},	{
				xtype: 'combobox',
				fieldLabel: 'Отделение',
				displayField: 'name',
				valueField: 'code',
				name: 'division',
				store: 'MyApp.store.service.ServiceDivisionStore',
				queryMode: 'local',
				typeAhead: true,
				anyMatch: true
			},	{
				xtype: 'combobox',
				fieldLabel: 'Профиль',
				displayField: 'name',
				name: 'profile',
				queryMode: 'local',
				typeAhead: true,
				anyMatch: true,
				store: 'MyApp.store.service.ServiceProfileStore',
			}			
			],

			buttons: [{
				text: 'Отмена',
			}, {
				text: 'Поехали!',
				formBind: true, 
				disabled: true,
				handler: 'onAdvancedSearchRun'
			}],			
		}
	]
});