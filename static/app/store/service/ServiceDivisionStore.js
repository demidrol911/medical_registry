Ext.define('MyApp.store.service.ServiceDivisionStore', {
	extend: 'Ext.data.Store',
	requires: ['MyApp.model.service.ServiceDivisionModel'],
	model: 'MyApp.model.service.ServiceDivisionModel',
	alias: 'store.service-division',
	storeId: 'service-division',
	sorters: 'name',
	
	proxy: {
		type: 'ajax',
		url: '/viewer/json/service-divisions/',
		timeout: 200000,
		reader: {
			type: 'json',
			rootProperty: 'divisions'
		}
	},
	autoLoad: true
})