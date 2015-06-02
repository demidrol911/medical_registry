Ext.define('MyApp.store.main.RegistryListStore', {
	extend: 'Ext.data.Store',
	model: 'MyApp.model.main.RegistryListModel',
	alias: 'store.RegistryListStore',

	proxy: {
		type: 'ajax',
		api: {
			read: '/viewer/json/organization-registries/',
			update: '/viewer/json/organization-registries/update/'
		},

		reader: {
			type: 'json',
			rootProperty: 'root'
		},
		writer: {
			type: 'json',
			writeAllFields: true,
		}
	},
	autoLoad: true,
	
	listeners: {
		load: function (me, records, success, opts) {
			var record = records[0];
			Ext.ComponentQuery.query('#current_period')[0].update({period: record.get('year') + '-' + record.get('period')});
		}
	}
})