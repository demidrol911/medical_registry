Ext.define('MyApp.model.main.RegistryImportModel', {
	extend: 'Ext.data.Model',
	fields: [
		{name: 'organization', type: 'string'},
		{name: 'filename', type: 'string'},
		{name: 'period', type: 'string'},
		{name: 'status', type: 'string'},
		{name: 'timestamp', type: 'string'},
		{name: 'name', type: 'string'},
	]
})
