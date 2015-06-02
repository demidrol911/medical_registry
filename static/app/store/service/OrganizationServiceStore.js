Ext.define('MyApp.store.service.OrganizationServiceStore', {
	extend: 'Ext.data.Store',
	requires: ['MyApp.model.service.OrganizationServiceModel'],
	model: 'MyApp.model.service.OrganizationServiceModel',
	alias: 'store.organization-services',
	storeId: 'organization-services',
	totalProperty: 'totalCount',

	proxy: {
		type: 'ajax',
		url: '/viewer/json/services/',
		timeout: 99999999,
		reader: {
			type: 'json',
			rootProperty: 'services'
		},
	},
	//groupField: 'event_id',
	listeners: {
		filterchange: function (store, filters, opts) {
			Ext.ComponentQuery.query('#status')[0].update({count: store.getCount()});
		}
				
	},
})