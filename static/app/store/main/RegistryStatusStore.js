Ext.define('MyApp.store.main.RegistryStatusStore', {
	extend: 'Ext.data.Store',
	model: 'MyApp.model.main.RegistryStatusModel',
	proxy: {
		type: 'ajax',
		url: '/viewer/json/statuses/',
		reader: {
			type: 'json',
			rootProperty: 'root'
		}
	},
	autoLoad: true	
})