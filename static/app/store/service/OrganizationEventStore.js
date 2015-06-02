Ext.define('MyApp.store.service.OrganizationEventStore', {
	extend: 'Ext.data.Store',
	requires: ['MyApp.model.service.OrganizationEventModel'],
	model: 'MyApp.model.service.OrganizationEventModel',
	alias: 'store.organization-event',
	proxy: {
		type: 'memory',
		reader: {
			type: 'json'
		}
	}
})