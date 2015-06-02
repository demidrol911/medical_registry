Ext.define('MyApp.view.main.PeriodWindow', { 
	extend: 'Ext.window.Window',
	
	requires: ['MyApp.view.main.PeriodWindowController'],
	controller: 'periodwindow',
	
	alias: 'widget.period-window',
	
	layout: 'fit',
	title: 'Выбрать период',
    height: 180,
    width: 300,	

	items: [{
		xtype: 'fieldset',
		title: 'Отчётный период',
		items: [
			{
				fieldLabel: 'Год',
				xtype: 'combobox',
				store: 'MyApp.store.main.YearStore',
				queryMode: 'local',
				valueField: 'abbr',
				displayField: 'name',
				editable: false,
				bind: '{year}'
			},
			{
				fieldLabel: 'Период',
				xtype: 'combobox',
				store: 'MyApp.store.main.PeriodStore',
				queryMode: 'local',
				valueField: 'abbr',
				displayField: 'name',
				editable: false,

				bind: '{period}'
			},

		]

	}],
	buttons: [
		{
			text: 'ОК',
			width: 80,
			handler: 'onConfirmPeriodClick'
		}
	]
})