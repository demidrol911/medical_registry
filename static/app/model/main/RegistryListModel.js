Ext.define('MyApp.model.main.RegistryListModel', {
	extend: 'Ext.data.Model',
	fields: [
		{name: 'organization_code', type: 'string'},
		{name: 'organization_name', type: 'string'},
		{name: 'year', type: 'string'},
		{name: 'period', type: 'string'},
		{name: 'organization_status', type: 'string'},
		{name: 'organization_timestamp', type: 'date', dateReadFormat: 'd-m-Y'},
	]
})