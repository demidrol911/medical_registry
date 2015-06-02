Ext.define('MyApp.store.service.ServiceProfileStore', {
	extend: 'Ext.data.Store',
	requires: ['MyApp.model.service.ServiceProfileModel'],
	model: 'MyApp.model.service.ServiceProfileModel',
	alias: 'store.service-profile',
	storeId: 'service-profile',
	
	proxy: {
		type: 'ajax',
		url: '/viewer/json/service-profiles/',
		timeout: 200000,
		reader: {
			type: 'json',
			rootProperty: 'profiles'
		}
	},
	autoLoad: true,
	sorters: 'name'
})