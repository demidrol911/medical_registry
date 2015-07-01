Ext.define('MyApp.store.main.RegistryImportStore', {
	extend: 'Ext.data.Store',
	model: 'MyApp.model.main.RegistryImportModel',
	alias: 'store.RegistryImportStore',

	proxy: {
		type: 'ajax',
		api: {
			read: '/viewer/json/registries-import/',
		},

		reader: {
			type: 'json',
			rootProperty: 'root'
		}
	},
	autoLoad: true,
})